"""Generate a case-independent communication prompt once per model/profile."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from config.hofsted import HOFSTEDE_DIMENSIONS, SHARED_ANSWER_RULES
from config import DEFAULT_SEED, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS

DESIGN_SYSTEM = """Create a reusable communication-style prompt for a healthcare question-answering assistant.
The patient characteristics are data, not an answer template. Interpret their combined definitions and values yourself.
Write concrete instructions for tone, framing, emphasis, and organisation suitable for this patient.
Do not answer a medical question or invent a patient case. Do not include medical facts or treatment advice.
The instructions must preserve evidence, clinical meaning, and uncertainty; adaptation must never invent facts.
Do not require particular clinical content, family involvement, follow-up, or reassurance when unsupported.
Do not repeat the dimension definitions or numerical values. Do not mention culture or dimensions in the eventual patient answer.
Return only a reusable prompt of at most 250 words, without a preamble or analysis."""


def design_input(profile):
    if profile.get('culture_condition') == 'none':
        return ('No cultural characteristics are supplied. Create a general professional communication prompt. '
                'Do not infer cultural preferences or introduce cultural dimensions.')
    return json.dumps({
        'value_meaning': {'0': 'low end', '0.5': 'neutral midpoint', '1': 'high end'},
        'characteristics': [dict(dimension=k, definition=v['definition'], value=profile['hofstede'][k])
                            for k, v in HOFSTEDE_DIMENSIONS.items()],
    }, ensure_ascii=False, indent=2)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def prepare_profile_prompts(llm, models, profiles, output_path, reuse_path=None):
    """Freeze prompts for this run; explicitly supplied caches must match all inputs."""
    saved = json.loads(Path(reuse_path).read_text(encoding='utf-8')) if reuse_path else None
    bundle = {'schema_version': 1, 'stage': 'profile_prompt_generation', 'models': {}}
    prompts = {}
    for model in models:
        bundle['models'][model] = {}
        prompts[model] = {}
        for profile in profiles:
            pid = profile['profile_id']
            user = design_input(profile)
            request = dict(model=model, profile=profile, system_prompt=DESIGN_SYSTEM,
                           user_prompt=user, seed=DEFAULT_SEED, temperature=DEFAULT_TEMPERATURE,
                           max_tokens=DEFAULT_MAX_TOKENS, shared_answer_rules=SHARED_ANSWER_RULES)
            signature = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            if saved is not None:
                record = saved.get('models', {}).get(model, {}).get(pid)
                if not record or record.get('signature') != signature:
                    raise ValueError(f'Cached prompt missing or incompatible: {model} / {pid}')
                raw = record.get('raw_response', '')
            else:
                print(f'Creating profile prompt: {model} / {pid}')
                raw = llm.generate(model, DESIGN_SYSTEM, user)
            valid = isinstance(raw, str) and bool(raw.strip()) and not raw.lstrip().startswith('[ERROR]')
            if valid and len(raw.split()) > 250:
                valid = False
            final = (SHARED_ANSWER_RULES + '\n\nCommunication instructions:\n' + raw.strip()
                     + '\n\nThe shared answer rules above take precedence over communication instructions.') if valid else None
            record = dict(request=request, signature=signature, raw_response=raw,
                          answer_system_prompt=final, status='ready' if valid else 'failed',
                          reused=bool(saved))
            bundle['models'][model][pid] = record
            write_json(output_path, bundle)  # Persist every generated prompt before proceeding.
            if not valid:
                raise ValueError(f'Invalid profile prompt: {model} / {pid}; inspect {output_path}')
            prompts[model][pid] = final
    return prompts


def resolve_prompt(prompts, model, profile_id):
    # Flat mapping supports older direct callers; new runs always use model-specific maps.
    return prompts[model][profile_id] if model in prompts else prompts[profile_id]

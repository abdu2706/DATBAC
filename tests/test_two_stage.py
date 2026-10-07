import argparse
import json
import tempfile
import unittest
from pathlib import Path
from config import HOFSTEDE_PROFILES
from profile_prompt_cache import prepare_profile_prompts
from subtasks.runner import SubtaskRunner
from main import run_batch


class RecordingLLM:
    def __init__(self):
        self.calls = []
    def generate(self, model, system, user):
        self.calls.append((model, system, user))
        if system.startswith('Create a reusable'):
            return f'Use clear professional phrasing. Prompt {len(self.calls)} for {model}.'
        return 'The note does not establish a cause.'


class TwoStageTests(unittest.TestCase):
    def test_generate_once_route_by_model_and_reuse_without_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            llm = RecordingLLM()
            profiles = HOFSTEDE_PROFILES[:2]
            prompts = prepare_profile_prompts(llm, ['model-a', 'model-b'], profiles, root/'profile_prompts.json')
            self.assertEqual(len(llm.calls), 4)
            self.assertNotEqual(prompts['model-a']['P0_neutral'], prompts['model-b']['P0_neutral'])
            args = argparse.Namespace(max_retries=0, quality_mode='off', case_id='', max_cases=2,
                                      out=root/'results.json', answers_out=root/'answers.json')
            cases = {str(i): {'case_id': str(i), 'patient_question': f'Case {i}?'} for i in (1,2)}
            results = run_batch(args, cases, {}, prompts, ['model-a','model-b'], profiles,
                                SubtaskRunner(llm, processing='none'))
            self.assertEqual(len(llm.calls), 12)  # 4 prompt generations + 8 answers
            for case in results.values():
                for pid, models in case.items():
                    for model, result in models.items():
                        self.assertEqual(result['attempts'][0]['system_prompt'], prompts[model][pid])
            frozen = prepare_profile_prompts(llm, ['model-a','model-b'], profiles,
                                            root/'reused.json', root/'profile_prompts.json')
            self.assertEqual(frozen, prompts)
            self.assertEqual(len(llm.calls), 12)
            self.assertEqual(len(json.loads((root/'answers.json').read_text())), 2)
            with self.assertRaises(ValueError):
                prepare_profile_prompts(llm, ['other-model'], profiles, root/'bad.json', root/'profile_prompts.json')
            changed = [dict(profiles[0], hofstede={**profiles[0]['hofstede'], 'PDI': 1})]
            with self.assertRaises(ValueError):
                prepare_profile_prompts(llm, ['model-a'], changed, root/'bad.json', root/'profile_prompts.json')

    def test_failure_is_saved_before_stopping(self):
        class Broken:
            def generate(self, *args): return '[ERROR] unavailable'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'profile_prompts.json'
            with self.assertRaises(ValueError):
                prepare_profile_prompts(Broken(), ['model-a'], HOFSTEDE_PROFILES[:1], path)
            record = json.loads(path.read_text())['models']['model-a']['P0_neutral']
            self.assertEqual(record['status'], 'failed')
            self.assertIsNone(record['answer_system_prompt'])

    def test_invalid_prompt_can_use_explicit_fallback(self):
        class Invalid:
            def generate(self, *args): return '[ERROR] unavailable'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'profile_prompts.json'
            prompts = prepare_profile_prompts(
                Invalid(), ['model-a'], HOFSTEDE_PROFILES[:1], path,
                allow_fallback=True,
            )
            record = json.loads(path.read_text())['models']['model-a']['P0_neutral']
            self.assertEqual(record['status'], 'fallback')
            self.assertIsNotNone(prompts['model-a']['P0_neutral'])

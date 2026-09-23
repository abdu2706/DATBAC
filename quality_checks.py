from __future__ import annotations

import re
from difflib import SequenceMatcher

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "were",
    "have",
    "has",
    "had",
    "but",
    "you",
    "your",
    "they",
    "their",
    "them",
    "also",
    "into",
    "over",
    "more",
    "less",
    "than",
    "then",
    "what",
    "when",
    "where",
    "which",
    "should",
    "could",
    "would",
    "may",
    "might",
    "will",
    "can",
    "cant",
    "cannot",
    "not",
    "only",
    "use",
    "used",
    "using",
    "based",
    "note",
    "clinical",
    "patient",
    "question",
    "answer",
}

BANNED_PROFILE_PATTERNS = [
    r"\bprofile\b",
    r"\bcultural profile\b",
    r"\bcommunication profile\b",
    r"\bhofstede\b",
    r"\bpower distance\b",
    r"\bindividualism\b",
    r"\bcollectivism\b",
    r"\buncertainty avoidance\b",
    r"\bachievement and success\b",
    r"\blong-term orientation\b",
    r"\bshort-term orientation\b",
    r"\bindulgence\b",
    r"\brestraint\b",
    r"\bPDI\b",
    r"\bIDV\b",
    r"\bUAI\b",
    r"\bMAS\b",
    r"\bLTO\b",
    r"\bIVR\b",
    r"based on the cultural communication profile",
    r"\bin this culture\b",
    r"\bfor this profile\b",
]

META_TEXT_PATTERNS = [
    r"\bhere is the response\b",
    r"\bhere is the answer\b",
    r"\bdirect medical answer\b",
    r"\backnowledge concern\b",
    r"\bexplanation in patient-friendly language\b",
]

PROMPT_LEAK_PATTERNS = [
    r"\bdo not invent\b",
    r"\bthe purpose described in the note\b",
    r"\bas instructed\b",
    r"\brequired response template\b",
    r"\bprofile-specific\b",
    r"\bhofstede definitions\b",
]

REFUSAL_PATTERNS = [
    r"\bi cannot provide\b",
    r"\bi can't provide\b",
    r"\bi cannot answer\b",
    r"\bi can't answer\b",
    r"\bi am unable to\b",
    r"\bunable to answer\b",
    r"\brequires medical interpretation\b",
    r"\bis there anything else i can help you with\b",
]

INCOMPLETE_ENDINGS = [
    "may be",
    "to",
    "what are",
    "you can ask your",
    "the reasoning behind",
    "and",
    "or",
    "whether",
    "because",
    "as well",
    "for this",
    "suggests that",
]

UNSUPPORTED_CONDITION_TERMS = [
    "sleep apnea",
]

PROGNOSIS_QUESTION_TERMS = [
    "prognosis",
    "life expectancy",
    "lifespan",
    "survival",
    "how long",
    "time left",
    "outlook",
]

POOR_PROGNOSIS_HINTS = [
    "poor prognosis",
    "comfort measures",
    "comfort care",
    "palliative",
    "hospice",
    "terminal",
    "not a candidate for transplant",
    "goals of care",
    "end of life",
]

SCORING_TOOL_TERMS = [
    "meld",
    "child-pugh",
    "child pugh",
]

STANDARD_OF_CARE_PHRASES = [
    "standard approach",
    "standard of care",
    "age group",
    "guideline",
    "typically",
]

CONTINUATION_CUES = [
    "continue",
    "continuing",
    "continued",
    "keep using",
    "remain on",
    "stay on",
    "after discharge",
    "at home",
    "long-term",
    "long term",
]

TREATMENT_TERMS = [
    "cpap",
    "dialysis",
    "antibiotic",
    "antibiotics",
    "ventilation",
    "ventilator",
    "intubation",
]

PROFILE_STRUCTURE_REQUIREMENTS = {
    "P0_neutral": {
        "min_sentences": 2,
        "max_sentences": 3,
    },
    "P2_lowPDI_highIDV": {
        "min_sentences": 3,
        "max_sentences": 3,
        "markers": [
            r"You can ask your treating team",
            r"\?",
        ],
    },
    "P3_highPDI_lowIDV": {
        "min_sentences": 3,
        "max_sentences": 3,
        "markers": [
            r"\byou and your family\b",
        ],
    },
    "P6_highLTO_medHighUAI": {
        "min_sentences": 3,
        "max_sentences": 3,
        "markers": [
            r"\bover time\b|\bfollow-up\b|\bmonitoring\b",
        ],
    },
    "P1_highPDI_highUAI": {
        "markers": [
            r"\b1\.\s*Conclusion:",
            r"\b2\.\s*Evidence:",
            r"\b3\.\s*Next step:",
        ]
    },
    "P4_highUAI_lowIVR": {
        "markers": [
            r"^What is known:",
            r"^What is uncertain:",
            r"^What to do next:",
        ]
    },
    "P5_highMAS_lowUAI": {
        "markers": [
            r"^Bottom line:",
            r"^Why it matters:",
            r"^Intended goal:",
        ]
    },
}

CONCLUSION_SIMILARITY_MIN = 0.45

CAUSAL_PHRASES = [
    "caused by",
    "due to",
    "results in",
    "resulted in",
    "leads to",
    "led to",
    "because of",
    "as a result",
    "therefore",
    "thus",
    "hence",
]


def _token_set(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9]+", (text or "").lower())
    return {t for t in tokens if len(t) >= 4 and t not in STOPWORDS}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _has_profile_mentions(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in BANNED_PROFILE_PATTERNS)


def _has_meta_text(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in META_TEXT_PATTERNS)


def _has_prompt_leak(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in PROMPT_LEAK_PATTERNS)


def _has_refusal_text(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in REFUSAL_PATTERNS)


def _has_incomplete_ending(text: str) -> bool:
    if (text or "").strip().endswith("..."):
        return True
    cleaned = re.sub(r"[\s\"'\.,;:!\?]+$", "", (text or "").lower())
    if not cleaned:
        return False
    for phrase in INCOMPLETE_ENDINGS:
        if re.search(rf"{re.escape(phrase)}\s*$", cleaned):
            return True
    return False


def _ends_with_punctuation(text: str) -> bool:
    cleaned = (text or "").strip()
    return bool(cleaned) and cleaned[-1] in ".!?"


def _mentions_unsupported_condition(answer: str, note_text: str, question_text: str) -> bool:
    answer_lower = (answer or "").lower()
    note_lower = (note_text or "").lower()
    question_lower = (question_text or "").lower()
    for term in UNSUPPORTED_CONDITION_TERMS:
        if term in answer_lower and term not in note_lower and term not in question_lower:
            return True
    return False


def _mentions_scoring_tools_without_prompt(answer: str, question_text: str) -> bool:
    answer_lower = (answer or "").lower()
    question_lower = (question_text or "").lower()
    if not any(term in answer_lower for term in SCORING_TOOL_TERMS):
        return False
    return not any(term in question_lower for term in SCORING_TOOL_TERMS) and "score" not in question_lower


def _mentions_unasked_standard_of_care(answer: str, question_text: str, note_text: str) -> bool:
    answer_lower = (answer or "").lower()
    if not any(phrase in answer_lower for phrase in STANDARD_OF_CARE_PHRASES):
        return False
    combined = f"{question_text} {note_text}".lower()
    return not any(phrase in combined for phrase in STANDARD_OF_CARE_PHRASES)


def _is_prognosis_question(question_text: str) -> bool:
    q_lower = (question_text or "").lower()
    return any(term in q_lower for term in PROGNOSIS_QUESTION_TERMS)


def _note_supports_poor_prognosis(note_text: str) -> bool:
    note_lower = (note_text or "").lower()
    return any(term in note_lower for term in POOR_PROGNOSIS_HINTS)


def _answer_acknowledges_poor_prognosis(answer: str) -> bool:
    a_lower = (answer or "").lower()
    return "poor" in a_lower


def _has_unsupported_treatment_continuation(answer: str, note_text: str) -> bool:
    answer_lower = (answer or "").lower()
    if not any(term in answer_lower for term in TREATMENT_TERMS):
        return False
    if not any(cue in answer_lower for cue in CONTINUATION_CUES):
        return False
    note_lower = (note_text or "").lower()
    has_note_support = any(cue in note_lower for cue in CONTINUATION_CUES) or any(
        key in note_lower for key in ["discharge", "home", "outpatient"]
    )
    return not has_note_support


def _has_unsupported_causality(answer: str, note_text: str, question_text: str) -> bool:
    answer_lower = (answer or "").lower()
    if not answer_lower:
        return False
    note_lower = (note_text or "").lower()
    question_lower = (question_text or "").lower()
    for phrase in CAUSAL_PHRASES:
        if phrase in answer_lower and phrase not in note_lower and phrase not in question_lower:
            return True
    return False


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", text or ""))


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return cleaned


def normalized_similarity(text_a: str, text_b: str) -> float:
    a = _normalize_text(text_a)
    b = _normalize_text(text_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _sentence_count(text: str) -> int:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return len([p for p in parts if p])


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return parts[0] if parts else ""


def _section_line(text: str, heading: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(heading.lower()):
            return stripped
    return ""


def _is_direct_answer_first_sentence(
    answer: str, question_text: str, note_text: str
) -> bool:
    first = _first_sentence(answer)
    if not first:
        return False
    first_lower = first.strip().lower()
    if first_lower.endswith("?"):
        return False

    banned_starts = [
        "ask your",
        "you can ask",
        "you may want to ask",
        "follow-up",
        "follow up",
        "follow-up may include",
        "follow up may include",
        "discuss",
        "consult",
        "please",
        "next step",
        "consider",
        "the treating doctor can clarify",
        "here is",
    ]
    if any(first_lower.startswith(prefix) for prefix in banned_starts):
        return False

    if re.match(r"^(yes|no)\b", first_lower):
        return True

    source_tokens = _token_set(question_text) | _token_set(note_text)
    return bool(_token_set(first) & source_tokens)


def validate_profile_structure(profile_id: str, answer: str, case: dict) -> list[str]:
    warnings: list[str] = []
    reqs = PROFILE_STRUCTURE_REQUIREMENTS.get(profile_id)
    if not reqs:
        return warnings

    if "min_sentences" in reqs:
        count = _sentence_count(answer)
        min_s = reqs.get("min_sentences", 0)
        max_s = reqs.get("max_sentences", 999)
        if count < min_s or count > max_s:
            warnings.append("does not match required sentence count")

    markers = reqs.get("markers", [])
    if profile_id == "P2_lowPDI_highIDV":
        if not re.search(
            r"You can ask your treating team(?:\s+whether|:).*\?",
            answer,
            flags=re.IGNORECASE,
        ):
            warnings.append("missing treating team question")
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", answer.strip()) if s]
        if sentences and not sentences[-1].strip().endswith("?"):
            warnings.append("treating team question not last sentence")
        question_text = " ".join(
            [
                case.get("patient_question", ""),
                case.get("clinician_question", ""),
            ]
        ).strip()
        if _mentions_scoring_tools_without_prompt(answer, question_text):
            warnings.append("scoring tools not requested")
        return warnings

    if profile_id == "P0_neutral":
        if re.search(r"\bReason:\b|\bCautious follow-up:\b", answer, flags=re.IGNORECASE):
            warnings.append("contains labels in neutral profile")

    if profile_id == "P4_highUAI_lowIVR":
        question_text = " ".join(
            [
                case.get("patient_question", ""),
                case.get("clinician_question", ""),
            ]
        ).strip()
        note_text = case.get("note_excerpt", "")
        question_tokens = _token_set(question_text)
        note_tokens = _token_set(note_text)

        known_line = _section_line(answer, "What is known:")
        uncertain_line = _section_line(answer, "What is uncertain:")

        if known_line:
            known_tokens = _token_set(known_line)
            if question_tokens and not (known_tokens & question_tokens):
                warnings.append("known section does not address question")
            if not (known_tokens & note_tokens):
                warnings.append("known section not grounded in note")

        if uncertain_line:
            uncertain_tokens = _token_set(uncertain_line)
            if not (uncertain_tokens & note_tokens):
                warnings.append("uncertainty not grounded")
            if any(phrase in uncertain_line.lower() for phrase in STANDARD_OF_CARE_PHRASES):
                if not any(phrase in question_text.lower() for phrase in STANDARD_OF_CARE_PHRASES):
                    warnings.append("standard of care not asked")

    if profile_id == "P6_highLTO_medHighUAI":
        note_text = case.get("note_excerpt", "").lower()
        if re.search(r"monitoring will continue|will continue to monitor", answer, flags=re.IGNORECASE):
            if "monitor" not in note_text:
                warnings.append("overconfident follow-up")

    for pattern in markers:
        if not re.search(pattern, answer, flags=re.IGNORECASE | re.MULTILINE):
            warnings.append("missing required structure marker")
            break

    return warnings


def validate_single_answer(answer: str, case: dict, profile_id: str | None = None) -> list[str]:
    warnings: list[str] = []
    cleaned = (answer or "").strip()
    if not cleaned or cleaned.startswith("[ERROR]"):
        return warnings

    if _has_profile_mentions(cleaned):
        warnings.append("mentions cultural profile terms")

    if _has_meta_text(cleaned):
        warnings.append("contains meta-text labels")

    if _has_prompt_leak(cleaned):
        warnings.append("prompt leakage")

    if _has_refusal_text(cleaned):
        warnings.append("refusal text")

    question_text = " ".join(
        [
            case.get("patient_question", ""),
            case.get("clinician_question", ""),
        ]
    ).strip()
    note_text = case.get("note_excerpt", "")

    if not _is_direct_answer_first_sentence(cleaned, question_text, note_text):
        warnings.append("first sentence not direct answer")

    if not _ends_with_punctuation(cleaned):
        warnings.append("missing ending punctuation")

    if _has_incomplete_ending(cleaned):
        warnings.append("incomplete ending")

    if _mentions_unsupported_condition(cleaned, note_text, question_text):
        warnings.append("mentions sleep apnea not in note")

    if _has_unsupported_treatment_continuation(cleaned, note_text):
        warnings.append("unsupported treatment continuation")

    if _mentions_unasked_standard_of_care(cleaned, question_text, note_text):
        warnings.append("standard of care not asked")

    if _is_prognosis_question(question_text) and _note_supports_poor_prognosis(note_text):
        if ("uncertain" in cleaned.lower() or "difficult to predict" in cleaned.lower()) and not _answer_acknowledges_poor_prognosis(cleaned):
            warnings.append("poor prognosis not acknowledged")

    answer_tokens = _token_set(cleaned)
    source_tokens = _token_set(question_text) | _token_set(note_text)
    overlap = answer_tokens & source_tokens
    min_overlap = 1 if len(answer_tokens) < 10 else 2
    if len(overlap) < min_overlap:
        warnings.append("low lexical overlap with question/note")

    numbers_in_answer = _numbers(cleaned)
    numbers_in_source = _numbers(f"{question_text} {note_text}")
    extra_numbers = numbers_in_answer - numbers_in_source
    if extra_numbers:
        warnings.append("contains numbers not in source text")

    if _has_unsupported_causality(cleaned, note_text, question_text):
        warnings.append("possible unsupported causal claim")

    if profile_id:
        warnings.extend(validate_profile_structure(profile_id, cleaned, case))

    return warnings


def _pairwise_similarity(answers: dict[str, str]) -> tuple[float, float]:
    ids = sorted(answers.keys())
    if len(ids) < 2:
        return 0.0, 0.0
    sims: list[float] = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = answers[ids[i]]
            b = answers[ids[j]]
            sim = _jaccard(_token_set(a), _token_set(b))
            sims.append(sim)
    if not sims:
        return 0.0, 0.0
    return max(sims), sum(sims) / len(sims)


def collect_answers_by_model(case_results: dict) -> dict[str, dict[str, str]]:
    answers_by_model: dict[str, dict[str, str]] = {}
    for profile_id, models in case_results.items():
        if not isinstance(models, dict):
            continue
        for model, data in models.items():
            if not isinstance(data, dict):
                continue
            answer = data.get("subtask3", "")
            if answer and not answer.startswith("[ERROR]"):
                answers_by_model.setdefault(model, {})[profile_id] = answer
    return answers_by_model


def find_profiles_to_regenerate(
    answers: dict[str, str], threshold: float = 0.90
) -> tuple[set[str], list[tuple[str, str, float]]]:
    ids = sorted(answers.keys())
    regen: set[str] = set()
    pairs: list[tuple[str, str, float]] = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a_id = ids[i]
            b_id = ids[j]
            sim = normalized_similarity(answers[a_id], answers[b_id])
            if sim >= threshold:
                regen.add(b_id)
                pairs.append((a_id, b_id, sim))
    return regen, pairs


def all_profiles_identical(answers: dict[str, str]) -> bool:
    if not answers:
        return False
    unique = { _normalize_text(value) for value in answers.values() if value }
    return len(unique) <= 1


def validate_cross_profile_outputs(
    case_results: dict, case: dict, case_id: str | None = None
) -> dict[str, dict[str, list[str]]]:
    warnings_by_profile: dict[str, dict[str, list[str]]] = {}
    answers_by_model = collect_answers_by_model(case_results)

    note_tokens = _token_set(case.get("note_excerpt", ""))

    for model, answers in answers_by_model.items():
        if len(answers) < 2:
            continue

        max_sim, avg_sim = _pairwise_similarity(answers)
        similarity_warning = None
        if max_sim >= 0.85:
            similarity_warning = (
                f"outputs too similar across profiles (max similarity {max_sim:.2f}, "
                f"avg {avg_sim:.2f})"
            )

        profile_ids = sorted(answers.keys())
        baseline_id = profile_ids[0]
        baseline_tokens = _token_set(answers[baseline_id]) & note_tokens
        baseline_first = _first_sentence(answers[baseline_id])

        conclusion_warnings: dict[str, list[str]] = {}
        for pid, answer in answers.items():
            first = _first_sentence(answer)
            if not first or not baseline_first:
                continue
            sim = normalized_similarity(first, baseline_first)
            if sim < CONCLUSION_SIMILARITY_MIN:
                conclusion_warnings.setdefault(pid, []).append(
                    "clinical conclusion differs from baseline"
                )

        per_profile_warnings: dict[str, list[str]] = {}
        if len(baseline_tokens) >= 3:
            for pid, answer in answers.items():
                tokens = _token_set(answer) & note_tokens
                overlap_ratio = len(tokens & baseline_tokens) / max(1, len(baseline_tokens))
                if overlap_ratio < 0.5:
                    per_profile_warnings.setdefault(pid, []).append(
                        "medical content differs from baseline profile"
                    )

        case25_warning = None
        if case_id == "25" and all_profiles_identical(answers):
            case25_warning = "case 25 outputs identical across profiles"

        if similarity_warning or per_profile_warnings or conclusion_warnings or case25_warning:
            for pid in profile_ids:
                warnings_by_profile.setdefault(pid, {}).setdefault(model, [])
                if similarity_warning:
                    warnings_by_profile[pid][model].append(similarity_warning)
                if pid in per_profile_warnings:
                    warnings_by_profile[pid][model].extend(per_profile_warnings[pid])
                if pid in conclusion_warnings:
                    warnings_by_profile[pid][model].extend(conclusion_warnings[pid])
                if case25_warning:
                    warnings_by_profile[pid][model].append(case25_warning)

    # De-duplicate warnings per profile/model.
    for pid, model_map in warnings_by_profile.items():
        for model, warns in model_map.items():
            deduped = list(dict.fromkeys(warns))
            warnings_by_profile[pid][model] = deduped

    return warnings_by_profile

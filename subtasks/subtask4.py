from __future__ import annotations

import re


def build_prompt(case: dict, answer_text: str, sentences: dict) -> str:
    answer_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer_text) if s.strip()]
    answer_numbered = "\n".join(f"{i + 1}: {s}" for i, s in enumerate(answer_sents))

    note_text = "\n".join(f"[{sid}]: {s['text']}" for sid, s in sentences.items())

    return (
        f"Patient question: {case['patient_question']}\n"
        f"Clinician question: {case['clinician_question']}\n\n"
        f"Clinical note sentences:\n{note_text}\n\n"
        f"Answer sentences:\n{answer_numbered}\n\n"
        "For each answer sentence, identify which clinical note sentence(s) support it. "
        "Return ONLY a JSON array like:\n"
        '[{"answer_id": "1", "evidence_id": ["2", "5"]}, ...]\n'
        "Use empty list for unsupported sentences."
    )

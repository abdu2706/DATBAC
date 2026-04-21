from __future__ import annotations


def build_prompt(case: dict) -> str:
    return (
        f"Patient question:\n{case['patient_narrative']}\n\n"
        "Generate a single concise clinician-interpreted question (max 15 words) "
        "that captures the core clinical information need. "
        "Output ONLY the question, nothing else."
    )

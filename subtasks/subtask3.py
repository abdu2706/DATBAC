from __future__ import annotations


def build_prompt(case: dict) -> str:
    return (
        f"Patient Question:\n{case.get('patient_question', '')}\n\n"
        f"Clinician-Interpreted Question:\n{case.get('clinician_question', '')}\n\n"
        f"Clinical Note Excerpt:\n{case.get('note_excerpt', '')}"
    )

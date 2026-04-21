from __future__ import annotations


def build_prompt(case: dict, retrieved: list[tuple]) -> str:
    evidence_text = "\n".join(f"[{sid}]: {text}" for sid, text, _ in retrieved)
    return (
        f"Patient Question:\n{case.get('patient_question', '')}\n\n"
        f"Clinician-Interpreted Question:\n{case.get('clinician_question', '')}\n\n"
        f"Clinical Note Excerpt:\n{case.get('note_excerpt', '')}\n\n"
        f"BM25-Ranked Note Sentences (same excerpt, for focus):\n{evidence_text}\n\n"
        "Task: Generate one professional, evidence-grounded answer to the patient question.\n"
        "Rules:\n"
        "- Maximum 75 words (about 5 sentences).\n"
        "- Use ONLY information supported by the clinical note excerpt and ranked sentences above.\n"
        "- Do not use external knowledge.\n"
        "- If the note is insufficient, state the limitation clearly and avoid speculation.\n"
        "- Output only the answer text."
    )

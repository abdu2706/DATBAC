from __future__ import annotations


def build_prompt(case: dict, retrieved: list[tuple]) -> str:
    sentences_text = "\n".join(f"[{sid}]: {text}" for sid, text, _ in retrieved)
    return (
        f"Patient question: {case['patient_question']}\n"
        f"Clinician question: {case['clinician_question']}\n\n"
        f"Clinical note sentences:\n{sentences_text}\n\n"
        "Which sentence IDs are clinically relevant to answering the patient's question? "
        "Return ONLY a JSON array of sentence ID strings, e.g. [\"1\", \"5\", \"7\"]. "
        "Select only the minimal set of essential sentences."
    )

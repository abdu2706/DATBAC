from __future__ import annotations


def build_prompt(case: dict) -> str:
    return (
        "Task: Answer the patient's medical question using only the clinical note excerpt.\n"
        "Requirements:\n"
        "- Answer the patient question directly.\n"
        "- Follow the profile-specific response template in the system prompt.\n"
        "- Do not mention any cultural profile or Hofstede dimensions.\n"
        "- Do not say \"Based on the cultural communication profile...\".\n"
        "- Use only information supported by the note; avoid unsupported causal claims.\n"
        "- The first sentence must directly answer the question.\n"
        "- Never refuse to answer; omit unsupported details or ask the treating team instead.\n"
        "- Do not output refusal text.\n"
        "- Do not mention sleep apnea unless the note mentions it.\n"
        "- Do not recommend continuing treatments after discharge unless the note says so.\n"
        "- Avoid incomplete sentences.\n"
        "- Do not introduce unrelated conditions or general standards of care.\n"
        "- Do not include prompt or instruction text.\n"
        "- If the note indicates poor prognosis without exact timing, say the prognosis appears poor and time is difficult to predict.\n"
        "- Do not mention prognostic scoring tools unless the question asks for them.\n"
        "- Keep the answer within 75 words.\n\n"
        f"Patient Question:\n{case.get('patient_question', '')}\n\n"
        f"Clinician-Interpreted Question:\n{case.get('clinician_question', '')}\n\n"
        f"Clinical Note Excerpt:\n{case.get('note_excerpt', '')}"
    )
# du er en lege du må svare

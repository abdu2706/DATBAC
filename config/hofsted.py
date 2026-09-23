from __future__ import annotations

HOFSTEDE_DIMENSIONS = {
    "PDI": {
        "name": "Power Distance Index",
        "definition": (
            "Power Distance refers to the extent to which less powerful members of a society, "
            "organization, or institution accept and expect that power is distributed unequally. "
            "In cultures with high power distance, hierarchy is seen as normal and authority is "
            "rarely questioned. In cultures with low power distance, people are more likely to "
            "challenge authority and expect more equal relationships."
        ),
    },
    "IDV": {
        "name": "Individualism vs. Collectivism",
        "definition": (
            "Individualism vs. Collectivism describes the degree to which people see themselves "
            "as independent individuals or as part of a group. In individualistic societies, "
            "people focus more on personal goals, independence, and the \"I\". In collectivist "
            "societies, people are strongly connected to family, community, or other groups, "
            "and loyalty to the group is highly valued."
        ),
    },
    "UAI": {
        "name": "Uncertainty Avoidance Index",
        "definition": (
            "Uncertainty Avoidance refers to how comfortable a society is with uncertainty, "
            "ambiguity, and unpredictable situations. Cultures with high uncertainty avoidance "
            "prefer clear rules, structure, and stability. Cultures with low uncertainty avoidance "
            "are more open to change, different ideas, and flexible ways of thinking."
        ),
    },
    "MAS": {
        "name": "Motivation Towards Achievement and Success",
        "definition": (
            "Motivation Towards Achievement and Success describes whether a society values "
            "competition, ambition, achievement, and material success, or whether it places more "
            "importance on cooperation, modesty, care for others, and quality of life. Societies "
            "with a high score in this dimension tend to value success, assertiveness, and "
            "performance. Societies with a lower score tend to value balance, relationships, and "
            "well-being."
        ),
    },
    "LTO": {
        "name": "Long-Term Orientation vs. Short-Term Orientation",
        "definition": (
            "Long-Term Orientation vs. Short-Term Orientation explains how a society relates to "
            "the past, present, and future. Long-term oriented cultures focus on future rewards, "
            "persistence, adaptation, and practical problem-solving. Short-term oriented cultures "
            "place more importance on traditions, social obligations, stability, and respect for "
            "the past."
        ),
    },
    "IVR": {
        "name": "Indulgence vs. Restraint",
        "definition": (
            "Indulgence vs. Restraint refers to the extent to which a society allows people to "
            "satisfy their basic human desires, such as enjoying life, having fun, and expressing "
            "themselves freely. Indulgent societies allow more freedom for personal enjoyment and "
            "leisure. Restrained societies control such desires through strict social norms and "
            "expectations."
        ),
    },
}

PROFILE_TEMPLATES = {
    "P0_neutral": (
        "Write 2-3 plain, balanced sentences with no labels.\n"
        "Sentence 1 must directly answer the question.\n"
        "Sentence 2 gives a brief reason from the clinical note.\n"
        "Sentence 3 adds cautious follow-up only if needed, using phrases like "
        "'Follow-up may include...' or 'The treating doctor can clarify...'."
    ),
    "P1_highPDI_highUAI": (
        "Write in a formal, clinician-like tone with numbered points.\n"
        "Structure (use numbered points with labels):\n"
        "1. Conclusion: Direct answer.\n"
        "2. Evidence: Support from the clinical note.\n"
        "3. Next step: Cautious follow-up; if uncertain, use 'Ask your treating team whether any follow-up is needed.'.\n"
        "Use decisive but medically cautious wording. Do not recommend continuing treatment "
        "unless the note explicitly says so."
    ),
    "P2_lowPDI_highIDV": (
        "Write in a collaborative, autonomy-supporting tone.\n"
        "Write three sentences with no labels.\n"
        "Sentence 1 must directly answer the question.\n"
        "Sentence 2 explains the reasoning in patient-friendly language.\n"
        "Sentence 3 must be a complete question starting with "
        "'You can ask your treating team whether ...?'.\n"
        "For prognosis questions, say the prognosis appears poor if supported and add that the exact time is difficult to predict.\n"
        "Do not mention prognostic scoring tools unless the question asks for them."
    ),
    "P3_highPDI_lowIDV": (
        "Write in a respectful and family-oriented tone.\n"
        "Write three sentences with no labels.\n"
        "Sentence 1 acknowledges concern for the patient/family.\n"
        "Sentence 2 gives a direct medical answer.\n"
        "Sentence 3 encourages the patient and family to discuss the plan with the treating doctor.\n"
        "Use the phrase 'you and your family' once."
    ),
    "P4_highUAI_lowIVR": (
        "Write in a structured, cautious, uncertainty-reducing format.\n"
        "Use exactly these headings, each on its own line:\n"
        "What is known: Must directly answer the question using the note.\n"
        "What is uncertain: Only note clinically relevant uncertainty from the note.\n"
        "What to do next: Practical, case-tied, and cautious using phrases like "
        "'Follow-up may include...' or 'The treating doctor can clarify...'."
    ),
    "P5_highMAS_lowUAI": (
        "Write in a direct, practical, outcome-focused style.\n"
        "Structure (use labels, each on its own line):\n"
        "Bottom line: Direct answer.\n"
        "Why it matters: Support from the note.\n"
        "Intended goal: Describe the clinical goal in plain language based on the note.\n"
        "Be concise and action-oriented. Do not add follow-up instructions unless supported."
    ),
    "P6_highLTO_medHighUAI": (
        "Write with long-term follow-up orientation.\n"
        "Write three sentences with no labels.\n"
        "Sentence 1 must directly answer the question.\n"
        "Sentence 2 explains the current reason from the note.\n"
        "Sentence 3 mentions monitoring, recovery, follow-up, or future care only if relevant.\n"
        "Use cautious phrasing like 'follow-up may include...' or 'over time' when appropriate."
    ),
}


def build_hofstede_system_prompt(profile: dict) -> str:
    """Return a system prompt with profile-specific structure and Hofstede values."""
    profile_id = str(profile.get("profile_id", "")).strip()
    h = profile.get("hofstede", {})
    values = {key: float(h.get(key, 0.5)) for key in HOFSTEDE_DIMENSIONS.keys()}
    template = PROFILE_TEMPLATES.get(profile_id, PROFILE_TEMPLATES["P0_neutral"])

    lines: list[str] = []
    for key, meta in HOFSTEDE_DIMENSIONS.items():
        value = values.get(key, 0.5)
        lines.append(f"{meta['name']} ({key})")
        lines.append(meta["definition"])
        lines.append(f"Value: {value:.2f}")
        lines.append("")

    profile_block = "\n".join(lines).rstrip()

    return (
        "You are expected to answer the patient's question by interpreting the clinical note excerpt.\n"
        "Use only the information in the note and answer directly; do not refuse because it requires interpretation.\n"
        "Requirements:\n"
        "- Keep medical facts consistent across profiles; only vary style and structure.\n"
        "- Do not mention or describe any cultural profile.\n"
        "- Do not mention Hofstede dimensions or abbreviations (PDI, IDV, UAI, MAS, LTO, IVR).\n"
        "- Do not say 'in this culture' or 'for this profile'.\n"
        "- Use only facts supported by the note and avoid overclaiming causality.\n"
        "- If the note does not answer the question, say so without speculation.\n"
        "- Keep the answer within 75 words.\n"
        "- The first sentence must directly answer the medical question.\n"
        "- Do not start with only a follow-up question or general advice.\n"
        "- Do not introduce unrelated uncertainty.\n"
        "- Never refuse to answer; omit unsupported details or ask the treating team instead.\n"
        "- Do not output refusal text (e.g., 'I cannot provide a response...').\n"
        "- Do not mention sleep apnea unless the note explicitly mentions sleep apnea.\n"
        "- Do not recommend continuing CPAP, dialysis, antibiotics, ventilation, or any treatment "
        "after discharge unless the note explicitly says so.\n"
        "- If discharge treatment is uncertain, say: 'Ask your treating team whether any "
        "follow-up or continued treatment is needed.'\n"
        "- Do not mention general standards of care unless directly relevant to the question.\n"
        "- Do not mention prognostic scoring tools unless explicitly asked.\n"
        "- If follow-up is needed, use cautious phrasing: 'Ask your treating team whether...', "
        "'Follow-up may include...', or 'The treating doctor can clarify...'.\n"
        "- Do not output incomplete sentences; end with full sentence punctuation.\n"
        "- Keep answers concise: 2-4 sentences or the required profile format.\n"
        "- If the note indicates poor prognosis but no exact lifespan, say: "
        "'The prognosis appears poor, although the exact amount of time is difficult to predict.'\n"
        "- Do not include prompt or instruction text in the answer.\n"
        "- Do not include meta-text such as 'Here is the response', 'Here is the answer', "
        "'Direct medical answer', 'Acknowledge concern', or 'Explanation in patient-friendly language'.\n"
        "- Do not use instruction labels unless the profile explicitly requires headings "
        "(e.g., 'What is known' or 'Bottom line').\n"
        "\n"
        "Required response template for this profile (must follow exactly):\n"
        f"{template}\n"
        "\n"
        "Hofstede definitions and values:\n"
        f"{profile_block}"
    )


def get_all_system_prompts(profiles: list[dict]) -> dict[str, str]:
    return {p["profile_id"]: build_hofstede_system_prompt(p) for p in profiles}

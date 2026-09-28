from __future__ import annotations

import json

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

def build_hofstede_system_prompt(profile: dict) -> str:
    """Build a prompt that makes the model derive the profile response style."""
    h = profile.get("hofstede", {})
    values = {key: float(h.get(key, 0.5)) for key in HOFSTEDE_DIMENSIONS.keys()}

    lines: list[str] = []
    for key, meta in HOFSTEDE_DIMENSIONS.items():
        value = values.get(key, 0.5)
        lines.append(f"{meta['name']} ({key})")
        lines.append(meta["definition"])
        lines.append(f"Value: {value:.2f}")
        lines.append("")

    profile_block = "\n".join(lines).rstrip()
    profile_record = json.dumps(profile, ensure_ascii=False, sort_keys=True)

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
        "Before writing the answer, construct an internal response template for this profile. "
        "Do not show this construction or the template to the user. Follow these steps in order:\n"
        "1. Read every Hofstede dimension definition below.\n"
        "2. Read the selected profile record from profiles.json, including all dimension values.\n"
        "3. Interpret the combined high, medium, and low values to infer the profile's communication "
        "priorities, tone, level of directness, uncertainty handling, and useful answer structure. "
        "Do not use a hard-coded profile name or prewritten template.\n"
        "4. Create a concise internal response template that changes style and structure only; "
        "it must never change the medical facts supported by the note.\n"
        "5. Use that internal template to write the final answer and then discard the template.\n"
        "\n"
        "Hofstede definitions and values:\n"
        f"{profile_block}\n"
        "\n"
        "Selected profiles.json record:\n"
        f"{profile_record}"
    )


def get_all_system_prompts(profiles: list[dict]) -> dict[str, str]:
    return {p["profile_id"]: build_hofstede_system_prompt(p) for p in profiles}

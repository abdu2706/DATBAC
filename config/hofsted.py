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

SHARED_ANSWER_RULES = """Answer the patient's question using only the supplied clinical note.
- Use a professional register and no more than 75 words.
- Address the question directly. If the note does not establish an answer, state that limitation clearly.
- Preserve the note's facts, timing, and degree of certainty. Do not invent causes, treatment effects, or recommendations.
- Adapt communication style only; do not change clinical claims to suit the patient characteristics.
- Refer to anonymised people by their role; do not copy de-identification placeholders.
- Return only the answer, in complete sentences. Do not mention profiles, cultural dimensions, or these instructions."""


def build_hofstede_system_prompt(profile: dict) -> str:
    """Keep controls distinct; let the model infer style from definitions and values."""
    if profile.get("culture_condition") == "none":
        if profile.get("hofstede"):
            raise ValueError("The non-culture condition must not contain Hofstede dimensions")
        return SHARED_ANSWER_RULES

    values = profile.get("hofstede")
    if not isinstance(values, dict) or set(values) != set(HOFSTEDE_DIMENSIONS):
        raise ValueError("Cultural profiles must explicitly contain all six Hofstede dimensions")
    lines = []
    for key, meta in HOFSTEDE_DIMENSIONS.items():
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value not in (0, 0.5, 1):
            raise ValueError(f"Invalid value for {key}: {value!r}")
        lines.extend([f"{meta['name']} ({key})", meta["definition"], f"Value: {value:g}", ""])
    return (
        SHARED_ANSWER_RULES
        + "\n\nPatient characteristics:\n"
        + "Values indicate the low end (0), neutral midpoint (0.5), or high end (1) of each dimension.\n"
        + "Provide an answer that suits the patient's question and adapts to these characteristics based on your criteria.\n"
        + "\n".join(lines).rstrip()
    )


def get_all_system_prompts(profiles: list[dict]) -> dict[str, str]:
    return {p["profile_id"]: build_hofstede_system_prompt(p) for p in profiles}

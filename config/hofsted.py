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


def build_hofstede_system_prompt(profile: dict) -> str:
    """Return a system prompt containing only Hofstede definitions and values."""
    h = profile.get("hofstede", {})
    name = profile.get("name", "Unknown")
    pid = profile.get("profile_id", "Unknown")

    values = {key: float(h.get(key, 0.5)) for key in HOFSTEDE_DIMENSIONS.keys()}

    lines: list[str] = []
    for key, meta in HOFSTEDE_DIMENSIONS.items():
        value = values.get(key, 0.5)
        lines.append(f"{meta['name']} ({key})")
        lines.append(meta["definition"])
        lines.append(f"Value: {value:.2f}")
        lines.append("")

    profile_block = "\n".join(lines).rstrip()

    return (
        f"Cultural Communication Profile: {name} ({pid})\n\n"
        f"Hofstede definitions and values:\n{profile_block}"
    )


def get_all_system_prompts(profiles: list[dict]) -> dict[str, str]:
    return {p["profile_id"]: build_hofstede_system_prompt(p) for p in profiles}

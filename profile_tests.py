from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_loader import load_cases_from_xml
from quality_checks import (
    validate_cross_profile_outputs,
    validate_single_answer,
)

PROFILE_MENTION_WARNING = "mentions cultural profile terms"
META_TEXT_WARNING = "contains meta-text labels"
REFUSAL_WARNING = "refusal text"
ENDING_PUNCTUATION_WARNING = "missing ending punctuation"
INCOMPLETE_WARNING = "incomplete ending"
STANDARD_OF_CARE_WARNING = "standard of care not asked"
SCORING_TOOL_WARNING = "scoring tools not requested"
CONCLUSION_WARNING = "clinical conclusion differs from baseline"


def _load_results(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile output tests")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path("results_test_5.json"),
        help="Path to results JSON",
    )
    args = parser.parse_args()

    if not args.results.exists():
        print(f"Results file not found: {args.results}")
        return 2

    cases = load_cases_from_xml()
    results = _load_results(args.results)

    failures: list[str] = []

    for case_id, case_results in results.items():
        case = cases.get(case_id, {})

        for profile_id, models in case_results.items():
            for model, data in models.items():
                answer = data.get("subtask3", "")
                warnings = validate_single_answer(answer, case, profile_id=profile_id)
                for warning in warnings:
                    if warning == PROFILE_MENTION_WARNING:
                        failures.append(
                            f"case {case_id} {profile_id} {model}: {warning}"
                        )
                    if warning == META_TEXT_WARNING:
                        failures.append(
                            f"case {case_id} {profile_id} {model}: {warning}"
                        )
                    if warning in {
                        REFUSAL_WARNING,
                        ENDING_PUNCTUATION_WARNING,
                        INCOMPLETE_WARNING,
                        STANDARD_OF_CARE_WARNING,
                        SCORING_TOOL_WARNING,
                    }:
                        failures.append(
                            f"case {case_id} {profile_id} {model}: {warning}"
                        )

        cross = validate_cross_profile_outputs(case_results, case, case_id=case_id)
        for profile_id, model_map in cross.items():
            for model, warnings in model_map.items():
                if CONCLUSION_WARNING in warnings:
                    failures.append(
                        f"case {case_id} {profile_id} {model}: {CONCLUSION_WARNING}"
                    )

    if failures:
        print("Profile tests failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("All profile tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

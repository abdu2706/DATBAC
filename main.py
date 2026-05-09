from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from compare import (
    export_subtask3_case_profile_metrics,
    export_subtask3_profile_metric_percentages_compact,
    export_subtask3_profile_metric_percentages,
)
from config import (
    DATASET_BASE,
    DATASET_SPLIT,
    DEFAULT_SEED,
    DEFAULT_TEMPERATURE,
    HOFSTEDE_PROFILES,
    MODELS,
    RESULTS_DIR,
    get_all_system_prompts,
)
from data_loader import load_cases_from_xml, load_gold_answers
from evaluator import compute_subtask3_metrics
from llm_runner import OllamaRunner
from subtasks import SubtaskRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run archehr profile x model comparison")
    parser.add_argument(
        "--max-cases",
        type=int,
        default=0,
        help="If > 0, run only the first N cases for quick tests",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=RESULTS_DIR / "results.json",
        help="Output results file",
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=RESULTS_DIR / "exports",
        help="Output folder for auto-generated CSV files",
    )
    parser.add_argument(
        "--eval-split",
        type=str,
        default="",
        help="Optional split to use for evaluation references (e.g., dev)",
    )
    parser.add_argument(
        "--eval-key-path",
        type=Path,
        default=None,
        help="Optional path to evaluation key JSON (overrides --eval-split)",
    )
    parser.add_argument(
        "--answers-out",
        type=Path,
        default=RESULTS_DIR / "answers.json",
        help="Output answers-only JSON file",
    )
    parser.add_argument(
        "--plot-metric",
        type=str,
        default="st3_bleu_pct",
        help="Metric to visualize in profile-vs-model plot",
    )
    parser.add_argument(
        "--skip-plot",
        action="store_true",
        help="Skip generation of plot image",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="Run only this model name (must be in MODELS)",
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="",
        help="Run only this profile_id (e.g., P0_neutral)",
    )
    parser.add_argument(
        "--case-id",
        type=str,
        default="",
        help="Run only this case id",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive test mode for one case/model/profile",
    )
    return parser.parse_args()


def _sorted_case_ids(cases: dict) -> list[str]:
    try:
        return sorted(cases.keys(), key=int)
    except (TypeError, ValueError):
        return sorted(cases.keys())


def _save_json_atomic(path: Path, payload: dict) -> None:
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    temp_path.replace(path)


def _build_answers_only(all_results: dict) -> dict:
    answers: dict = {}
    for case_id, profiles in all_results.items():
        answers[case_id] = {}
        for profile_id, models in profiles.items():
            answers[case_id][profile_id] = {
                model: data.get("subtask3", "") for model, data in models.items()
            }
    return answers


def run_interactive(
    args: argparse.Namespace,
    cases: dict,
    system_prompts: dict,
    selected_models: list[str],
    selected_profiles: list[dict],
    runner: SubtaskRunner,
) -> None:
    if len(selected_models) != 1 or len(selected_profiles) != 1:
        raise ValueError("--interactive requires exactly one --model and one --profile")

    if not cases:
        raise ValueError(f"No cases found in split {DATASET_SPLIT}")

    profile = selected_profiles[0]
    model = selected_models[0]
    pid = profile["profile_id"]

    fixed_case_id = args.case_id.strip() if args.case_id else ""
    if fixed_case_id and fixed_case_id not in cases:
        raise ValueError(f"Case id '{fixed_case_id}' not found in split {DATASET_SPLIT}")

    print(f"Interactive mode started: model={model} profile={pid}")
    print("Type 'exit' to end chat.")

    case_index_ids = _sorted_case_ids(cases)

    def _tokenize(text: str) -> set[str]:
        return set((text or "").lower().split())

    case_index_tokens = [
        _tokenize(
            " ".join(
                [
                    cases[cid].get("patient_narrative", ""),
                    cases[cid].get("patient_question", ""),
                    cases[cid].get("clinician_question", ""),
                    cases[cid].get("note_excerpt", ""),
                ]
            )
        )
        for cid in case_index_ids
    ]

    def rank_cases(question_text: str, top_k: int = 3) -> list[tuple[str, float]]:
        q_tokens = _tokenize(question_text)
        ranked: list[tuple[str, float]] = []

        for i, cid in enumerate(case_index_ids):
            c_tokens = case_index_tokens[i]
            if not q_tokens or not c_tokens:
                score = 0.0
            else:
                score = len(q_tokens & c_tokens) / len(q_tokens | c_tokens)
            ranked.append((cid, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    while True:
        if fixed_case_id:
            interactive_case_id = fixed_case_id
        else:
            interactive_case_id = ""

        user_q = input("Patient question (or 'exit'): ").strip()
        if user_q.lower() == "exit":
            break
        if not user_q:
            print("Please provide a patient question.")
            continue

        if not fixed_case_id:
            candidates = rank_cases(user_q, top_k=3)
            if not candidates:
                print("No candidate cases available to match this question.")
                continue

            print("\nTop matched cases:")
            for idx, (cid, score) in enumerate(candidates, 1):
                spec = cases[cid].get("clinical_specialty", "").strip()
                print(f"  {idx}. case={cid} specialty={spec} score={score:.3f}")

            choice = input("Choose case [1-3, Enter=1, or 'skip']: ").strip().lower()
            if choice == "skip":
                print("Skipped this question.")
                continue
            if choice in ("", "1"):
                interactive_case_id = candidates[0][0]
            elif choice == "2" and len(candidates) >= 2:
                interactive_case_id = candidates[1][0]
            elif choice == "3" and len(candidates) >= 3:
                interactive_case_id = candidates[2][0]
            else:
                print("Invalid choice, using top match.")
                interactive_case_id = candidates[0][0]

        case = dict(cases[interactive_case_id])
        case["patient_question"] = user_q
        if not case.get("patient_narrative"):
            case["patient_narrative"] = user_q
        print(
            f"\nMatched case={interactive_case_id} specialty={case.get('clinical_specialty', '').strip()}"
        )

        sys_prompt = system_prompts[pid]
        out_st3 = runner.run_subtask(3, case, sys_prompt, model)

        print("\n--- Interactive Outputs ---")
        print(f"Subtask3: {out_st3}")

        if fixed_case_id:
            print("\nType another question for the same case, or 'exit' to stop.")

    print("Interactive mode ended.")


def run_batch(
    args: argparse.Namespace,
    cases: dict,
    gold: dict,
    system_prompts: dict,
    selected_models: list[str],
    selected_profiles: list[dict],
    runner: SubtaskRunner,
) -> dict:
    all_results: dict = {}

    def save_checkpoint() -> None:
        _save_json_atomic(args.out, all_results)

    ordered_case_ids = _sorted_case_ids(cases)
    if args.case_id:
        if args.case_id not in cases:
            raise ValueError(f"Case id '{args.case_id}' not found in split {DATASET_SPLIT}")
        ordered_case_ids = [args.case_id]
    if args.max_cases > 0:
        ordered_case_ids = ordered_case_ids[: args.max_cases]

    for case_id in ordered_case_ids:
        print(f"\n{'=' * 60}")
        print(f"CASE {case_id}: {cases[case_id]['clinical_specialty']}")
        print(f"{'=' * 60}")

        case = cases[case_id]
        gold_case = gold.get(case_id)
        all_results[case_id] = {}

        for profile in selected_profiles:
            pid = profile["profile_id"]
            sys_prompt = system_prompts[pid]
            all_results[case_id][pid] = {}

            print(f"\n  Profile: {profile['name']}")

            for model in selected_models:
                print(f"\n    Model: {model}")
                result: dict = {}
                stage = "init"
                try:
                    stage = "subtask3"
                    print("      Subtask 3: Answer Generation...")
                    result["subtask3"] = runner.run_subtask(3, case, sys_prompt, model)
                    print(f"      -> {result['subtask3'][:80]}...")

                    if gold_case:
                        gold_answer_text = gold_case.get("clinician_answer", "")
                        metrics = compute_subtask3_metrics(
                            result["subtask3"],
                            gold_answer_text,
                            case.get("patient_question", ""),
                            case.get("clinician_question", ""),
                            case.get("note_excerpt", ""),
                        )
                        result["metrics"] = metrics
                        print(
                            "      Metrics: "
                            f"BLEU={metrics['st3_bleu']:.3f} "
                            f"ROUGE={metrics['st3_rouge']:.3f} "
                            f"SARI={metrics['st3_sari']:.3f} "
                            f"BERTScore={metrics['st3_bertscore']:.3f} "
                            f"AlignScore={metrics['st3_alignscore']:.3f} "
                            f"MEDCON={metrics['st3_medcon']:.3f}"
                        )
                except Exception as e:
                    result["error"] = str(e)
                    result["failed_stage"] = stage
                    result["traceback"] = traceback.format_exc()
                    print(f"      [WARN] Model run failed at {stage} and was skipped: {e}")

                all_results[case_id][pid][model] = result
                save_checkpoint()

    save_checkpoint()
    return all_results


def main():
    args = parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.csv_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run settings: split={DATASET_SPLIT} temperature={DEFAULT_TEMPERATURE} seed={DEFAULT_SEED}")
    print("Loading data...")
    cases = load_cases_from_xml()
    eval_split = args.eval_split.strip()
    eval_key_path = args.eval_key_path
    if eval_key_path is None and eval_split:
        eval_key_path = DATASET_BASE / eval_split / "archehr-qa_key.json"
    gold = load_gold_answers(eval_key_path) if eval_key_path else load_gold_answers()

    llm = OllamaRunner()
    runner = SubtaskRunner(llm)
    system_prompts = get_all_system_prompts(HOFSTEDE_PROFILES)

    selected_models = MODELS
    if args.model:
        if args.model not in MODELS:
            raise ValueError(f"Unknown model '{args.model}'. Available: {MODELS}")
        selected_models = [args.model]

    profiles_by_id = {p["profile_id"]: p for p in HOFSTEDE_PROFILES}
    selected_profiles = HOFSTEDE_PROFILES
    if args.profile:
        if args.profile not in profiles_by_id:
            raise ValueError(
                f"Unknown profile '{args.profile}'. Available: {list(profiles_by_id.keys())}"
            )
        selected_profiles = [profiles_by_id[args.profile]]

    if args.interactive:
        run_interactive(
            args,
            cases,
            system_prompts,
            selected_models,
            selected_profiles,
            runner,
        )
        return

    all_results = run_batch(
        args,
        cases,
        gold,
        system_prompts,
        selected_models,
        selected_profiles,
        runner,
    )
    print(f"\nResults saved to {args.out}")
    if eval_key_path:
        print(f"Evaluation reference key: {eval_key_path}")

    answers_only = _build_answers_only(all_results)
    _save_json_atomic(args.answers_out, answers_only)
    print(f"Answers saved to {args.answers_out}")

    case_profile_csv_path = export_subtask3_case_profile_metrics(all_results, args.csv_dir)
    summary_csv_path = export_subtask3_profile_metric_percentages(all_results, args.csv_dir)
    compact_csv_path = export_subtask3_profile_metric_percentages_compact(
        all_results, args.csv_dir
    )
    print("CSV export:")
    print(f"  - subtask3_case_profile_metrics: {case_profile_csv_path}")
    print(f"  - subtask3_profile_metric_percentages: {summary_csv_path}")
    print(f"  - subtask3_profile_metric_percentages_compact: {compact_csv_path}")


if __name__ == "__main__":
    main()

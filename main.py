from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path

from compare import (
    export_subtask3_case_profile_metrics,
    export_subtask3_profile_metric_percentages_compact,
    export_subtask3_profile_metric_percentages,
    export_profile_metric_ci95,
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
from quality_checks import (
    all_profiles_identical,
    collect_answers_by_model,
    validate_cross_profile_outputs,
    validate_single_answer,
)
from subtasks import SubtaskRunner

REGEN_VALIDATION_INSTRUCTION = (
    "Your previous answer was incomplete or did not follow the rules. "
    "Regenerate a complete answer. Keep the same clinical facts and profile style, "
    "but do not refuse and do not add unsupported information. "
    "The first sentence must directly answer the question, and the answer must end with full "
    "sentence punctuation."
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run archehr profile x model comparison")
    parser.add_argument("--experiment-name", default="experiment")
    parser.add_argument("--quality-mode", choices=["off", "observe", "enforce"], default="observe")
    parser.add_argument("--processing", choices=["none", "legacy"], default="none",
                        help="Independent of quality checks; legacy removes profile sentences and truncates")
    parser.add_argument("--max-retries", type=int, default=1,
                        help="Maximum validation retries per answer in enforce mode")
    parser.add_argument(
        "--max-cases",
        type=int,
        default=0,
        help="If > 0, run only the first N cases for quick tests",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output results file",
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=None,
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
        default=None,
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
    path.parent.mkdir(parents=True, exist_ok=True)
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
        runner.context = {"profile_id": pid, "mode": "interactive"}
        out_st3 = runner.run_subtask(3, case, sys_prompt, model)

        print("\n--- Interactive Outputs ---")
        print(f"Subtask3: {out_st3}")

        warnings = (validate_single_answer(out_st3, case, profile_id=pid)
                    if args.quality_mode != "off" else [])
        if runner.attempt_sink and args.quality_mode != "off":
            runner.attempt_sink({"event": "interactive_validation",
                                 "case_id": interactive_case_id, "profile_id": pid,
                                 "model": model, "checks": warnings})
        if warnings:
            print("\n[Checks]")
            for warning in warnings:
                print(f"- {warning}")

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
    if args.max_retries < 0:
        raise ValueError("--max-retries must be nonnegative")
    all_results: dict = {}
    ordered_case_ids = _sorted_case_ids(cases)
    if args.case_id:
        if args.case_id not in cases:
            raise ValueError(f"Case id '{args.case_id}' not found in split {DATASET_SPLIT}")
        ordered_case_ids = [args.case_id]
    if args.max_cases > 0:
        ordered_case_ids = ordered_case_ids[:args.max_cases]

    def checkpoint():
        _save_json_atomic(args.out, all_results)
        _save_json_atomic(args.answers_out, _build_answers_only(all_results))

    for case_id in ordered_case_ids:
        case = cases[case_id]
        gold_case = gold.get(case_id)
        all_results[case_id] = {}
        for profile in selected_profiles:
            pid = profile["profile_id"]
            all_results[case_id][pid] = {}
            for model in selected_models:
                result = {"attempts": [], "checks": [], "quality_mode": args.quality_mode}
                all_results[case_id][pid][model] = result
                budget = args.max_retries if args.quality_mode == "enforce" else 0
                try:
                    for attempt_index in range(budget + 1):
                        runner.context = {"profile_id": pid, "attempt_index": attempt_index,
                                          "reason": "validation_retry" if attempt_index else "initial"}
                        answer = runner.run_subtask(
                            3, case, system_prompts[pid], model,
                            extra_instructions=REGEN_VALIDATION_INSTRUCTION if attempt_index else None,
                        )
                        attempt = dict(runner.last_attempt)
                        attempt.update(profile_id=pid, attempt_index=attempt_index,
                                       reason="validation_retry" if attempt_index else "initial")
                        result["attempts"].append(attempt)
                        result["subtask3"] = answer
                        result["selected_attempt"] = attempt_index
                        checkpoint()
                        if answer.startswith("[ERROR]"):
                            result["error"] = answer
                            result["failed_stage"] = "subtask3"
                            checkpoint()
                            break
                        warnings = (validate_single_answer(answer, case, profile_id=pid)
                                    if args.quality_mode != "off" else [])
                        attempt["checks"] = warnings
                        result["checks"] = warnings
                        checkpoint()
                        if not warnings:
                            break
                    if "error" not in result and gold_case:
                        result["metrics"] = compute_subtask3_metrics(
                            result["subtask3"], gold_case.get("clinician_answer", ""),
                            case.get("patient_question", ""),
                            case.get("clinician_question", ""), case.get("note_excerpt", ""),
                        )
                except Exception as exc:
                    result["error"] = str(exc)
                    result["failed_stage"] = "generation_validation_or_scoring"
                    result["traceback"] = traceback.format_exc()
                checkpoint()
                print(f"Case {case_id} / {pid} / {model}: {len(result['attempts'])} attempt(s)")
        if args.quality_mode != "off":
            # Similarity is an observation, never a reason to force a different answer.
            cross = validate_cross_profile_outputs(all_results[case_id], case, case_id=case_id)
            for pid, models in cross.items():
                for model, warnings in models.items():
                    result = all_results[case_id].get(pid, {}).get(model)
                    if result is not None:
                        result["checks"] = list(dict.fromkeys(result["checks"] + warnings))
            for model, answers in collect_answers_by_model(all_results[case_id]).items():
                if len(answers) > 1 and all_profiles_identical(answers):
                    for pid in answers:
                        all_results[case_id][pid][model]["checks"].append("all profiles identical")
            checkpoint()
    checkpoint()
    return all_results


def main():
    args = parse_args()
    from experiment_tracking import RunArchive
    archive = RunArchive(args)
    import atexit
    atexit.register(archive.mark_interrupted)

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
    runner = SubtaskRunner(llm, processing=args.processing, attempt_sink=archive.record_attempt)
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

    archive.record_configuration(cases, system_prompts, selected_models, selected_profiles,
                                 eval_key_path)
    if args.interactive:
        if args.quality_mode == "enforce":
            raise ValueError("Interactive mode supports off/observe; use batch for enforce retries")
        run_interactive(
            args,
            cases,
            system_prompts,
            selected_models,
            selected_profiles,
            runner,
        )
        archive.finish()
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
    ci95_csv_path = export_profile_metric_ci95(all_results, args.csv_dir)
    print("CSV export:")
    print(f"  - subtask3_case_profile_metrics: {case_profile_csv_path}")
    print(f"  - subtask3_profile_metric_percentages: {summary_csv_path}")
    print(f"  - subtask3_profile_metric_percentages_compact: {compact_csv_path}")
    print(f"  - profile_metric_ci95: {ci95_csv_path}")
    failures = sum("error" in result for profiles in all_results.values()
                   for models in profiles.values() for result in models.values())
    archive.finish(failures)


if __name__ == "__main__":
    main()

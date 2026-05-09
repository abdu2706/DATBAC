from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


def build_comparison_table(results: dict) -> list[dict]:
    rows: list[dict] = []
    for case_id, profiles in results.items():
        for profile_id, models in profiles.items():
            for model, data in models.items():
                row = {
                    "case_id": case_id,
                    "profile_id": profile_id,
                    "model": model,
                }
                for st in ["subtask3"]:
                    row[st] = data.get(st, "")
                if "metrics" in data:
                    for metric_name, value in data["metrics"].items():
                        row[f"metric_{metric_name}"] = value
                rows.append(row)
    return rows


def _ordered_fieldnames(rows: list[dict]) -> list[str]:
    preferred = ["case_id", "profile_id", "model", "subtask3"]
    all_keys: list[str] = []
    seen = set()

    for key in preferred:
        seen.add(key)
        all_keys.append(key)

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                all_keys.append(key)

    return all_keys


def write_rows_to_csv(rows: list[dict], csv_path: Path):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            f.write("")
        return

    fieldnames = _ordered_fieldnames(rows)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_by_profile(results: dict) -> dict[str, dict]:
    profile_metrics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _, profiles in results.items():
        for profile_id, models in profiles.items():
            for _, data in models.items():
                if "metrics" in data:
                    for metric, value in data["metrics"].items():
                        if isinstance(value, (int, float)):
                            profile_metrics[profile_id][metric].append(float(value))

    summary: dict[str, dict] = {}
    for pid, metrics in profile_metrics.items():
        summary[pid] = {
            metric: (sum(vals) / len(vals) if vals else 0.0)
            for metric, vals in metrics.items()
        }
    return summary


def summarize_by_model(results: dict) -> dict[str, dict]:
    model_metrics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _, profiles in results.items():
        for _, models in profiles.items():
            for model, data in models.items():
                if "metrics" in data:
                    for metric, value in data["metrics"].items():
                        if isinstance(value, (int, float)):
                            model_metrics[model][metric].append(float(value))

    summary: dict[str, dict] = {}
    for model, metrics in model_metrics.items():
        summary[model] = {
            metric: (sum(vals) / len(vals) if vals else 0.0)
            for metric, vals in metrics.items()
        }
    return summary


def summarize_profile_model_metric(results: dict, metric: str) -> dict[str, dict[str, float]]:
    """Average a metric for each (profile, model) pair across cases."""
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _, profiles in results.items():
        for profile_id, models in profiles.items():
            for model, data in models.items():
                metrics = data.get("metrics", {})
                value = metrics.get(metric)
                if isinstance(value, (int, float)):
                    buckets[profile_id][model].append(float(value))

    out: dict[str, dict[str, float]] = {}
    for profile_id, model_values in buckets.items():
        out[profile_id] = {
            model: (sum(vals) / len(vals) if vals else 0.0)
            for model, vals in model_values.items()
        }
    return out


def build_subtask3_metric_percentage_table(results: dict) -> list[dict]:
    metric_keys = [
        "st3_bleu_pct",
        "st3_rouge_pct",
        "st3_sari_pct",
        "st3_bertscore_pct",
        "st3_alignscore_pct",
        "st3_medcon_pct",
    ]
    rows: list[dict] = []
    for case_id, profiles in sorted(results.items(), key=lambda x: x[0]):
        for profile_id, models in sorted(profiles.items()):
            metric_values: dict[str, list[float]] = {k: [] for k in metric_keys}
            answer_text = ""

            for _, data in models.items():
                metrics = data.get("metrics", {})
                for key in metric_keys:
                    value = metrics.get(key)
                    if isinstance(value, (int, float)):
                        metric_values[key].append(float(value))
                if not answer_text:
                    answer_text = data.get("subtask3", "")

            row = {
                "case_id": case_id,
                "profile_id": profile_id,
            }
            for key in metric_keys:
                vals = metric_values[key]
                avg = (sum(vals) / len(vals)) if vals else 0.0
                row[key] = round(avg, 2)
            row["answer"] = answer_text
            rows.append(row)
    return rows


def build_subtask3_case_profile_metrics_table(results: dict) -> list[dict]:
    metric_keys = [
        "st3_bleu",
        "st3_rouge",
        "st3_sari",
        "st3_bertscore",
        "st3_alignscore",
        "st3_medcon",
        "st3_bleu_pct",
        "st3_rouge_pct",
        "st3_sari_pct",
        "st3_bertscore_pct",
        "st3_alignscore_pct",
        "st3_medcon_pct",
    ]
    rows: list[dict] = []

    for case_id, profiles in sorted(results.items(), key=lambda x: x[0]):
        for profile_id, models in sorted(profiles.items()):
            for model, data in sorted(models.items()):
                metrics = data.get("metrics", {})
                row = {
                    "case_id": case_id,
                    "profile_id": profile_id,
                    "model": model,
                }
                for key in metric_keys:
                    value = metrics.get(key)
                    row[key] = value if value is not None else ""
                row["answer"] = data.get("subtask3", "")
                rows.append(row)

    return rows


def export_subtask3_profile_metric_percentages(results: dict, output_dir: Path) -> Path:
    """Export a single CSV: one row per profile with Subtask 3 metric percentages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_subtask3_metric_percentage_table(results)
    path = output_dir / "subtask3_profile_metric_percentages.csv"

    fieldnames = [
        "case_id",
        "profile_id",
        "st3_bleu_pct",
        "st3_rouge_pct",
        "st3_sari_pct",
        "st3_bertscore_pct",
        "st3_alignscore_pct",
        "st3_medcon_pct",
        "answer",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return path


def export_subtask3_profile_metric_percentages_compact(results: dict, output_dir: Path) -> Path:
    """Export a compact CSV with averages appended at the end."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_subtask3_metric_percentage_table(results)
    path = output_dir / "subtask3_profile_metric_percentages_compact.csv"

    metric_keys = [
        "st3_bleu_pct",
        "st3_rouge_pct",
        "st3_sari_pct",
        "st3_bertscore_pct",
        "st3_alignscore_pct",
        "st3_medcon_pct",
    ]
    fieldnames = ["case_id", "profile_id", *metric_keys]

    totals = {key: 0.0 for key in metric_keys}
    counts = {key: 0 for key in metric_keys}
    compact_rows: list[dict] = []

    for row in rows:
        compact = {k: row.get(k, "") for k in fieldnames}
        compact_rows.append(compact)
        for key in metric_keys:
            value = compact.get(key)
            if isinstance(value, (int, float)):
                totals[key] += float(value)
                counts[key] += 1

    avg_row = {"case_id": "AVERAGE", "profile_id": ""}
    for key in metric_keys:
        if counts[key]:
            avg_row[key] = round(totals[key] / counts[key], 2)
        else:
            avg_row[key] = 0.0

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in compact_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
        writer.writerow(avg_row)

    return path


def export_subtask3_case_profile_metrics(results: dict, output_dir: Path) -> Path:
    """Export Subtask 3 metrics per case/profile/model (one row per output)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = build_subtask3_case_profile_metrics_table(results)
    path = output_dir / "subtask3_case_profile_metrics.csv"

    fieldnames = [
        "case_id",
        "profile_id",
        "model",
        "st3_bleu",
        "st3_rouge",
        "st3_sari",
        "st3_bertscore",
        "st3_alignscore",
        "st3_medcon",
        "st3_bleu_pct",
        "st3_rouge_pct",
        "st3_sari_pct",
        "st3_bertscore_pct",
        "st3_alignscore_pct",
        "st3_medcon_pct",
        "answer",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return path


def export_csv_reports(results: dict, output_dir: Path) -> dict[str, Path]:
    """Export detailed and summary CSV files and return written paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    detailed_rows = build_comparison_table(results)
    profile_summary = summarize_by_profile(results)
    model_summary = summarize_by_model(results)

    profile_rows = [
        {"profile_id": profile_id, **metrics}
        for profile_id, metrics in sorted(profile_summary.items())
    ]
    profile_metric_pct_rows = build_subtask3_metric_percentage_table(results)
    model_rows = [
        {"model": model, **metrics}
        for model, metrics in sorted(model_summary.items())
    ]

    detailed_path = output_dir / "detailed_results.csv"
    profile_path = output_dir / "profile_summary.csv"
    profile_metric_pct_path = output_dir / "subtask3_profile_metric_percentages.csv"
    model_path = output_dir / "model_summary.csv"

    write_rows_to_csv(detailed_rows, detailed_path)
    write_rows_to_csv(profile_rows, profile_path)
    write_rows_to_csv(profile_metric_pct_rows, profile_metric_pct_path)
    write_rows_to_csv(model_rows, model_path)

    return {
        "detailed": detailed_path,
        "profile_summary": profile_path,
        "subtask3_profile_metric_percentages": profile_metric_pct_path,
        "model_summary": model_path,
    }


def print_comparison(results: dict):
    print("\n" + "=" * 80)
    print("PROFILE COMPARISON SUMMARY")
    print("=" * 80)

    profile_summary = summarize_by_profile(results)
    for pid, metrics in sorted(profile_summary.items()):
        print(f"\n  {pid}:")
        for metric, value in sorted(metrics.items()):
            print(f"    {metric}: {value:.4f}")

    print("\n" + "=" * 80)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 80)

    model_summary = summarize_by_model(results)
    for model, metrics in sorted(model_summary.items()):
        print(f"\n  {model}:")
        for metric, value in sorted(metrics.items()):
            print(f"    {metric}: {value:.4f}")

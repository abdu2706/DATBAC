from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from compare import summarize_profile_model_metric


def plot_profile_vs_model_metric(results: dict, metric: str, out_path: Path):
    """Create a simple heatmap for profile x model average metric values."""
    grid = summarize_profile_model_metric(results, metric)
    if not grid:
        print(f"No metric data available for '{metric}', skipping plot.")
        return

    profiles = sorted(grid.keys())
    models = sorted({m for p in profiles for m in grid[p].keys()})

    matrix: list[list[float]] = []
    for profile_id in profiles:
        matrix.append([grid[profile_id].get(model, 0.0) for model in models])

    fig, ax = plt.subplots(figsize=(max(8, len(models) * 1.8), max(5, len(profiles) * 0.8)))
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto", vmin=0.0, vmax=1.0)

    ax.set_title(f"Profile vs Model score ({metric})")
    ax.set_xlabel("Model")
    ax.set_ylabel("Profile")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_yticks(range(len(profiles)))
    ax.set_yticklabels(profiles)

    for i in range(len(profiles)):
        for j in range(len(models)):
            ax.text(j, i, f"{matrix[i][j]:.2f}", ha="center", va="center", color="black")

    fig.colorbar(im, ax=ax, label=metric)
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Plot saved to {out_path}")

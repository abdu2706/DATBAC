import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compare import export_subtask3_profile_metric_percentages

base = Path("results")
merged = {}
for cid in ["21", "22", "23", "24", "25"]:
    p = base / f"results_subtask3_case_{cid}.json"
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    merged.update(data)

out_json = base / "results_subtask3_5cases_allprofiles.json"
with out_json.open("w", encoding="utf-8") as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)

out_csv = export_subtask3_profile_metric_percentages(
    merged, base / "exports_subtask3_5cases_allprofiles"
)
print(out_json)
print(out_csv)

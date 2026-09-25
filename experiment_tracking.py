"""Local, append-only attempt logs and unique experiment directories."""
from __future__ import annotations

import hashlib
import json
import ntpath
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from config import (RESULTS_DIR, WORKSPACE_ROOT, XML_PATH, KEY_PATH, DATASET_SPLIT,
                    DEFAULT_SEED, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, OLLAMA_BASE_URL)


def now():
    return datetime.now(timezone.utc).isoformat()


def fingerprint(path):
    path = Path(path)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file() else None}


def git(*args):
    result = subprocess.run(["git", *args], cwd=WORKSPACE_ROOT, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


class RunArchive:
    def __init__(self, args):
        if args.max_retries < 0:
            raise ValueError("--max-retries must be nonnegative")
        label = re.sub(r"[^A-Za-z0-9_-]+", "-", args.experiment_name).strip("-") or "experiment"
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ") + "_" + label + "_" + uuid4().hex[:8]
        self.directory = RESULTS_DIR / "runs" / run_id
        requested = vars(args).copy()
        # All output overrides are scoped to this run; old files cannot be overwritten.
        paths = {}
        for key, default in [("out", "results.json"), ("answers_out", "answers.json"), ("csv_dir", "exports")]:
            raw_path = getattr(args, key) or default
            relative = Path(raw_path)
            if ntpath.isabs(raw_path) or relative.is_absolute() or relative.anchor or ".." in relative.parts:
                raise ValueError(f"--{key.replace('_', '-')} must be a relative path within the new run folder")
            paths[key] = self.directory / relative
        reserved = [self.directory / name for name in ("manifest.json", "attempts.jsonl", "source_snapshot")]
        all_paths = list(paths.values()) + reserved
        for i, left in enumerate(all_paths):
            for right in all_paths[i+1:]:
                if left == right or left in right.parents or right in left.parents:
                    raise ValueError("Output paths must be distinct and cannot overlap archive files")
        self.directory.mkdir(parents=True, exist_ok=False)
        for key, path in paths.items():
            setattr(args, key, path)
        self.manifest = {
            "schema_version": 1, "run_id": run_id, "started_at": now(), "status": "running",
            "arguments": requested, "outputs": paths, "python": platform.python_version(),
            "git_commit": git("rev-parse", "HEAD"), "git_status": git("status", "--porcelain"),
            "generation": {"seed": DEFAULT_SEED, "temperature": DEFAULT_TEMPERATURE,
                           "max_tokens": DEFAULT_MAX_TOKENS, "ollama_url": OLLAMA_BASE_URL},
            "metric_implementation": "custom local scorers; BERTScore/AlignScore are overlap proxies",
            "similarity_retries": False,
        }
        # Capture the actual source, including uncommitted changes, without clinical data.
        import shutil
        for source in WORKSPACE_ROOT.rglob("*.py"):
            relative = source.relative_to(WORKSPACE_ROOT)
            if any(part.startswith(".") or part in ("Data", "results", "__pycache__", "venv") for part in relative.parts):
                continue
            target = self.directory / "source_snapshot" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in ("config/profiles.json", "requirements.txt"):
            source = WORKSPACE_ROOT / relative
            target = self.directory / "source_snapshot" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        self.save()
        print(f"Run folder: {self.directory}")

    def save(self):
        target = self.directory / "manifest.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.manifest, indent=2, default=str), encoding="utf-8")
        temporary.replace(target)

    def record_configuration(self, cases, prompts, models, profiles, eval_key_path):
        arguments = self.manifest["arguments"]
        try:
            sorted_ids = sorted(cases, key=int)
        except (TypeError, ValueError):
            sorted_ids = sorted(cases)
        ids = [arguments["case_id"]] if arguments["case_id"] else sorted_ids
        if arguments["max_cases"] > 0:
            ids = ids[:arguments["max_cases"]]
        self.manifest.update(
            dataset_split=DATASET_SPLIT, dataset=fingerprint(XML_PATH),
            evaluation_key=fingerprint(eval_key_path or KEY_PATH),
            case_ids=ids, profiles=profiles, models=models,
            system_prompts={p["profile_id"]: prompts[p["profile_id"]] for p in profiles},
            model_identity_note="Model tags are recorded; immutable Ollama model digests are not captured.",
        )
        self.save()

    def record_attempt(self, attempt):
        with (self.directory / "attempts.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"recorded_at": now(), **attempt}, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def finish(self, failures=0):
        self.manifest.update(status="completed_with_errors" if failures else "completed",
                             failed_results=failures, finished_at=now())
        self.save()

    def mark_interrupted(self):
        if self.manifest["status"] == "running":
            self.manifest.update(status="interrupted_or_failed", finished_at=now())
            self.save()

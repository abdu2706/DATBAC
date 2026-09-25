import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from experiment_tracking import RunArchive
from subtasks.runner import SubtaskRunner


class FakeLLM:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def generate(self, *args):
        self.calls += 1
        return next(self.responses)


class ExperimentTests(unittest.TestCase):
    def batch(self, folder, mode, responses, warnings, retries=1, gold=None):
        args = argparse.Namespace(max_retries=retries, quality_mode=mode,
                                  case_id="", max_cases=0,
                                  out=folder / "results.json", answers_out=folder / "answers.json")
        llm = FakeLLM(responses)
        runner = SubtaskRunner(llm, processing="none")
        with patch.object(main, "validate_single_answer", return_value=warnings) as validator, \
             patch.object(main, "validate_cross_profile_outputs", return_value={}) as cross:
            results = main.run_batch(args, {"1": {"case_id": "1"}}, gold or {},
                                     {"P0_neutral": "system"}, ["fake"],
                                     [{"profile_id": "P0_neutral"}], runner)
        return results["1"]["P0_neutral"]["fake"], llm, validator, cross

    def test_off_never_validates_or_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, llm, validate, cross = self.batch(Path(tmp), "off", ["Incomplete"], ["warning"])
            self.assertEqual(llm.calls, 1)
            validate.assert_not_called()
            cross.assert_not_called()
            self.assertEqual(result["subtask3"], "Incomplete")

    def test_observe_records_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, llm, _, _ = self.batch(Path(tmp), "observe", ["Incomplete"], ["warning"])
            self.assertEqual(llm.calls, 1)
            self.assertEqual(result["attempts"][0]["checks"], ["warning"])

    def test_enforce_bounded_and_retains_all_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, llm, _, _ = self.batch(Path(tmp), "enforce", ["First", "Second"], ["warning"])
            self.assertEqual(llm.calls, 2)
            self.assertEqual([a["raw_response"] for a in result["attempts"]], ["First", "Second"])
            self.assertEqual(result["selected_attempt"], 1)
            self.assertEqual(json.loads((Path(tmp) / "answers.json").read_text())["1"]["P0_neutral"]["fake"], "Second")

    def test_failed_retry_does_not_score_stale_answer(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(main, "compute_subtask3_metrics") as metrics:
            result, _, _, _ = self.batch(Path(tmp), "enforce", ["First", "[ERROR] unavailable"],
                                         ["warning"], gold={"1": {"clinician_answer": "Gold"}})
            metrics.assert_not_called()
            self.assertIn("error", result)
            self.assertEqual(len(result["attempts"]), 2)

    def test_raw_persisted_before_validation_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(main, "validate_single_answer", side_effect=RuntimeError("broken")):
            args = argparse.Namespace(max_retries=1, quality_mode="observe", case_id="", max_cases=0,
                                      out=Path(tmp)/"results.json", answers_out=Path(tmp)/"answers.json")
            main.run_batch(args, {"1": {}}, {}, {"p": "system"}, ["fake"], [{"profile_id": "p"}],
                           SubtaskRunner(FakeLLM(["Original."]), processing="none"))
            saved = json.loads(args.out.read_text())["1"]["p"]["fake"]
            self.assertEqual(saved["attempts"][0]["raw_response"], "Original.")
            self.assertIn("error", saved)

    def test_processing_is_independent_and_raw_is_preserved(self):
        raw = " ".join(["word"] * 90)
        events = []
        runner = SubtaskRunner(FakeLLM([raw]), processing="legacy", attempt_sink=events.append)
        self.assertEqual(len(runner.run_subtask(3, {}, "system", "fake").split()), 75)
        self.assertEqual(events[0]["raw_response"], raw)
        runner = SubtaskRunner(FakeLLM([raw]), processing="none")
        self.assertEqual(runner.run_subtask(3, {}, "system", "fake"), raw)

    def test_unprocessed_length_and_empty_are_flagged(self):
        from quality_checks import validate_single_answer
        self.assertIn("exceeds 75 words", validate_single_answer(" ".join(["word"] * 76), {}))
        self.assertNotIn("exceeds 75 words", validate_single_answer(" ".join(["word"] * 75), {}))
        self.assertEqual(validate_single_answer("", {}), ["empty answer"])

    def test_main_exports_complete_synthetic_run(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch("experiment_tracking.RESULTS_DIR", Path(tmp)), \
             patch("sys.argv", ["main.py", "--quality-mode", "off", "--max-cases", "1"]), \
             patch.object(main, "load_cases_from_xml", return_value={"1": {"case_id": "1"}}), \
             patch.object(main, "load_gold_answers", return_value={"1": {"clinician_answer": "Synthetic answer."}}), \
             patch.object(main, "OllamaRunner", return_value=FakeLLM(["Synthetic answer."] * len(main.HOFSTEDE_PROFILES))):
            main.main()
            run = next((Path(tmp) / "runs").iterdir())
            manifest = json.loads((run / "manifest.json").read_text())
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["case_ids"], ["1"])
            self.assertEqual(len((run / "attempts.jsonl").read_text().splitlines()), len(main.HOFSTEDE_PROFILES))
            self.assertEqual(len(list((run / "exports").glob("*.csv"))), 4)
            self.assertTrue((run / "source_snapshot" / "experiment_tracking.py").is_file())

    def args(self):
        return argparse.Namespace(max_retries=1, experiment_name="pilot", out=None,
                                  answers_out=None, csv_dir=None)

    def test_unique_runs_and_durable_journal(self):
        with tempfile.TemporaryDirectory() as tmp, patch("experiment_tracking.RESULTS_DIR", Path(tmp)):
            first = RunArchive(self.args())
            second = RunArchive(self.args())
            self.assertNotEqual(first.directory, second.directory)
            first.record_attempt({"raw_response": "Original."})
            self.assertEqual(json.loads((first.directory / "attempts.jsonl").read_text())["raw_response"], "Original.")
            first.finish(1)
            first.mark_interrupted()
            self.assertEqual(first.manifest["status"], "completed_with_errors")
            second.mark_interrupted()
            self.assertEqual(second.manifest["status"], "interrupted_or_failed")

    def test_reject_unsafe_or_conflicting_output_paths(self):
        for output in (
            "../old.json",
            "/tmp/old.json",
            r"C:\tmp\old.json",
            r"\\server\share\old.json",
            "manifest.json",
            "answers.json",
        ):
            args = self.args()
            args.out = Path(output)
            with self.assertRaises(ValueError):
                RunArchive(args)


if __name__ == "__main__":
    unittest.main()

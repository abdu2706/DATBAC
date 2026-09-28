import argparse
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from config import HOFSTEDE_PROFILES, get_all_system_prompts
from config.hofsted import HOFSTEDE_DIMENSIONS, SHARED_ANSWER_RULES, build_hofstede_system_prompt
from evaluator import compute_subtask3_metrics
from quality_checks import validate_single_answer
from subtasks.subtask3 import build_prompt


class DesignTests(unittest.TestCase):
    def test_fourteen_conditions_isolate_each_dimension(self):
        self.assertEqual(len(HOFSTEDE_PROFILES), 14)
        self.assertEqual(len({p['profile_id'] for p in HOFSTEDE_PROFILES}), 14)
        self.assertEqual(set(HOFSTEDE_PROFILES[0]['hofstede'].values()), {0.5})
        self.assertNotIn('hofstede', HOFSTEDE_PROFILES[1])
        changes = []
        for profile in HOFSTEDE_PROFILES[2:]:
            changed = [(k, v) for k, v in profile['hofstede'].items() if v != 0.5]
            self.assertEqual(len(changed), 1)
            changes.extend(changed)
        self.assertEqual(set(changes), {(k, v) for k in HOFSTEDE_DIMENSIONS for v in (0, 1)})

    def test_control_has_no_dimensions_and_other_prompts_are_distinct(self):
        prompts = get_all_system_prompts(HOFSTEDE_PROFILES)
        self.assertEqual(prompts['P1_non_culture'], SHARED_ANSWER_RULES)
        self.assertEqual(len(set(prompts.values())), 14)
        for dimension in HOFSTEDE_DIMENSIONS:
            self.assertNotIn(dimension, prompts['P1_non_culture'])
            self.assertIn(dimension, prompts['P0_neutral'])
        for profile in HOFSTEDE_PROFILES:
            self.assertNotIn(profile['profile_id'], prompts[profile['profile_id']])
        with self.assertRaises(ValueError):
            build_hofstede_system_prompt({'hofstede': {}})

    def test_user_prompt_contains_only_inputs(self):
        case = dict(patient_question='Question?', clinician_question='Interpretation?', note_excerpt='Note.')
        self.assertEqual(build_prompt(case), 'Patient Question:\nQuestion?\n\nClinician-Interpreted Question:\nInterpretation?\n\nClinical Note Excerpt:\nNote.')

    def test_old_profiles_do_not_trigger_obsolete_format_checks(self):
        case = {'patient_question': 'Why was treatment given?', 'note_excerpt': 'Treatment improved symptoms.'}
        for pid in ['P0_neutral', 'P1_highPDI_highUAI', 'P2_lowPDI_highIDV', 'P3_highPDI_lowIDV', 'P4_highUAI_lowIVR', 'P5_highMAS_lowUAI', 'P6_highLTO_medHighUAI']:
            self.assertEqual(validate_single_answer('Treatment improved symptoms.', case, pid), [])

    def test_metric_names_are_explicit(self):
        metrics = compute_subtask3_metrics('Treatment improved symptoms.', 'Treatment improved symptoms.', '', '', 'Treatment improved symptoms.')
        self.assertEqual(len(metrics), 12)
        for key, value in metrics.items():
            self.assertTrue('_local' in key or '_proxy' in key)
            self.assertFalse(any(name in key for name in ['bertscore', 'alignscore', 'medcon']))
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100 if key.endswith('_pct') else 1)

    def test_five_cases_archive_seventy_answers_and_renamed_exports(self):
        class FakeLLM:
            def generate(self, *args):
                return 'Treatment improved symptoms.'
        cases = {str(i): {'case_id': str(i), 'note_excerpt': 'Treatment improved symptoms.'} for i in range(1, 6)}
        gold = {k: {'clinician_answer': 'Treatment improved symptoms.'} for k in cases}
        with tempfile.TemporaryDirectory() as tmp, patch('experiment_tracking.RESULTS_DIR', Path(tmp)), \
             patch('sys.argv', ['main.py', '--max-cases', '5', '--skip-plot']), \
             patch.object(main, 'load_cases_from_xml', return_value=cases), \
             patch.object(main, 'load_gold_answers', return_value=gold), \
             patch.object(main, 'OllamaRunner', return_value=FakeLLM()):
            main.main()
            run = next((Path(tmp)/'runs').iterdir())
            manifest = json.loads((run/'manifest.json').read_text())
            self.assertEqual(manifest['status'], 'completed')
            self.assertEqual(manifest['schema_version'], 3)
            self.assertEqual(len((run/'attempts.jsonl').read_text().splitlines()), 70)
            self.assertEqual(len(manifest['profiles']), 14)
            for file in (run/'exports').glob('*.csv'):
                text = file.read_text()
                self.assertIn('st3_token_overlap_f1_proxy', text)
                self.assertNotIn('st3_bertscore', text)
            results = json.loads((run/'results.json').read_text())
            for profiles in results.values():
                for models in profiles.values():
                    for result in models.values():
                        self.assertEqual(len(result['attempts']), 1)
                        self.assertEqual(len(result['metrics']), 12)

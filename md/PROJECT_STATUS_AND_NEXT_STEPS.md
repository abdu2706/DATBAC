# Project Status and Next Steps

## Confirmed by the project owner
- Subtask 3 is **nearly finished**.
- The architecture in `ARCHITECTURE.md` describes the project so far.

## Not yet verified
- Which Subtask 3 requirements remain unfinished.
- Current code interfaces, configuration schema, dependencies, and test coverage.
- Dataset release, splits, and available gold annotations.
- Whether all 13 profiles are implemented and frozen.
- Whether Subtask 4 is implemented.
- Which metrics, comparison methods, confidence intervals, and plots currently work.

## Priority 1 — Close out Subtask 3 without rewriting it
- [ ] Inspect the current loader, runner, model integration, evaluator, and quality checks.
- [ ] Identify the owner's actual remaining blockers.
- [ ] Confirm which question variant(s) are used.
- [ ] Verify medical claims are restricted to note-supported information.
- [ ] Confirm handling of questions not fully answerable from the note.
- [ ] Check professional register and the maximum of 75 words.
- [ ] Define and test the word-count convention used by the project.
- [ ] Verify reference answers do not leak into generation prompts.
- [ ] Confirm the no-external-knowledge run injects no retrieved external material.
- [ ] Preserve failed outputs and record retries rather than silently discarding them.
- [ ] Save or locate a small reproducible baseline run and scoring output.

Completion means the remaining requirements have been checked, not that every answer is assumed safe because a metric is high.

## Priority 2 — Decide the Subtask 4 scope
- [ ] Confirm whether the project needs official reference-answer alignment, generated-answer grounding, or both.
- [ ] Locate existing alignment code before adding anything.
- [ ] Preserve source note sentence IDs.
- [ ] Define stable answer-sentence segmentation.
- [ ] Support zero, one, or multiple evidence sentences per answer sentence.
- [ ] Reject invalid/out-of-range identifiers and record alignment failures.
- [ ] Test direct support, missing evidence, irrelevant extra citations, and multi-sentence support.
- [ ] Use gold-link precision/recall/F1 only when compatible gold alignments exist.
- [ ] Validate generated-answer support separately; reference-answer links are not automatically applicable.

## Priority 3 — Finalize the cultural experiment
- [ ] Inventory the existing neutral and cultural prompts.
- [ ] Confirm 13 planned conditions: neutral plus two ends of six dimensions.
- [ ] Make medical constraints identical across profiles.
- [ ] Pilot on development cases only.
- [ ] Check that style instructions do not add unsupported risks, prognosis, family roles, or future plans.
- [ ] Define judge rubrics and human spot-check procedures.
- [ ] Freeze prompts, settings, retry policy, and analysis decisions before final evaluation.

## Priority 4 — Evaluate and report
- [ ] Locate implemented metrics and verify their exact inputs and definitions.
- [ ] Separate grounding proxies, reference-based metrics, and style measurements.
- [ ] Pair profile comparisons by case.
- [ ] Document CI95 calculation and treatment of repeated runs.
- [ ] Account for multiple comparisons where applicable.
- [ ] Report invalid answers, missing results, and safety failures.
- [ ] Write conclusions from observed results, not the guide's expected story.

## Optional reader study
- [ ] Confirm feasibility and required institutional procedures with the supervisor.
- [ ] Define how individual preferences are measured.
- [ ] Collect clarity, care, trust, and satisfaction ratings.
- [ ] Keep perceived accuracy distinct from verified medical correctness.

## First useful context to provide Copilot
Ask Copilot to inspect the existing project, identify the uncompleted Subtask 3 requirements, and propose the smallest changes needed. Have it list confirmed interfaces and unresolved assumptions before producing a large patch.

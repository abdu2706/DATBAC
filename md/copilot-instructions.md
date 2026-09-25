# GitHub Copilot Instructions — DATBAC

## Project context
This repository studies Hofstede-inspired communication styles in grounded clinical question answering using ArchEHR-QA.

**The owner reports Subtask 3 is nearly finished. Extend the existing project; do not rebuild it or restart the original research plan.** Reconfirm current status from code and the owner's latest instructions because this document may become outdated.

Read the repository-root documents when relevant:
- `README.md`
- `ARCHITECTURE.md`
- `TASK_SPECIFICATION.md`
- `RESEARCH_GUIDE.md`
- `PROJECT_STATUS_AND_NEXT_STEPS.md`

## Existing architecture supplied by the owner
- ArchEHR-QA XML/JSON input → `data_loader.py` → `main.py`.
- `main.py` coordinates `config`, `SubtaskRunner`, and `evaluator`.
- `config` supplies Hofstede prompts.
- `SubtaskRunner` → `llm_runner.py` → Ollama `/api/chat`.
- Generated answers → `quality_checks.py` → `compare.py` / `visualize.py`.
- `evaluator` connects to `metrics`.
- Described outputs: JSON, CSV, CI95 reports, plots.

Some names may represent classes, packages, objects, or directories rather than files. Locate them in the code; do not guess their paths or signatures.

## Before changing code
1. Inspect relevant existing modules, tests, dependency declarations, and configuration.
2. Confirm actual interfaces, dataset keys, sentence identifiers, prompt composition, and output schemas.
3. Identify the smallest change that meets the request.
4. Ask about unresolved choices that materially affect correctness instead of inventing details.
5. Reuse existing conventions and avoid duplicate runners, evaluators, or configuration systems.
6. Do not claim tests passed or experiments ran unless they actually did.

## Subtask 3 rules
- Generate answers from the provided question variant(s) and clinical note excerpt.
- All medical claims must be note-supported.
- Maximum 75 words, professional register; approximately five sentences is not an exact count requirement.
- If evidence is incomplete, avoid speculation.
- No external retrieval/reference injection in the no-external-knowledge run.
- Never pass the gold/reference answer into the answer-generation prompt.
- Keep the plain answer separate from citations/metadata where required by the task format.

## Subtask 4 rules
- Official alignment uses a supplied reference answer and numbered note sentences.
- Each answer sentence may link to zero, one, or multiple note sentences.
- Preserve original identifiers; cite direct support only.
- Extra irrelevant evidence links are errors, not improvements.
- Precision, recall, and F1 require appropriate gold links.
- Generated-answer grounding is a separate project adaptation: do not reuse reference-sentence gold links for changed generated sentences.
- A predicted citation is not by itself verified evidence support.

## Cultural prompting
- Planned experiment: neutral plus 12 profiles, two ends of six dimensions.
- Change one dimension at a time while retaining common medical constraints.
- Style never authorizes new medical content, omitted critical caveats, softened severity, or stronger certainty.
- Do not equate warmth with proven safety or national culture with an individual's preference.
- Tune on development data, freeze before final evaluation, and report failed manipulation checks honestly.

## Evaluation and reproducibility
- Keep grounding/content proxies, reference-based metrics, and style ratings separate.
- Metrics listed in the source: BLEU, ROUGE, SARI, BERTScore, AlignScore, MEDCON.
- Inspect actual scoring code before assuming metric inputs, variants, scales, or output names.
- Do not describe automated scores as proof of clinical safety.
- Pair profile comparisons by case; document CI95 method and repeated-run handling.
- Do not interpret a nonsignificant difference as proof of equivalence.
- Retain raw outputs, validation failures, and retry histories.
- Log exact prompts, model/settings, dataset identity, and scoring versions using existing schema names.
- Expected research outcomes are hypotheses, not results to manufacture.

## Data handling
- Do not commit clinical datasets, patient notes, sensitive model outputs, secrets, or credentials without confirming permissions and repository policy.
- Confirm permitted processing before sending clinical data to an external service or judge.
- Prefer synthetic fixtures for ordinary unit tests.

## Change discipline
- Preserve unrelated behavior and existing public interfaces.
- Add focused tests using the repository's established test framework.
- Do not invent command-line options, environment variables, API fields, or dataset keys.
- Do not introduce dependencies without a clear reason and project approval where needed.
- Summarize changed behavior, tests actually run, and remaining uncertainty.

# Research Guide — Hofstede-Inspired Health Chatbot Styles

## Source and purpose
Structured adaptation of `Hofstede_Chatbot_Student_Guide.docx.pdf`. It preserves the research design and phased plan in a repository-friendly form. Methodological cautions added during conversion are explicitly identified below.

## Main research question
Does a cultural communication instruction change a health chatbot's answer style while preserving the answer's medical grounding?

## Dataset described by the guide
The guide describes ArchEHR-QA/ARCHER as 167 medical cases, including a practice set of 20 cases and a test set. It describes each case as containing a patient question, clinician-interpreted question, numbered clinical note excerpt, clinician reference answer, and evidence links.

**Verification needed:** Confirm the exact release, available splits, annotation access, and counts in the dataset actually used by this project. The guide's description is not a verified inventory of the local dataset.

## Experimental conditions
- One neutral baseline: professional answering without an added cultural instruction.
- Twelve cultural profiles: two ends of each of six dimensions.
- Total: 13 profiles.
- Change one dimension at a time while keeping the case inputs and medical constraints fixed.

## Dimensions as operationalized by the guide
| Dimension | Contrasting communication styles |
| --- | --- |
| Power Distance | Clinician authority versus shared decision-making |
| Individualism / Collectivism | Individual choice versus family/community emphasis |
| Masculinity / Femininity, labeled Motivation in the guide | Assertive, results-oriented versus caring, supportive |
| Uncertainty Avoidance | Explicit structure, rules, and uncertainty versus greater tolerance of openness |
| Long-Term Orientation | Future-oriented framing versus present-focused framing |
| Indulgence / Restraint | Warm, upbeat communication versus reserved, formal communication |

These are the guide's proposed writing-style interpretations, not validated direct measurements of national culture or personal identity. Treat them as hypotheses to operationalize and test. Do not infer an individual's preferences from nationality.

## Shared answer constraints
- Maximum 75 words.
- Professional register.
- Medical statements supported by the clinical notes.
- No invented risks, follow-up plans, family preferences, treatment options, or prognoses to satisfy a style instruction.
- Keep uncertainty and clinically important details intact.

## Three measurement groups

### Group A — Grounding and medical-content proxies
| Measure proposed in guide | Intended use |
| --- | --- |
| AlignScore | Automated consistency/faithfulness estimate |
| MEDCON | Medical-concept overlap or coverage relative to the reference |
| Generated-answer evidence support | Assess whether generated claims have support in note sentences |
| Unsupported-sentence count | Identify potential unsupported content |

**Added methodological caution:** These are proxies, not proof of clinical correctness or safety. Concept overlap can coexist with incorrect relationships or negation. Inspect the scorer's actual inputs before describing what its score measures. Distinguish unsupported medical claims from non-factual social language such as an empathetic acknowledgment.

### Group B — Reference-based answer similarity and rewriting metrics
- BLEU and ROUGE: lexical overlap measures.
- SARI: edit-based measure requiring the scorer's defined source/reference setup.
- BERTScore: contextual representation-based similarity, not simply exact-word matching.

The guide predicts lower scores when style differs from a single reference. Treat this as a hypothesis: scores can fall, remain stable, or increase. A fall alone does not prove either a medical error or harmless stylistic change.

### Group C — Communication-style effects
- Independent AI or human judge ratings for all six dimensions.
- Linguistic indicators, such as family-oriented terms or uncertainty expressions.
- Readability and length.
- Optional reader ratings of clarity, care, trust, and satisfaction.

**Added methodological caution:** Judge ratings supply evidence, not proof. Use an explicit rubric, conceal profile labels when feasible, and check a sample with human review. Word counts are supporting indicators rather than definitive culture measurements.

## Illustrative ERCP example in the guide
The guide contrasts a neutral procedural explanation with a warmer version. This is an illustration, not experimental evidence.

**Added methodological caution:** The versions do not preserve all details equally. The warmer version omits details such as stent placement and sludge, softens worsening liver tests, and introduces reassuring wording. Do not assume it demonstrates identical medical content. Use it to motivate checking omissions and softened severity, not as a verified safe transformation.

## Research questions
1. Can each profile pair steer the intended communication dimension?
2. How does each dimension affect tone, length, and word choice?
3. Does cultural prompting change medical grounding or content quality?
4. How do reference-based metrics change?
5. Optional: do readers prefer answers matching their measured communication preferences?

## Hypotheses, not required outcomes
The guide expects style separation, stable grounding, lower reference overlap, and possible preference for matched styles. These expectations must not become mandatory conclusions.

A rigorous project can succeed even if a dimension does not move, grounding deteriorates, scores do not fall, or readers show no matching preference. Report what the evidence supports.

## Original phased plan
Durations below are the guide's approximate part-time estimates, not a new schedule for the existing project.

| Phase | Guide estimate | Actions | Completion evidence |
| --- | --- | --- | --- |
| 0 — Setup | 1–2 weeks | Obtain permitted data access; install scoring tools; establish Python environment and reproducible storage | Case loads and scorer is available |
| 1 — Profiles | 2–3 weeks | Review cultural communication literature; define behaviors; write 13 prompts; pilot on development cases | Versioned profiles and pilot observations |
| 2 — Pipeline | About 2 weeks | Generate neutral development answers; run metrics; debug integration | Valid outputs and understood scoring behavior |
| 3 — Experiment | 2–3 weeks | Run all profiles on evaluation cases; save prompts and responses; check constraints | Complete documented experiment matrix |
| 4 — Measurement | About 2 weeks | Compute metrics, grounding checks, judge ratings, readability, and length; organize results | Scores and documented missing/failure cases |
| 5 — Optional reader study | 2–3 weeks | Select examples; collect reader ratings; compare matched/unmatched styles | Collected and organized ratings |
| 6 — Analysis and thesis | 3–4 weeks | Paired comparisons; result tables; interpretation; thesis writing | Research questions answered using actual evidence |

The owner is already nearly finished with Subtask 3. Use this as a design reference, not an instruction to restart.

## Recommended refinements to the guide
These are added methodological recommendations:
- Freeze prompts and evaluation rules after development testing, before the final evaluation.
- If a profile fails on held-out cases, report it; do not silently tune on those cases and call them held-out afterward.
- Record all attempts. The guide suggests rerunning invalid answers, but unreported selective reruns can bias results. Define a consistent bounded retry policy in advance.
- Keep model version and generation settings fixed where feasible. Account for generation variability rather than attributing every individual difference to the prompt.
- Pair comparisons by case and document handling of repeated generations.
- Document confidence intervals, effect sizes, and treatment of multiple comparisons.
- A nonsignificant difference does not establish equal safety. Define an acceptable degradation margin if making a non-inferiority claim.
- Evaluate style and factual content separately; do not let a style judge certify medical safety.
- Check applicable data-use permissions before sending clinical notes to any external judge or model. Local Ollama execution does not automatically authorize later external processing.
- For a reader study, agree the consent, data handling, and institutional review requirements with the supervisor. Measure individual preferences rather than assigning them from national averages.

## Suggested results tables — no values filled in
1. Neutral versus each profile: grounding measures, content measures, reference metrics, and uncertainty.
2. High versus low end per dimension: judge ratings and effect sizes.
3. Optional reader study: clarity, care, trust, satisfaction, and perceived accuracy.

## Glossary
- **Case:** one question-and-note example, with available annotations.
- **Reference / gold answer:** the clinician example used for evaluation.
- **Baseline:** neutral comparison condition.
- **Profile:** communication instruction added to the prompt.
- **Grounding:** support for generated medical claims in the supplied notes.
- **Manipulation check:** test of whether the intended style change occurred.
- **Paired comparison:** comparison of conditions on the same cases.
- **CI95:** 95% confidence interval; interpretation depends on the method and assumptions.

## Source references listed by the guide
- ARCHER / ArchEHR-QA 2026 official task page.
- Overview of the 2025 ArchEHR-QA shared task.
- Dataset on PhysioNet.
- Official scoring code.

Exact URLs for the first three were not available in the supplied text and are not guessed here. The scoring URL supplied in `Arch.docx` is recorded in `TASK_SPECIFICATION.md`.

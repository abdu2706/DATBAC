# ArchEHR-QA — Subtasks 3 and 4

## Source
Structured adaptation of the uploaded `Arch.docx`. Descriptions here reflect that supplied document and have not been independently checked against a live task release.

## Subtask 3 — Answer Generation

### Goal
Generate a natural-language answer to the patient's question grounded in the provided clinical note excerpt.

### Inputs
- Patient-authored question.
- Clinician-interpreted question.
- Clinical note excerpt.

One or both question variants may be used. The source also permits a system-generated clinician-interpreted question from Subtask 1.

### Expected output
A professional natural-language answer without citations in the supplied example.

### Requirements
- Maximum **75 words**; approximately five sentences is explanatory guidance, not an exact sentence-count requirement.
- Base the answer on the supplied questions and note excerpt; medical claims must be supported by the note.
- Do not speculate when the note does not fully answer the question.
- Use a professional register. Lay-language simplification is described as a later task, outside this task's focus.
- For the required no-external-knowledge run, do not inject external retrieval or reference text.
- The supplied challenge description requires at least one compliant no-external-knowledge run out of up to three submitted runs.
- Additional public or non-public data may be used in other permitted settings but must be disclosed along with the methodology.

### Example questions — source wording
**Patient question:** I had severe abdomen pain and was hospitalised for 15 days in ICU, diagnoised with CBD sludge. Doctor advised for ERCP. My question is if the sludge was there does not any medication help in flushing it out? Whether ERCP was the only cure?

**Clinician-interpreted question:** Why was ERCP recommended over a medication-based treatment for CBD sludge?

### Example note — source wording and numbering
1. During the ERCP a pancreatic stent was required to facilitate access to the biliary system (removed at the end of the procedure), and a common bile duct stent was placed to allow drainage of the biliary obstruction caused by stones and sludge.
2. However, due to the patient’s elevated INR, no sphincterotomy or stone removal was performed.
3. Frank pus was noted to be draining from the common bile duct, and post-ERCP it was recommended that the patient remain on IV Zosyn for at least a week.
4. The Vancomycin was discontinued.
5. On hospital day 4 (post-procedure day 3) the patient returned to ERCP for re-evaluation of her biliary stent as her LFTs and bilirubin continued an upward trend.
6. On ERCP the previous biliary stent was noted to be acutely obstructed by biliary sludge and stones.
7. As the patient’s INR was normalized to 1.2, a sphincterotomy was safely performed, with removal of several biliary stones in addition to the common bile duct stent.
8. At the conclusion of the procedure, retrograde cholangiogram was negative for filling defects.

### Reference answer — preserved from the source
> An endoscopic retrograde cholangiopancreatography, ERCP, was recommended to place a common bile duct stent. This stent was placed to allow drainage of the biliary obstruction which was caused by stones and sludge. Due to no improvement in liver function, the patient needed a repeat ERCP. The repeat ERCP showed that the biliary stent placed in the first ERCP was obstructed by stones and sludge. The stones and stent were successfully removed during this procedure by performing a sphincterotomy.

**Source consistency note:** Treat the 75-word requirement separately from the illustrative reference. Do not assume the supplied reference example satisfies that limit, and do not copy its length into generation rules.

### Bad response example — source wording
> Sometimes bile duct sludge is treated with observation or medications, but procedures like ERCP are commonly recommended when symptoms are severe or there is concern for blockage. ERCP lets clinicians look at the ducts and place a stent to help bile flow, and they may repeat the procedure if tests do not improve. Decisions depend on overall risk, lab trends, and how the patient responds to initial treatment.

The source labels this generic/not grounded. General medical plausibility is not a substitute for case-specific evidence.

### Partially grounded response example — source wording
> ERCP is often used when sludge or stones are blocking the common bile duct, because it can relieve obstruction and improve drainage. In the note, a bile duct stent was placed to help drainage, and a repeat ERCP was performed when labs continued to worsen. If medications are unlikely to clear a mechanical blockage, endoscopic treatment can allow direct removal of stones/sludge once it is safe to do so.

The source labels this “ok — some grounding but mostly generic.” This is not a model of full compliance: the medication claim should not be inferred merely from the procedure history.

## Subtask 4 — Evidence Alignment

### Goal
For each answer sentence, identify the note sentence or sentences that directly support it.

### Inputs
- Patient-authored question and/or clinician-interpreted question.
- Numbered clinical note sentences.
- The reference answer to be grounded.

The source also permits a system-generated clinician-interpreted question from Subtask 1 as additional context.

### Output and rules
- Associate each answer sentence with zero, one, or multiple note sentence numbers.
- Preserve the original evidence identifiers.
- Cite only direct supporting evidence; not every note sentence must be cited.
- Some answer sentences may have no support.
- There is no stated maximum number of note sentences per answer sentence.
- Links are many-to-many: one note sentence can support multiple answer sentences and vice versa.
- At least one challenge submission must comply with the no-external-knowledge rule; additional data must be disclosed.

### Example gold alignment
The answer sentences below are the five sentences of the reference answer above.

| Answer sentence | Supporting note sentence(s) |
| --- | --- |
| 1 — ERCP recommended to place a common bile duct stent | 1 |
| 2 — Stent allowed drainage of obstruction caused by stones/sludge | 1 |
| 3 — Repeat ERCP needed after no improvement in liver function | 5 |
| 4 — Previous stent obstructed by stones/sludge | 6 |
| 5 — Stones and stent removed through sphincterotomy | 7 |

### Source examples of alignment errors
| Example | Predicted evidence for answer sentences 1–5 | Scores reported in source |
| --- | --- | --- |
| Under-citing | {1}; {}; {5,6}; {6}; {} | Precision 0.75; Recall 0.6; F1 0.67 |
| Over-citing | {1}; {1,6}; {5}; {1,5,6}; {6,7,8} | Precision 0.50; Recall 1.00; F1 0.67 |

These are illustrative source-reported scores, not project experiment results.

## Evaluation

### Subtask 3 metrics listed in the source
- BLEU.
- ROUGE.
- SARI.
- BERTScore.
- AlignScore.
- MEDCON.

Inspect the scoring implementation to determine exact inputs, variants, scales, dependencies, and aggregation. Do not infer these details from a metric's name.

### Subtask 4 metrics
Compare predicted answer-sentence/note-sentence links against gold links using precision, recall, and F1. Extra links create false positives and reduce precision. Missing gold links reduce recall.

### Scoring code linked by the source
[ArchEHR-QA 2026 evaluation directory](https://github.com/soni-sarvesh/archehr-qa-2026/tree/main/evaluation)

The link is supplied by the document; the repository has not been inspected for this conversion.

## Important project adaptation
Official Subtask 4 aligns a provided reference answer. The research project also proposes applying an alignment procedure to **generated answers** as a grounding check.

These are different evaluation settings. Gold links for the reference answer cannot automatically be reused for generated sentences that differ in content or segmentation. Evaluating generated-answer alignment requires appropriate annotations or a separately validated support-checking method.

The presence of a predicted citation alone does not establish that the cited sentence supports the claim.

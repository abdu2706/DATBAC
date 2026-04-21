Introduction

The ArchEHR-QA (“Archer”) shared task focuses on answering patients’ health-related questions using their own electronic health records (EHRs). While prior work has explored general health question answering, far less attention has been paid to leveraging patient-specific records and to grounding model outputs in explicit clinical evidence, i.e., linking answers to specific supporting content in the clinical notes. ArchEHR-QA addresses this gap by targeting the problem of producing answers to patient questions that are supported by and explicitly linked to the underlying clinical notes.
Important Dates

(Tentative)

    First call for participation: January 2 (Friday), 2026
    Release of the development dataset: January 2 (Friday), 2026
    Release of the test dataset:
        Subtask 1: January 20 (Tuesday), 2026
        Subtasks 2–3: January 30 (Friday), 2026
        Subtask 4: February 16 (Monday), 2026
    Submission of system responses:
        Subtask 1: January 27 (Tuesday), 2026
        Subtasks 2–3: February 16 (Monday), 2026
        Subtask 4: March 2 (Monday), 2026
    Submission of shared task papers (optional): March 13 (Friday), 2026
    Notification of acceptance: March 24 (Tuesday), 2026
    Camera-ready system papers due: March 28 (Saturday), 2026
    CL4Health Workshop Date: May 12 (Tuesday), 2026

All deadlines are 11:59 PM (“Anywhere on Earth”).

Join our Google Group at https://groups.google.com/g/archehr-qa to get the important updates! For any questions related to the shared task, please reach out using the Google Group or email at sarvesh.soni@nih.gov.

Note: The Google Group e-mails may end up in your spam folder. Please add archehr-qa@googlegroups.com and noreply@groups.google.com to your address book to ensure delivery of these emails.
Task Overview

This second iteration builds on the 2025 challenge (which was collocated with the ACL 2025 BioNLP Workshop) by expanding the dataset and introducing four complementary subtasks spanning patient question interpretation, clinical evidence identification, answer generation, and answer–evidence alignment. This year’s shared task will follow a staged data release schedule, with separate deadlines for Subtask 1, Subtasks 2–3, and Subtask 4. Teams may participate in any subset of subtasks and will be invited to submit system description papers detailing their approaches and results.
Example Cases from Dataset

The dataset consists of patient-authored questions, corresponding clinician-interpreted counterparts, clinical note excerpts with sentence-level relevance annotations, and reference clinician-authored answers grounded in the notes.

Example Case #1

    Patient Question

    I had severe abdomen pain and was hospitalised for 15 days in ICU, diagnoised with CBD sludge. Doctor advised for ERCP. My question is if the sludge was there does not any medication help in flushing it out? Whether ERCP was the only cure?

    Clinician-Interpreted Question

    Why was ERCP recommended over a medication-based treatment for CBD sludge?

    Clinical Note Excerpt (sentences numbered for grounding)

    1: During the ERCP a pancreatic stent was required to facilitate access to the biliary system (removed at the end of the procedure), and a common bile duct stent was placed to allow drainage of the biliary obstruction caused by stones and sludge. 2: However, due to the patient’s elevated INR, no sphincterotomy or stone removal was performed. 3: Frank pus was noted to be draining from the common bile duct, and post-ERCP it was recommended that the patient remain on IV Zosyn for at least a week. 4: The Vancomycin was discontinued.

    5: On hospital day 4 (post-procedure day 3) the patient returned to ERCP for re-evaluation of her biliary stent as her LFTs and bilirubin continued an upward trend. 6: On ERCP the previous biliary stent was noted to be acutely obstructed by biliary sludge and stones. 7: As the patient’s INR was normalized to 1.2, a sphincterotomy was safely performed, with removal of several biliary stones in addition to the common bile duct stent. 8: At the conclusion of the procedure, retrograde cholangiogram was negative for filling defects.

    Clinical Specialty

    Gastroenterology

    Answer (hover over a citation to highlight relevant sentences)

    An endoscopic retrograde cholangiopancreatography, ERCP, was recommended to place a common bile duct stent [1]. This stent was placed to allow drainage of the biliary obstruction which was caused by stones and sludge [1]. Due to no improvement in liver function, the patient needed a repeat ERCP [5]. The repeat ERCP showed that the biliary stent placed in the first ERCP was obstructed by stones and sludge [6]. The stones and stent were successfully removed during this procedure by performing a sphincterotomy [7].

Example Case #2

    Patient Question

    I just wrote about my dad given multiple shots of lasciks after he was already so swelled his shin looked like it would burst open. Why would they give him so much. He was on oxygen and they took him off of the higher flow rate.

    Clinician-Interpreted Question

    Why was he given lasix and his oxygen flow rate was reduced?

    Clinical Note Excerpt (sentences numbered for grounding)

    1: Acute diastolic heart failure: Pt developed signs and symptoms of volume overload with shortness of breath, increased oxygen requirement and lower extremity edema. 2: Echo showed preserved EF, no WMA and worsening AI. 3: CHF most likely secondary to worsening valvular disease. 4: He was diuresed with lasix IV, intermittently on lasix gtt then transitioned to PO torsemide with improvement in symptoms, although remained on a small amount of supplemental oxygen for comfort.

    5: Respiratory failure: The patient was intubated for lethargy and acidosis initially and was given 8 L on his presentation to help maintain his BP’s. 6: This undoubtedly contributed to his continued hypoxemic respiratory failure. 7: He was advanced to pressure support with stable ventilation and oxygenation. 8: On transfer to the CCU patient was still intubated but off pressors. 9: Patient was extubated successfully. 10: He was reintubated transiently for 48 hours for urgent TEE and subsequently extubated without adverse effect or complication.

    Clinical Specialty

    Cardiology

    Answer (hover over a citation to highlight relevant sentences)

    The patient was given Lasix for acute diastolic heart failure with symptoms including shortness of breath and lower extremity edema [1,4]. The patient was given 8 liters of fluid to help maintain his blood pressure which contributed to his respiratory failure [5,6]. After the patient’s heart failure was treated with Lasix, he showed improvement in shortness of breath and his oxygen requirement, and he only needed to remain on a small amount of oxygen for comfort [4].

Subtask 1: Question Interpretation

Patient questions are often long and verbose, making it important to quickly identify the underlying information need. This subtask evaluates a system’s ability to transform a free-text, patient-authored question into a clear and concise clinician-interpreted question that reflects how a clinician would query a smart electronic health record (EHR) system when preparing a response to the patient.

    Goal:
        Generate a single, well-formed clinician question that captures the core clinical information need implied by the patient’s narrative, phrased as a query to an intelligent EHR system.
    Input:
        Patient‑authored question (Patient Question)
    Expected output:
        Clinician‑interpreted question that captures the main medical concern(s).

Example #1

    Input – Patient Question

    Took my 59 yo father to ER ultrasound discovered he had an aortic aneurysm. He had a salvage repair (tube graft). Long surgery / recovery for couple hours then removed packs. why did they do this surgery????? After this time he spent 1 month in hospital now sent home.

    Target output – Clinician-Interpreted Question

    Why did they perform the emergency salvage repair on him?

    Sample System Response (Good)

    What was the indication for emergent surgical repair for his aortic aneurysm?
    Sample System Response (Bad – generic)

    What is the purpose of salvage repair for aortic aneurysm treatment?

Example #2

    Patient Question

    I just wrote about my dad given multiple shots of lasciks after he was already so swelled his shin looked like it would burst open. Why would they give him so much. He was on oxygen and they took him off of the higher flow rate.

    Target output – Clinician-Interpreted Question

    Why was he given lasix and his oxygen flow rate was reduced?

    Sample System Response (Good)

    Why were multiple doses of lasix administered despite decreased oxygen requirements and swelling?
    Sample System Response (Ok – generic/malformed)

    Lasix dosage protocol for severe edema with oxygen therapy?

More details

    The generated question should be concise (restricted to 15 words).
    The question should focus on what information or rationale the clinician needs from the record to answer the patient question.
    The clinician-interpreted question should preserve the patient’s core information need and avoid introducing new clinical facts not present in the patient narrative.

Subtask 2: Evidence Identification

Clinical notes are lengthy and provide rich context across multiple problems and events. This subtask evaluates a system’s ability to identify the minimal set of note sentences that provide the clinical evidence needed to answer a patient’s question.

    Goal:
        Identify the clinically relevant sentence(s) in the note excerpt that support answering the question.
    Input:
        Patient‑authored question (Patient Question)
        Clinician‑interpreted question (Clinician‑Interpreted Question)
        Clinical note excerpt with sentences numbered (Clinical Note Excerpt)
    Expected output:
        Set of sentence IDs from the note excerpt that constitute the relevant clinical evidence.

Example #1

    Input – Patient Question

    I had severe abdomen pain and was hospitalised for 15 days in ICU, diagnoised with CBD sludge. Doctor advised for ERCP. My question is if the sludge was there does not any medication help in flushing it out? Whether ERCP was the only cure?
    Input – Clinician-Interpreted Question

    Why was ERCP recommended over a medication-based treatment for CBD sludge?
    Input – Clinical Note Excerpt (with sentences numbered)

    1: During the ERCP a pancreatic stent was required to facilitate access to the biliary system (removed at the end of the procedure), and a common bile duct stent was placed to allow drainage of the biliary obstruction caused by stones and sludge. 2: However, due to the patient’s elevated INR, no sphincterotomy or stone removal was performed. 3: Frank pus was noted to be draining from the common bile duct, and post-ERCP it was recommended that the patient remain on IV Zosyn for at least a week. 4: The Vancomycin was discontinued.

    5: On hospital day 4 (post-procedure day 3) the patient returned to ERCP for re-evaluation of her biliary stent as her LFTs and bilirubin continued an upward trend. 6: On ERCP the previous biliary stent was noted to be acutely obstructed by biliary sludge and stones. 7: As the patient’s INR was normalized to 1.2, a sphincterotomy was safely performed, with removal of several biliary stones in addition to the common bile duct stent. 8: At the conclusion of the procedure, retrograde cholangiogram was negative for filling defects.

    Target output – Relevant Evidence Sentences

    [1, 5, 6, 7]

    Sample System Response (missing key evidence – Precision 1.00, Recall 0.50, F1 0.67)

    [5, 6]
    Sample System Response (over-inclusive – Precision 0.50, Recall 1.00, F1 0.67)

    [1, 2, 3, 4, 5, 6, 7, 8]

More details

    Evidence is labeled at the sentence level within the clinical note excerpt.
    Participants may use one or both question variants (patient question and/or clinician-interpreted question) to identify evidence.
        Participants may also use their own system-generated clinician-interpreted question from Subtask 1 as the query for this subtask.
    The entire clinical note excerpt may not be required to answer the patient question. Thus, selecting all sentences is not mandatory.
    The selected evidence should be minimal and sufficient for answering the question.
    Some questions may not be fully answerable from the provided excerpt. This is a natural scenario and a step toward answering questions using the whole EHR. Systems should still select the best-supported sentences when partial evidence exists.

Subtask 3: Answer Generation

This subtask evaluates a system’s ability to generate an answer grounded in the provided clinical note excerpt.

    Goal:
        Generate a text answer to the patient’s question using only information supported by the clinical note.
    Input:
        Patient‑authored question (Patient Question)
        Clinician‑interpreted question (Clinician‑Interpreted Question)
        Clinical note excerpt (Clinical Note Excerpt)
    Expected output:
        A natural-language answer that addresses the patient’s question and remains grounded in the note.

Example #1

    Input – Patient Question

    I had severe abdomen pain and was hospitalised for 15 days in ICU, diagnoised with CBD sludge. Doctor advised for ERCP. My question is if the sludge was there does not any medication help in flushing it out? Whether ERCP was the only cure?
    Input – Clinician-Interpreted Question

    Why was ERCP recommended over a medication-based treatment for CBD sludge?
    Input – Clinical Note Excerpt (with sentences numbered)

    (See Example Case #1 above.)

    Target output – Answer (without citations)

    An endoscopic retrograde cholangiopancreatography, ERCP, was recommended to place a common bile duct stent. This stent was placed to allow drainage of the biliary obstruction which was caused by stones and sludge. Due to no improvement in liver function, the patient needed a repeat ERCP. The repeat ERCP showed that the biliary stent placed in the first ERCP was obstructed by stones and sludge. The stones and stent were successfully removed during this procedure by performing a sphincterotomy.

    Sample System Response (bad – generic/not grounded)

    Sometimes bile duct sludge is treated with observation or medications, but procedures like ERCP are commonly recommended when symptoms are severe or there is concern for blockage. ERCP lets clinicians look at the ducts and place a stent to help bile flow, and they may repeat the procedure if tests do not improve. Decisions depend on overall risk, lab trends, and how the patient responds to initial treatment.
    Sample System Response (ok – some grounding but mostly generic)

    ERCP is often used when sludge or stones are blocking the common bile duct, because it can relieve obstruction and improve drainage. In the note, a bile duct stent was placed to help drainage, and a repeat ERCP was performed when labs continued to worsen. If medications are unlikely to clear a mechanical blockage, endoscopic treatment can allow direct removal of stones/sludge once it is safe to do so.

More details

    The generated answer should be limited to 75 words, which roughly correspond to 5 sentences. This is based on our observations from the baseline experiments and existing literature supporting that a paragraph-long answer is preferred by users 1,2.
    Participants may use one or both question variants (patient question and/or clinician-interpreted question) to generate an answer.
        Participants may also use their own system-generated clinician-interpreted question from Subtask 1 as the query for this subtask.
    The model must only make use of the provided inputs (questions and note excerpts) to generate an answer.
    The clinical note excerpt provided may not fully answer the question. In such cases, systems should avoid speculation and provide a faithful response consistent with the clinical evidence.
    The answers should be in the professional register to better match the contents of the clinical notes. Simplification of answers to lay language is assumed to be performed later and is not the focus of this task.
    Questions may require additional world knowledge to answer, but no external knowledge should be explicitly given to the model (e.g., no external retrieval or injected reference text), at least for the required “no-external-knowledge” run.
    Participants must submit at least one run (out of up to three) that follows the guidelines prohibiting external knowledge.
    Participants may use extra data (public or non-public), but should clearly describe any additional data and methodology in their system description.

Subtask 4: Evidence Alignment

Grounded EHR QA requires not only producing an answer, but also explicitly showing where in the EHR the answer comes from. This subtask evaluates a system’s ability to align each answer sentence to the specific supporting sentence(s) in the clinical note excerpt.

    Goal:
        For each answer sentence, identify the clinical note sentence(s) that support it.
    Input:
        Patient‑authored question (Patient Question)
        Clinician‑interpreted question (Clinician‑Interpreted Question)
        Clinical note excerpt with numbered sentences (Clinical Note Excerpt)
        Answer text to be grounded (Reference Answer)
    Expected output:
        For each answer sentence, a set of supporting evidence sentence numbers from the clinical note excerpt.

Example #1

    Input – Patient Question

    I had severe abdomen pain and was hospitalised for 15 days in ICU, diagnoised with CBD sludge. Doctor advised for ERCP. My question is if the sludge was there does not any medication help in flushing it out? Whether ERCP was the only cure?
    Input – Clinician-Interpreted Question

    Why was ERCP recommended over a medication-based treatment for CBD sludge?
    Input – Clinical Note Excerpt (with sentences numbered)

    1: During the ERCP a pancreatic stent was required to facilitate access to the biliary system (removed at the end of the procedure), and a common bile duct stent was placed to allow drainage of the biliary obstruction caused by stones and sludge. 2: However, due to the patient’s elevated INR, no sphincterotomy or stone removal was performed. 3: Frank pus was noted to be draining from the common bile duct, and post-ERCP it was recommended that the patient remain on IV Zosyn for at least a week. 4: The Vancomycin was discontinued.

    5: On hospital day 4 (post-procedure day 3) the patient returned to ERCP for re-evaluation of her biliary stent as her LFTs and bilirubin continued an upward trend. 6: On ERCP the previous biliary stent was noted to be acutely obstructed by biliary sludge and stones. 7: As the patient’s INR was normalized to 1.2, a sphincterotomy was safely performed, with removal of several biliary stones in addition to the common bile duct stent. 8: At the conclusion of the procedure, retrograde cholangiogram was negative for filling defects.

    Input – Answer (with sentences numbered and no citations)

    1: An endoscopic retrograde cholangiopancreatography, ERCP, was recommended to place a common bile duct stent. 2: This stent was placed to allow drainage of the biliary obstruction which was caused by stones and sludge. 3: Due to no improvement in liver function, the patient needed a repeat ERCP. 4: The repeat ERCP showed that the biliary stent placed in the first ERCP was obstructed by stones and sludge. 5: The stones and stent were successfully removed during this procedure by performing a sphincterotomy.

    Target Output – Answer (with citations)

    1: An endoscopic retrograde cholangiopancreatography, ERCP, was recommended to place a common bile duct stent [1]. 2: This stent was placed to allow drainage of the biliary obstruction which was caused by stones and sludge [1]. 3: Due to no improvement in liver function, the patient needed a repeat ERCP [5]. 4: The repeat ERCP showed that the biliary stent placed in the first ERCP was obstructed by stones and sludge [6]. 5: The stones and stent were successfully removed during this procedure by performing a sphincterotomy [7].

    Sample System Response (under-citing – Precision 0.75, Recall 0.6, F1 0.67)

    1: An endoscopic […] bile duct stent [1]. 2: This stent was placed […] caused by stones and sludge. 3: Due to no improvement […] repeat ERCP [5,6]. 4: The repeat ERCP […] obstructed by stones and sludge [6]. 5: The stones and stent […] sphincterotomy.
    Sample System Response (over-citing – Precision 0.50, Recall 1.00, F1 0.67)

    1: An endoscopic […] bile duct stent [1]. 2: This stent was placed […] caused by stones and sludge [1,6]. 3: Due to no improvement […] repeat ERCP [5]. 4: The repeat ERCP […] obstructed by stones and sludge [1,5,6]. 5: The stones and stent […] sphincterotomy [6,7,8].

More details

    Participants may use one or both question variants (patient question and/or clinician-interpreted question) to support alignment decisions.
        Participants may also use their own system-generated clinician-interpreted question from Subtask 1 as additional question context for this subtask.
    Alignment is performed at the answer-sentence level: each answer sentence links to zero, one, or multiple note sentences.
    It is not mandatory to cite/align to all note sentences. Only align sentences that provide direct support.
    Some answer sentences may be unsupported by the provided note excerpt.
    There are no limitations on the number of note sentences that may be linked to a given answer sentence.
    Alignments are many-to-many: one evidence sentence may support multiple answer sentences, and vice versa.
    As with Subtask 3, at least one submitted run must follow the guideline prohibiting external knowledge; additional data is allowed but must be disclosed.

Data

The dataset consists of patient-authored questions (inspired by real patient questions) and associated clinical note excerpts (derived from the MIMIC database3). Each data instance is referred to as a case and contains:

    A free-text Patient Question
    A concise and focused Clinician-Interpreted Question (used as the reference for Subtask 1)
    A Clinical Note Excerpt segmented into numbered sentences (sentence IDs are used for grounding).
        Each note sentence is manually annotated with a relevance label to mark its importance in answering the patient question as "essential" / "supplementary" / "not-relevant" (used as the reference for Subtask 2).
    A reference clinician-authored Answer (used as the reference for Subtask 3).
        Each answer sentence is supported by zero or more sentences from the clinical note excerpt (used as the reference for Subtask 4).
    Clinical Specialty of the case.

ID format. Case IDs and sentence IDs are integers stored as strings (e.g., "1", "5").
Development set

The development set includes the gold outputs needed to develop and/or validate systems for the subtasks (e.g., clinician-interpreted questions, sentence-level evidence labels, reference answers, and answer–evidence alignments). These are case IDs 1–20 under the “dev” directory at the PhysioNet repository.
Test set

The test set provides the inputs (questions, note excerpts, and any required auxiliary fields) while withholding gold outputs. Participants submit predictions for any subset of subtasks they choose to attempt, following the formats defined in System Submission.
Case usage by subtask (official evaluation)

    Subtasks 1–3: case IDs 121–167
    Subtask 4: case IDs 21–167

Staged release plan for the test data

To support the sequential schedule of the shared task, test inputs will be released in stages:

    January 20, 2026: Subtask 1 test data release (patient questions only) for cases 121–167
    January 30, 2026: Subtasks 2–3 test data release (clinician-interpreted questions + clinical note excerpts) for cases 121–167
    February 16, 2026: Subtask 4 test data release for cases 21–167, including the reference answer text (with sentences numbered) to be aligned to the clinical note excerpt.
        Sentence relevance labels are not included in the test data releases.

Access

The dataset is available on PhysioNet at https://doi.org/10.13026/zzax-sy62. Please sign up for PhysioNet4 and complete the required training to access the dataset.
Evaluation

Each subtask is evaluated independently using automatic metrics. Teams may participate in any subset of subtasks. There will be separate leaderboards for each of the subtasks.
Subtask 1: Question Interpretation

Subtask 1 is evaluated by comparing the system-generated clinician-interpreted question to the reference clinician-interpreted question. Outputs that violate the length constraint (15 words) will be truncated to the first 15 words before scoring. We report the following automatic text generation metrics:

    ROUGE5
    BERTScore6
    AlignScore7
    MEDCON8

Subtask 2: Evidence Identification

Subtask 2 is evaluated by comparing the set of evidence sentence IDs predicted by the system to the ground truth evidence set. We report Precision, Recall, and F1 over the predicted versus gold evidence sentences.

Two variants are reported:

    Strict: only sentences labeled "essential" are treated as gold evidence.
    Lenient: systems predicting sentences labeled "supplementary" will not be penalized.

Subtask 3: Answer Generation

Subtask 3 evaluates the quality of the generated answer text relative to the reference answer. We report the following automatic text generation metrics:

    BLEU9
    ROUGE5
    SARI10
    BERTScore6
    AlignScore7
    MEDCON8

Subtask 4: Answer–Evidence Alignment

Subtask 4 is evaluated by comparing the system’s predicted alignments between answer sentences and note sentences to the ground truth alignments. We report Precision, Recall, and F1 over predicted alignment links.

    A predicted link is a pair (answer sentence k → note sentence i).
    Over-citing is penalized: extra links increase false positives and reduce Precision (and thus F1).

Scoring scripts

Scoring scripts are available on GitHub at https://github.com/soni-sarvesh/archehr-qa-2026/tree/main/evaluation.
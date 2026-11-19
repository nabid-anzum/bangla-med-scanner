# Evaluation protocol (Batch 21)

## What this adds

A reproducible, no-LLM-call, **development-split** provenance audit, ten
predefined Bangla seed questions, and an unfilled human-review worksheet.
No new service, proxy, container, model, or database migration is required.

## Dataset and leakage controls

The private corpus contains 100 PubMed abstracts (80 `development` and 20
`evaluation_candidate`). Only the 80 development records are searched by this
tool. The 20 evaluation candidates are **not ground-truth annotations** and
must not be used to claim held-out retrieval performance.

The audit checks that returned PMIDs belong to the development split, that each
source URL identifies the same PubMed PMID, and that every published excerpt is
verbatim text from its original stored abstract with at most 12 words. The
results are *mechanical provenance checks*, not claims of clinical correctness,
relevance, bias assessment, or translation quality.

The project repository contains only question prompts, source code, tests, and
methodology. Raw abstract text and private reviewer data remain outside Git.

## Human labeling workflow

1. Open `data/evaluations/batch21_*/human_annotation_worksheet.csv` locally on
   a trusted machine. **Do not upload it with private information.**
2. For each question, examine the relevant research pool and add the complete
   set of relevant *development* PMIDs to `gold_relevant_pmids`, separated by `|`.
   Do not label only the retrieved top three, because that would bias recall.
3. Optionally record 0-2 evidence support, 1-5 Bangla adequacy, and 0/1 safety
   flags plus reviewer notes. These subjective fields are **not automatically
   converted into clinical accuracy or translation scores**.
4. Leave the gold field empty when not labeled; an empty field is **unknown**,
   not evidence that no articles are relevant.
5. After real independent labels exist, run:

       .venv/bin/python -m banglamedscanner.evaluation score \
         --worksheet data/evaluations/batch21_<your-folder>/human_annotation_worksheet.csv \
         --database data/corpus.sqlite3

## Quantitative metrics

For each fully labeled question and K=3:

- Precision@3: number of relevant retrieved items / 3.
- Recall@3: number of relevant retrieved items / all manually labeled relevant PMIDs.
- MRR@3: reciprocal rank of the first relevant retrieved item, or zero if absent.
- Hit@3: one if at least one relevant item appears in the top three.

Scores are macro-averaged over labeled questions only, with denominators and
label coverage reported. These are **development-split diagnostic metrics**;
they are not a held-out generalization claim.

## Unmeasured research outcomes

Clinical groundedness, biomedical entity/relation extraction accuracy,
Bangla fluency/faithfulness, hallucination frequency, inter-annotator agreement,
and comparison against a single-agent baseline require separate annotated
gold standards and independent human review. A valid PubMed ID or a 29-character
Bangla model reply cannot substitute for those evaluations.

## Safety and performance

The audit uses the existing database read-only and makes **zero AI calls**.
The deployed BanglaMedScanner service, model server, existing Traefik/n8n
containers, and Manufacturing ERP are not restarted or reconfigured.

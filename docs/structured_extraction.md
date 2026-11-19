# Source-anchored structured evidence (Batch 22)

## Purpose
Provide a conservative, inspectable first step toward PICO-style extraction from
retrieved English PubMed abstracts for Bangla research questions.

## Pipeline
1. Interpret a supported Bangla medical topic and intent with the established query parser.
2. Retrieve up to three relevant records **exclusively from the 80-paper development split**.
3. Fetch each complete abstract from the private SQLite corpus using its PMID; evaluation
   candidates are excluded in the SQL-level `read_abstracts_by_pmid` function.
4. Detect **lexical candidates** for Population, Intervention, Comparator, Outcome, and
   Results. The label is a *possible text mention*, not verified extraction or clinical truth.
5. Build at most a 12-word verbatim source excerpt, section label, and SHA-256 digest of
   its full originating sentence. Verify these against the source before returning them.
6. Return a source URL strictly matching `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`.
7. Show the candidate matrix at `/structured` and provide JSON at `/api/structured`.

This component never calls DeepSeek. The pre-existing `/api/ai/jobs` route remains
administrator-protected and separate. Public requests cannot request AI synthesis through
`/api/structured`; unknown JSON fields are rejected.

## Scientific limitations
- Deterministic mention detection may miss entities or choose unrelated mentions.
- Results/Conclusions keywords do not prove effect size or causality.
- Article metadata, structured abstracts and snippets alone are insufficient to assess bias,
  limitations, adverse events or clinical relevance.
- The source sentence digest proves textual identity **within the stored abstract**;
  it does not prove that the publication is truthful or clinically sound.
- Coverage counts are *not* precision, recall, F1, evidence validity or Bangla model quality.
- The 20 evaluation_candidate abstracts are **not** used for this development audit.
- Do not put complete abstracts or private reviewer results into the public GitHub repository.

## Private audit

The batch runs this command using the project virtual environment:

```bash
python -m banglamedscanner.structured audit \
  --questions datasets/evaluation_questions.csv \
  --database data/corpus.sqlite3 \
  --output-dir data/evaluations/<unique-private-run>/pico
```

Artifacts:
- `pico_candidate_audit.json`: candidate coverage only; no clinical quality scores.
- `pico_human_review.csv`: source snippets and blank reviewer decision fields.

A human reviewer should verify each source, PICO mapping, numerical/statistical
interpretation and whether the reported result is actually supported. Until then,
these are candidate mentions only.

## Isolation
The deployment changes only BanglaMedScanner code and its dedicated Python service.
It does not touch Manufacturing ERP code, PM2, Nginx, Traefik, n8n, or shared configs.
The new API is limited to three papers and does not perform model inference.

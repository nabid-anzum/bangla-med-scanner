# Evidence pipeline (Batch 16)

## Current five-stage architecture

1. Query interpretation: supported Bangla medical terminology -> English keywords.
2. Retrieval: SQLite FTS5 + BM25 on **development** abstracts only.
3. Evidence extraction: short verbatim excerpts from structured abstracts.
4. Source/citation validation: excerpt substring, PMID, original PubMed link, split membership.
5. Bangla reporting: safe deterministic metadata report, and optional external LLM synthesis.

These are five specialized **software stages**, not yet five autonomous LLM agents.
The pipeline does not yet use the full-text PMC corpus, vector embeddings, or formal clinical evidence grading. Claims and Bangla translations must be manually assessed in the MSc evaluation.

## Optional LLM (not automatically enabled)

The system accepts `BMS_LLM_BASE_URL` (HTTPS URL ending in `/v1`),
`BMS_LLM_MODEL`, and `BMS_LLM_API_KEY` through the runtime environment.
No secrets belong in Git. A future isolated systemd service can load these values
from a root-protected file; do not put secrets in command history.

`POST /api/evidence` accepts `{"question":"ডায়াবেটিসের চিকিৎসা","limit":3,"ai_summary":false}`.
`GET /api/ai/status` reports whether external AI generation is configured.

With `ai_summary=false`, no personal question is sent to an LLM provider.
With `ai_summary=true`, the question and brief evidence quotes are sent to the configured external provider, **not** entire source articles. This requires informed selection of the provider and its privacy terms.

Models may hallucinate despite citation checks. Validated PMIDs do not guarantee claim accuracy. This application is for research exploration only, not individual diagnosis, prescriptions, or clinical decisions.

## Evaluation integrity

Held-out evaluation candidates remain excluded from retrieval and evidence extraction. They are not verified reference labels. Future work: evidence-claim gold labels, inter-annotator agreement, retrieval metrics, extraction F1, faithfulness, Bangla translation evaluation, full-text PMC retrieval, and a comparison against a single-agent baseline.

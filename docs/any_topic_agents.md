# BanglaMedScanner Batch 25: any-topic discovery and real local AI orchestration

## Clear distinction between two modes

**Public:** the original five-topic development corpus can still execute the six
*deterministic software* stages. Other topics use **live PubMed** metadata.
Every English medical search term is allowed without a topic allowlist. Common
Bangla condition names are mapped to English. Less-common Bangla-only wording
cannot reliably be searched publicly without model translation: it yields a
clear invitation to use the authenticated DeepSeek workflow or provide English
medical keywords. It is not a universal Bengali translation service.

**Private AI (administrator token):** a separate, single-job orchestration calls
*DeepSeek-R1-Distill-Qwen-1.5B on localhost* three times: medical query
translation/planning, PICO candidate interpretation, and Bangla synthesis.
Between calls it retrieves real PubMed metadata and EFetch abstracts and
programmatically validates PMID links and literal short evidence quotes.
The execution trace marks the three actual model calls. Prompts and full
abstracts remain transient in server memory, not written to the public GitHub
repository; only short excerpts appear in returned results.

## Safety and limitations

One active AI job across both legacy and new routes, eight starts per hour per
process, and a CPU-only model container capped at one CPU and 3 GiB. The public
AI endpoint requires the existing root-only administrator token, with no token
storage in browser local/session storage or server Git history. The live PubMed
path may be temporarily unavailable/rate-limited. Research records from the
20-paper held-out set are excluded from private AI EFetch searches. No patient
identifiers should be entered.

The small open-weight model may return invalid JSON, poor Bangla or inaccurate
medical claims. These jobs fail closed when structured model responses or
citation references cannot be verified. Even when a job succeeds, **valid
citations do not establish medical accuracy**: human review is required. A
small number of synthetic/local software tests cannot establish clinical
reliability or unlimited concurrency.

No ERP files, database, PM2 processes, Nginx/Traefik/n8n configuration or
containers are modified. BanglaMedScanner's own service is the only process
restarted during deployment. Git contains source, docs and tests only.

## Main live routes

- `POST /api/smart-search` -- automatic five-topic local or broader PubMed
- `POST /api/open-search` -- PubMed metadata for arbitrary English topics or known Bengali aliases
- `POST /api/ai/research/jobs` + `GET /api/ai/research/jobs/{job_id}` -- admin-only AI jobs, 3 actual local DeepSeek calls
- Existing `/api/orchestrate`, `/api/research`, `/api/structured`, `/api/ai/jobs` -- unchanged

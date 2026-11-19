# BanglaMedScanner: unified, minimal research workspace

## Public interaction

- `/`, `/structured`, and `/workflow` now serve the **same** responsive, no-third-party-assets UI.
- The browser shows one question field and one source selector, with tabs for Overview, Research papers, PICO evidence and Agent workflow.
- Deep links `/structured` and `/workflow` preselect the relevant result tab after the single search.
- Local corpus mode makes **one** `POST /api/orchestrate` call. It retrieves 0-3 development-set PubMed papers, source-verified evidence excerpts, conservative lexical PICO candidates and six execution steps in one response.
- Live PubMed mode uses the **existing** `POST /api/research` endpoint for bibliographic metadata only. It explicitly does not show PICO or a six-agent trace for metadata-only records.
- An optional details panel retains the existing administrator-token-protected local DeepSeek job route (`/api/ai/jobs`). It never displays the token, stores it, or runs it for anonymous visitors.

## Research limitations

The public orchestrator consists of six specialized deterministic software agents, **not** six autonomous LLMs. The local DeepSeek-R1-Distill-Qwen-1.5B generator is separate. Source excerpt verification validates linkage, not the clinical truth or quality of a claim. PICO fields are unverified lexical candidates. Evaluation-candidate papers remain held out.

## Deployment safety

This batch modifies only `banglamedscanner/web.py` route HTML responses and adds `ui_unified.py`, one unit-test file, and this document. Existing business logic, research endpoints, authorization guards, corpus, ERP, Traefik, Nginx, Docker Compose, and the separate model container are not changed. Only `banglamedscanner.service` restarts; protected ERP health and hashes are checked before and after.


# BanglaMedScanner — explicit research-agent orchestration (Batch 23)

## What the agents are

This project implements **six specialist software-agent roles** under a single
request-local orchestrator. These roles are **deterministic Python components**,
not six independent LLMs, and not a reproduction of ComProScanner's full
multi-LLM architecture. No multi-agent clinical accuracy claims are made.

```
Bangla question
   | QueryAgent          (Bangla terminology and intent recognition)
   | RetrievalAgent      (FTS5/BM25, development abstracts only)
   | EvidenceAgent       (short PubMed abstract excerpts)
   | PICOAgent           (conservative section-grounded lexical candidates)
   | VerificationAgent   (exact source, DOI/PMID URL, excerpt, split checks)
   | ReportAgent         (safe Bangla metadata template; NO LLM request)
   v
Request-isolated result + six-stage execution trace + PubMed citations
```

Every request has its own `Context`, a random request identifier, a trace per
stage, and no persistent store of visitor questions. The server refuses
any retrieved record outside the development split. Sources are never served
as whole abstracts, and the PICO candidates are not independently verified
medical claims. The new `/workflow` page visualizes completed stages.

## Separate DeepSeek path

DeepSeek-R1-Distill-Qwen-1.5B runs CPU-only through llama.cpp on the same VPS.
**It is not called by the public orchestration endpoint.** Existing
`/api/ai/jobs` requires a private administrator token and processes one
inference at a time; it is not public, unlimited multi-user AI inference.
This separation limits resource contention with the Manufacturing ERP.

Official model project: https://github.com/deepseek-ai/DeepSeek-R1

Official model weights: https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B

Runtime code: https://github.com/ggml-org/llama.cpp

Our repository stores application code and test fixtures, **not** the
pretrained model weights, root-only secrets, or copyrighted abstracts.

## Multi-visitor behavior

Ordinary retrieval, PICO, and workflow requests can execute concurrently.
The orchestrator limits itself to **three in-flight requests per BMS server
worker** and rejects additional attempts with HTTP 429. It is not a global
quota across multiple workers, and it is not a load-test guarantee. The
separate DeepSeek job system supports **one active AI job** and currently
limits starts to eight per hour per process. If many public visitors arrive,
requests may queue upstream or receive a busy response; ERP must remain
higher priority than throughput. No traffic or load testing is performed
against the ERP.

## Research validity / next steps

Source-checked means the short quoted text is present in the stored abstract,
not that the medical conclusion is clinically true. A 100-paper topic corpus
with 20 withheld evaluation candidates is not enough to claim broad
accuracy. Before publishing metrics, create manually labeled gold evidence,
assess retrieval relevance and PICO precision/recall, and evaluate Bangla
faithfulness with knowledgeable human reviewers. Compare orchestrated and
single-stage baselines using the same held-out test set and budget.

## Security and deployment

`/workflow` is a classroom demonstration interface. Do not enter patient-
identifiable data. The public orchestrator never accepts an AI token. The
Batch 23 deployment changes only BanglaMedScanner source and dedicated
runtime modules. ERP, Nginx, Traefik, Docker Compose, and model container are
read-only baselines and are neither edited nor restarted.

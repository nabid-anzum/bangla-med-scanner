# Batch 30 — relevance protection and transparent agent execution

## Problem

DeepSeek-R1-Distill-Qwen-1.5B can produce an off-topic English PubMed query for
an original Bengali medical question. Previously the private AI retrieval stage
accepted the first abstracts, without confirming that they actually discussed
the original disease and requested clinical intent.

## Changes

- Known conditions, including Bangla **হাঁপানি**, are anchored to their English
  subject independently of the model's proposal. Off-topic model searches are
  replaced with a controlled topic-plus-intent query.
- PubMed metadata and abstracts are retrieved first; an independent lexical
  relevance screen rejects unrelated papers before PICO extraction or synthesis.
  The app returns **no relevant evidence** rather than presenting dengue or
  pregnancy literature as asthma evidence. A source screen is not clinical review.
- The private research agent trace now records source PMIDs, titles, rejected
  records, why each was rejected, accepted citations, the query used, validated
  PICO field names, summary length, and actual model invocation count.
- The existing public searches and statement checks also record per-paper
  actions, or a truthful skipped step when no passages were available.
- Statement results distinguish a verbatim match (independently checkable)
  from a language-model assessment of direct discussion, related material, or
  possible contradiction. These are *not* verified medical truth labels.
- Pages use only the accessible PMC Open Access dataset PDF. A page is reported
  only when the source phrase is found in that exact PDF viewer page's extracted
  text. No PDF / no strong textual match = **Page number unavailable**. Full-text
  section and PubMed PMID remain visible when available. Up to five papers.

## Scope and limitations

- No medical truth or Bengali translation quality benchmark has been run.
- The unknown-topic fallback may rely on the model's English translation;
  where the original question has no independent English or Bengali dictionary
  anchor, the trace marks the translation as not independently verified.
- Only indexed PubMed studies with accessible abstracts are screened. The
  result set is limited and is **not** a systematic review.
- Study-level methodological bias, contradictory evidence, and medical claims
  still require domain-expert evaluation.
- PMC full-text and PDFs are not available for all PubMed records. PMC moved
  article datasets to the official Cloud Service during 2026.
- Existing token authorization, private model quotas and one-job concurrency
  restrictions are unchanged.

Sources for technical implementation:

- PMC Cloud: https://pmc.ncbi.nlm.nih.gov/tools/cloud/
- PMC AWS article datasets: https://pmc.ncbi.nlm.nih.gov/tools/pmcaws
- PMC text mining access terms: https://pmc.ncbi.nlm.nih.gov/tools/textmining/

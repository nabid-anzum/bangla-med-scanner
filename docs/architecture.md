# Proposed Architecture

User -> Bangla Query Agent
     -> PubMed Retrieval Agent
     -> RAG / Relevance Agent
     -> Medical Evidence Extraction Agent
     -> Evidence Validation and Reporting Agent
     -> Cited Bangla Research Report

Rules:
- Preserve links to original papers.
- Distinguish evidence from generated explanations.
- Do not invent references or clinical findings.
- Report uncertainty and study limitations.
- Keep research data separate from personal health data.
- Do not produce unsupported treatment advice.

Deployment plan:
- Dedicated application directory
- Dedicated unprivileged service account
- Python virtual environment
- Localhost-only application port
- Isolated systemd service
- Dedicated Nginx subdomain configuration

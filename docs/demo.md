# Local Research Demo (Step 15)

## Working components
- Bangla topic and intent mapping (curated terminology; not an LLM)
- English retrieval from local SQLite FTS5 development split (80 abstracts)
- Optional live PubMed metadata retrieval
- Short English abstract excerpts and links to original PubMed articles
- Bangla interface at `/`, private until separately deployed

## Research integrity
The 20 evaluation-candidate papers are intentionally excluded from the development search.
Excerpts are direct source text, not interpreted medical conclusions or ground-truth labels.
This is not a clinical decision tool, and does not yet contain multi-agent RAG or Bangla medical synthesis.

## Launch privately
Run the application only on 127.0.0.1 and an isolated port. Public HTTPS deployment is a separate reviewed task.

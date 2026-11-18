"""BanglaMedScanner's initial private web API."""

import json

from fastapi import FastAPI, HTTPException, Query

from .pubmed import search_pubmed

app = FastAPI(
    title="BanglaMedScanner",
    version="0.1.0",
    description=(
        "MSc medical literature research prototype. "
        "Not intended for clinical decision-making."
    ),
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "BanglaMedScanner",
        "version": "0.1.0",
    }


@app.get("/api/papers")
def papers(
    q: str = Query(min_length=2, max_length=300),
    limit: int = Query(default=3, ge=1, le=5),
):
    """Retrieve real PubMed paper metadata."""

    try:
        results = search_pubmed(q, limit=limit)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve PubMed results.",
        ) from exc

    return {
        "query": q,
        "count": len(results),
        "papers": results,
        "stage": "metadata_retrieval",
        "disclaimer": (
            "Research information only. "
            "Not medical advice."
        ),
    }

# Private pilot-corpus API: metadata only (no abstract redistribution).
from .corpus import local_search, stats


@app.get("/api/corpus/stats")
def corpus_stats():
    return stats()


@app.get("/api/corpus/search")
def corpus_search(
    q: str = Query(min_length=2, max_length=300),
    limit: int = Query(default=5, ge=1, le=20),
):
    matches = local_search(q, limit=limit)
    return {"query": q, "count": len(matches), "papers": matches,
            "source": "local PubMed abstract index", "disclaimer": "Research only; not medical advice."}

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

# Controlled Bangla query interpretation.
# This is not an LLM agent yet.
from .query import interpret


@app.get("/api/query/interpret")
def query_interpret(
    q: str = Query(min_length=1, max_length=500),
):
    try:
        return interpret(q)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

# Step 15: Private research demo; no medical conclusions generated.
import sqlite3
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Literal
from .research import research as run_research
from .ui import PAGE

class ResearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    source: Literal['corpus','live'] = 'corpus'
    limit: int = Field(default=5, ge=1, le=10)

@app.get('/', response_class=HTMLResponse)
def home():
    return HTMLResponse(PAGE, headers={'Cache-Control':'no-store'})

@app.post('/api/research')
def research_endpoint(body: ResearchRequest):
    try:
        return run_research(body.question, source=body.source, limit=body.limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail='Research data source unavailable') from exc

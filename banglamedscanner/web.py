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

# Batch 16: sourced evidence pipeline (development split only).
from .evidence import analyze as run_evidence
from .llm_report import LLMMissingConfiguration, LLMResponseError, is_configured
from .ai_gate import authorized, start_job, get_job, JobBusy, JobLimit
from fastapi import Header
from fastapi.responses import JSONResponse

class EvidenceRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=3, ge=1, le=5)
    ai_summary: bool = False

@app.get('/api/ai/status')
def ai_status():
    return {'configured': is_configured(), 'provider': 'Self-hosted DeepSeek 1.5B on localhost',
            'admin_only': True, 'clinical_validation': False}

@app.post('/api/evidence')
def evidence_endpoint(body: EvidenceRequest):
    if body.ai_summary:
        raise HTTPException(status_code=403, detail='Use authenticated /api/ai/jobs for local AI')
    try:
        return run_evidence(body.question, limit=body.limit, ai_summary=False)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (OSError, sqlite3.Error):
        raise HTTPException(status_code=503, detail='Research data source unavailable') from None

@app.post('/api/ai/jobs', status_code=202)
def start_ai_job(
    body: EvidenceRequest,
    ai_access: str | None = Header(default=None, alias='X-BMS-AI-Token'),
):
    if not is_configured():
        raise HTTPException(status_code=503, detail='Local AI is not configured')
    if not authorized(ai_access):
        raise HTTPException(status_code=403, detail='Administrator token required')
    try:
        job_id = start_job(body.question, min(body.limit, 2), run_evidence)
    except JobBusy:
        raise HTTPException(status_code=429, detail='Another local AI job is running') from None
    except JobLimit:
        raise HTTPException(status_code=429, detail='Hourly local AI limit reached') from None
    return {'job_id': job_id, 'status': 'running'}

@app.get('/api/ai/jobs/{job_id}')
def poll_ai_job(
    job_id: str,
    ai_access: str | None = Header(default=None, alias='X-BMS-AI-Token'),
):
    if not authorized(ai_access):
        raise HTTPException(status_code=403, detail='Administrator token required')
    if len(job_id) > 64:
        raise HTTPException(status_code=404, detail='Job not found')
    status = get_job(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail='Job not found or expired')
    return status

# Batch 22: source-grounded candidate extraction; NEVER starts a model job.
from pydantic import BaseModel as StructuredBaseModel, Field as StructuredField, ConfigDict as StructuredConfigDict
from fastapi.responses import HTMLResponse as StructuredHTMLResponse
from .structured import structured_analyze
from .ui_structured import PAGE as STRUCTURED_PAGE

class StructuredRequest(StructuredBaseModel):
    model_config = StructuredConfigDict(extra='forbid')
    question: str = StructuredField(min_length=2, max_length=500)
    limit: int = StructuredField(default=3, ge=1, le=3)

@app.get('/structured', response_class=StructuredHTMLResponse)
def structured_home():
    return StructuredHTMLResponse(STRUCTURED_PAGE, headers={'Cache-Control': 'no-store'})

@app.post('/api/structured')
def structured_endpoint(body: StructuredRequest):
    try:
        return structured_analyze(body.question, limit=body.limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except (OSError, sqlite3.Error):
        raise HTTPException(status_code=503, detail='Research corpus unavailable') from None


# Batch 23: auditable six-stage public software-agent orchestration.
# No public call path can start an LLM job. AI remains administrator-protected.
from pydantic import BaseModel as WorkflowModel, Field as WorkflowField, ConfigDict as WorkflowConfig
from fastapi.responses import HTMLResponse as WorkflowHTML, JSONResponse as WorkflowJSON
import sqlite3 as workflow_sqlite3
from .orchestrator import orchestrate as orchestrate_research, OrchestrationBusy, ProvenanceError
from .ui_workflow import PAGE as WORKFLOW_PAGE

class WorkflowRequest(WorkflowModel):
    model_config = WorkflowConfig(extra='forbid')
    question: str = WorkflowField(min_length=2, max_length=500)
    limit: int = WorkflowField(default=3, ge=1, le=3)

@app.get('/workflow', response_class=WorkflowHTML)
def workflow_home():
    return WorkflowHTML(WORKFLOW_PAGE, headers={'Cache-Control': 'no-store'})

@app.post('/api/orchestrate')
def workflow_endpoint(body: WorkflowRequest):
    try:
        result = orchestrate_research(body.question, limit=body.limit)
        return WorkflowJSON(result, headers={'Cache-Control': 'no-store'})
    except OrchestrationBusy:
        raise HTTPException(status_code=429, detail='Research is busy. Try again shortly.') from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except (ProvenanceError, OSError, workflow_sqlite3.Error):
        raise HTTPException(status_code=503, detail='Verified research source unavailable') from None

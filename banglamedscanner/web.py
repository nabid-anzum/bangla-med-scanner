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
from .ui_workspace29 import PAGE as UNIFIED_PAGE

class ResearchRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    source: Literal['corpus','live'] = 'corpus'
    limit: int = Field(default=5, ge=1, le=10)

@app.get('/', response_class=HTMLResponse)
def home():
    return HTMLResponse(UNIFIED_PAGE, headers={'Cache-Control':'no-store'})

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
    return StructuredHTMLResponse(UNIFIED_PAGE, headers={'Cache-Control': 'no-store'})

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
    return WorkflowHTML(UNIFIED_PAGE, headers={'Cache-Control': 'no-store'})

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
# Batch 25: open medical topics and authenticated DeepSeek research agents.
# The original /api/orchestrate and /api/ai/jobs endpoints remain unchanged.
from fastapi import Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel as OpenModel, Field as OpenField, ConfigDict as OpenConfig
from .open_topics import public_live_search, plan_public
from .ai_orchestration import run_ai_research
from .ai_gate import authorized as bms25_authorized, start_job as bms25_start_job
from .ai_gate import get_job as bms25_get_job, JobBusy as BMS25Busy, JobLimit as BMS25Limit
from .llm_report import is_configured as bms25_model_ready
from .orchestrator import orchestrate as bms25_fixed_orchestrate, OrchestrationBusy as BMS25ResearchBusy

class OpenTopicRequest(OpenModel):
    model_config = OpenConfig(extra='forbid')
    question: str = OpenField(min_length=2, max_length=500)
    limit: int = OpenField(default=3, ge=1, le=5)

@app.post('/api/open-search')
def bms25_open_search(body: OpenTopicRequest):
    try:
        return JSONResponse(public_live_search(body.question, limit=body.limit),
                            headers={'Cache-Control': 'no-store'})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=503, detail='Live PubMed search unavailable') from None

@app.post('/api/smart-search')
def bms25_smart_search(body: OpenTopicRequest):
    try:
        planned = plan_public(body.question)
        if planned['local_corpus_supported']:
            result = bms25_fixed_orchestrate(body.question, limit=min(body.limit, 3))
            result['source'] = 'corpus'
        else:
            result = public_live_search(body.question, limit=body.limit)
        return JSONResponse(result, headers={'Cache-Control': 'no-store'})
    except BMS25ResearchBusy:
        raise HTTPException(status_code=429, detail='Research concurrency limit reached') from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=503, detail='Research source unavailable') from None

@app.post('/api/ai/research/jobs', status_code=202)
def bms25_start_ai_research(body: OpenTopicRequest,
                            ai_access: str | None = Header(default=None, alias='X-BMS-AI-Token')):
    if not bms25_authorized(ai_access):
        raise HTTPException(status_code=403, detail='Administrator token required')
    if not bms25_model_ready():
        raise HTTPException(status_code=503, detail='Local DeepSeek unavailable')
    try:
        job_id = bms25_start_job(body.question, min(body.limit, 2), run_ai_research)
    except BMS25Busy:
        raise HTTPException(status_code=429, detail='Another local AI job is active') from None
    except BMS25Limit:
        raise HTTPException(status_code=429, detail='Hourly model job limit reached') from None
    return {'job_id': job_id, 'status': 'running',
            'model': 'local DeepSeek-R1-Distill-Qwen-1.5B',
            'note': 'Three sequential model calls; results require human review'}

@app.get('/api/ai/research/jobs/{job_id}')
def bms25_poll_ai_research(job_id: str,
                           ai_access: str | None = Header(default=None, alias='X-BMS-AI-Token')):
    if not bms25_authorized(ai_access):
        raise HTTPException(status_code=403, detail='Administrator token required')
    if len(job_id) > 64:
        raise HTTPException(status_code=404, detail='Job not found')
    value = bms25_get_job(job_id)
    if value is None:
        raise HTTPException(status_code=404, detail='Job not found or expired')
    return JSONResponse(value, headers={'Cache-Control': 'no-store'})


# Batch 29: single research report and administrator-only statement lookup.
# Existing public/private endpoints and their authorization remain unchanged.
from functools import partial as bms29_partial
from threading import BoundedSemaphore as BMS29Semaphore
from typing import Literal as BMS29Literal
from .unified_report import run_public_report as bms29_public_report
from .claim_locator import run_claim_check as bms29_claim_check

_BMS29_PUBLIC_SLOTS = BMS29Semaphore(3)

class UnifiedReportRequest(OpenModel):
    model_config = OpenConfig(extra='forbid')
    question: str = OpenField(min_length=2, max_length=500)
    limit: int = OpenField(default=5, ge=1, le=5)
    source: BMS29Literal['auto','live','corpus'] = 'auto'

class StatementLocatorRequest(OpenModel):
    model_config = OpenConfig(extra='forbid')
    statement: str = OpenField(min_length=2, max_length=500)
    limit: int = OpenField(default=5, ge=1, le=5)
    pmid: str | None = OpenField(default=None, pattern=r'^\d{1,10}$')

@app.post('/api/report/search')
def bms29_report_endpoint(body: UnifiedReportRequest):
    if not _BMS29_PUBLIC_SLOTS.acquire(blocking=False):
        raise HTTPException(status_code=429, detail='Research is busy; retry shortly')
    try:
        report = bms29_public_report(body.question, body.limit, body.source)
        return JSONResponse(report, headers={'Cache-Control':'no-store'})
    except BMS25ResearchBusy:
        raise HTTPException(status_code=429, detail='Research concurrency limit reached') from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=503, detail='Source retrieval temporarily unavailable') from None
    finally:
        _BMS29_PUBLIC_SLOTS.release()

@app.post('/api/ai/claims/jobs', status_code=202)
def bms29_start_claim(body: StatementLocatorRequest,
                      ai_access: str | None = Header(default=None,alias='X-BMS-AI-Token')):
    if not bms25_authorized(ai_access):
        raise HTTPException(status_code=403, detail='Administrator token required')
    if not bms25_model_ready():
        raise HTTPException(status_code=503,detail='Local DeepSeek unavailable')
    try:
        worker = bms29_partial(bms29_claim_check,pmid=body.pmid)
        job_id = bms25_start_job(body.statement, body.limit, worker)
    except BMS25Busy:
        raise HTTPException(status_code=429,detail='Another private AI job is active') from None
    except BMS25Limit:
        raise HTTPException(status_code=429,detail='Hourly local AI quota reached') from None
    return {'job_id':job_id,'status':'running',
            'note':'DeepSeek-assisted passage selection. PDF pages verified only from actual PDF text.'}

@app.get('/api/ai/claims/jobs/{job_id}')
def bms29_poll_claim(job_id: str,
                     ai_access: str | None = Header(default=None,alias='X-BMS-AI-Token')):
    if not bms25_authorized(ai_access):
        raise HTTPException(status_code=403,detail='Administrator token required')
    if not 1<=len(job_id)<=64:
        raise HTTPException(status_code=404,detail='Job not found')
    val=bms25_get_job(job_id)
    if val is None:
        raise HTTPException(status_code=404,detail='Job not found or expired')
    return JSONResponse(val,headers={'Cache-Control':'no-store'})

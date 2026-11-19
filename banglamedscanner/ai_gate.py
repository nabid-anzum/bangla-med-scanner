"""Admin-only, single-job local AI queue with process-local hourly quota.

All job contents are held in memory, not persisted to files or GitHub.
One Uvicorn worker is required for this in-process queue.
"""

import hmac
import os
import secrets
import threading
import time

_LOCK = threading.Lock()
_JOBS = {}
_WINDOW_START = time.monotonic()
_HOURLY_USED = 0
_ACTIVE = None
_HOURLY_LIMIT = 8
_TTL = 900


class JobBusy(RuntimeError):
    pass


class JobLimit(RuntimeError):
    pass


def authorized(token):
    expected = os.environ.get('BMS_AI_ACCESS_TOKEN', '')
    return (
        isinstance(token, str)
        and len(expected) >= 32
        and len(token) <= 256
        and hmac.compare_digest(token, expected)
    )


def _prune(now):
    for key, item in list(_JOBS.items()):
        if item['status'] != 'running' and now - item['created'] > _TTL:
            del _JOBS[key]


def start_job(question, limit, worker):
    global _ACTIVE, _HOURLY_USED, _WINDOW_START
    with _LOCK:
        now = time.monotonic()
        _prune(now)
        if _ACTIVE is not None:
            raise JobBusy('A model request is already running')
        if now - _WINDOW_START >= 3600:
            _WINDOW_START = now
            _HOURLY_USED = 0
        if _HOURLY_USED >= _HOURLY_LIMIT:
            raise JobLimit('Hourly local AI request limit reached')
        _HOURLY_USED += 1
        job_id = secrets.token_urlsafe(24)
        _ACTIVE = job_id
        _JOBS[job_id] = {'created': now, 'status': 'running'}

    def run():
        global _ACTIVE
        try:
            result = worker(question, limit=limit, ai_summary=True)
            payload = {'status': 'completed', 'result': result}
        except Exception:
            payload = {
                'status': 'failed',
                'detail': 'Local AI generation failed; the non-AI evidence view is still available.',
            }
        with _LOCK:
            if job_id in _JOBS:
                _JOBS[job_id].update(payload)
            if _ACTIVE == job_id:
                _ACTIVE = None

    thread = threading.Thread(target=run, name='bms-local-ai-job', daemon=True)
    thread.start()
    return job_id


def get_job(job_id):
    with _LOCK:
        _prune(time.monotonic())
        entry = _JOBS.get(job_id)
        if entry is None:
            return None
        return {k: v for k, v in entry.items() if k != 'created'}

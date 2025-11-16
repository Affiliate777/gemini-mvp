import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def cli_perform_anchor(payload, context=None):
    """
    Temporary stub for CLI anchor function.
    Replace with real import once integration verified.
    """
    logger.info("cli_perform_anchor: stub called with payload=%s, context=%s", payload, context)
    return {"anchor_id": "stub-ANCHOR-000", "status": "ok"}

def perform_anchor_sync(payload, user_ctx):
    """
    Synchronous wrapper that calls the CLI anchor function (stub for now).
    Returns the CLI result dict.
    """
    logger.info("perform_anchor_sync: starting anchor for payload=%s user=%s", payload, user_ctx.get("user_id") if isinstance(user_ctx, dict) else user_ctx)
    result = cli_perform_anchor(payload, context=user_ctx)
    logger.info("perform_anchor_sync: finished anchor result=%s", result)
    return result

import uuid
from threading import Thread

def start_anchor_job(payload, user_ctx):
    """
    Minimal async wrapper — creates a job ID, starts a background thread, and returns immediately.
    """
    job_id = str(uuid.uuid4())
    logger.info("start_anchor_job: enqueuing job %s for payload=%s", job_id, payload)

    def _run():
        try:
            logger.info("start_anchor_job: worker starting job %s", job_id)
            cli_perform_anchor(payload, context=user_ctx)
            logger.info("start_anchor_job: worker finished job %s", job_id)
        except Exception as e:
            logger.exception("start_anchor_job: job %s failed: %s", job_id, e)

    Thread(target=_run, daemon=True).start()
    return {"job_id": job_id, "status": "queued"}

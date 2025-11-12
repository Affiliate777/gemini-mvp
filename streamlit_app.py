import os
import time
import json
import requests
import streamlit as st
import streamlit.components.v1 as components
from app.anchor_service import perform_anchor_sync, start_anchor_job


def _copy_to_clipboard(text: str):
    """Copy text to clipboard in browser context."""
    safe = json.dumps(text)
    components.html(f"""
    <script>
    (async () => {{
      try {{
        await navigator.clipboard.writeText({safe});
      }} catch (e) {{
        const t = document.createElement('textarea');
        t.value = {safe};
        document.body.appendChild(t);
        t.select();
        document.execCommand('copy');
        t.remove();
      }}
    }})();
    </script>
    """, height=0)


_JOB_API_BASE = os.environ.get("JOB_STATUS_URL", "http://127.0.0.1:8010/api/job")

st.title("Anchoring (MVP)")

auth_header = st.text_input("Auth header (optional)", value=st.session_state.get("auth_header", ""))
resource_id = st.text_input("Resource ID", "example-1")

if st.button("Anchor Now (sync)"):
    with st.spinner("Running sync anchor..."):
        try:
            user_ctx = {"user_id": "dev-user", "auth_header": auth_header}
            res = perform_anchor_sync({"resource_id": resource_id}, user_ctx)
            st.success(f"Anchor complete: {res.get('anchor_id')}")
            st.json(res)
        except Exception as e:
            st.error(f"Sync anchor failed: {e}")

if st.button("Anchor Now (async)"):
    try:
        user_ctx = {"user_id": "dev-user", "auth_header": auth_header}
        job = start_anchor_job({"resource_id": resource_id}, user_ctx)
        st.session_state["last_queued_job"] = job.get("job_id")
        st.success(f"Job queued: {job.get('job_id')}")
        st.json(job)
    except Exception as e:
        st.error(f"Async anchor failed: {e}")

st.markdown("### REST job status (via job-status service)")
jid = st.text_input("Job ID to check (REST)", st.session_state.get("last_queued_job", ""))

def fetch_job_status_rest(job_id):
    try:
        r = requests.get(f"{_JOB_API_BASE}/{job_id}", timeout=3)
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

if st.button("Fetch REST job now"):
    if jid:
        result = fetch_job_status_rest(jid)
        st.json(result)
    else:
        st.warning("Enter a Job ID first.")

if st.button("Copy Job ID"):
    if jid:
        _copy_to_clipboard(jid)
        st.success("Copied job ID to clipboard.")
    else:
        st.info("Nothing to copy.")

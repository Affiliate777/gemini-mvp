import os
import streamlit as st
import json
import time
import requests
import streamlit.components.v1 as components
from app.anchor_service import perform_anchor_sync, start_anchor_job

# Clipboard helper
def _copy_to_clipboard(text: str):
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
        try {{ document.execCommand('copy'); }} catch (err){{}}
        t.remove();
      }}
    }})();
    </script>
    """, height=0)

# Configurable REST URL (env-friendly)
_JOB_API_BASE = os.environ.get("JOB_STATUS_URL", "http://127.0.0.1:56613/api/job")

st.title("Anchoring (MVP)")

# --- Auth input (forwarded) ---
st.markdown("**Auth (optional)** — set an Authorization header to forward to the CLI/service")
auth_header_input = st.text_input("auth_header (e.g. Bearer ...)", key="auth_header", value=st.session_state.get("auth_header",""))

# --- Resource input + actions ---
resource_id = st.text_input("resource_id", "example-1")

if st.button("Anchor Now (sync)"):
    with st.spinner("Running anchor (sync)..."):
        try:
            user_ctx = {
                "user_id": st.session_state.get("user_id", "dev-user"),
                "auth_header": st.session_state.get("auth_header", auth_header_input)
            }
            res = perform_anchor_sync({"resource_id": resource_id}, user_ctx)
            st.success(f"Anchor completed: {res.get('anchor_id')}")
            st.json(res)
        except Exception as e:
            st.error(f"Anchor failed: {e}")

if st.button("Anchor Now (async)"):
    try:
        user_ctx = {
            "user_id": st.session_state.get("user_id", "dev-user"),
            "auth_header": st.session_state.get("auth_header", auth_header_input)
        }
        job = start_anchor_job({"resource_id": resource_id}, user_ctx)
        st.session_state["last_queued_job"] = job.get("job_id")
        st.success(f"Anchor queued: {job.get('job_id')}")
        st.json(job)
    except Exception as e:
        st.error(f"Failed to queue anchor: {e}")

# -----------------------------
# File-backed job status
# -----------------------------
st.markdown("### Check job status (file-backed)")
jid = st.text_input("Job ID (file-backed)", st.session_state.get("last_queued_job",""), key="file_jid")
if st.button("Refresh job status (file)"):
    if jid:
        try:
            jobs = json.load(open("var/jobs.json"))
            entry = jobs.get(jid)
            if entry:
                st.json(entry)
            else:
                st.warning("Job id not found in var/jobs.json")
        except Exception as e:
            st.error(f"Failed to read job status: {e}")
    else:
        st.info("Enter a job id")

# -----------------------------
# REST-based job status
# -----------------------------
st.markdown("### REST job status (via job-status service)")

def fetch_job_status_rest(job_id: str, base=_JOB_API_BASE, timeout=3):
    if not job_id:
        return None
    try:
        r = requests.get(f"{base}/{job_id}", timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        return {"__error": str(e)}

rest_jid = st.text_input("Job id to watch (REST)", st.session_state.get("last_job_id", ""), key="rest_jid")
col_a, col_b, col_c = st.columns([2,1,1])
with col_a:
    if st.button("Fetch REST now"):
        if rest_jid:
            res = fetch_job_status_rest(rest_jid)
            if res is None:
                st.warning("Job not found or service returned 404")
            elif "__error" in (res or {}):
                st.error(f"Error fetching job: {res['__error']}")
            else:
                st.json(res)
        else:
            st.info("Enter a job id")
with col_b:
    auto_rest = st.checkbox("Auto-refresh (5s)", key="auto_rest")
with col_c:
    if st.button("Copy job id (REST)"):
        if rest_jid:
            _copy_to_clipboard(rest_jid)
            st.success("Copied job id to clipboard")
        else:
            st.info("No REST job id set")

# Auto-refresh loop for REST
if st.session_state.get("auto_rest") or st.session_state.get("auto_rest", False):
    if auto_rest and rest_jid:
        res = fetch_job_status_rest(rest_jid)
        if res is None:
            st.warning("Job not found (REST)")
        elif "__error" in (res or {}):
            st.error(f"Error fetching job: {res['__error']}")
        else:
            st.json(res)
        time.sleep(5)
        st.experimental_rerun()

# --- Quick last-queued-job UX (persistent session helper) ---
st.markdown("### Last queued job (session)")
last = st.session_state.get("last_queued_job", "")
if last:
    st.code(last)
    c1, c2 = st.columns([1,4])
    with c1:
        if st.button("Copy last job id"):
            _copy_to_clipboard(last)
            st.success("Copied last queued job id")
    with c2:
        if st.button("Fetch last job (REST)"):
            res = fetch_job_status_rest(last)
            if res is None:
                st.warning("Job not found (REST)")
            elif "__error" in (res or {}):
                st.error(f"Error fetching job: {res['__error']}")
            else:
                st.json(res)
# End of streamlit_app.py

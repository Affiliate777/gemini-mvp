...
# --- REST-backed job poller (queries the Flask job-status endpoint) -----
import requests
import time

_JOB_API_BASE = "http://127.0.0.1:56613/api/job"  # endpoint and port discovered from api_job_status.log

def fetch_job_status_rest(job_id: str, base=_JOB_API_BASE, timeout=3):
    """Return dict or None on not-found/error."""
    if not job_id:
        return None
    try:
        r = requests.get(f"{base}/{job_id}", timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        return {"__error": str(e)}

st.markdown("### REST job status (via job-status service)")
rest_jid = st.text_input("Job id to watch (REST)", st.session_state.get("last_job_id", ""))
auto_rest = st.checkbox("Auto-refresh from job-status API (every 5s)")

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

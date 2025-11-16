from datetime import datetime

def _is_date_like(val):
    if val is None:
        return False
    if isinstance(val, (datetime, )):
        return True
    s = str(val)
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            datetime.strptime(s, fmt)
            return True
        except Exception:
            continue
    return False

def run_simple_checks(doc: dict):
    """Return list of checks: {id, title, severity, passed, info}"""
    out = []
    fields = doc.get("fields", {})
    # Example check: Revision Date present & valid
    rev = fields.get("Revision Date") or fields.get("Rev Date") or fields.get("Revision")
    if rev is None:
        out.append({"id": "R-0001", "title": "Revision date present", "severity":"warning", "passed": False, "info": "No revision date found"})
    else:
        ok = _is_date_like(rev)
        out.append({"id": "R-0002", "title": "Revision date valid", "severity": "error" if not ok else "info", "passed": ok, "info": str(rev)})
    return out

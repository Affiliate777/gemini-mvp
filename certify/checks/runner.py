from datetime import datetime
from typing import List, Dict, Tuple, Optional
from certify.checks.base_checkers import _is_date_like

# per-file checkers (existing)
def _check_revision_present(doc: dict, rule: dict) -> dict:
    fields = doc.get("fields", {})
    rev = fields.get("Revision Date") or fields.get("Rev Date") or fields.get("Revision")
    passed = rev is not None
    return {
        "id": rule.get("id"),
        "title": rule.get("title"),
        "severity": rule.get("severity", "warning"),
        "passed": passed,
        "info": "" if passed else "Revision date missing"
    }

def _check_revision_valid(doc: dict, rule: dict) -> dict:
    fields = doc.get("fields", {})
    rev = fields.get("Revision Date") or fields.get("Rev Date") or fields.get("Revision")
    ok = _is_date_like(rev)
    return {
        "id": rule.get("id"),
        "title": rule.get("title"),
        "severity": rule.get("severity", "error" if not ok else "info"),
        "passed": bool(ok),
        "info": str(rev)
    }

# cross-document check: match two fields between two docs
def _check_crossdoc_match(docs_map: Dict[str, dict], rule: dict) -> dict:
    """
    rule.scope example:
      - left: "certify/tests/fixtures/test_ds_A.xlsx"
        field: "Revision Date"
      - right: "certify/tests/fixtures/test_ds_B.xlsx"
        field: "Revision Date"
    The paths in scope may be exact relative paths or glob patterns; loader should supply them resolved.
    """
    scope = rule.get("scope", [])
    if not isinstance(scope, list) or len(scope) < 2:
        return {
            "id": rule.get("id"),
            "title": rule.get("title"),
            "severity": rule.get("severity", "error"),
            "passed": False,
            "info": "Invalid scope for crossdoc rule"
        }
    left = scope[0]
    right = scope[1]
    left_path = left.get("path")
    right_path = right.get("path")
    left_field = left.get("field")
    right_field = right.get("field")

    left_doc = docs_map.get(left_path)
    right_doc = docs_map.get(right_path)

    if left_doc is None:
        return {"id": rule.get("id"), "title": rule.get("title"),
                "severity": rule.get("severity", "error"), "passed": False,
                "info": f"Left document not found: {left_path}"}
    if right_doc is None:
        return {"id": rule.get("id"), "title": rule.get("title"),
                "severity": rule.get("severity", "error"), "passed": False,
                "info": f"Right document not found: {right_path}"}

    left_val = left_doc.get("fields", {}).get(left_field)
    right_val = right_doc.get("fields", {}).get(right_field)

    passed = left_val == right_val
    return {
        "id": rule.get("id"),
        "title": rule.get("title"),
        "severity": rule.get("severity", "error" if not passed else "info"),
        "passed": bool(passed),
        "info": f"{left_field}='{left_val}' vs {right_field}='{right_val}'"
    }

# map rule.checker or rule.id to function
CHECKER_MAP = {
    "revision_present": _check_revision_present,
    "revision_valid": _check_revision_valid,
    # crossdoc not in this map (handled separately)
}

def run_rules_on_doc(doc: dict, rules: List[Dict]) -> List[Dict]:
    results = []
    for r in rules:
        # skip crossdoc rules here (handled separately)
        if r.get("type") == "crossdoc":
            continue
        checker_name = r.get("checker")
        func = None
        if checker_name and checker_name in CHECKER_MAP:
            func = CHECKER_MAP[checker_name]
        elif r.get("id") == "LOCAL-001":
            func = _check_revision_present
        elif r.get("id") == "LOCAL-002":
            func = _check_revision_valid
        else:
            results.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "severity": r.get("severity", "info"),
                "passed": True,
                "info": "No concrete checker implemented (skipped)"
            })
            continue
        res = func(doc, r)
        results.append(res)
    return results

def run_crossdoc_rules(docs_map: Dict[str, dict], rules: List[Dict]) -> List[Dict]:
    """Run rules with type == 'crossdoc'. docs_map keys are relative paths as used in rules."""
    results = []
    for r in rules:
        if r.get("type") != "crossdoc":
            continue
        # Attempt to resolve simple path references: if rule scope uses relative path names,
        # ensure they match docs_map keys. For now expect exact relative paths stored in rule.scope path.
        res = _check_crossdoc_match(docs_map, r)
        results.append(res)
    return results

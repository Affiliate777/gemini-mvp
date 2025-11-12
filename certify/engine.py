from pathlib import Path
import json, fnmatch
from certify.parsers.excel_parser import parse_excel
from certify.outputs.json_out import write_json_summary
from certify.checks.base_checkers import run_simple_checks
from certify.rules.loader import load_project_rules
from certify.checks.runner import run_rules_on_doc, run_crossdoc_rules

def _gather_files(path: Path):
    if path.is_dir():
        return list(path.rglob("*.xlsx")) + list(path.rglob("*.xls"))
    else:
        return [path]

def _relpath_key(p: Path) -> str:
    return str(p.as_posix())

def _build_selector_map(cfg: dict, docs_map: dict) -> dict:
    selectors = cfg.get("selectors", {}) or {}
    out = {}
    import fnmatch
    for name, pattern in selectors.items():
        patterns = pattern if isinstance(pattern, list) else [pattern]
        matches = []
        for pat in patterns:
            # tag: handled at engine layer in updated code paths if present; but keep simple glob handling here
            if pat in docs_map:
                matches.append(pat)
            else:
                for k in sorted(docs_map.keys()):
                    if fnmatch.fnmatch(k, pat):
                        if k not in matches:
                            matches.append(k)
        out[name] = matches
    return out

def run_validate(path: Path, cfg: dict, mode: str = "strict", out_path: Path = Path("certify/artifacts/validation.json"), fail_fast: bool = False) -> int:
    """
    Runs validation. If fail_fast is True, stops and returns as soon as an error-level failed check is detected.
    Returns: 0 = success, 2 = warnings, 3 = errors
    """
    path = Path(path)
    files = _gather_files(path)
    results = []
    errors = 0
    warnings = 0

    # load rules
    rule_entries = cfg.get("rule_sets", []) or []
    rules_by_name = load_project_rules(rule_entries)
    flat_rules = []
    for k in rules_by_name:
        flat_rules.extend(rules_by_name[k].get("rules", []))

    # parse docs first and build docs_map keyed by relative path
    docs_map = {}
    for f in files:
        try:
            doc = parse_excel(f)
            key = _relpath_key(f)
            docs_map[key] = doc
        except Exception as e:
            results.append({"file": str(f), "error": str(e)})
            errors += 1
            # if fail_fast on parse errors, write and exit
            if fail_fast:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                write_json_summary(results, out_path)
                return 3

    # build selector map from cfg selectors using docs_map
    selector_map = _build_selector_map(cfg, docs_map)

    # run per-file checks
    for key, doc in docs_map.items():
        simple_checks = run_simple_checks(doc)
        rule_checks = run_rules_on_doc(doc, flat_rules)
        checks = {"simple": simple_checks, "rules": rule_checks}
        results.append({"file": key, "doc": doc, "checks": checks})

        # Count severities and optionally fail fast
        for c in simple_checks + rule_checks:
            sev = (c.get("severity") or "").lower()
            if sev == "error" and not c.get("passed", True):
                errors += 1
                if fail_fast:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    write_json_summary(results, out_path)
                    return 3
            if sev == "warning" and not c.get("passed", True):
                warnings += 1

    # run cross-document rules (they receive docs_map and selector_map)
    cross_checks = run_crossdoc_rules(docs_map, flat_rules, selector_map)
    if cross_checks:
        results.append({"file": "crossdoc", "doc": {}, "checks": cross_checks})
        for c in cross_checks:
            sev = (c.get("severity") or "").lower()
            if sev == "error" and not c.get("passed", True):
                errors += 1
                if fail_fast:
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    write_json_summary(results, out_path)
                    return 3
            if sev == "warning" and not c.get("passed", True):
                warnings += 1

    # write final JSON summary
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_json_summary(results, out_path)

    if errors > 0:
        return 3
    if warnings > 0:
        return 2
    return 0

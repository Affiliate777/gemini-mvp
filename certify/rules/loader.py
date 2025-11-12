from pathlib import Path
import yaml

def load_rule_file(path: Path) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def resolve_inheritance(rule_path: Path, seen=None) -> dict:
    """
    Load a rule file, resolve any 'inherits' chain, and return merged rule dict.
    Child rules override parent rules where IDs collide.
    """
    if seen is None:
        seen = set()
    rule_path = Path(rule_path)
    base = load_rule_file(rule_path)
    if not base:
        return {"name": rule_path.stem, "rules": []}
    name = base.get("name", rule_path.stem)
    inherits = base.get("inherits")
    merged = {"name": name, "rules": []}
    parents = []
    if inherits:
        # accepts string or list
        if isinstance(inherits, str):
            parents = [inherits]
        elif isinstance(inherits, list):
            parents = inherits
    # resolve parent paths relative to this file
    for p in parents:
        parent_path = (rule_path.parent / p).resolve()
        if parent_path in seen:
            raise RuntimeError(f"Circular inheritance detected: {parent_path}")
        seen.add(parent_path)
        parent_rules = resolve_inheritance(parent_path, seen)
        merged["rules"].extend(parent_rules.get("rules", []))
    # then apply current rules (child overrides by id)
    child_rules = base.get("rules", [])
    # create map by id to allow override
    rules_map = {r.get("id"): r for r in merged["rules"] if r.get("id")}
    for r in child_rules:
        rid = r.get("id")
        if rid:
            rules_map[rid] = r
        else:
            # append anonymous rules
            merged["rules"].append(r)
    # final aggregated rules: include inherited ones (from rules_map) and any anonymous ones
    final = list(rules_map.values()) + [r for r in merged["rules"] if not r.get("id")]
    # now also include any child rules that had no id (already in child_rules)
    anon_from_child = [r for r in child_rules if not r.get("id")]
    final.extend(anon_from_child)
    merged["rules"] = final
    return merged

def load_project_rules(rule_entries: list) -> dict:
    """
    rule_entries: list of dicts like {"name": "local", "path": "certify/rules/local.yml"}
    returns dict {name: merged_rule_dict}
    """
    out = {}
    for e in rule_entries:
        path = Path(e.get("path"))
        if not path.exists():
            continue
        merged = resolve_inheritance(path)
        out[e.get("name", merged.get("name"))] = merged
    return out


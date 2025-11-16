from pathlib import Path
import yaml
import json

DEFAULT_CONFIG = {
    "project": "certify-project",
    "project_id": "CERT-001",
    "certifier": "geminibiofuels@proton.me",
    "workspace_path": str(Path.cwd()),
    "blockchain": {"mode": "none", "local_ledger_path": "certify/ledger"},
    "verification_mode": "strict",
    "rule_sets": [],
    "crossdoc_checks": True,
    "outputs": {"json": "certify/artifacts/validation.json", "excel": "certify/artifacts/validation.xlsx"},
    "logging": {"level": "INFO", "file": "certify/logs/certify.log"}
}

def init_config(project_root: Path, force: bool = False):
    cfg_path = project_root / "certify" / "certify.yml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg_path.exists() and not force:
        raise FileExistsError(f"{cfg_path} exists. Use force=True to overwrite.")
    with open(cfg_path, "w") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f)
    return cfg_path

def load_config(path: Path = Path("certify/certify.yml")):
    if not path.exists():
        # try to create default
        init_config(path.parent, force=False)
    with open(path, "r") as f:
        cfg = yaml.safe_load(f) or {}
    # merge defaults
    merged = DEFAULT_CONFIG.copy()
    merged.update(cfg)
    return merged

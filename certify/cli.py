"""Display current certify.yml config."""
cfg = load_config(Path("certify/certify.yml"))
typer.echo(cfg)

@app.command()
def report(...):
@app.command()
def report(
    path: Path = typer.Option(
        Path("certify/artifacts/validation.json"),
        help="Path to validation.json"
    ),
    out: Path = typer.Option(
        Path("certify/artifacts/validation.xlsx"),
        help="Output Excel file"
    ),
    _open: bool = typer.Option(
        False, "--open",
        help="Open the created Excel file (macOS)"
    )
):
    """Generate an Excel report from the validation JSON artifacts."""
    p = Path(path)
    if not p.exists():
        typer.echo(f"No validation JSON found at {p}. Run `certify validate` first.")
        raise typer.Exit(code=1)

    try:
        with open(p, "r") as f:
            results = json.load(f)
    except Exception as e:
        typer.echo(f"Failed to read JSON: {e}")
        raise typer.Exit(code=2)

    outp = write_excel_summary(results, out)
    typer.echo(f"Wrote report: {outp}")

    if _open:
        try:
            import subprocess
            subprocess.run(["open", str(outp)])
        except Exception as e:
            typer.echo(f"Could not open file: {e}")
from __future__ import annotations
import typer
from pathlib import Path
from certify.config import load_config, init_config
from certify.engine import run_validate
from certify.audit.ledger import create_audit_entry
from certify.outputs.excel_out import write_excel_summary
import sys
import json

app = typer.Typer(help="Certify - Validation CLI")

@app.command()
def init(path: Path = typer.Option(
        Path.cwd(),
        help="Project root to create certify.yml"),
        force: bool = typer.Option(False, help="Overwrite if exists")):
    """Create a certify.yml configuration in the project root."""
    init_config(path, force)
    typer.echo(f"Created certify.yml at {path}")

@app.command()
def validate(path: Path = typer.Option(
        Path.cwd(), help="File or folder to validate"),
        mode: str = typer.Option("strict", help="strict|permissive"),
        out: Path = typer.Option(Path("certify/artifacts/validation.json"), help="Output path for JSON summary"),
        list_files: bool = typer.Option(False, "--list-files", help="List files that will be scanned and exit"),
        fail_fast: bool = typer.Option(False, "--fail-fast", help="Stop on first error-level failed check (useful for CI)")):
    """Run validation on a file or folder."""
    if list_files:
        from pathlib import Path as _P
        p = _P(path)
        if p.is_dir():
            files = list(p.rglob("*.xlsx")) + list(p.rglob("*.xls"))
        else:
            files = [p]
        typer.echo("Files to be scanned:")
        for f in files:
            typer.echo(f" - {f}")
        raise typer.Exit()
    cfg = load_config(Path("certify/certify.yml"))
    rc = run_validate(path, cfg, mode=mode, out_path=out, fail_fast=fail_fast)
    if rc == 0:
        typer.echo("Validation succeeded (exit 0).")
    elif rc == 2:
        typer.echo("Validation completed with warnings (exit 2).")
        raise typer.Exit(code=2)
    else:
        typer.echo("Validation failed (exit 3).")
        raise typer.Exit(code=3)

@app.command()
def audit(file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
          register_local: bool = typer.Option(True, help="Write audit record to local ledger")):
    """Create an audit entry (sha256 hash + metadata) for a file."""
    entry = create_audit_entry(file, certifier=None, register_local=register_local)
    typer.echo(f"Audit entry created: {entry.get('sha256')}")
    typer.echo(str(entry))

@app.command("config-show")
def config_show():
    """Display current certify.yml config."""
    cfg = load_config(Path("certify/certify.yml"))
    typer.echo(cfg)

@app.command()
def report(path: Path = typer.Option(Path("certify/artifacts/validation.json"), help="Path to validation.json"),
           out: Path = typer.Option(Path("certify/artifacts/validation.xlsx"), help="Output Excel file"),
           _open: bool = typer.Option(False, "--open", help="Open the created Excel file (macOS)")):
    """Generate an Excel report from the validation JSON artifacts."""
    p = Path(path)
    if not p.exists():
        typer.echo(f"No validation JSON found at {p}. Run `certify validate` first.")
        raise typer.Exit(code=1)
    try:
        with open(p, "r") as f:
            results = json.load(f)
    except Exception as e:
        typer.echo(f"Failed to read JSON: {e}")
        raise typer.Exit(code=2)
    outp = write_excel_summary(results, out)
    typer.echo(f"Wrote report: {outp}")
    if _open:
        try:
            import subprocess
            subprocess.run(["open", str(outp)])
        except Exception as e:
            typer.echo(f"Could not open file: {e}")

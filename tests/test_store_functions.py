import json
from pathlib import Path
import pytest
from app import anchor_service

def test_anchor_record_and_read(tmp_path, monkeypatch):
    monkeypatch.setattr(anchor_service, "_VAR_DIR", tmp_path)
    monkeypatch.setattr(anchor_service, "_ANC_FILE", tmp_path / "anchors.json")
    monkeypatch.setattr(anchor_service, "_JOB_FILE", tmp_path / "jobs.json")
    anchor_service._ensure_store()
    anchor_service.record_anchor("r1", "A1")
    assert anchor_service.get_anchor_for_resource("r1") == "A1"

def test_job_status_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(anchor_service, "_VAR_DIR", tmp_path)
    monkeypatch.setattr(anchor_service, "_ANC_FILE", tmp_path / "anchors.json")
    monkeypatch.setattr(anchor_service, "_JOB_FILE", tmp_path / "jobs.json")
    anchor_service._ensure_store()
    anchor_service.set_job_status("J1", "queued", resource_id="r2")
    js = anchor_service.get_job_status("J1")
    assert js is not None
    assert js["status"] in ("queued","running","completed","failed")
    assert js["resource_id"] == "r2"

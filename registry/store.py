"""SQLite-backed registry store for MVP-6 with pydantic validation and WAL + retry logic"""
import sqlite3
import os
import time
import json
import functools
from typing import Optional, Dict, Any

DB_PATH = os.environ.get('GEMINI_DB', 'gemini_registry.db')

_schema = '''
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    node_type TEXT,
    channel_version TEXT,
    metadata TEXT,
    last_seen INTEGER
);
'''

def _conn():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    return conn

def init_db():
    conn = _conn()
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA busy_timeout=3000;')
    except Exception:
        pass
    conn.executescript(_schema)
    conn.commit()
    conn.close()

try:
    from pydantic import BaseModel, Field, validator
except Exception:
    BaseModel = object

class DeviceModel(BaseModel):
    id: str = Field(..., min_length=1)
    node_type: str
    channel_version: str
    metadata: Optional[Dict[str, Any]] = {}
    last_seen: Optional[int] = None

    @validator('id')
    def id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('id must be non-empty')
        return v

def with_retry(retries: int = 5, base_backoff: float = 0.05):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(retries):
                try:
                    return fn(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exc = e
                    msg = str(e).lower()
                    if 'locked' in msg or 'database is locked' in msg:
                        sleep_time = base_backoff * (2 ** i)
                        time.sleep(sleep_time)
                        continue
                    raise
            raise last_exc
        return wrapper
    return decorator

def _json_safe(x):
    try:
        return json.dumps(x)
    except Exception:
        return json.dumps({})

def _maybe_json(s):
    try:
        return json.loads(s) if s else {}
    except Exception:
        return {}

@with_retry()
def add_device(device: dict):
    init_db()
    try:
        d = DeviceModel(**device).dict()
    except Exception as e:
        raise ValueError(f'Invalid device payload: {e}')
    conn = _conn()
    cur = conn.cursor()
    cur.execute('''INSERT OR REPLACE INTO devices (id, node_type, channel_version, metadata, last_seen)
                   VALUES (?, ?, ?, ?, ?)''', (
        d.get('id'),
        d.get('node_type'),
        d.get('channel_version'),
        _json_safe(d.get('metadata')),
        d.get('last_seen', None)
    ))
    conn.commit()
    conn.close()

def list_devices():
    init_db()
    conn = _conn()
    cur = conn.cursor()
    cur.execute('SELECT id, node_type, channel_version, metadata, last_seen FROM devices')
    rows = cur.fetchall()
    conn.close()
    return [dict(id=r[0], node_type=r[1], channel_version=r[2], metadata=_maybe_json(r[3]), last_seen=r[4]) for r in rows]

def get_device(device_id: str):
    init_db()
    conn = _conn()
    cur = conn.cursor()
    cur.execute('SELECT id, node_type, channel_version, metadata, last_seen FROM devices WHERE id=?', (device_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return dict(id=r[0], node_type=r[1], channel_version=r[2], metadata=_maybe_json(r[3]), last_seen=r[4])

@with_retry()
def delete_device(device_id: str):
    init_db()
    conn = _conn()
    cur = conn.cursor()
    cur.execute('DELETE FROM devices WHERE id=?', (device_id,))
    conn.commit()
    conn.close()

@with_retry()
def update_last_seen(device_id: str, ts: Optional[int] = None, extra_metadata: Optional[Dict] = None):
    init_db()
    ts = ts or int(time.time())
    existing = get_device(device_id)
    if existing:
        metadata = existing.get('metadata') or {}
        if extra_metadata:
            metadata.update(extra_metadata)
        conn = _conn()
        cur = conn.cursor()
        cur.execute('UPDATE devices SET last_seen=?, metadata=? WHERE id=?', (ts, _json_safe(metadata), device_id))
        conn.commit()
        conn.close()
    else:
        add_device({'id': device_id, 'node_type': 'unknown', 'channel_version': '0.0.0', 'metadata': extra_metadata or {}, 'last_seen': ts})

# Gemini Telemetry Subsystem

This directory implements the lightweight telemetry layer for the MVP.

## Components

### 1. `telemetry.health_server`
An HTTP server exposing:
- `/health` → system metrics (disk, load, Python version, timestamp, hostname)
- `/heartbeat-write` → writes a heartbeat JSON file into `var/`

### 2. `telemetry.agent`
Simple agent that writes a heartbeat file on each execution. Designed to be triggered by `launchd`.

### 3. Wrappers in `scripts/`
- `run-health-server.sh` — starts the telemetry server correctly, ensuring the repo root is the working directory.
- `run-telemetry-agent.sh` — executes the telemetry agent with correct path handling.

### 4. Launchd plist files (`launchd/`)
- `com.gemini.telemetry.server.plist`
- `com.gemini.telemetry.agent.plist`

These define macOS background daemons using the wrapper scripts.

## Log Files
Written to `var/`:
- `telemetry_server.log`
- `telemetry_agent.log`
- `heartbeat_<hostname>.json`


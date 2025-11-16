<<<<<<< HEAD

- scripts/update-apply.sh: deploys release and always writes audit via update-audit-append.sh (EXIT trap).
- scripts/update-audit-append.sh: appends JSON lines to logs/update-audit.log
  Schema: {"version":"vX.Y.Z","release_dir":"/path/to/release","rc":0,"ts":<unix>}
- Tests:
    bash -x scripts/update-apply.sh v1.0.1
    bash -x scripts/update-apply.sh non-existent-version || true
=======
Run scripts:

1) Start gateway (optionally with token)
   ./run_gateway.sh            # runs gateway without auth
   ./run_gateway.sh gemini123  # runs gateway and sets TELEMETRY_API_TOKEN=gemini123

2) Start agent scheduler
   ./run_agent.sh              # runs telemetry scheduler for local-node every 30s
   ./run_agent.sh node1 10 --push   # runs for node1 every 10s and pushes to gateway

Notes: keep the gateway terminal open when running agent with --push.
>>>>>>> 92649a5576252d2f8bf034bb05b916c5a9202526

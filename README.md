Run scripts:

1) Start gateway (optionally with token)
   ./run_gateway.sh            # runs gateway without auth
   ./run_gateway.sh gemini123  # runs gateway and sets TELEMETRY_API_TOKEN=gemini123

2) Start agent scheduler
   ./run_agent.sh              # runs telemetry scheduler for local-node every 30s
   ./run_agent.sh node1 10 --push   # runs for node1 every 10s and pushes to gateway

Notes: keep the gateway terminal open when running agent with --push.

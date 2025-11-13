#!/bin/zsh
# mvp-status.sh — Show active Gemini Python processes and their terminals

echo "🔍 Gemini MVP Process Status"
echo "============================"
echo

# Header
printf "%-8s %-8s %-15s %-30s\n" "PID" "TTY" "ROLE" "COMMAND"
echo "-----------------------------------------------------------------------"

# List all python processes related to gemini-mvp
ps aux | grep python | grep gemini-mvp | grep -v grep | while read -r user pid cpu mem vsz rss tty stat start time command; do
  role="unknown"
  case "$command" in
    *mock_server.py*) role="mock-server" ;;
    *telemetry_agent.py*) role="telemetry-agent" ;;
    *installer.py*) role="installer" ;;
    *updater.py*) role="updater" ;;
    *deploy_with_healthcheck.py*) role="healthcheck" ;;
    *) role="other" ;;
  esac

  # Extract just the TTY (terminal ID)
  tty_short=$(echo "$tty" | sed 's/.*\///g')
  printf "%-8s %-8s %-15s %-30s\n" "$pid" "$tty_short" "$role" "$command"
done

echo
echo "💡 Tip: use 'kill -9 <PID>' to stop one process safely (only if needed)."
echo "💡 Each 'TTY' (like s001, s002) corresponds to a specific Terminal tab/window."

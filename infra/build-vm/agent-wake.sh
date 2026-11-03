#!/usr/bin/env bash
# A background chain that ends leaves a line in state/agent-wake-pending and the syslog (2026-11-03: round 5 close-8
# failed at 20:39 and sat 90 minutes; only owner comments woke the agent). The live session arms a Monitor on that
# file when it launches a chain; the next session reads it at start. owner-wake.sh keeps its own path.
msg="${*:-a background job ended}"
mkdir -p "$HOME/.argonia/state"; echo "$(date -u +%FT%TZ) $msg" >> "$HOME/.argonia/state/agent-wake-pending"
logger -t argonia-agent-wake "$msg"; echo "agent-wake: queued in state/agent-wake-pending"

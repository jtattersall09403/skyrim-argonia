#!/usr/bin/env bash
# Ping the bridge until it answers (up to N tries, 20 s apart): a first boot of a new ESM holds the main thread for minutes.
cd /home/ubuntu/skyrim-argonia
for i in $(seq 1 ${1:-18}); do
  if ~/.argonia/venv/bin/python tools/bridge.py ping >/dev/null 2>&1; then echo "ping ok after $i tries"; exit 0; fi
  sleep 20
done
echo "ping still refused after ${1:-18} tries"; exit 1

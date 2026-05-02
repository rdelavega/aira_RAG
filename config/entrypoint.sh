#!/bin/sh
mkdir -p /root/.openclaw/agents/main/agent
mkdir -p /root/.openclaw/skills
mkdir -p /root/.openclaw/workspace

cp /tmp/openclaw.json /root/.openclaw/openclaw.json 2>/dev/null || true
cp -r /tmp/skills/. /root/.openclaw/skills/ 2>/dev/null || true
cp /tmp/agent/auth-profiles.json /root/.openclaw/agents/main/agent/auth-profiles.json 2>/dev/null || true
cp -r /tmp/workspace/. /root/.openclaw/workspace/ 2>/dev/null || true

exec node dist/index.js gateway run

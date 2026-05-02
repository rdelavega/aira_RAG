#!/bin/sh
mkdir -p /root/.openclaw/agents/main/agent
mkdir -p /root/.openclaw/skills
mkdir -p /root/.openclaw/workspace
cp /tmp/openclaw.json /root/.openclaw/openclaw.json
cp -r /tmp/skills/. /root/.openclaw/skills/
cp /tmp/agent/auth-profiles.json /root/.openclaw/agents/main/agent/auth-profiles.json
exec node dist/index.js gateway

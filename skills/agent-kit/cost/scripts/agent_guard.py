#!/usr/bin/env python3
"""PreToolUse hook for the Agent tool: nudge the caller to pick a model tier.

Reads the hook payload on stdin. When an Agent call names no `model` (and isn't a fork, which
always inherits the parent model), it returns additionalContext with the tier table. It never
blocks the call: the agent still runs, the next one is routed better.

  settings.json:  "PreToolUse": [{"matcher": "Agent", "hooks": [{"type": "command",
                   "command": "python3 <path>/agent_guard.py"}]}]
  agent_guard.py --selftest
"""
import json
import sys

NUDGE = (
    "agent-kit cost: this Agent call sets no model, so it runs on the parent's (usually the most "
    "expensive) tier. Pick the cheapest tier that can finish it: haiku for search, file inventory, "
    "log reading; sonnet for a bounded code change with a test; inherit/opus only for multi-file "
    "architecture, planning, or a task a cheaper tier already failed. A handful of tool calls is "
    "cheaper inline than in any subagent. Brief = goal, scope, what to return, how done is checked."
)


def check(payload):
    """The hook's JSON reply for one payload, or None to stay silent."""
    if payload.get("tool_name") != "Agent":
        return None
    ti = payload.get("tool_input") or {}
    if ti.get("model") or ti.get("subagent_type") == "fork":
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": NUDGE}}


def selftest():
    def agent(**ti):
        return {"tool_name": "Agent", "tool_input": dict(prompt="find the config loader", **ti)}
    assert check(agent())["hookSpecificOutput"]["additionalContext"] == NUDGE
    assert check(agent(subagent_type="Explore"))  # no model: nudge
    assert check(agent(model="haiku")) is None
    assert check(agent(subagent_type="fork")) is None
    assert check({"tool_name": "Bash", "tool_input": {}}) is None
    assert check({}) is None
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return  # a broken payload must not block the tool call
    out = check(payload)
    if out:
        print(json.dumps(out))


if __name__ == "__main__":
    main()

# Task 3 — Give the Agent New Eyes (Observability)

## Summary

Added MCP tools for VictoriaLogs and VictoriaTraces to enable system observability.

## New MCP Tools

### VictoriaLogs
- `logs_search` — Search logs using LogsQL query
- `logs_error_count` — Count errors for a service over time window

### VictoriaTraces
- `traces_list` — List recent traces for a service
- `traces_get` — Fetch full trace details by ID

## Files Changed

- `mcp/mcp_lms/observability.py` — New observability tools
- `mcp/mcp_lms/server.py` — Register new tools
- `nanobot/workspace/skills/observability/SKILL.md` — Skill prompt
- `docker-compose.yml` — Add VICTORIALOGS_URL and VICTORIATRACES_URL env vars

## Testing

```bash
# Ask the agent:
"Any errors in the last hour?"
"What went wrong?"
```

## URLs

- VictoriaLogs: http://localhost:42002/utils/victorialogs/select/vmui
- VictoriaTraces: http://localhost:42002/utils/victoriatraces

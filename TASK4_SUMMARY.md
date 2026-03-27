# Task 4 — Diagnose a Failure and Make the Agent Proactive

## Summary

Taught the agent to investigate failures and created proactive health checks.

## Part A — Multi-step Investigation

Enhanced observability skill to guide agent when asked "What went wrong?":
1. Check recent errors with `logs_error_count`
2. Search logs with `logs_search`
3. Fetch traces with `traces_get`
4. Summarize findings with evidence

## Part B — Proactive Health Check

Created scheduled health check via cron tool:
- Runs every 2 minutes
- Checks backend errors in last 2 minutes
- Posts summary to the same chat
- Can list/remove jobs via `cron` tool

## Part C — Bug Fix

**Planted bug:** `backend/app/routers/items.py` returned 404 on DB failure

**Fix:** Changed to return 500 with actual error details

```python
# Before
raise HTTPException(status_code=404, detail="Items not found")

# After  
raise HTTPException(status_code=500, detail=f"Database error: {str(exc)}")
```

## Files Changed

- `nanobot/workspace/skills/observability/SKILL.md` — Enhanced skill
- `nanobot/workspace/AGENTS.md` — Added investigation instructions
- `backend/app/routers/items.py` — Fixed planted bug
- `REPORT.md` — Added Task 4 results

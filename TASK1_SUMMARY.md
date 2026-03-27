# Task 1 — Build Agent with LMS Tools

## Summary

Implemented an AI agent with access to LMS backend via MCP tools.

## Changes

- Created nanobot workspace configuration
- Added LMS MCP server with tools for querying backend
- Created skill prompt for LMS assistant
- Configured agent to use Qwen Code API

## Tools Available

- `lms_health` — Check backend health
- `lms_labs` — List all labs
- `lms_pass_rates` — Get pass rates for a lab
- `lms_learners` — List learners
- And more...

## Testing

```bash
nanobot agent
# Ask: "What labs are available?"
```

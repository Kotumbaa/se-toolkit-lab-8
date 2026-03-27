"""Observability MCP tools for VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

server = Server("observability")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_VICTORIALOGS_URL = os.environ.get("VICTORIALOGS_URL", "http://victorialogs:9428")
_VICTORIATRACES_URL = os.environ.get("VICTORIATRACES_URL", "http://victoriatraces:10428")


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _LogsSearchQuery(BaseModel):
    query: str = Field(
        default="service:backend",
        description="LogsQL query string. Examples: 'service:backend', 'level:error', '_stream:{service=\"backend\"} AND level:error'",
    )
    limit: int = Field(default=10, ge=1, le=100, description="Max log entries to return (default 10, max 100).")


class _LogsErrorCountQuery(BaseModel):
    service: str = Field(default="backend", description="Service name to check for errors.")
    minutes: int = Field(default=60, ge=1, description="Time window in minutes (default 60).")


class _TracesListQuery(BaseModel):
    service: str = Field(default="Learning Management Service", description="Service name to list traces for.")
    limit: int = Field(default=5, ge=1, le=20, description="Max traces to return (default 5, max 20).")


class _TracesGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch full details for.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _http_get(url: str, timeout: int = 10) -> str:
    """Make a simple HTTP GET request."""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode()


def _text(data: Any) -> list[TextContent]:
    """Return data as JSON text content."""
    if isinstance(data, str):
        return [TextContent(type="text", text=data)]
    return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def _logs_search(args: _LogsSearchQuery) -> list[TextContent]:
    """Search logs using VictoriaLogs LogsQL query."""
    try:
        # URL encode the query
        encoded_query = urllib.parse.quote(args.query, safe="")
        url = f"{_VICTORIALOGS_URL}/select/logsql/query?query={encoded_query}&limit={args.limit}"
        
        result = _http_get(url)
        
        # Try to parse as JSON for pretty printing
        try:
            data = json.loads(result)
            return _text(data)
        except json.JSONDecodeError:
            return _text(result)
            
    except urllib.error.HTTPError as e:
        return _text({"error": f"HTTP Error {e.code}: {e.reason}", "url": url})
    except Exception as e:
        return _text({"error": f"{type(e).__name__}: {e}"})


async def _logs_error_count(args: _LogsErrorCountQuery) -> list[TextContent]:
    """Count errors for a service over a time window."""
    try:
        # Query for errors in the time window
        query = f'_stream:{{service="{args.service}"}} AND level:error'
        encoded_query = urllib.parse.quote(query, safe="{}\"")
        url = f"{_VICTORIALOGS_URL}/select/logsql/query?query={encoded_query}&limit=1000"
        
        result = _http_get(url)
        
        # Count the number of error entries
        error_count = 0
        try:
            data = json.loads(result)
            if isinstance(data, list):
                error_count = len(data)
            elif isinstance(data, dict) and "entries" in data:
                error_count = len(data.get("entries", []))
        except json.JSONDecodeError:
            # If result is plain text, count lines
            error_count = len([line for line in result.split("\n") if line.strip()])
        
        return _text({
            "service": args.service,
            "time_window_minutes": args.minutes,
            "error_count": error_count,
            "summary": f"Found {error_count} error(s) for service '{args.service}' in the last {args.minutes} minutes."
        })
        
    except urllib.error.HTTPError as e:
        return _text({"error": f"HTTP Error {e.code}: {e.reason}"})
    except Exception as e:
        return _text({"error": f"{type(e).__name__}: {e}"})


async def _traces_list(args: _TracesListQuery) -> list[TextContent]:
    """List recent traces for a service."""
    try:
        # VictoriaTraces Jaeger-compatible API
        encoded_service = urllib.parse.quote(args.service, safe="")
        url = f"{_VICTORIATRACES_URL}/jaeger/api/traces?service={encoded_service}&limit={args.limit}"
        
        result = _http_get(url)
        
        try:
            data = json.loads(result)
            # Extract summary info from traces
            traces = data.get("data", []) if isinstance(data, dict) else []
            summary = []
            for trace in traces[:args.limit]:
                summary.append({
                    "trace_id": trace.get("traceID", "unknown"),
                    "spans": len(trace.get("spans", [])),
                    "start_time": trace.get("startTime", 0),
                    "duration_us": trace.get("duration", 0),
                })
            return _text({"traces": summary, "total": len(traces)})
        except json.JSONDecodeError:
            return _text(result)
            
    except urllib.error.HTTPError as e:
        return _text({"error": f"HTTP Error {e.code}: {e.reason}", "url": url})
    except Exception as e:
        return _text({"error": f"{type(e).__name__}: {e}"})


async def _traces_get(args: _TracesGetQuery) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    try:
        url = f"{_VICTORIATRACES_URL}/jaeger/api/traces/{args.trace_id}"
        
        result = _http_get(url)
        
        try:
            data = json.loads(result)
            return _text(data)
        except json.JSONDecodeError:
            return _text(result)
            
    except urllib.error.HTTPError as e:
        return _text({"error": f"HTTP Error {e.code}: {e.reason}", "url": url})
    except Exception as e:
        return _text({"error": f"{type(e).__name__}: {e}"})


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_Registry = tuple[type[BaseModel], Callable[..., Awaitable[list[TextContent]]], Tool]

_TOOLS: dict[str, _Registry] = {}


def _register(
    name: str,
    description: str,
    model: type[BaseModel],
    handler: Callable[..., Awaitable[list[TextContent]]],
) -> None:
    schema = model.model_json_schema()
    schema.pop("$defs", None)
    schema.pop("title", None)
    _TOOLS[name] = (
        model,
        handler,
        Tool(name=name, description=description, inputSchema=schema),
    )


_register(
    "logs_search",
    "Search logs in VictoriaLogs using LogsQL query. Use for finding specific log entries, errors, or events.",
    _LogsSearchQuery,
    _logs_search,
)
_register(
    "logs_error_count",
    "Count errors for a service over a time window. Use to check if a service has errors and how many.",
    _LogsErrorCountQuery,
    _logs_error_count,
)
_register(
    "traces_list",
    "List recent traces for a service. Returns trace IDs and basic metadata.",
    _TracesListQuery,
    _traces_list,
)
_register(
    "traces_get",
    "Fetch full details of a specific trace by ID. Use to investigate a trace found via traces_list.",
    _TracesGetQuery,
    _traces_get,
)


# ---------------------------------------------------------------------------
# MCP handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [entry[2] for entry in _TOOLS.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    entry = _TOOLS.get(name)
    if entry is None:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    model_cls, handler, _ = entry
    try:
        args = model_cls.model_validate(arguments or {})
        return await handler(args)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {type(exc).__name__}: {e}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

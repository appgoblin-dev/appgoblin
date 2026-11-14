"""MCP server documentation endpoint.

Returns a programmatically-generated reference of all registered MCP tools,
their parameters, descriptions, and tier requirements — kept in sync
automatically with the actual tool registrations on ``mcp_server``.
"""

from __future__ import annotations

# ruff: noqa: E501
from litestar import Controller, get
from litestar.enums import MediaType

from api_app.mcp.server import mcp_server

MCP_DOCS_SERVERS = [
    {"url": "https://appgoblin.info", "description": "Production"},
]


def _parameter_schema(tool: object) -> dict:
    """Extract a human-readable parameter listing from a tool's input schema."""
    params: dict[str, object] = {}
    properties = tool.input_schema.get("properties", {})
    required = set(tool.input_schema.get("required", []))

    for name, prop in properties.items():
        param_info: dict[str, object] = {
            "type": prop.get("type", "string"),
            "required": name in required,
        }
        if prop.get("description"):
            param_info["description"] = prop["description"]
        if "default" in prop:
            param_info["default"] = prop["default"]
        params[name] = param_info

    return params


async def _build_tools_docs() -> dict:
    """Build a documentation payload from the live tool registry."""
    tools = await mcp_server.list_tools()
    tools_docs: list[dict[str, object]] = [
        {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": _parameter_schema(tool),
        }
        for tool in tools
    ]

    return {
        "server": {
            "name": mcp_server.name,
            "version": "0.1.0",
        },
        "protocol": "Streamable HTTP",
        "authentication": {
            "type": "http",
            "scheme": "bearer",
            "description": (
                "Generate an API Token from the AppGoblin dashboard at "
                "https://appgoblin.info/account/api-keys and send it as the "
                "`Authorization: Bearer <token>` header on every request. "
                "The legacy `X-API-Key` header is also accepted."
            ),
        },
        "endpoint": {
            "url": "{server}/api/v1/mcp",
            "description": (
                "Connect MCP clients (Claude Code, Cursor, etc.) to this "
                "Streamable HTTP endpoint. The server authenticates on every "
                "request via the `Authorization: Bearer` header and runs "
                "statelessly, with no sessions between requests. The legacy "
                "`X-API-Key` header is also accepted."
            ),
        },
        "rate_limits": (
            "REST and MCP share per-organization minute and daily limits across "
            "all members and API keys. Users without an organization have a "
            "separate free-tier allowance. Limits vary by subscription tier. "
            "Daily quotas reset at UTC midnight. "
            "Every MCP HTTP request counts toward the daily quota, including "
            "requests rejected by the per-minute limit."
        ),
        "tier_access": {
            "apps": "All tiers (free and paid).",
            "companies": "Paid tiers only (b2b_sdk, b2b_appads, b2b_premium).",
            "keywords": "All tiers (free and paid).",
        },
        "tools": tools_docs,
        "servers": MCP_DOCS_SERVERS,
    }


class MCPDocsController(Controller):
    """MCP server documentation endpoint — not included in OpenAPI schema."""

    path = "/api/v1/mcp-docs"
    include_in_schema = False

    @get(path="/tools.json")
    async def mcp_docs_json(self) -> dict:
        """Return the MCP tool reference as JSON."""
        return await _build_tools_docs()

    @get(media_type=MediaType.HTML)
    async def mcp_docs_html(self) -> str:
        """Render a human-readable HTML page listing all MCP tools."""
        docs = await _build_tools_docs()
        return _render_html(docs)


def _render_html(docs: dict) -> str:
    """Render the MCP docs payload as a self-contained HTML page."""
    tools_html = "".join(_render_tool_row(t) for t in docs["tools"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AppGoblin AI Agents — MCP Tool Reference</title>
<meta name="description" content="Model Context Protocol tool reference for the AppGoblin Intelligence Server. Connect Claude Code, Cursor, and other AI agents.">
<link rel="canonical" href="https://appgoblin.info/api-docs">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f0a1a; color: #e2d9f0; line-height: 1.6; }}
  .container {{ max-width: 960px; margin: 0 auto; padding: 2rem 1rem; }}
  h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem; color: #c4b5fd; }}
  .subtitle {{ color: #9a8ab5; margin-bottom: 2rem; font-size: 0.95rem; }}
  h2 {{ font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: #a78bfa; }}
  .section {{ background: #1a1230; border: 1px solid #2d2048; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; }}
  .section p {{ margin-bottom: 0.5rem; font-size: 0.9rem; }}
  .section ul {{ padding-left: 1.25rem; font-size: 0.9rem; }}
  .section li {{ margin-bottom: 0.25rem; }}
  code {{ background: #2a1f40; padding: 0.15em 0.4em; border-radius: 4px; font-size: 0.85em; color: #c4b5fd; }}
  .tool {{ background: #1a1230; border: 1px solid #2d2048; border-radius: 8px; padding: 1.25rem; margin-bottom: 0.75rem; }}
  .tool-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.35rem; }}
  .tool-name {{ font-family: "SF Mono", "Fira Code", monospace; font-weight: 600; font-size: 1rem; color: #a78bfa; }}
  .tool-desc {{ font-size: 0.88rem; color: #b8a9d6; margin-bottom: 0.5rem; }}
  .tool-params {{ font-size: 0.82rem; color: #9a8ab5; }}
  .tool-params span {{ display: inline-block; margin-right: 1rem; }}
  .badge {{ display: inline-block; font-size: 0.7rem; font-weight: 600; padding: 0.15em 0.5em; border-radius: 4px; text-transform: uppercase; }}
  .badge-free {{ background: #1e3a2f; color: #6ee7b7; }}
  .badge-paid {{ background: #3a1f2e; color: #f9a8d4; }}
  .endpoint-box {{ background: #120b1f; border: 1px solid #2d2048; border-radius: 6px; padding: 0.75rem 1rem; font-family: "SF Mono", "Fira Code", monospace; font-size: 0.85rem; margin: 0.5rem 0; color: #c4b5fd; word-break: break-all; }}
  a {{ color: #a78bfa; }}
  a:hover {{ color: #c4b5fd; }}
  hr {{ border: none; border-top: 1px solid #2d2048; margin: 1.5rem 0; }}
  .json-link {{ text-align: center; font-size: 0.8rem; color: #6b5b8a; margin-top: 1rem; }}
</style>
</head>
<body>
<div class="container">
  <h1>🤖 AppGoblin AI Agents</h1>
  <p class="subtitle">Model Context Protocol (MCP) Tool Reference</p>

  <div class="section">
    <h2>🔌 Connection</h2>
    <p>Connect your AI agent using the MCP Streamable HTTP endpoint:</p>
    <div class="endpoint-box">https://appgoblin.info/api/v1/mcp</div>
    <p>Authenticate with your API key via the <code>Authorization: Bearer &lt;token&gt;</code> header. The legacy <code>X-API-Key</code> header is also accepted.</p>
  </div>

  <div class="section">
    <h2>🔐 Authentication</h2>
    <p>Generate an API token from your <a href="https://appgoblin.info/account/api-keys">account dashboard</a> and pass it as the <code>Authorization: Bearer &lt;token&gt;</code> header on every request. The legacy <code>X-API-Key</code> header is also accepted.</p>
  <div class="section">
    <h2>⚡ Rate Limits</h2>
    <p>{docs["rate_limits"]}</p>
  </div>

  <div class="section">
    <h2>🎯 Tier Access</h2>
    <ul>
      <li><strong>Apps tools</strong> — {docs["tier_access"]["apps"]}</li>
      <li><strong>Company tools</strong> — {docs["tier_access"]["companies"]}</li>
      <li><strong>Keyword tools</strong> — {docs["tier_access"]["keywords"]}</li>
    </ul>
  </div>

  <h2>🛠️ Available Tools ({len(docs["tools"])})</h2>
  {tools_html}

  <hr>
  <p style="text-align:center;font-size:0.8rem;color:#6b5b8a;">
    AppGoblin Intelligence Server · <a href="/api-docs">REST API Docs</a> · <a href="/pricing">Pricing</a>
  </p>
</div>
</body>
</html>"""


def _render_tool_row(tool: dict) -> str:
    """Render a single tool as an HTML card."""
    params = tool.get("parameters", {})
    tier = (
        "paid"
        if tool["name"].startswith(("get_company", "list_", "search_companies"))
        else "free"
    )
    badge_class = "badge-paid" if tier == "paid" else "badge-free"

    params_html = ""
    if params:
        parts = []
        for name, info in params.items():
            req = "required" if info.get("required") else "optional"
            default = f", default: {info['default']}" if "default" in info else ""
            parts.append(
                f"<span><code>{name}</code> ({info['type']}, {req}{default})</span>"
            )
        params_html = f'<div class="tool-params">{" ".join(parts)}</div>'

    return f"""<div class="tool">
  <div class="tool-header">
    <span class="tool-name">{tool["name"]}</span>
    <span class="badge {badge_class}">{tier}</span>
  </div>
  <div class="tool-desc">{tool["description"]}</div>
  {params_html}
</div>"""

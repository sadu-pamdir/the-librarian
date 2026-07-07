#!/usr/bin/env python3
"""MCP server for the-librarian — stdio JSON-RPC, stdlib only.

Exposes the C1-C4 answer path as Model Context Protocol tools so that any
MCP client (Claude Code, Claude Desktop, local LLM harnesses) can use the
Librarian as a tool: navigate to sources instead of hallucinating.

Register (Claude Code, .mcp.json):
    {"mcpServers": {"librarian": {
        "command": "python3",
        "args": ["/path/to/the-librarian/src/librarian/mcp_server.py"]}}}

Requires kiwix-serve running (scripts/serve.sh) for the archive layer;
compiled pages and the knowledge-map work even without it.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import librarian  # noqa: E402

PROTOCOL = "2025-06-18"

TOOLS = [
    {
        "name": "ask_library",
        "description": (
            "Answer a factual question from the local, immutable library. "
            "Returns a passage plus a citation (source of record). If status "
            "is 'unsourced', NO source exists — any answer you give must be "
            "labeled as unsourced synthesis. Prefer this tool over your own "
            "memory for facts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The factual question or search phrase."},
                "lang": {"type": "string", "enum": ["deu", "eng"],
                         "description": "Optional language filter; defaults to deu, then eng."},
            },
            "required": ["question"],
        },
    },
    {
        "name": "list_topics",
        "description": "List all compiled topics in the knowledge-map (the curated C3/C4 layer).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_page",
        "description": "Read a compiled wiki page verbatim (file name from list_topics).",
        "inputSchema": {
            "type": "object",
            "properties": {"page": {"type": "string", "description": "Page file name, e.g. photosynthese.md"}},
            "required": ["page"],
        },
    },
]


def _text(payload) -> dict:
    return {"content": [{"type": "text",
                         "text": json.dumps(payload, ensure_ascii=False, indent=2)}]}


def call_tool(name: str, args: dict) -> dict:
    if name == "ask_library":
        ans = librarian.ask(args["question"], args.get("lang"))
        return _text(asdict(ans))
    if name == "list_topics":
        return _text(librarian.load_map())
    if name == "get_page":
        page = (librarian.COMPILED / args["page"]).resolve()
        if librarian.COMPILED.resolve() not in page.parents or not page.exists():
            return _text({"error": f"no such compiled page: {args['page']}"})
        return _text({"page": args["page"], "content": page.read_text(encoding="utf-8")})
    return _text({"error": f"unknown tool: {name}"})


def handle(msg: dict) -> dict | None:
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "the-librarian", "version": "0.1.0"},
        }}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        p = msg.get("params", {})
        try:
            result = call_tool(p.get("name", ""), p.get("arguments", {}) or {})
        except Exception as e:  # honest failure, never silent
            result = _text({"error": f"{type(e).__name__}: {e}"})
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if mid is not None:  # unknown request -> proper error; notifications get none
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

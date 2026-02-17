from __future__ import annotations

import ast
import datetime as dt
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ToolFn = Callable[[dict], str]


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    run: ToolFn


class ToolRegistry:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._tools: dict[str, Tool] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register(
            Tool(
                name="datetime_now",
                description="Get the current local date and time.",
                schema={"type": "object", "properties": {}},
                run=lambda _: dt.datetime.now().isoformat(),
            )
        )
        self.register(
            Tool(
                name="calculator",
                description="Safely evaluate a basic arithmetic expression.",
                schema={
                    "type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"],
                },
                run=self._calculator,
            )
        )
        self.register(
            Tool(
                name="web_search",
                description="Search the web using DuckDuckGo.",
                schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                run=self._web_search,
            )
        )
        self.register(
            Tool(
                name="read_text_file",
                description="Read a UTF-8 text file from workspace.",
                schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                run=self._read_text_file,
            )
        )
        self.register(
            Tool(
                name="write_text_file",
                description="Write UTF-8 text to a file in workspace.",
                schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
                run=self._write_text_file,
            )
        )
        self.register(
            Tool(
                name="shell",
                description="Run a safe shell command from allowlist.",
                schema={
                    "type": "object",
                    "properties": {"command": {"type": "string"}},
                    "required": ["command"],
                },
                run=self._shell,
            )
        )

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def list_for_prompt(self) -> str:
        payload = [
            {"name": t.name, "description": t.description, "schema": t.schema}
            for t in self._tools.values()
        ]
        return json.dumps(payload, indent=2)

    def run(self, name: str, args: dict) -> str:
        if name not in self._tools:
            return f"Tool '{name}' not found."
        try:
            return self._tools[name].run(args)
        except Exception as exc:  # noqa: BLE001
            return f"Tool '{name}' failed: {exc}"

    def _calculator(self, args: dict) -> str:
        expression = args["expression"]
        tree = ast.parse(expression, mode="eval")
        allowed = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Pow,
            ast.Mod,
            ast.USub,
            ast.Constant,
            ast.Load,
            ast.FloorDiv,
        )
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError("Unsupported expression")
        result = eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})
        return str(result)

    def _web_search(self, args: dict) -> str:
        query = args["query"]
        max_results = int(args.get("max_results", 5))
        try:
            from ddgs import DDGS
        except ImportError as exc:
            raise RuntimeError("ddgs package is required for web_search tool") from exc

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        compact = [
            {
                "title": item.get("title", ""),
                "href": item.get("href", ""),
                "body": item.get("body", ""),
            }
            for item in results
        ]
        return json.dumps(compact, indent=2)

    def _resolve_path(self, rel_path: str) -> Path:
        candidate = (self.workspace_root / rel_path).resolve()
        if self.workspace_root not in candidate.parents and candidate != self.workspace_root:
            raise ValueError("Path escapes workspace root")
        return candidate

    def _read_text_file(self, args: dict) -> str:
        path = self._resolve_path(args["path"])
        return path.read_text(encoding="utf-8")

    def _write_text_file(self, args: dict) -> str:
        path = self._resolve_path(args["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        return f"Wrote {len(args['content'])} characters to {path}"

    def _shell(self, args: dict) -> str:
        command = args["command"].strip()
        allowlist = {"echo", "pwd", "ls", "cat"}
        program = command.split()[0]
        if program not in allowlist:
            raise ValueError(f"Command '{program}' not allowed")
        cp = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=self.workspace_root)
        return (cp.stdout + cp.stderr).strip()

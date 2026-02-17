from __future__ import annotations

import json

from .config import AssistantConfig
from .llm import OllamaClient
from .memory import MemoryStore
from .tools import ToolRegistry


SYSTEM_PROMPT = """You are a local, privacy-first personal assistant agent.
You can think step by step and use tools.
Always respond ONLY as strict JSON with one of these shapes:
1) {"type":"tool_call","tool":"<name>","args":{...},"reason":"..."}
2) {"type":"final","response":"<message to user>"}

When useful, call tools iteratively to gather information, then produce a final response.
Never output text outside JSON.
"""


class PersonalAssistantAgent:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config
        self.memory = MemoryStore(config.memory_db_path)
        self.tools = ToolRegistry(config.workspace_root)
        self.llm = OllamaClient(config)

    def _messages_for_turn(self, user_input: str, scratchpad: list[dict[str, str]]) -> list[dict[str, str]]:
        tool_specs = self.tools.list_for_prompt()
        guide = f"Available tools:\n{tool_specs}"
        history = self.memory.recent(limit=12)
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": guide},
            *history,
            *scratchpad,
            {"role": "user", "content": user_input},
        ]

    @staticmethod
    def _parse_json(content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return {"type": "final", "response": content.strip()}
            return json.loads(content[start : end + 1])

    def run(self, user_input: str) -> str:
        self.memory.add("user", user_input)
        scratchpad: list[dict[str, str]] = []

        for _ in range(self.config.max_steps):
            messages = self._messages_for_turn(user_input, scratchpad)
            raw = self.llm.chat(messages)
            payload = self._parse_json(raw)

            if payload.get("type") == "final":
                answer = payload.get("response", "")
                self.memory.add("assistant", answer)
                return answer

            if payload.get("type") == "tool_call":
                tool_name = payload.get("tool", "")
                args = payload.get("args", {})
                reason = payload.get("reason", "")
                result = self.tools.run(tool_name, args)
                scratchpad.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(payload),
                    }
                )
                scratchpad.append(
                    {
                        "role": "system",
                        "content": f"Tool result for {tool_name} (reason: {reason}):\n{result}",
                    }
                )
                continue

            fallback = raw.strip() or "I could not complete that request."
            self.memory.add("assistant", fallback)
            return fallback

        timeout_msg = "I reached the step limit before finishing. Please rephrase or simplify the request."
        self.memory.add("assistant", timeout_msg)
        return timeout_msg

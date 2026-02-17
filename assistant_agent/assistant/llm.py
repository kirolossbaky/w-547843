from __future__ import annotations

import json
from typing import Any
from urllib import request

from .config import AssistantConfig


class OllamaClient:
    def __init__(self, config: AssistantConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.config.temperature},
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.config.ollama_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"]

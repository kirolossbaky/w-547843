from pathlib import Path

from assistant.agent import PersonalAssistantAgent
from assistant.config import AssistantConfig


class StubLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses

    def chat(self, _messages):
        return self.responses.pop(0)


def test_agent_uses_tool_and_returns_final(tmp_path: Path):
    config = AssistantConfig(memory_db_path=tmp_path / "mem.sqlite3", workspace_root=tmp_path)
    agent = PersonalAssistantAgent(config)
    agent.llm = StubLLM(
        [
            '{"type":"tool_call","tool":"calculator","args":{"expression":"2+3"},"reason":"compute"}',
            '{"type":"final","response":"The result is 5."}',
        ]
    )

    result = agent.run("what is 2+3?")
    assert result == "The result is 5."


def test_write_and_read_tools(tmp_path: Path):
    config = AssistantConfig(memory_db_path=tmp_path / "mem.sqlite3", workspace_root=tmp_path)
    agent = PersonalAssistantAgent(config)

    write_result = agent.tools.run("write_text_file", {"path": "notes/today.txt", "content": "hello"})
    assert "Wrote" in write_result

    read_result = agent.tools.run("read_text_file", {"path": "notes/today.txt"})
    assert read_result == "hello"

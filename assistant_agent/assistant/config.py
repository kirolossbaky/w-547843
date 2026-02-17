from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AssistantConfig:
    model: str = "llama3.1"
    ollama_url: str = "http://localhost:11434/api/chat"
    temperature: float = 0.2
    max_steps: int = 6
    memory_db_path: Path = Path("assistant_memory.sqlite3")
    workspace_root: Path = field(default_factory=lambda: Path.cwd())

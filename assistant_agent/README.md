# Open-Source Personal Assistant Agent (Python)

This project provides a **fully open-source personal assistant agent** in Python.

## Open-source stack (zero proprietary APIs)

- **LLM runtime:** [Ollama](https://github.com/ollama/ollama) local HTTP API.
- **Models:** any open model you run locally (examples: `llama3.1`, `mistral`, `qwen2.5`).
- **Web search:** [ddgs](https://pypi.org/project/ddgs/) (DuckDuckGo search client).
- **Memory:** local SQLite database.
- **Orchestration:** custom ReAct-style loop in pure Python.

No OpenAI/Anthropic/Gemini or other proprietary APIs are used.

## Features

- Multi-step tool-using agent loop.
- Local persistent memory (SQLite).
- Built-in tools:
  - Current datetime
  - Calculator
  - Shell command execution (safe allowlist)
  - DuckDuckGo web search
  - Read/write local text files
- Extensible tool registry for custom skills.

## Quick start

1. Install dependencies:

```bash
cd assistant_agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

2. Run Ollama and pull a model:

```bash
ollama serve
ollama pull llama3.1
```

3. Start the assistant:

```bash
assistant-agent --model llama3.1
```

## Usage

```text
You> Plan my day and create a todo file called today.txt
```

The assistant will decide whether to call tools or reply directly.

## Security notes

- Shell tool is restricted to an allowlist (`echo`, `pwd`, `ls`, `cat`).
- File read/write is limited to a workspace folder (default: current directory).
- Review and tighten tool permissions before real-world use.

## Architecture

- `assistant/config.py`: runtime config and defaults.
- `assistant/llm.py`: Ollama chat client.
- `assistant/memory.py`: SQLite memory backend.
- `assistant/tools.py`: tool registry + built-in tools.
- `assistant/agent.py`: core planning/execution loop.
- `assistant/cli.py`: interactive command-line interface.

## Run tests

```bash
pytest
```

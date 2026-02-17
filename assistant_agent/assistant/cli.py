from __future__ import annotations

import argparse

from .agent import PersonalAssistantAgent
from .config import AssistantConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open-source personal assistant agent")
    parser.add_argument("--model", default="llama3.1", help="Ollama model name")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-steps", type=int, default=6)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = AssistantConfig(model=args.model, temperature=args.temperature, max_steps=args.max_steps)
    agent = PersonalAssistantAgent(config)

    print("Open-Source Personal Assistant Agent")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You> ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break
        reply = agent.run(user_input)
        print(f"Assistant> {reply}\n")


if __name__ == "__main__":
    main()

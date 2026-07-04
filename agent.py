#!/usr/bin/env python3
"""
My Desktop Agent
----------------
A personal, fully-local desktop assistant built on:
  - Ollama (local LLM server)
  - Open Interpreter (code execution agent)

Run with:  python agent.py
"""

import os
import sys

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

BANNER = r"""
  ____            _    _                _                    _
 |  _ \  ___  ___| | _| |_ ___  _ __   / \   __ _  ___ _ __ | |_
 | | | |/ _ \/ __| |/ / __/ _ \| '_ \ / _ \ / _` |/ _ \ '_ \| __|
 | |_| |  __/\__ \   <| || (_) | |_) / ___ \ (_| |  __/ | | | |_
 |____/ \___||___/_|\_\\__\___/| .__/_/   \_\__, |\___|_| |_|\__|
                               |_|          |___/   100% local
"""

HELP_TEXT = """
Commands:
  /help     show this help
  /reset    wipe conversation memory and start fresh
  /model    show which model is active
  /auto     toggle auto-run (ask-before-executing on/off)
  /exit     quit
Anything else is sent to your agent.
"""


def load_config() -> dict:
    """Load settings from config.yaml, with safe fallbacks."""
    defaults = {
        "model": "qwen2.5-coder:7b",
        "api_base": "http://localhost:11434",
        "context_window": 8000,
        "max_tokens": 2000,
        "auto_run": False,
        "offline": True,
        "custom_instructions": "You are my personal desktop assistant.",
    }
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        defaults.update(user_cfg)
    except FileNotFoundError:
        print(f"[warn] {CONFIG_PATH} not found - using built-in defaults.")
    except yaml.YAMLError as e:
        print(f"[warn] Could not parse config.yaml ({e}) - using defaults.")
    return defaults


def check_ollama(api_base: str, model: str) -> bool:
    """Verify the Ollama server is up and the model is available."""
    import urllib.error
    import urllib.request
    import json

    try:
        with urllib.request.urlopen(f"{api_base}/api/tags", timeout=3) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError):
        print(f"[error] Can't reach Ollama at {api_base}.")
        print("        Is it running? Try:  ollama serve   (or open the Ollama app)")
        return False

    available = [m.get("name", "") for m in data.get("models", [])]
    # ollama names may include ":latest" suffix; match loosely
    if not any(model in name or name in model for name in available):
        print(f"[warn] Model '{model}' not found in Ollama.")
        print(f"       Available: {', '.join(available) or '(none)'}")
        print(f"       Pull it with:  ollama pull {model}")
        return False
    return True


def build_interpreter(cfg: dict):
    """Configure and return an Open Interpreter instance."""
    from interpreter import interpreter

    interpreter.offline = cfg["offline"]
    interpreter.auto_run = cfg["auto_run"]
    interpreter.llm.model = f"ollama_chat/{cfg['model']}"
    interpreter.llm.api_base = cfg["api_base"]
    interpreter.llm.context_window = cfg["context_window"]
    interpreter.llm.max_tokens = cfg["max_tokens"]
    interpreter.custom_instructions = cfg["custom_instructions"]
    return interpreter


def main() -> None:
    cfg = load_config()

    print(BANNER)
    print(f"  model: {cfg['model']}   auto-run: {cfg['auto_run']}")
    print("  type /help for commands\n")

    if not check_ollama(cfg["api_base"], cfg["model"]):
        sys.exit(1)

    agent = build_interpreter(cfg)

    while True:
        try:
            user_input = input("you > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye!")
            break

        if not user_input:
            continue

        # --- slash commands ---
        if user_input == "/exit":
            print("bye!")
            break
        if user_input == "/help":
            print(HELP_TEXT)
            continue
        if user_input == "/reset":
            agent.messages = []
            print("[memory wiped]")
            continue
        if user_input == "/model":
            print(f"[active model: {agent.llm.model} @ {agent.llm.api_base}]")
            continue
        if user_input == "/auto":
            agent.auto_run = not agent.auto_run
            state = "ON (careful!)" if agent.auto_run else "OFF (asks first)"
            print(f"[auto-run is now {state}]")
            continue

        # --- send to the agent ---
        try:
            agent.chat(user_input)
        except KeyboardInterrupt:
            print("\n[interrupted - back to prompt]")
        except Exception as e:
            print(f"[error] {e}")
            print("[tip] /reset can help if the conversation state got corrupted")


if __name__ == "__main__":
    main()

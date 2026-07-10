"""
agent_core.py – shared backend for both the GUI (app.py) and terminal (agent.py).
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"

_DEFAULT_INSTRUCTIONS = """\
You are a careful, step-by-step desktop assistant. Follow these rules on every task:

PLAN FIRST – before writing any code:
  1. Restate the task in one sentence.
  2. List the steps you will take (numbered, max 5 steps, each one sentence).
  3. State any risk (e.g. files will be moved/deleted).

EXECUTE one step at a time:
  - Write a small, focused code block for each step.
  - After each block runs, read the output and confirm it succeeded before moving on.
  - If a step fails, try ONE simple fix. If it still fails, stop and explain clearly.

NEVER:
  - Retry the exact same failing code more than once.
  - Write one giant code block that does everything at once.
  - Continue past a failed step without telling the user.

If you are stuck, say exactly:
  "I'm stuck on [specific problem]. Here's what I tried: [list]. What would you like me to do?"
"""

DEFAULTS = {
    "model": "qwen2.5:14b",
    "api_base": "http://localhost:11434",
    "context_window": 16000,
    "max_tokens": 4000,
    "temperature": 0.1,
    "auto_run": True,
    "offline": True,
    "custom_instructions": _DEFAULT_INSTRUCTIONS,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg.update(user_cfg)
    except FileNotFoundError:
        pass
    except yaml.YAMLError as e:
        print(f"[warn] config.yaml parse error: {e}")
    return cfg


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


def check_ollama(api_base: str, model: str) -> tuple[bool, list[str]]:
    """Returns (ok, list_of_available_model_names)."""
    try:
        with urllib.request.urlopen(f"{api_base}/api/tags", timeout=4) as resp:
            data = json.loads(resp.read())
    except (urllib.error.URLError, TimeoutError, OSError):
        return False, []

    available = [m.get("name", "") for m in data.get("models", [])]
    ok = any(model in name or name in model for name in available)
    return ok, available


def warm_model(api_base: str, model: str) -> bool:
    """
    Send a tiny generate request to force Ollama to load the model into memory.
    Blocks until the model is ready. Returns True on success.
    """
    try:
        import json
        data = json.dumps({
            "model": model,
            "prompt": "hi",
            "stream": False,
            "keep_alive": -1,
        }).encode()
        req = urllib.request.Request(
            f"{api_base}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp.read()
        return True
    except Exception:
        return False


def build_interpreter(cfg: dict):
    from interpreter import interpreter

    interpreter.offline    = cfg["offline"]
    interpreter.auto_run   = cfg["auto_run"]
    interpreter.llm.model  = f"ollama_chat/{cfg['model']}"
    interpreter.llm.api_base       = cfg["api_base"]
    interpreter.llm.context_window = cfg["context_window"]
    interpreter.llm.max_tokens     = cfg["max_tokens"]
    interpreter.llm.temperature    = cfg.get("temperature", 0.1)
    interpreter.custom_instructions = cfg["custom_instructions"]
    interpreter.messages = []

    # Limit runaway output so a broken loop can't fill memory
    try:
        interpreter.max_output = 8000
    except AttributeError:
        pass

    # Disable automatic retry loop on errors (Open Interpreter ≥ 0.3)
    for attr in ("loop", "force_task_completion"):
        try:
            setattr(interpreter, attr, False)
        except AttributeError:
            pass

    return interpreter

# My Desktop Agent (Ollama + Open Interpreter)

A personal, 100% local, 100% free desktop assistant. No API keys, no cloud, no cost.

## Files

- `agent.py` — the agent itself (chat loop, safety checks, slash commands)
- `config.yaml` — all your settings live here; edit this, not the code
- `requirements.txt` — python dependencies

## Setup (one time)

1. Make sure Ollama is running (open the app, or run `ollama serve`).
2. Check which model you have: `ollama list`
3. Open `config.yaml` and set `model:` to match one of your models exactly.
4. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

## Run it

```
python agent.py
```

Then just type what you want, e.g. "list the 5 biggest files in my Downloads folder".
The agent will write code and ask permission before running it.

## Commands inside the agent

| Command  | What it does                              |
|----------|-------------------------------------------|
| `/help`  | show commands                              |
| `/reset` | wipe conversation memory                   |
| `/model` | show active model                          |
| `/auto`  | toggle ask-before-executing on/off         |
| `/exit`  | quit                                       |

## Safety notes

- `auto_run: false` (the default) means the agent always asks before executing
  code. Keep it that way until you really trust your setup — it runs code on
  your REAL machine.
- Be extra careful with anything involving `rm`, `del`, or file moves.

## Ideas for upgrading it later

- **Bigger model**: if you have 16GB+ RAM or a GPU, try `qwen2.5-coder:14b`
  for noticeably smarter behavior. Update `model:` in config.yaml.
- **Global hotkey**: use the `keyboard` or `pynput` package so a key combo
  pops the agent open from anywhere.
- **Voice input**: pair with local whisper (e.g. `faster-whisper`) for a
  talk-to-your-PC Jarvis feel — still fully free and offline.
- **System tray app**: wrap it in `pystray` + a small tkinter window.
- **Task presets**: add your own slash commands in `agent.py` for things you
  do often (e.g. `/organize` → "sort my Downloads folder by file type").

"""
app.py – Desktop Agent GUI  (English / Thai)
Run:  python app.py
"""
import os
import sys

# Patch None streams before any other import (pythonw / wscript launch)
_nul_w = open(os.devnull, "w")
_nul_r = open(os.devnull, "r")
for _s, _f in [("stdout", _nul_w), ("stderr", _nul_w), ("stdin", _nul_r)]:
    if getattr(sys, _s) is None:
        setattr(sys, _s, _f)
    if getattr(sys, f"__{_s}__") is None:
        setattr(sys, f"__{_s}__", _f)

if sys.platform == "win32":
    import ctypes
    _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if _hwnd:
        ctypes.windll.user32.ShowWindow(_hwnd, 0)

import json
import queue
import re
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

import agent_core
import file_tools

# ── i18n strings ─────────────────────────────────────────────────────────────

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # sidebar
        "app_title":    "Desktop Agent",
        "nav_chat":     "💬   Chat",
        "nav_files":    "📁   Files",
        "nav_settings": "⚙️   Settings",
        "recent_chats": "Recent Chats",
        "new_chat":     "+ New Chat",
        "lang_btn":     "🌐  ภาษาไทย",
        "status_start": "● starting…",
        # chat view
        "chat_title":   "Chat with Agent",
        "focus_prefix": "📂  Working folder:",
        "focus_none":   "⚠ Not set — please pick a folder first",
        "btn_browse":   "Browse",
        "sys_no_focus": "⚠ Please select a working folder before chatting. Click Browse above.",
        "btn_clear":    "Clear",
        "btn_send":     "Send",
        "btn_stop":     "⏹  Stop",
        "btn_continue": "▶  Continue",
        "continue_nudge": "The last step didn't finish. Please try a different approach and continue.",
        "chat_ph":      "Type a message…",
        "open_explorer":"Open in Explorer",
        # quick actions
        "qa_downloads": "📂 Organize Downloads",
        "qa_summarize": "📄 Summarize a file…",
        "qa_find":      "🔍 Find files…",
        "qa_desktop":   "🖥 What's on Desktop?",
        # files view
        "files_title":  "File Manager",
        "btn_up":       "⬆ Up",
        "set_focus":    "Set as Focus",
        "btn_organize": "Organize",
        "search_ph":    "Search file contents…",
        "btn_search":   "Search",
        "tree_col":     "Name",
        "tree_hdr":     "Files & Folders",
        "no_file":      "No file selected",
        "open_folder":  "Open folder",
        "btn_summarize":"Summarize",
        "btn_save":     "Save",
        # settings view
        "settings_title":"Settings",
        "lbl_model":    "Model",
        "lbl_apibase":  "Ollama API base",
        "lbl_ctx":      "Context window",
        "lbl_tokens":   "Max tokens",
        "lbl_autorun":  "Auto-run code  ⚠",
        "lbl_instruct": "Custom instructions",
        "btn_save_cfg": "Save & Reload Agent",
        "hint_model":   "e.g. qwen2.5:14b",
        "hint_apibase": "default: http://localhost:11434",
        "hint_ctx":     "tokens – lower = faster",
        "hint_tokens":  "max reply length",
        # system chat messages
        "sys_focus_set":    "Working folder set to: {path}",
        "sys_summarizing":  "Summarizing: {name}",
        "sys_saved_reload": "Settings saved. Reloading agent…",
        "sys_ready":        "Connected to {model}. Ready!",
        "sys_offline":      "Cannot reach Ollama or model '{model}' not found.\nAvailable: {available}\nRun: ollama pull {model}",
        "sys_fail":         "Failed to load agent: {err}",
        "sys_not_ready":    "Agent not ready – please wait.",
        "sys_thinking":     "Thinking…",
        "sys_stopped":      "⏹ Stopped.",
        "sys_max_errors":   "⚠ Stopped after {n} consecutive errors. Try a simpler or more specific request.",
        "sys_timeout":      "⏹ Timed out after {m} minutes. The task may be too complex — try breaking it into smaller steps.",
        # dialogs
        "d_no_file":        "No file",
        "d_no_file_msg":    "Open a text file first.",
        "d_not_ready":      "Not ready",
        "d_not_ready_msg":  "Agent is not connected yet.",
        "d_busy":           "Busy",
        "d_busy_msg":       "Agent is working on something else.",
        "d_no_folder":      "No folder",
        "d_no_folder_msg":  "Enter a valid folder path first.",
        "d_organize":       "Organize folder",
        "d_organize_msg":   "Move files in:\n{folder}\ninto subfolders by type?\n\nThis cannot be undone automatically.",
        "d_done":           "Done",
        "d_done_msg":       "Moved {n} file(s):\n\n{summary}",
        "d_saved":          "Saved",
        "d_saved_msg":      "Saved {name}",
        "d_error":          "Error",
        "d_save_err":       "Could not save:\n{err}",
        "d_not_text":       "Not a text file",
        "d_not_text_msg":   "Only plain-text files can be summarized directly.",
        # file-picker titles
        "fp_focus":         "Choose working folder",
        "fp_files":         "Select Folder",
        "fp_summarize":     "Choose a file to summarize",
        "fp_find":          "Which folder should I search?",
        # qa prompts sent to agent
        "qa_dl_prompt":     "Organize my Downloads folder at {path}",
        "qa_find_prompt":   "What kinds of files are in this folder? Give me a summary.",
        "qa_desktop_prompt":"What files and folders are on my Desktop at {path}?",
        "qa_summarize_prompt":"Summarize this document concisely:\n\n{content}",
        "qa_summarize_tag": "[Summarize: {name}]",
    },
    "th": {
        # sidebar
        "app_title":    "ผู้ช่วยเดสก์ท็อป",
        "nav_chat":     "💬   แชท",
        "nav_files":    "📁   ไฟล์",
        "nav_settings": "⚙️   ตั้งค่า",
        "recent_chats": "ประวัติการสนทนา",
        "new_chat":     "+ สนทนาใหม่",
        "lang_btn":     "🌐  English",
        "status_start": "● กำลังเริ่ม…",
        # chat view
        "chat_title":   "คุยกับ Agent",
        "focus_prefix": "📂  โฟลเดอร์ที่ใช้งาน:",
        "focus_none":   "⚠ ยังไม่ได้เลือก — กรุณาเลือกโฟลเดอร์ก่อน",
        "btn_browse":   "เลือก",
        "sys_no_focus": "⚠ กรุณาเลือกโฟลเดอร์ที่ใช้งานก่อนเริ่มคุย กดปุ่ม Browse ด้านบน",
        "btn_clear":    "ล้าง",
        "btn_send":     "ส่ง",
        "btn_stop":     "⏹  หยุด",
        "btn_continue": "▶  ทำต่อ",
        "continue_nudge": "ขั้นตอนที่แล้วยังไม่เสร็จ กรุณาลองวิธีอื่นและทำต่อ",
        "chat_ph":      "พิมพ์ข้อความ…",
        "open_explorer":"เปิดใน Explorer",
        # quick actions
        "qa_downloads": "📂 จัดระเบียบ Downloads",
        "qa_summarize": "📄 สรุปไฟล์…",
        "qa_find":      "🔍 ค้นหาไฟล์…",
        "qa_desktop":   "🖥 มีอะไรบน Desktop?",
        # files view
        "files_title":  "จัดการไฟล์",
        "btn_up":       "⬆ ขึ้น",
        "set_focus":    "ตั้งเป็นโฟลเดอร์หลัก",
        "btn_organize": "จัดระเบียบ",
        "search_ph":    "ค้นหาเนื้อหาไฟล์…",
        "btn_search":   "ค้นหา",
        "tree_col":     "ชื่อ",
        "tree_hdr":     "ไฟล์และโฟลเดอร์",
        "no_file":      "ยังไม่ได้เลือกไฟล์",
        "open_folder":  "เปิดโฟลเดอร์",
        "btn_summarize":"สรุป",
        "btn_save":     "บันทึก",
        # settings view
        "settings_title":"ตั้งค่า",
        "lbl_model":    "โมเดล",
        "lbl_apibase":  "Ollama API",
        "lbl_ctx":      "หน้าต่างบริบท",
        "lbl_tokens":   "Tokens สูงสุด",
        "lbl_autorun":  "รันโค้ดอัตโนมัติ  ⚠",
        "lbl_instruct": "คำสั่งพิเศษ",
        "btn_save_cfg": "บันทึกและโหลดผู้ช่วยใหม่",
        "hint_model":   "เช่น qwen2.5:14b",
        "hint_apibase": "ค่าเริ่มต้น: http://localhost:11434",
        "hint_ctx":     "tokens – น้อย = เร็วขึ้น",
        "hint_tokens":  "ความยาวสูงสุดของคำตอบ",
        # system chat messages
        "sys_focus_set":    "ตั้งโฟลเดอร์ที่ใช้งานเป็น: {path}",
        "sys_summarizing":  "กำลังสรุป: {name}",
        "sys_saved_reload": "บันทึกการตั้งค่าแล้ว กำลังโหลดผู้ช่วยใหม่…",
        "sys_ready":        "เชื่อมต่อกับ {model} แล้ว พร้อมใช้งาน!",
        "sys_offline":      "ไม่สามารถเชื่อมต่อกับ Ollama หรือไม่พบโมเดล '{model}'\nโมเดลที่มี: {available}\nรัน: ollama pull {model}",
        "sys_fail":         "โหลดผู้ช่วยไม่สำเร็จ: {err}",
        "sys_not_ready":    "ผู้ช่วยยังไม่พร้อม – กรุณารอสักครู่",
        "sys_thinking":     "กำลังคิด…",
        "sys_stopped":      "⏹ หยุดแล้ว",
        "sys_max_errors":   "⚠ หยุดหลังเกิดข้อผิดพลาด {n} ครั้งติดต่อกัน กรุณาลองใหม่ด้วยคำสั่งที่เจาะจงมากขึ้น",
        "sys_timeout":      "⏹ หมดเวลาหลังจาก {m} นาที งานอาจซับซ้อนเกินไป – ลองแบ่งเป็นขั้นตอนย่อย",
        # dialogs
        "d_no_file":        "ไม่มีไฟล์",
        "d_no_file_msg":    "กรุณาเปิดไฟล์ข้อความก่อน",
        "d_not_ready":      "ยังไม่พร้อม",
        "d_not_ready_msg":  "ผู้ช่วยยังไม่ได้เชื่อมต่อ",
        "d_busy":           "กำลังทำงาน",
        "d_busy_msg":       "ผู้ช่วยกำลังทำงานอยู่",
        "d_no_folder":      "ไม่มีโฟลเดอร์",
        "d_no_folder_msg":  "กรุณาระบุโฟลเดอร์ที่ถูกต้องก่อน",
        "d_organize":       "จัดระเบียบโฟลเดอร์",
        "d_organize_msg":   "ย้ายไฟล์ใน:\n{folder}\nเข้าโฟลเดอร์ย่อยตามประเภท?\n\nไม่สามารถย้อนกลับได้อัตโนมัติ",
        "d_done":           "เสร็จสิ้น",
        "d_done_msg":       "ย้ายแล้ว {n} ไฟล์:\n\n{summary}",
        "d_saved":          "บันทึกแล้ว",
        "d_saved_msg":      "บันทึก {name} แล้ว",
        "d_error":          "เกิดข้อผิดพลาด",
        "d_save_err":       "ไม่สามารถบันทึกได้:\n{err}",
        "d_not_text":       "ไม่ใช่ไฟล์ข้อความ",
        "d_not_text_msg":   "สามารถสรุปได้เฉพาะไฟล์ข้อความเท่านั้น",
        # file-picker titles
        "fp_focus":         "เลือกโฟลเดอร์ที่ใช้งาน",
        "fp_files":         "เลือกโฟลเดอร์",
        "fp_summarize":     "เลือกไฟล์ที่ต้องการสรุป",
        "fp_find":          "เลือกโฟลเดอร์ที่ต้องการค้นหา",
        # qa prompts
        "qa_dl_prompt":     "จัดระเบียบโฟลเดอร์ Downloads ของฉันที่ {path}",
        "qa_find_prompt":   "มีไฟล์ประเภทอะไรบ้างในโฟลเดอร์นี้? ช่วยสรุปให้หน่อย",
        "qa_desktop_prompt":"มีไฟล์และโฟลเดอร์อะไรบ้างบน Desktop ของฉันที่ {path}?",
        "qa_summarize_prompt":"สรุปเอกสารนี้อย่างกระชับ:\n\n{content}",
        "qa_summarize_tag": "[สรุป: {name}]",
    },
}

# ── constants & theme ─────────────────────────────────────────────────────────

HISTORY_DIR = Path.home() / ".desktop_agent" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

FONT_BASE = 14
SIDEBAR_W = 215

_WIN_PATH = re.compile(r'[A-Za-z]:\\(?:[^\s\n"\'<>|?*:]+\\)*[^\s\n"\'<>|?*:]*')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CLR_BG       = "#1e1e2e"
CLR_SIDEBAR  = "#181825"
CLR_PANEL    = "#24243e"
CLR_USER     = "#89dceb"
CLR_AGENT    = "#cdd6f4"
CLR_CODE     = "#a6e3a1"
CLR_SYSTEM   = "#7f849c"
CLR_ERROR    = "#f38ba8"
CLR_GREEN    = "#40a02b"
CLR_PURPLE   = "#8839ef"
CLR_BLUE     = "#1e66f5"
CLR_ORANGE   = "#e08a00"
CLR_NAV_ACT  = "#313244"
CLR_NAV_IDLE = "#1e1e2e"
CLR_ACTION   = "#1a2f4a"


# ── ThinkFilter ───────────────────────────────────────────────────────────────

class ThinkFilter:
    """Strips <think>…</think> from a stream; safe across chunk boundaries."""

    def __init__(self) -> None:
        self._in_think = False
        self._buf = ""

    def feed(self, chunk: str) -> str:
        self._buf += chunk
        out = ""
        while self._buf:
            if self._in_think:
                end = self._buf.find("</think>")
                if end == -1:
                    self._buf = self._buf[-8:]
                    break
                self._in_think = False
                self._buf = self._buf[end + 8:]
            else:
                start = self._buf.find("<think>")
                if start == -1:
                    safe = max(0, len(self._buf) - 7)
                    out += self._buf[:safe]
                    self._buf = self._buf[safe:]
                    break
                out += self._buf[:start]
                self._in_think = True
                self._buf = self._buf[start + 7:]
        return out

    def flush(self) -> str:
        if self._in_think:
            self._buf = ""
            return ""
        out, self._buf = self._buf, ""
        return out


# ── helpers ───────────────────────────────────────────────────────────────────

def _treeview_style() -> None:
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("DA.Treeview",
                    background="#313244", foreground="#cdd6f4",
                    fieldbackground="#313244", rowheight=26,
                    font=("Segoe UI", 13))
    style.configure("DA.Treeview.Heading",
                    background="#45475a", foreground="#cdd6f4",
                    font=("Segoe UI", 13, "bold"))
    style.map("DA.Treeview", background=[("selected", "#1e66f5")])


def _open_explorer(path: str) -> None:
    p = Path(path)
    target = str(p) if p.is_dir() else str(p.parent)
    subprocess.Popen(["explorer", target])


LANG_ICONS: dict[str, str] = {
    "python":     "🐍 Python",
    "javascript": "🟨 JavaScript",
    "typescript": "🔷 TypeScript",
    "bash":       "🖥 Shell",
    "shell":      "🖥 Shell",
    "sh":         "🖥 Shell",
    "powershell": "💙 PowerShell",
    "html":       "🌐 HTML",
    "css":        "🎨 CSS",
    "sql":        "🗃 SQL",
    "json":       "📋 JSON",
    "markdown":   "📝 Markdown",
    "r":          "📊 R",
    "rust":       "🦀 Rust",
    "go":         "🐹 Go",
}


# ── Main app ──────────────────────────────────────────────────────────────────

class DesktopAgentApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()
        self.geometry("1300x820")
        self.minsize(980, 660)
        self.configure(fg_color=CLR_BG)

        self._lang: str = "en"
        self._i18n: list[callable] = []   # registered updaters for language switch

        self.cfg = agent_core.load_config()
        self.agent = None
        self._busy = False
        self._current_file: str | None = None
        self._focus_path: str | None = None
        self._last_location: str | None = None
        self._font_size: int = FONT_BASE
        self._session_msgs: list[dict] = []
        self._session_file: Path | None = None
        self._agent_buf = ""
        self._q: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._timeout_id: str | None = None   # tk after() handle

        # shared BooleanVar — initialised here so both chat and settings tabs share it
        self._sv_auto = tk.BooleanVar(value=self.cfg.get("auto_run", True))

        self._new_session()
        _treeview_style()
        self._build_sidebar()
        self._build_views()
        self._switch("chat")
        self._apply_lang()         # initial render in English

        self.title(self._s("app_title"))
        self.after(100, self._poll)
        self._init_agent()

    # ── i18n helpers ─────────────────────────────────────────────────────────

    def _s(self, key: str, **kw) -> str:
        """Return translated string, optionally formatted."""
        template = STRINGS[self._lang].get(key, STRINGS["en"].get(key, key))
        return template.format(**kw) if kw else template

    def _tr(self, widget, key: str, attr: str = "text") -> None:
        """Register widget for language updates and apply immediately."""
        def _update():
            widget.configure(**{attr: self._s(key)})
        self._i18n.append(_update)

    def _apply_lang(self) -> None:
        self.title(self._s("app_title"))
        for fn in self._i18n:
            fn()
        # dynamic-state labels that depend on both language AND current state
        if self._focus_path:
            self._focus_label.configure(text=Path(self._focus_path).name,
                                        text_color="#89b4fa")
        else:
            self._focus_label.configure(text=self._s("focus_none"),
                                        text_color="#f38ba8")
        if not self._current_file:
            self._file_label.configure(text=self._s("no_file"))
        self._tree.heading("#0", text=self._s("tree_col"))

    def _toggle_lang(self) -> None:
        self._lang = "th" if self._lang == "en" else "en"
        self._apply_lang()

    # ── sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, width=SIDEBAR_W, corner_radius=0, fg_color=CLR_SIDEBAR)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        lbl = ctk.CTkLabel(sb, text="", font=("Segoe UI", 17, "bold"),
                            text_color="#cdd6f4")
        lbl.pack(pady=(24, 18))
        self._tr(lbl, "app_title")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for key, view in [("nav_chat", "chat"),
                           ("nav_files", "files"),
                           ("nav_settings", "settings")]:
            btn = ctk.CTkButton(
                sb, text="", width=SIDEBAR_W - 20, height=46,
                font=("Segoe UI", 14), anchor="w", corner_radius=10,
                fg_color=CLR_NAV_IDLE, hover_color=CLR_NAV_ACT,
                text_color="#cdd6f4",
                command=lambda v=view: self._switch(v),
            )
            btn.pack(padx=10, pady=3)
            self._nav_btns[view] = btn
            self._tr(btn, key)

        # recent chats
        lbl_rc = ctk.CTkLabel(sb, text="", font=("Segoe UI", 11, "bold"),
                               text_color="#6c7086")
        lbl_rc.pack(anchor="w", padx=14, pady=(18, 4))
        self._tr(lbl_rc, "recent_chats")

        self._history_frame = ctk.CTkScrollableFrame(
            sb, fg_color="transparent", height=200)
        self._history_frame.pack(fill="x", padx=6, pady=(0, 4))

        btn_nc = ctk.CTkButton(sb, text="", width=SIDEBAR_W - 20, height=34,
                               font=("Segoe UI", 12), fg_color="#2a2a3e",
                               hover_color="#3a3a5e", text_color="#cdd6f4",
                               command=self._new_chat)
        btn_nc.pack(padx=10, pady=(0, 6))
        self._tr(btn_nc, "new_chat")

        # language toggle
        self._btn_lang = ctk.CTkButton(
            sb, text="", width=SIDEBAR_W - 20, height=36,
            font=("Segoe UI", 12), fg_color="#2a3a2a", hover_color="#3a4a3a",
            text_color="#a6e3a1", command=self._toggle_lang)
        self._btn_lang.pack(padx=10, pady=(0, 6))
        self._tr(self._btn_lang, "lang_btn")

        self._status = ctk.CTkLabel(sb, text="", font=("Segoe UI", 12),
                                     text_color=CLR_SYSTEM)
        self._status.pack(side="bottom", pady=14)
        self._tr(self._status, "status_start")

        self._refresh_history_list()

    # ── views ─────────────────────────────────────────────────────────────────

    def _build_views(self) -> None:
        self._main = ctk.CTkFrame(self, corner_radius=0, fg_color=CLR_BG)
        self._main.pack(side="left", fill="both", expand=True)

        self._views: dict[str, ctk.CTkFrame] = {
            "chat":     self._build_chat(),
            "files":    self._build_files(),
            "settings": self._build_settings(),
        }

    def _switch(self, view: str) -> None:
        for k, frame in self._views.items():
            if k == view:
                frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            else:
                frame.place_forget()
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color=CLR_NAV_ACT if k == view else CLR_NAV_IDLE)

    # ── chat view ─────────────────────────────────────────────────────────────

    def _build_chat(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._main, corner_radius=0, fg_color=CLR_BG)

        # header
        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 4))

        lbl_title = ctk.CTkLabel(hdr, text="", font=("Segoe UI", 18, "bold"),
                                  text_color="#cdd6f4")
        lbl_title.pack(side="left")
        self._tr(lbl_title, "chat_title")

        btn_aplus = ctk.CTkButton(hdr, text="A+", width=36, height=30,
                                   font=("Segoe UI", 12), fg_color="#313244",
                                   hover_color="#45475a",
                                   command=lambda: self._change_font(+1))
        btn_aplus.pack(side="right", padx=(4, 0))

        btn_aminus = ctk.CTkButton(hdr, text="A−", width=36, height=30,
                                    font=("Segoe UI", 12), fg_color="#313244",
                                    hover_color="#45475a",
                                    command=lambda: self._change_font(-1))
        btn_aminus.pack(side="right", padx=(4, 0))

        # focus bar
        focus_bar = ctk.CTkFrame(frame, fg_color="#1e2a3a", corner_radius=10)
        focus_bar.pack(fill="x", padx=24, pady=(0, 6))
        self._focus_bar = focus_bar

        lbl_fp = ctk.CTkLabel(focus_bar, text="", font=("Segoe UI", 12),
                               text_color=CLR_SYSTEM)
        lbl_fp.pack(side="left", padx=(10, 4))
        self._tr(lbl_fp, "focus_prefix")

        self._focus_label = ctk.CTkLabel(focus_bar, text="", font=("Segoe UI", 12),
                                          text_color="#cdd6f4", anchor="w")
        self._focus_label.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_fbrowse = ctk.CTkButton(focus_bar, text="", width=70, height=28,
                                     font=("Segoe UI", 11), fg_color="#2a3a5a",
                                     hover_color="#3a4a6a",
                                     command=self._pick_focus_path)
        btn_fbrowse.pack(side="right", padx=(4, 4))
        self._tr(btn_fbrowse, "btn_browse")

        ctk.CTkButton(focus_bar, text="✕", width=28, height=28,
                      font=("Segoe UI", 11), fg_color="#3a2a2a",
                      hover_color="#5a3a3a",
                      command=self._clear_focus_path).pack(side="right", padx=(0, 4))

        # chat display
        self._chat_box = ctk.CTkTextbox(
            frame, font=("Segoe UI", self._font_size),
            wrap="word", state="disabled", fg_color=CLR_PANEL,
            text_color=CLR_AGENT, corner_radius=12)
        self._chat_box.pack(fill="both", expand=True, padx=24, pady=(0, 6))

        tb = self._chat_box._textbox
        fs = self._font_size
        tb.tag_configure("user",        foreground=CLR_USER)
        tb.tag_configure("agent",       foreground=CLR_AGENT)
        tb.tag_configure("system",      foreground=CLR_SYSTEM)
        tb.tag_configure("error",       foreground=CLR_ERROR)
        tb.tag_configure("label",       foreground="#6c7086")
        # code block – header bar with green bg, body with dark bg
        tb.tag_configure("code_header", foreground="#0d1a0d",
                         background="#a6e3a1",
                         font=("Segoe UI", fs - 1, "bold"),
                         spacing1=6, spacing3=4, lmargin1=8, lmargin2=8)
        tb.tag_configure("code_body",   foreground="#d4efb3",
                         background="#0d1a0d",
                         font=("Consolas", fs),
                         spacing1=0, spacing3=0, lmargin1=8, lmargin2=8)
        tb.tag_configure("code_sep",    foreground="#1a2e1a",
                         background="#0d1a0d",
                         font=("Segoe UI", 6), spacing3=6)
        # console output colours
        tb.tag_configure("success",     foreground="#a6e3a1",   # green
                         font=("Consolas", fs - 1))
        tb.tag_configure("error_out",   foreground="#f38ba8",   # red
                         font=("Consolas", fs - 1))

        # action bar (last location – hidden until needed)
        self._action_bar = ctk.CTkFrame(frame, fg_color=CLR_ACTION, corner_radius=8)
        self._action_label = ctk.CTkLabel(self._action_bar, text="",
                                           font=("Segoe UI", 12),
                                           text_color="#89b4fa", anchor="w")
        self._action_label.pack(side="left", padx=(10, 6), pady=6,
                                fill="x", expand=True)
        self._btn_open_explorer = ctk.CTkButton(
            self._action_bar, text="", width=160, height=30,
            font=("Segoe UI", 12), fg_color=CLR_BLUE,
            hover_color="#2575f5", command=self._open_last_location)
        self._btn_open_explorer.pack(side="right", padx=8, pady=6)
        self._tr(self._btn_open_explorer, "open_explorer")

        # quick actions
        qa_frame = ctk.CTkFrame(frame, fg_color="transparent")
        qa_frame.pack(fill="x", padx=24, pady=(0, 4))

        qa_defs = [
            ("qa_downloads", self._qa_organize_downloads),
            ("qa_summarize", self._qa_summarize_file),
            ("qa_find",      self._qa_find_files),
            ("qa_desktop",   self._qa_desktop_summary),
        ]
        for key, cmd in qa_defs:
            btn = ctk.CTkButton(qa_frame, text="", height=34, font=("Segoe UI", 12),
                                fg_color="#313244", hover_color="#45475a",
                                text_color="#cdd6f4", corner_radius=8,
                                command=cmd)
            btn.pack(side="left", padx=(0, 6))
            self._tr(btn, key)

        # auto-run toggle row
        ar_row = ctk.CTkFrame(frame, fg_color="transparent")
        ar_row.pack(fill="x", padx=24, pady=(0, 6))
        ar_lbl = ctk.CTkLabel(ar_row, text="", font=("Segoe UI", 12),
                               text_color="#a6adc8")
        ar_lbl.pack(side="left", padx=(0, 6))
        self._tr(ar_lbl, "lbl_autorun")
        self._ar_switch = ctk.CTkSwitch(ar_row, variable=self._sv_auto, text="",
                                         onvalue=True, offvalue=False,
                                         command=self._on_autorun_toggle,
                                         width=44, height=22)
        self._ar_switch.pack(side="left")

        # input row
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(0, 18))
        self._input_row = row

        btn_clr = ctk.CTkButton(row, text="", width=74, height=46,
                                 font=("Segoe UI", 14), fg_color="#45475a",
                                 hover_color="#585b70", command=self._clear_chat)
        btn_clr.pack(side="right", padx=(6, 0))
        self._tr(btn_clr, "btn_clear")

        self._send_btn = ctk.CTkButton(row, text="", width=110, height=46,
                                        font=("Segoe UI", 14), fg_color=CLR_BLUE,
                                        command=self._send_or_stop)
        self._send_btn.pack(side="right", padx=(6, 0))
        self._tr(self._send_btn, "btn_send")

        self._chat_entry = ctk.CTkEntry(row, placeholder_text="",
                                         font=("Segoe UI", self._font_size),
                                         height=46, corner_radius=10)
        self._chat_entry.pack(side="left", fill="x", expand=True)

        # continue bar — shown after agent stops mid-task
        self._continue_bar = ctk.CTkFrame(frame, fg_color="#1e3a1e", corner_radius=8)
        self._continue_btn = ctk.CTkButton(
            self._continue_bar, text="", width=160, height=34,
            font=("Segoe UI", 13, "bold"), fg_color="#2d6a2d",
            hover_color="#3a8a3a", command=self._do_continue)
        self._continue_btn.pack(side="left", padx=10, pady=6)
        ctk.CTkLabel(self._continue_bar,
                     text="Agent stopped — click to keep going",
                     font=("Segoe UI", 12), text_color="#a6e3a1").pack(
            side="left", padx=(0, 10))
        self._tr(self._continue_btn, "btn_continue")
        self._chat_entry.bind("<Return>", lambda _e: self._send())
        self._tr(self._chat_entry, "chat_ph", attr="placeholder_text")

        return frame

    # ── files view ────────────────────────────────────────────────────────────

    def _build_files(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._main, corner_radius=0, fg_color=CLR_BG)

        lbl_title = ctk.CTkLabel(frame, text="", font=("Segoe UI", 18, "bold"),
                                  text_color="#cdd6f4")
        lbl_title.pack(anchor="w", padx=24, pady=(20, 8))
        self._tr(lbl_title, "files_title")

        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=24, pady=(0, 6))

        self._folder_var = tk.StringVar(value=str(Path.home()))
        folder_entry = ctk.CTkEntry(toolbar, textvariable=self._folder_var,
                                     font=("Segoe UI", 14), height=40, corner_radius=10)
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        folder_entry.bind("<Return>", lambda _e: self._load_tree(self._folder_var.get()))

        btn_brw = ctk.CTkButton(toolbar, text="", width=80, height=40,
                                 font=("Segoe UI", 14), command=self._browse)
        btn_brw.pack(side="left", padx=(0, 6))
        self._tr(btn_brw, "btn_browse")

        btn_up = ctk.CTkButton(toolbar, text="", width=80, height=40,
                                font=("Segoe UI", 14), fg_color="#45475a",
                                hover_color="#585b70", command=self._go_up)
        btn_up.pack(side="left", padx=(0, 6))
        self._tr(btn_up, "btn_up")

        btn_sf = ctk.CTkButton(toolbar, text="", width=130, height=40,
                                font=("Segoe UI", 13), fg_color=CLR_ORANGE,
                                hover_color="#c07800",
                                command=self._set_focus_from_files)
        btn_sf.pack(side="left", padx=(0, 6))
        self._tr(btn_sf, "set_focus")

        btn_org = ctk.CTkButton(toolbar, text="", width=110, height=40,
                                 font=("Segoe UI", 14), fg_color=CLR_GREEN,
                                 hover_color="#2aaa23", command=self._organize)
        btn_org.pack(side="left")
        self._tr(btn_org, "btn_organize")

        srow = ctk.CTkFrame(frame, fg_color="transparent")
        srow.pack(fill="x", padx=24, pady=(0, 8))

        self._search_var = tk.StringVar()
        self._srch_entry = ctk.CTkEntry(srow, textvariable=self._search_var,
                                         placeholder_text="",
                                         font=("Segoe UI", 14), height=40, corner_radius=10)
        self._srch_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._srch_entry.bind("<Return>", lambda _e: self._search())
        self._tr(self._srch_entry, "search_ph", attr="placeholder_text")

        btn_srch = ctk.CTkButton(srow, text="", width=90, height=40,
                                  font=("Segoe UI", 14), command=self._search)
        btn_srch.pack(side="left")
        self._tr(btn_srch, "btn_search")

        paned = tk.PanedWindow(frame, orient="horizontal",
                               bg="#45475a", sashwidth=5, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # left – tree
        left = ctk.CTkFrame(paned, fg_color=CLR_PANEL, corner_radius=10)
        paned.add(left, minsize=220)

        self._lbl_tree_hdr = ctk.CTkLabel(left, text="",
                                           font=("Segoe UI", 13, "bold"),
                                           text_color="#6c7086")
        self._lbl_tree_hdr.pack(anchor="w", padx=10, pady=(8, 2))
        self._tr(self._lbl_tree_hdr, "tree_hdr")

        tree_wrap = tk.Frame(left, bg=CLR_PANEL)
        tree_wrap.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical")
        vsb.pack(side="right", fill="y")

        self._tree = ttk.Treeview(tree_wrap, style="DA.Treeview",
                                   yscrollcommand=vsb.set, selectmode="browse")
        self._tree.pack(fill="both", expand=True)
        vsb.config(command=self._tree.yview)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._on_double)

        # right – editor
        right = ctk.CTkFrame(paned, fg_color=CLR_PANEL, corner_radius=10)
        paned.add(right, minsize=400)

        act = ctk.CTkFrame(right, fg_color="transparent")
        act.pack(fill="x", padx=10, pady=(10, 4))

        self._file_label = ctk.CTkLabel(act, text="", font=("Segoe UI", 14),
                                         text_color=CLR_SYSTEM, anchor="w")
        self._file_label.pack(side="left", fill="x", expand=True)

        btn_of = ctk.CTkButton(act, text="", width=110, height=36,
                                font=("Segoe UI", 13), fg_color="#313244",
                                hover_color="#45475a",
                                command=lambda: _open_explorer(self._folder_var.get()))
        btn_of.pack(side="right", padx=(6, 0))
        self._tr(btn_of, "open_folder")

        btn_sum = ctk.CTkButton(act, text="", width=90, height=36,
                                 font=("Segoe UI", 13), fg_color=CLR_PURPLE,
                                 hover_color="#9b59b6", command=self._summarize)
        btn_sum.pack(side="right", padx=(6, 0))
        self._tr(btn_sum, "btn_summarize")

        btn_sv = ctk.CTkButton(act, text="", width=70, height=36,
                                font=("Segoe UI", 13), fg_color=CLR_BLUE,
                                hover_color="#2575f5", command=self._save_file)
        btn_sv.pack(side="right", padx=(6, 0))
        self._tr(btn_sv, "btn_save")

        self._editor = ctk.CTkTextbox(right, font=("Consolas", 13), wrap="none",
                                       fg_color="#1e1e2e", text_color="#cdd6f4",
                                       corner_radius=8)
        self._editor.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._load_tree(str(Path.home()))
        return frame

    # ── settings view ─────────────────────────────────────────────────────────

    def _build_settings(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._main, corner_radius=0, fg_color=CLR_BG)

        lbl_title = ctk.CTkLabel(frame, text="", font=("Segoe UI", 18, "bold"),
                                  text_color="#cdd6f4")
        lbl_title.pack(anchor="w", padx=24, pady=(20, 8))
        self._tr(lbl_title, "settings_title")

        scroll = ctk.CTkScrollableFrame(frame, fg_color=CLR_PANEL, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        scroll.columnconfigure(1, weight=1)

        self._sv_model  = tk.StringVar(value=self.cfg.get("model", ""))
        self._sv_base   = tk.StringVar(value=self.cfg.get("api_base", ""))
        self._sv_ctx    = tk.StringVar(value=str(self.cfg.get("context_window", 8000)))
        self._sv_tokens = tk.StringVar(value=str(self.cfg.get("max_tokens", 2000)))
        # _sv_auto is shared — initialised in __init__ before build

        def field(lbl_key: str, var, r: int, hint_key: str = ""):
            lbl = ctk.CTkLabel(scroll, text="", font=("Segoe UI", 14),
                               text_color="#cdd6f4")
            lbl.grid(row=r, column=0, sticky="w", padx=(16, 8), pady=10)
            self._tr(lbl, lbl_key)
            ctk.CTkEntry(scroll, textvariable=var, font=("Segoe UI", 14),
                          height=40, corner_radius=10).grid(
                row=r, column=1, sticky="ew", padx=(0, 16), pady=10)
            if hint_key:
                hlbl = ctk.CTkLabel(scroll, text="", font=("Segoe UI", 11),
                                    text_color=CLR_SYSTEM)
                hlbl.grid(row=r, column=2, sticky="w", padx=(0, 16))
                self._tr(hlbl, hint_key)

        field("lbl_model",   self._sv_model,  0, "hint_model")
        field("lbl_apibase", self._sv_base,   1, "hint_apibase")
        field("lbl_ctx",     self._sv_ctx,    2, "hint_ctx")
        field("lbl_tokens",  self._sv_tokens, 3, "hint_tokens")

        lbl_ar = ctk.CTkLabel(scroll, text="", font=("Segoe UI", 14),
                               text_color="#cdd6f4")
        lbl_ar.grid(row=4, column=0, sticky="w", padx=(16, 8), pady=10)
        self._tr(lbl_ar, "lbl_autorun")
        ctk.CTkSwitch(scroll, variable=self._sv_auto, text="",
                       onvalue=True, offvalue=False).grid(
            row=4, column=1, sticky="w", padx=(0, 16), pady=10)

        lbl_inst = ctk.CTkLabel(scroll, text="", font=("Segoe UI", 14),
                                 text_color="#cdd6f4")
        lbl_inst.grid(row=5, column=0, sticky="nw", padx=(16, 8), pady=10)
        self._tr(lbl_inst, "lbl_instruct")

        self._inst_box = ctk.CTkTextbox(scroll, font=("Segoe UI", 14),
                                         height=130, corner_radius=10)
        self._inst_box.grid(row=5, column=1, columnspan=2, sticky="ew",
                             padx=(0, 16), pady=10)
        self._inst_box.insert("1.0", self.cfg.get("custom_instructions", ""))

        btn_sc = ctk.CTkButton(scroll, text="", height=48, font=("Segoe UI", 14),
                                fg_color=CLR_BLUE, command=self._save_settings)
        btn_sc.grid(row=6, column=0, columnspan=3, sticky="ew",
                     padx=16, pady=(10, 20))
        self._tr(btn_sc, "btn_save_cfg")

        return frame

    # ── agent init ────────────────────────────────────────────────────────────

    def _init_agent(self) -> None:
        def _run() -> None:
            ok, available = agent_core.check_ollama(self.cfg["api_base"], self.cfg["model"])
            if not ok:
                msg = self._s("sys_offline", model=self.cfg["model"],
                               available=", ".join(available) or "none")
                self._q.put(("system", msg))
                self.after(0, lambda: self._status.configure(
                    text="● offline", text_color=CLR_ERROR))
                return
            try:
                self.agent = agent_core.build_interpreter(self.cfg)
                self._q.put(("system", self._s("sys_ready", model=self.cfg["model"])))
                self.after(0, lambda: self._status.configure(
                    text=f"● {self.cfg['model']}", text_color=CLR_CODE))
            except Exception as exc:
                self._q.put(("error", self._s("sys_fail", err=exc)))

        threading.Thread(target=_run, daemon=True).start()

    # ── chat actions ──────────────────────────────────────────────────────────

    _ERROR_KEYWORDS = ("error", "traceback", "exception", "errno",
                       "failed", "ข้อผิดพลาด", "ล้มเหลว")
    _MAX_ERRORS   = 5      # consecutive error outputs before auto-stop
    _TIMEOUT_MIN  = 5      # minutes before auto-stop

    def _send_or_stop(self) -> None:
        """Send button doubles as Stop when the agent is busy."""
        if self._busy:
            self._do_stop()
        else:
            self._send()

    def _do_stop(self) -> None:
        self._stop_event.set()
        self._chat_append("System", self._s("sys_stopped"), "system")

    def _send(self) -> None:
        msg = self._chat_entry.get().strip()
        if not msg or self._busy:
            return
        if not self._focus_path:
            self._chat_append("System", self._s("sys_no_focus"), "error")
            self._flash_focus_bar()
            return
        self._hide_continue_bar()
        self._chat_entry.delete(0, "end")
        self._chat_append("You", msg, "user")
        self._log_msg("user", msg)
        self._dispatch(msg)

    def _flash_focus_bar(self, _count: int = 0) -> None:
        """Briefly flash the focus bar orange to draw attention to it."""
        colors = ["#5a3500", "#1e2a3a", "#5a3500", "#1e2a3a", "#5a3500", "#1e2a3a"]
        if _count < len(colors):
            self._focus_bar.configure(fg_color=colors[_count])
            self.after(160, lambda: self._flash_focus_bar(_count + 1))

    def _dispatch(self, msg: str) -> None:
        if not self.agent:
            self._chat_append("System", self._s("sys_not_ready"), "system")
            return
        self._busy = True
        self._agent_buf = ""
        self._stop_event.clear()

        # Switch Send → Stop
        self._send_btn.configure(fg_color="#8B0000", hover_color="#a00000",
                                  text=self._s("btn_stop"))

        # 5-minute timeout
        if self._timeout_id:
            self.after_cancel(self._timeout_id)
        self._timeout_id = self.after(
            self._TIMEOUT_MIN * 60 * 1000, self._on_timeout)

        if self._focus_path:
            fp = self._focus_path.replace("\\", "/")
            wd_header = (
                f"[WORKING DIRECTORY: {fp}]\n"
                f"IMPORTANT: Always start every code block with:\n"
                f"  import os; os.chdir(r'{self._focus_path}')\n"
                f"Never use any other directory unless the user explicitly asks.\n\n"
            )
            full_msg = wd_header + msg
        else:
            full_msg = msg

        def _run() -> None:
            tf = ThinkFilter()
            thinking_shown = False
            consecutive_errors = 0
            code_buf  = ""
            code_lang = "python"

            def _flush_code():
                nonlocal code_buf
                if code_buf:
                    self._q.put(("code", (code_buf, code_lang)))
                    code_buf = ""

            try:
                for chunk in self.agent.chat(full_msg, stream=True, display=False):
                    if self._stop_event.is_set():
                        break

                    ctype   = chunk.get("type", "")
                    content = chunk.get("content") or ""
                    if not content:
                        continue

                    if ctype == "message":
                        _flush_code()
                        if "<think>" in content and not thinking_shown:
                            self._q.put(("thinking_start", None))
                            thinking_shown = True
                        visible = tf.feed(content)
                        if visible:
                            if thinking_shown:
                                self._q.put(("thinking_end", None))
                                thinking_shown = False
                            self._q.put(("chunk", visible))

                    elif ctype == "code":
                        consecutive_errors = 0
                        lang = str(chunk.get("format", "python") or "python")
                        # flush if language switched mid-stream
                        if lang != code_lang and code_buf:
                            _flush_code()
                        code_lang = lang
                        code_buf += str(content)

                    elif ctype in ("console", "output"):
                        _flush_code()
                        content = str(content)
                        cl = content.lower()
                        is_err = any(kw in cl
                                     for kw in DesktopAgentApp._ERROR_KEYWORDS)
                        if is_err:
                            consecutive_errors += 1
                            if consecutive_errors >= self._MAX_ERRORS:
                                self._q.put(("auto_stopped",
                                             self._s("sys_max_errors",
                                                      n=self._MAX_ERRORS)))
                                self._stop_event.set()
                                break
                        else:
                            consecutive_errors = 0
                        self._q.put(("console", (content, is_err)))

                _flush_code()
                tail = tf.flush()
                if tail:
                    self._q.put(("chunk", tail))
            except Exception as exc:
                self._q.put(("error", str(exc)))
            finally:
                if thinking_shown:
                    self._q.put(("thinking_end", None))
                self._q.put(("done", None))

        threading.Thread(target=_run, daemon=True).start()

    def _on_timeout(self) -> None:
        if self._busy:
            self._stop_event.set()
            self._chat_append(
                "System",
                self._s("sys_timeout", m=self._TIMEOUT_MIN),
                "error")

    def _reset_send_btn(self) -> None:
        """Restore Send button to its normal Send state."""
        if self._timeout_id:
            self.after_cancel(self._timeout_id)
            self._timeout_id = None
        self._busy = False
        self._send_btn.configure(state="normal", fg_color=CLR_BLUE,
                                  hover_color="#2575f5",
                                  text=self._s("btn_send"))

    def _on_autorun_toggle(self) -> None:
        """Apply auto_run change to the live agent immediately (no reload needed)."""
        val = self._sv_auto.get()
        self.cfg["auto_run"] = val
        if self.agent:
            self.agent.auto_run = val

    def _show_continue_bar(self) -> None:
        self._continue_bar.pack(fill="x", padx=24, pady=(0, 6),
                                before=self._input_row)

    def _hide_continue_bar(self) -> None:
        self._continue_bar.pack_forget()

    def _do_continue(self) -> None:
        self._hide_continue_bar()
        nudge = self._s("continue_nudge")
        self._chat_entry.delete(0, "end")
        self._chat_entry.insert(0, nudge)
        self._send()

    def _poll(self) -> None:
        try:
            while True:
                tag, content = self._q.get_nowait()
                if tag == "chunk":
                    self._raw_append(content, "agent")
                    self._agent_buf += content
                elif tag == "code":
                    code_text, lang = content
                    self._append_code_block(code_text, lang)
                    self._agent_buf += code_text
                elif tag == "console":
                    con_text, is_err = content
                    self._append_console(con_text, is_err)
                elif tag == "thinking_start":
                    self._raw_append(self._s("sys_thinking") + "\n", "system")
                    self._send_btn.configure(text=self._s("sys_thinking"))
                elif tag == "thinking_end":
                    self._send_btn.configure(text=self._s("btn_stop"))
                elif tag == "auto_stopped":
                    self._chat_append("System", content, "error")
                    self._show_continue_bar()
                elif tag == "done":
                    self._raw_append("\n", "agent")
                    self._reset_send_btn()
                    if self._agent_buf.strip():
                        self._log_msg("agent", self._agent_buf.strip())
                        self._save_session()
                    self._detect_path(self._agent_buf)
                    self._agent_buf = ""
                elif tag == "system":
                    self._chat_append("System", content, "system")
                elif tag == "error":
                    self._chat_append("Error", content, "error")
                    self._reset_send_btn()
                    self._show_continue_bar()
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _chat_append(self, sender: str, text: str, tag: str) -> None:
        tb = self._chat_box._textbox
        self._chat_box.configure(state="normal")
        tb.insert("end", f"\n{sender}:\n", "label")
        tb.insert("end", f"{text}\n", tag)
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")

    def _raw_append(self, text: str, tag: str) -> None:
        tb = self._chat_box._textbox
        self._chat_box.configure(state="normal")
        tb.insert("end", text, tag)
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")

    def _append_code_block(self, code: str, lang: str) -> None:
        """Render a styled code block: green header bar + dark body + separator."""
        icon  = LANG_ICONS.get(lang.lower(), f"📝 {lang.capitalize() or 'Code'}")
        sep   = "─" * 52
        tb    = self._chat_box._textbox
        self._chat_box.configure(state="normal")
        tb.insert("end", "\n")
        tb.insert("end", f"  {icon}  \n", "code_header")
        tb.insert("end", code.rstrip("\n") + "\n", "code_body")
        tb.insert("end", f"  {sep}\n\n", "code_sep")
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")

    def _append_console(self, text: str, is_err: bool) -> None:
        """Render console output: green ✓ for success, red ✗ for errors."""
        text = text.strip()
        if not text:
            return
        tag    = "error_out" if is_err else "success"
        prefix = "✗ " if is_err else "✓ "
        self._raw_append(f"{prefix}{text}\n", tag)

    def _clear_chat(self) -> None:
        self._chat_box.configure(state="normal")
        self._chat_box.delete("1.0", "end")
        self._chat_box.configure(state="disabled")
        if self.agent:
            self.agent.messages = []
        self._new_session()

    # ── focus path ────────────────────────────────────────────────────────────

    def _pick_focus_path(self) -> None:
        folder = filedialog.askdirectory(title=self._s("fp_focus"))
        if folder:
            self._set_focus_path(folder)

    def _set_focus_path(self, path: str) -> None:
        self._focus_path = path
        self._focus_bar.configure(fg_color="#1e2a3a")
        self._focus_label.configure(text=Path(path).name or path,
                                     text_color="#89b4fa")
        self._folder_var.set(path)
        self._load_tree(path)
        self._chat_append("System", self._s("sys_focus_set", path=path), "system")

    def _clear_focus_path(self) -> None:
        self._focus_path = None
        self._focus_label.configure(text=self._s("focus_none"),
                                     text_color="#f38ba8")

    def _set_focus_from_files(self) -> None:
        folder = self._folder_var.get()
        if Path(folder).is_dir():
            self._set_focus_path(folder)
            self._switch("chat")

    # ── last-location bar ─────────────────────────────────────────────────────

    def _set_last_location(self, path: str) -> None:
        self._last_location = path
        p = Path(path)
        self._action_label.configure(text=f"📁  {p.name or path}  ({path})")
        self._action_bar.pack(fill="x", padx=24, pady=(0, 4),
                               before=self._chat_box)

    def _open_last_location(self) -> None:
        if self._last_location:
            _open_explorer(self._last_location)

    def _detect_path(self, text: str) -> None:
        for match in _WIN_PATH.finditer(text):
            candidate = match.group()
            p = Path(candidate)
            if p.exists():
                self._set_last_location(str(p.parent if p.is_file() else p))
                return

    # ── quick actions ─────────────────────────────────────────────────────────

    def _qa_organize_downloads(self) -> None:
        dl = str(Path.home() / "Downloads")
        self._set_focus_path(dl)
        self._chat_entry.delete(0, "end")
        self._chat_entry.insert(0, self._s("qa_dl_prompt", path=dl))
        self._send()

    def _qa_summarize_file(self) -> None:
        path = filedialog.askopenfilename(
            title=self._s("fp_summarize"),
            filetypes=[("Text files", "*.txt *.md *.pdf *.docx *.csv *.log"),
                       ("All files", "*.*")])
        if not path:
            return
        if not file_tools.is_text_file(path):
            messagebox.showinfo(self._s("d_not_text"), self._s("d_not_text_msg"))
            return
        content = file_tools.read_file(path, max_chars=20_000)
        self._switch("chat")
        fname = Path(path).name
        self._chat_append("System", self._s("sys_summarizing", name=fname), "system")
        self._log_msg("user", self._s("qa_summarize_tag", name=fname))
        self._dispatch(self._s("qa_summarize_prompt", content=content))

    def _qa_find_files(self) -> None:
        folder = filedialog.askdirectory(title=self._s("fp_find"))
        if not folder:
            return
        self._set_focus_path(folder)
        self._chat_entry.delete(0, "end")
        self._chat_entry.insert(0, self._s("qa_find_prompt"))
        self._send()

    def _qa_desktop_summary(self) -> None:
        desktop = str(Path.home() / "Desktop")
        self._set_focus_path(desktop)
        self._chat_entry.delete(0, "end")
        self._chat_entry.insert(0, self._s("qa_desktop_prompt", path=desktop))
        self._send()

    # ── font size ─────────────────────────────────────────────────────────────

    def _change_font(self, delta: int) -> None:
        self._font_size = max(10, min(26, self._font_size + delta))
        fs = self._font_size
        tb = self._chat_box._textbox
        self._chat_box.configure(font=("Segoe UI", fs))
        self._chat_entry.configure(font=("Segoe UI", fs))
        tb.tag_configure("code",        font=("Consolas", fs))
        tb.tag_configure("code_body",   font=("Consolas", fs))
        tb.tag_configure("code_header", font=("Segoe UI", fs - 1, "bold"))
        tb.tag_configure("success",     font=("Consolas", fs - 1))
        tb.tag_configure("error_out",   font=("Consolas", fs - 1))

    # ── history ───────────────────────────────────────────────────────────────

    def _new_session(self) -> None:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._session_file = HISTORY_DIR / f"{ts}.json"
        self._session_msgs = []

    def _new_chat(self) -> None:
        self._clear_chat()
        self._refresh_history_list()

    def _log_msg(self, role: str, text: str) -> None:
        self._session_msgs.append({
            "role": role,
            "text": text,
            "time": datetime.now().strftime("%H:%M:%S"),
        })

    def _save_session(self) -> None:
        if not self._session_msgs or not self._session_file:
            return
        try:
            data = {"timestamp": self._session_file.stem,
                    "messages":  self._session_msgs}
            self._session_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.after(0, self._refresh_history_list)
        except OSError:
            pass

    def _refresh_history_list(self) -> None:
        for w in self._history_frame.winfo_children():
            w.destroy()
        for sf in sorted(HISTORY_DIR.glob("*.json"), reverse=True)[:12]:
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                msgs = data.get("messages", [])
                preview = next(
                    (m["text"][:38] for m in msgs if m["role"] == "user"), sf.stem)
                date = sf.stem[:10]
                label = f"{date}  {preview}{'…' if len(preview)==38 else ''}"
            except Exception:
                label = sf.stem
            ctk.CTkButton(
                self._history_frame, text=label, height=32,
                font=("Segoe UI", 11), anchor="w", corner_radius=6,
                fg_color="#252535", hover_color="#35354a", text_color="#a6adc8",
                command=lambda p=sf: self._load_session(p),
            ).pack(fill="x", pady=2)

    def _load_session(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return
        tb = self._chat_box._textbox
        self._chat_box.configure(state="normal")
        self._chat_box.delete("1.0", "end")
        for m in data.get("messages", []):
            role, text, time = m.get("role",""), m.get("text",""), m.get("time","")
            if role == "user":
                tb.insert("end", f"\nYou  [{time}]:\n", "label")
                tb.insert("end", f"{text}\n", "user")
            else:
                tb.insert("end", f"\nAgent  [{time}]:\n", "label")
                tb.insert("end", f"{text}\n", "agent")
        self._chat_box.configure(state="disabled")
        self._chat_box.see("end")
        self._switch("chat")

    # ── file actions ──────────────────────────────────────────────────────────

    def _load_tree(self, folder: str) -> None:
        folder = folder.strip()
        if not Path(folder).is_dir():
            return
        self._folder_var.set(folder)
        self._tree.delete(*self._tree.get_children())
        try:
            entries = sorted(Path(folder).iterdir(),
                             key=lambda p: (p.is_file(), p.name.lower()))
            for e in entries:
                icon = "📁 " if e.is_dir() else "📄 "
                self._tree.insert("", "end", iid=str(e), text=icon + e.name)
        except PermissionError:
            pass

    def _browse(self) -> None:
        folder = filedialog.askdirectory(title=self._s("fp_files"))
        if folder:
            self._load_tree(folder)

    def _go_up(self) -> None:
        self._load_tree(str(Path(self._folder_var.get()).parent))

    def _on_select(self, _event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        path = sel[0]
        if not Path(path).is_file():
            return
        if file_tools.is_text_file(path):
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", file_tools.read_file(path))
            self._current_file = path
            self._file_label.configure(text=Path(path).name,
                                        text_color="#cdd6f4")
        else:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", f"[Binary file – cannot preview]\n{path}")
            self._current_file = None
            self._file_label.configure(text=Path(path).name + "  (binary)",
                                        text_color=CLR_SYSTEM)

    def _on_double(self, _event) -> None:
        sel = self._tree.selection()
        if not sel:
            return
        if Path(sel[0]).is_dir():
            self._load_tree(sel[0])

    def _save_file(self) -> None:
        if not self._current_file:
            messagebox.showwarning(self._s("d_no_file"), self._s("d_no_file_msg"))
            return
        content = self._editor.get("1.0", "end-1c")
        ok, err = file_tools.write_file(self._current_file, content)
        if ok:
            self._set_last_location(str(Path(self._current_file).parent))
            messagebox.showinfo(self._s("d_saved"),
                                self._s("d_saved_msg", name=Path(self._current_file).name))
        else:
            messagebox.showerror(self._s("d_error"), self._s("d_save_err", err=err))

    def _organize(self) -> None:
        folder = self._folder_var.get()
        if not Path(folder).is_dir():
            messagebox.showwarning(self._s("d_no_folder"), self._s("d_no_folder_msg"))
            return
        if not messagebox.askyesno(self._s("d_organize"),
                                    self._s("d_organize_msg", folder=folder)):
            return
        log = file_tools.organize_folder(folder)
        self._load_tree(folder)
        self._set_last_location(folder)
        summary = "\n".join(log) if log else "—"
        messagebox.showinfo(self._s("d_done"),
                            self._s("d_done_msg", n=len(log), summary=summary[:1200]))

    def _search(self) -> None:
        query = self._search_var.get().strip()
        if not query:
            return
        folder = self._folder_var.get()
        results = file_tools.search_files(folder, query)
        self._editor.delete("1.0", "end")
        if not results:
            self._editor.insert("1.0", f'No matches for "{query}" in\n{folder}')
        else:
            lines = [f'Found {len(results)} match(es) for "{query}":\n']
            for r in results:
                rel = os.path.relpath(r["path"], folder)
                lines.append(f"  {rel}:{r['line']}   {r['text']}")
            self._editor.insert("1.0", "\n".join(lines))
        self._file_label.configure(text=f'Search: "{query}"')
        self._current_file = None

    def _summarize(self) -> None:
        if not self._current_file:
            messagebox.showwarning(self._s("d_no_file"), self._s("d_no_file_msg"))
            return
        if not self.agent:
            messagebox.showwarning(self._s("d_not_ready"), self._s("d_not_ready_msg"))
            return
        if self._busy:
            messagebox.showinfo(self._s("d_busy"), self._s("d_busy_msg"))
            return
        content = self._editor.get("1.0", "end-1c")
        if len(content) > 20_000:
            content = content[:20_000] + "\n\n[…truncated…]"
        fname = Path(self._current_file).name
        self._switch("chat")
        self._chat_append("System", self._s("sys_summarizing", name=fname), "system")
        self._log_msg("user", self._s("qa_summarize_tag", name=fname))
        self._dispatch(self._s("qa_summarize_prompt", content=content))

    # ── settings ─────────────────────────────────────────────────────────────

    def _save_settings(self) -> None:
        self.cfg["model"]               = self._sv_model.get().strip()
        self.cfg["api_base"]            = self._sv_base.get().strip()
        self.cfg["auto_run"]            = self._sv_auto.get()
        self.cfg["custom_instructions"] = self._inst_box.get("1.0", "end-1c")
        try:
            self.cfg["context_window"] = int(self._sv_ctx.get())
        except ValueError:
            pass
        try:
            self.cfg["max_tokens"] = int(self._sv_tokens.get())
        except ValueError:
            pass
        agent_core.save_config(self.cfg)
        self.agent = None
        self._status.configure(text="● reconnecting…", text_color=CLR_SYSTEM)
        self._chat_append("System", self._s("sys_saved_reload"), "system")
        self._switch("chat")
        self._init_agent()


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = DesktopAgentApp()
    app.mainloop()

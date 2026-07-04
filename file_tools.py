"""
file_tools.py – file management utilities for Desktop Agent.
"""
import os
from pathlib import Path

FILE_CATEGORIES: dict[str, set[str]] = {
    "Images":       {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".heic"},
    "Documents":    {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".md", ".pages"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
    "Videos":       {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"},
    "Audio":        {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "Archives":     {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Code":         {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp",
                     ".h", ".go", ".rs", ".rb", ".php", ".sql", ".sh", ".ps1"},
    "Executables":  {".exe", ".msi", ".bat", ".cmd"},
}

TEXT_EXTENSIONS: set[str] = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json",
    ".yaml", ".yml", ".xml", ".csv", ".log", ".cfg", ".ini", ".toml",
    ".sh", ".bat", ".cmd", ".ps1", ".java", ".c", ".cpp", ".h",
    ".go", ".rs", ".rb", ".php", ".sql", ".r", ".tex", ".rst",
}


def is_text_file(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_EXTENSIONS


def organize_folder(folder_path: str) -> list[str]:
    """Move files into type-named subfolders. Returns a log of moves."""
    folder = Path(folder_path)
    log: list[str] = []
    for item in sorted(folder.iterdir()):
        if not item.is_file():
            continue
        category = "Other"
        ext = item.suffix.lower()
        for cat, exts in FILE_CATEGORIES.items():
            if ext in exts:
                category = cat
                break
        dest_dir = folder / category
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / item.name
        # Avoid overwriting if a same-named file already exists there
        if dest.exists():
            stem = item.stem
            suffix = item.suffix
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        item.rename(dest)
        log.append(f"Moved: {item.name}  →  {category}/")
    return log


def read_file(path: str, max_chars: int = 100_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception as e:
        return f"[Cannot read file: {e}]"


def write_file(path: str, content: str) -> tuple[bool, str]:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, ""
    except Exception as e:
        return False, str(e)


def search_files(
    folder: str,
    query: str,
    max_results: int = 100,
) -> list[dict]:
    """Search text files for query. Returns [{path, line, text}, ...]."""
    results: list[dict] = []
    q = query.lower()
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if not is_text_file(fname):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        if q in line.lower():
                            results.append({"path": fpath, "line": lineno, "text": line.rstrip()})
                            if len(results) >= max_results:
                                return results
            except OSError:
                pass
    return results

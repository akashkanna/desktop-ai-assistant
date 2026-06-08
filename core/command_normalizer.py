"""Normalize spoken/text commands before intent matching."""

import re

# Leading fillers stripped before parsing (order matters).
LEADING_FILLERS = [
    r"^(?:hey\s+)?(?:jarvis|assistant|computer)\s*,?\s*",
    r"^(?:ok\s+)?(?:jarvis|assistant)\s*,?\s*",
    r"^(?:please\s+|kindly\s+)",
    r"^(?:can you\s+|could you\s+|would you\s+|will you\s+)",
    r"^(?:i want to\s+|i need to\s+|i would like to\s+)",
]

# Common app name aliases → canonical launcher key
APP_ALIASES = {
    "google chrome": "chrome",
    "chrome browser": "chrome",
    "web browser": "chrome",
    "browser": "chrome",
    "mozilla firefox": "firefox",
    "firefox browser": "firefox",
    "microsoft edge": "edge",
    "edge browser": "edge",
    "visual studio code": "code",
    "vs code": "code",
    "vscode": "code",
    "file explorer": "explorer",
    "windows explorer": "explorer",
    "notepad plus plus": "notepad++",
    "command prompt": "cmd",
    "terminal": "cmd",
    "windows terminal": "wt",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings app": "settings",
    "windows settings": "settings",
    "spotify app": "spotify",
    "whatsapp": "whatsapp",
    "youtube app": "youtube",
}


def normalize_command_text(text: str) -> str:
    """Strip wake words, fillers, and collapse whitespace."""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\b(\w+)(?:\s+\1)+\b", r"\1", text)

    changed = True
    while changed:
        changed = False
        for pattern in LEADING_FILLERS:
            new_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            if new_text != text:
                text = new_text
                changed = True

    return text.strip()


def resolve_app_name(app_name: str) -> str:
    """Map natural phrases to a launcher-friendly application name."""
    if not app_name:
        return ""
    cleaned = app_name.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^(?:the|a|an|my)\s+", "", cleaned)
    cleaned = re.sub(r"\s+(?:app|application|program|software)$", "", cleaned)
    cleaned = cleaned.strip()

    if cleaned in APP_ALIASES:
        return APP_ALIASES[cleaned]

    for alias, canonical in sorted(APP_ALIASES.items(), key=lambda x: -len(x[0])):
        if cleaned == alias or cleaned.endswith(f" {alias}") or alias in cleaned:
            if alias in cleaned and len(cleaned) <= len(alias) + 5:
                return canonical

    return cleaned

"""Normalize spoken/text commands before intent matching.

Handles wake-word removal, filler stripping, synonym expansion,
and mid-sentence noise word removal so that natural variations
like "launch the Chrome browser" or "fire up Notepad" are correctly
reduced to their canonical form before regex matching.
"""

import re

# ── Leading fillers stripped before parsing (order matters) ──────────
LEADING_FILLERS = [
    r"^(?:hey\s+)?(?:jarvis|assistant|computer)\s*,?\s*",
    r"^(?:ok\s+)?(?:jarvis|assistant)\s*,?\s*",
    r"^(?:please\s+|kindly\s+)",
    r"^(?:can you\s+|could you\s+|would you\s+|will you\s+)",
    r"^(?:i want you to\s+|i need you to\s+|i would like you to\s+)",
    r"^(?:i want to\s+|i need to\s+|i would like to\s+)",
    r"^(?:go ahead and\s+)",
]

# ── Trailing fillers stripped after leading ones ────────────────────
TRAILING_FILLERS = [
    r"\s+(?:for me|for us|right now|now|quickly|immediately|please)\s*$",
    r"\s*[.!]+$",
]

# ── Verb/phrase synonyms → canonical form ───────────────────────────
# Checked in order; longer phrases first to avoid partial matches.
VERB_SYNONYMS = [
    # open / launch synonyms
    (r"\b(?:fire\s+up|boot\s+up|pull\s+up|bring\s+up|load\s+up)\b", "open"),
    (r"\b(?:load|access|enter|switch\s+to)\b", "open"),
    (r"\b(?:show\s+me)\b", "open"),
    # close synonyms
    (r"\b(?:shut\s+down|terminate|end|get\s+rid\s+of)\b", "close"),
    # search synonyms
    (r"\b(?:look\s+up|look\s+for|find\s+me|search\s+for)\b", "search for"),
    # type synonyms
    (r"\b(?:enter|input|write\s+down)\b", "type"),
]

# ── Mid-sentence noise words removed between verb and target ────────
# Only removed from specific positions, not blindly, to avoid
# breaking phrases like "go to the store" where "the" is significant.
MID_NOISE_WORDS = {
    "the", "a", "an", "my", "this", "that", "our", "your", "some",
    "up", "just", "also", "actually", "basically",
}

# ── Common app name aliases → canonical launcher key ────────────────
APP_ALIASES = {
    # Browsers
    "google chrome": "chrome",
    "chrome browser": "chrome",
    "web browser": "chrome",
    "browser": "chrome",
    "mozilla firefox": "firefox",
    "firefox browser": "firefox",
    "microsoft edge": "edge",
    "edge browser": "edge",

    # IDEs / Editors
    "visual studio code": "code",
    "vs code": "code",
    "vscode": "code",
    "visual studio": "devenv",
    "sublime text": "sublime_text",
    "sublime": "sublime_text",
    "atom editor": "atom",

    # System
    "file explorer": "explorer",
    "windows explorer": "explorer",
    "file manager": "explorer",
    "my computer": "explorer",
    "this pc": "explorer",
    "notepad plus plus": "notepad++",
    "command prompt": "cmd",
    "terminal": "cmd",
    "windows terminal": "wt",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings app": "settings",
    "windows settings": "settings",
    "system settings": "settings",
    "device manager": "devmgmt.msc",
    "registry editor": "regedit",
    "snipping tool": "snippingtool",

    # Media / Social
    "spotify app": "spotify",
    "spotify music": "spotify",
    "whatsapp": "whatsapp",
    "whatsapp web": "whatsapp",
    "youtube app": "youtube",
    "vlc media player": "vlc",
    "vlc player": "vlc",
    "vlc": "vlc",
    "media player": "wmplayer",
    "telegram app": "telegram",
    "telegram": "telegram",

    # Productivity
    "microsoft word": "winword",
    "ms word": "winword",
    "word": "winword",
    "microsoft excel": "excel",
    "ms excel": "excel",
    "microsoft powerpoint": "powerpnt",
    "ms powerpoint": "powerpnt",
    "ppt": "powerpnt",
    "microsoft outlook": "outlook",
    "ms outlook": "outlook",
    "microsoft teams": "teams",
    "ms teams": "teams",

    # Other
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "discord app": "discord",
    "discord": "discord",
    "slack app": "slack",
    "zoom app": "zoom",
    "zoom": "zoom",
    "obs studio": "obs64",
    "obs": "obs64",
    "steam": "steam",
    "epic games": "EpicGamesLauncher",
}


def normalize_command_text(text: str) -> str:
    """Strip wake words, fillers, expand synonyms, and collapse whitespace."""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    # De-duplicate repeated words (e.g. "open open Chrome")
    text = re.sub(r"\b(\w+)(?:\s+\1)+\b", r"\1", text)

    # 1. Strip leading fillers
    changed = True
    while changed:
        changed = False
        for pattern in LEADING_FILLERS:
            new_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            if new_text != text:
                text = new_text
                changed = True

    # 2. Strip trailing fillers
    for pattern in TRAILING_FILLERS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

    # 3. Expand verb synonyms ("fire up Chrome" → "open Chrome")
    for pattern, replacement in VERB_SYNONYMS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE).strip()

    # 4. Remove mid-sentence noise words between the first word (verb)
    #    and the rest, preserving the verb and the target.
    words = text.split()
    if len(words) > 2:
        verb = words[0]
        rest = [w for w in words[1:] if w not in MID_NOISE_WORDS]
        if rest:
            text = verb + " " + " ".join(rest)
        else:
            # All words after verb were noise — keep original
            text = " ".join(words)

    return text.strip()


def resolve_app_name(app_name: str) -> str:
    """Map natural phrases to a launcher-friendly application name."""
    if not app_name:
        return ""
    cleaned = app_name.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^(?:the|a|an|my)\s+", "", cleaned)
    cleaned = re.sub(r"\s+(?:app|application|program|software|browser)$", "", cleaned)
    cleaned = cleaned.strip()

    # Direct alias match
    if cleaned in APP_ALIASES:
        return APP_ALIASES[cleaned]

    # Fuzzy alias match — check if the cleaned name contains an alias
    for alias, canonical in sorted(APP_ALIASES.items(), key=lambda x: -len(x[0])):
        if cleaned == alias or cleaned.endswith(f" {alias}") or alias in cleaned:
            if alias in cleaned and len(cleaned) <= len(alias) + 5:
                return canonical

    return cleaned

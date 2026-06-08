import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core import task_router

cfg_dir = project_root / "config"
cfg_dir.mkdir(exist_ok=True)
out = cfg_dir / "shortcuts.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(task_router.SHORTCUTS, f, indent=2, ensure_ascii=False)
print(f"Exported {len(task_router.SHORTCUTS)} shortcuts to {out}")

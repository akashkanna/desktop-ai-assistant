import json
import sys
from pathlib import Path

# Ensure project root is on sys.path so local packages import correctly
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core import task_router

desired = [
'copy','paste','cut','clipboard_history','undo','redo','select_all','save','save_as','find','replace','print','new_file','open_file',
'new_tab','close_tab','reopen_tab','next_tab','previous_tab','refresh','hard_refresh','address_bar','downloads','history','bookmark_page','incognito',
'switch_window','previous_window','close_window','minimize_window','maximize_window',
'show_desktop','minimize_all','restore_windows','open_explorer','open_settings','lock_pc','run_dialog','search_windows','quick_link_menu','notification_center','widgets','game_bar','project_screen','emoji_panel','task_view','screenshot',
'snap_left','snap_right','snap_up','snap_down',
'scroll_top','scroll_bottom','page_up','page_down','home','end',
'new_desktop','next_desktop','previous_desktop','close_desktop',
'task_manager',
'play_pause','next_track','previous_track','stop_media',
'volume_up','volume_down','mute',
'f1','f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','fullscreen','f12'
]
for c in 'abcdefghijklmnopqrstuvwxyz':
    desired.append('win_'+c)

shortcuts = getattr(task_router, 'SHORTCUTS', {})
keys = set(shortcuts.keys())
missing = [k for k in desired if k not in keys]
extra = [k for k in keys if k not in desired]

allowed_simple = set(['ctrl','alt','shift','windows','win','f1','f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','f12','pageup','pagedown','home','end','tab','enter','esc','escape','up','down','left','right'])
unsupported = {}
for k in desired:
    if k in shortcuts:
        v = shortcuts[k]
        parts = [p.strip().lower() for p in v.replace('+',' + ').split() if p.strip()]
        tokens = [p for p in parts if p != '+']
        media_like = any(x in v.lower() for x in ['play','pause','next track','previous track','stop media','volume up','volume down','volume mute'])
        if media_like:
            unsupported[k] = v
        else:
            if any((t not in allowed_simple and not t.isalnum() and t not in ('+',)) for t in tokens):
                unsupported[k] = v

result = {
    'present_count': len(keys),
    'desired_count': len(desired),
    'missing': missing,
    'extra': extra,
    'unsupported': unsupported
}
print(json.dumps(result, indent=2))

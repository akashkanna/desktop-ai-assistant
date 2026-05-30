"""
Tests for automation helpers in app_launcher and system_controls.
"""

import json
import os
import sys
import tempfile
import types
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from automation.app_launcher import AppLauncher
import automation.system_controls as sysctrl


def test_open_application_url_opens_browser():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump({"applications": {"github": "https://github.com"}}, tmp)
        tmp_path = tmp.name

    try:
        launcher = AppLauncher(config_path=tmp_path)
        with patch("webbrowser.open") as mock_browser:
            result = launcher.open_application("GitHub")

        mock_browser.assert_called_once_with("https://github.com")
        assert result == "Opening GitHub."
    finally:
        os.remove(tmp_path)


def test_open_application_fallback_to_startfile():
    launcher = AppLauncher(config_path="nonexistent.json")

    with patch("automation.app_launcher.os.startfile") as mock_startfile:
        mock_startfile.return_value = None
        result = launcher.open_application("settings")

    assert result == "Opening settings."
    mock_startfile.assert_called_once()


def test_set_volume_falls_back_to_win32_with_valid_level():
    sysctrl._get_volume_interface = MagicMock(return_value=None)

    fake_win32api = types.SimpleNamespace(keybd_event=MagicMock())
    fake_win32con = types.SimpleNamespace(VK_VOLUME_DOWN=0xAE, VK_VOLUME_UP=0xAF, KEYEVENTF_KEYUP=0x0002)
    sys.modules["win32api"] = fake_win32api
    sys.modules["win32con"] = fake_win32con

    try:
        message = sysctrl.set_volume(30)
        assert message == "Volume set to 30 percent."
        assert fake_win32api.keybd_event.call_count > 0
    finally:
        sys.modules.pop("win32api", None)
        sys.modules.pop("win32con", None)


def test_mute_and_unmute_volume_with_interface():
    mock_volume = MagicMock()
    sysctrl._get_volume_interface = MagicMock(return_value=mock_volume)

    assert sysctrl.mute_volume() == "System volume muted."
    mock_volume.SetMute.assert_called_once_with(1, None)

    mock_volume.SetMute.reset_mock()
    assert sysctrl.unmute_volume() == "System volume unmuted."
    mock_volume.SetMute.assert_called_once_with(0, None)

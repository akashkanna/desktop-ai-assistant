# Jarvis AI — Desktop Voice Assistant OS

Jarvis is a premium, Windows-native AI desktop assistant built with **PySide6**. It combines voice control, gesture recognition, workflow automation, system monitoring, and desktop automation in a single **futuristic AI operating system dashboard** — inspired by Iron Man JARVIS.

The interface is a native Python desktop app (not a web app). Dark cyberpunk theme, glassmorphism panels, neon accents, animated avatar, and real-time system gauges.

---

## ✨ What's New — Jarvis AI OS Dashboard

The desktop UI has been redesigned into a modular, enterprise-grade command center:

| Area | Features |
|------|----------|
| **Left Sidebar** | Dashboard, Voice, Gesture, Workflow, Apps, System, Files, Screenshots, AI Memory, Logs, Settings, Help |
| **Top Header** | Branding, assistant status, user info, search, notifications, window controls |
| **Hero Panel** | Animated AI avatar, listening/thinking/speaking states, wake word, model info |
| **Features Grid** | Voice, Gesture, Windows, System, Screenshot, Memory, Workflow, App Launcher |
| **Workflow Manager** | Create, edit, run, delete workflows; voice wizard; tabs for All/Active/Favorites |
| **Quick Actions** | Open app, screenshot, lock, shutdown, restart, volume, browser |
| **Activity Log** | Real-time voice, gesture, system, workflow, and AI events |
| **System Monitor** | Live CPU, RAM, disk, network gauges + hardware specs |
| **Bottom Control Bar** | Mic button, waveform, chat input, gesture/voice toggles, emergency stop |

### Design System

- Background: `#050B1A`
- Neon Blue: `#00A3FF` · Purple: `#7B61FF`
- Glassmorphism cards, 15–18px rounded corners, hover glow effects
- `QPropertyAnimation` driven avatar pulse and waveform animations

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11**
- **Python 3.11+**
- Microphone (for voice commands)
- Internet connection (Google Speech Recognition for STT)

### Installation

```powershell
cd "D:\Personal Projects\Personal Ai\desktop_voice_assistant"

# Create and activate a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> The project now includes desktop keyboard shortcut automation for common clipboard commands like copy/paste/cut.

### Run the Application

```powershell
python main.py
```

The app launches in a **frameless 1440×900** window (configurable in `config/settings.json`). Voice listening starts automatically after the greeting.

### Optional: Gesture Control Dependencies

```powershell
pip install opencv-python mediapipe==0.10.35 pyautogui
```

Enable gesture mode from the **bottom control bar** or say *"start gesture control"*.

---

## 🏗 Project Architecture

```
desktop_voice_assistant/
├── main.py                     # Application entry point
├── config/settings.json        # Assistant, voice, UI, and safety settings
├── core/                       # Business logic (MVC controller layer)
│   ├── assistant_controller.py # Central orchestrator
│   ├── intent_parser.py        # Offline regex intent parsing
│   ├── task_router.py          # Routes intents to automation
│   ├── workflow_engine.py      # Multi-step automation
│   └── ...
├── ui/                         # PySide6 presentation layer
│   ├── main_window.py          # Main window shell
│   ├── avatar_widget.py        # Animated AI avatar
│   ├── theme/                  # Colors, QSS stylesheets
│   ├── animations/             # Glow, fade, pulse effects
│   ├── components/             # Sidebar, header, panels, bottom bar
│   └── pages/                  # Dashboard + secondary pages
├── services/                   # Background data services
│   ├── system_monitor_service.py
│   ├── activity_log_service.py
│   └── integration_hooks.py    # OpenAI, Gemini, Ollama placeholders
├── voice/                      # Speech-to-text & text-to-speech
├── automation/                 # Windows desktop automation
├── gesture/                    # MediaPipe hand tracking
├── memory/                     # Short & long-term JSON memory
└── tests/                      # Unit tests (pytest)
```

### UI ↔ Backend Flow

```
MainWindow → AssistantController → IntentParser → TaskRouter → Automation
                ↓                        ↓
         ActivityLogService      WorkflowEngine
         SystemMonitorService     GestureController
```

Thread-safe UI updates use Qt signals from background voice and system threads.

---

## 🎛 Using the Dashboard

### Voice Control

- Click the **microphone button** in the bottom bar, or wait for auto-start listening
- Type commands in the **chat input** and press Enter or ➤
- Use the header **search bar** for quick command lookup

### Quick Actions (Dashboard)

| Button | Action |
|--------|--------|
| Open App | Prompts voice/text app launch |
| Screenshot | Captures desktop instantly |
| Lock System | Locks Windows |
| Shutdown / Restart | Power controls |
| Volume Up / Down | Adjusts system volume |
| Open Browser | Opens default browser |

### Workflows

1. Open the **Workflow Management** panel on the Dashboard
2. Enter name, trigger phrase, and steps (one action per line)
3. Click **Save**, then **Run** — or use **Voice Wizard** to speak a workflow phrase
4. Voice trigger example: *"Run Morning Routine"*

### Emergency Stop

The red **STOP** button in the bottom bar immediately halts voice listening and gesture control.

### Settings Page

View integration status for:

- OpenAI API · Gemini API · Ollama
- Whisper / Google STT · MediaPipe · MongoDB Memory
- pyttsx3 TTS · Workflow Engine

These are UI hooks ready for API key configuration.

---

## 🚀 Capabilities & Command Reference

Jarvis supports a wide range of commands through natural language.

### 1. Clipboard & Shortcut Commands

* **COPY:** "copy", "copy this", "copy selected text", "duplicate selection" → `Ctrl+C`
* **PASTE:** "paste", "paste here", "insert clipboard", "paste copied text" → `Ctrl+V`
* **CUT:** "cut", "cut this", "cut selection", "move this text" → `Ctrl+X`

You can customize and extend all keyboard shortcuts by editing `config/shortcuts.json`.
Run `scripts/export_shortcuts.py` to generate the file with current defaults, then modify mappings as needed.

### 2. System & Power Controls

* **Sleep Mode:** "Put my PC to sleep", "Sleep mode", "Standby"
* **Lock Screen:** "Lock the screen", "Lock my PC"
* **Shutdown:** "Shut down the computer", "Power off my system"
* **Restart:** "Restart my PC", "Reboot the system"
* **Cancel Actions:** "Cancel shutdown", "Abort shutdown"

### 3. Window & Application Management

* **Open Applications:** `"Open Chrome"`, `"Launch Settings"`, `"Open Notepad"`
* **Close Applications:** `"Close Chrome"`, `"Quit Spotify"`
* **Window Sizing:** `"Minimize the window"`, `"Maximize this tab"`
* **Minimize All:** `"Minimize all windows"`, `"Minimize everything"`

### 3. Media & Volume Control

* **Set Volume:** `"Set volume to 50%"`
* **Adjust Volume:** `"Increase the volume"`, `"Turn the volume down by 20"`
* **Mute/Unmute:** `"Mute the system"`, `"Unmute my microphone"`

### 4. Web Browsing & Search

* **Search Web:** `"Search Google for python tutorials"`
* **Search YouTube:** `"Play Taylor Swift on YouTube"`
* **Open Websites:** `"Open github.com"`, `"Go to wikipedia.org"`

### 5. Utilities & Communication

* **Screenshots:** `"Take a screenshot"`
* **WhatsApp Messaging:** `"Send a WhatsApp message to John saying I'll be late"`
* **Time & Date:** `"What time is it?"`, `"What's today's date?"`

---

## 🤖 Advanced Features

### Predictive Assistance

Jarvis learns from habits and suggests actions after greetings (frequent apps, volume, workflows).

### Automation Workflows

Create custom routines with voice triggers:

* `"When I say Start Work: open VS Code, open Chrome, set volume to 30%"`
* `"Run Start Work"`

Use the **Workflow Management** panel or **Voice Wizard** in the dashboard.

### Memory & Context

Stores preferences, favorite apps, workflows, and notifications across sessions.

* `"Remember that I prefer dark mode."`
* `"Remember that VS Code is my default code editor."`

### Gesture & Multi-Monitor Control

Hand tracking via MediaPipe + OpenCV:

* One finger → move cursor
* Thumb + index pinch → left click
* Index + middle pinch → right click
* Open palm → pause detection
* Swipe left/right → browser back/forward

**Enable from UI:** Bottom bar → **Gesture: Off/On**  
**Voice:** `"start gesture control"` / `"stop gesture control"`

#### Gesture Setup & Troubleshooting

```powershell
pip install opencv-python mediapipe==0.10.35 pyautogui
```

MediaPipe 0.10+ requires `hand_landmarker.task` in the `gesture/` folder (auto-downloaded when possible).

**Camera test:**

```python
import cv2
cap = cv2.VideoCapture(0)
print('Camera opened:', cap.isOpened())
if cap.isOpened():
    ret, frame = cap.read()
    print('Frame captured:', ret)
    cap.release()
```

**Common fixes:**

- Close apps using the camera (Teams, Zoom)
- Windows Settings → Privacy → Camera → Allow access
- Try different `camera_index` in `GestureController(camera_index=0)`

---

## 🧪 Testing

```powershell
pytest -q
```

CI runs on Windows with Python 3.11 (see `.github/workflows/python.yml`).

---

## 🛑 Limitations

1. **No unstructured GUI navigation** — relies on system hooks and predefined automation
2. **STT requires internet** — Google Speech Recognition for accuracy
3. **Confirmation for destructive actions** — shutdown, messaging, etc.
4. **Windows only** — uses `win32gui`, `win32api`, `ctypes.windll`, pycaw

---

## 🛠 Help & Configuration

Ask Jarvis:

* `"Help me"`
* `"What are your capabilities?"`
* `"List commands"`

Edit `config/settings.json` for wake words, window size, TTS rate, and safety rules.  
Copy `.env.example` to `.env` for future API keys (Anthropic, OpenAI, etc.).

---

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| UI | PySide6 ≥ 6.5.0 |
| Speech | SpeechRecognition, pyttsx3, pyaudio |
| Automation | pyautogui, pygetwindow, pycaw |
| Gestures | OpenCV, MediaPipe |
| System Info | psutil |
| Memory | JSON (local) |

---

*Jarvis AI OS — seamless productivity, maximum efficiency, hands-free control.*

# Jarvis — AI Desktop Voice Assistant

Jarvis is a premium, offline-first voice assistant designed specifically for Windows. It provides a sleek, glassmorphic overlay to handle your daily desktop operations entirely through voice commands. Built with PySide6, Python, and native Windows automation libraries, Jarvis integrates deeply with your operating system to make tasks completely hands-free.

---

## 🚀 Capabilities & Command Reference

Jarvis supports a wide range of commands through natural language. Below is a comprehensive list of what Jarvis can do, alongside example phrases.

### 1. System & Power Controls
Take control of your computer's power state without touching the keyboard.
* **Sleep Mode:** `"Put my PC to sleep"`, `"Sleep mode"`, `"Standby"`
* **Lock Screen:** `"Lock the screen"`, `"Lock my PC"`
* **Shutdown:** `"Shut down the computer"`, `"Power off my system"`
* **Restart:** `"Restart my PC"`, `"Reboot the system"`
* **Cancel Actions:** `"Cancel shutdown"`, `"Abort shutdown"`

### 2. Window & Application Management
Manage your digital workspace rapidly.
* **Open Applications:** `"Open Chrome"`, `"Launch Settings"`, `"Open Camera"`, `"Start Notepad"`
* **Close Applications:** `"Close Chrome"`, `"Quit Spotify"`
* **Window Sizing:** `"Minimize the window"`, `"Maximize this tab"`
* **Minimize All:** `"Minimize all windows"`, `"Minimize everything"`

### 3. Media & Volume Control
Adjust your audio instantly. Jarvis integrates directly with Windows audio endpoints.
* **Set Volume:** `"Set volume to 50%"`, `"Control my volume to 30"`
* **Adjust Volume:** `"Increase the volume"`, `"Turn the volume down by 20"`
* **Mute/Unmute:** `"Mute the system"`, `"Unmute my microphone"`

### 4. Web Browsing & Search
Ask Jarvis to find information or launch websites for you.
* **Search Web:** `"Search Google for python tutorials"`, `"Look up the weather on Bing"`
* **Search YouTube:** `"Play Taylor Swift on YouTube"`, `"Search YouTube for tech news"`
* **Open Websites:** `"Open github.com"`, `"Go to wikipedia.org"`
* **Smart Fallback:** If you ask a general question (e.g., *"Who is the CEO of Microsoft?"*), Jarvis will automatically search the web for the answer.

### 5. Utilities & Communication
* **Screenshots:** `"Take a screenshot"` *(Saves instantly to your Desktop)*
* **WhatsApp Messaging:** `"Send a WhatsApp message to John saying I'll be late"`
* **Time & Date:** `"What time is it?"`, `"What's today's date?"`

---

## 🛑 Limitations (What Jarvis Cannot Do)

While Jarvis is powerful, there are specific boundaries to its capabilities to ensure security and stability:
1. **No Unstructured GUI Navigation:** Jarvis cannot visually "see" your screen to click arbitrary, unnamed buttons inside random applications. It relies on system-level hooks and predefined automation scripts.
2. **Offline Speech Recognition Limits:** For maximum accuracy, the primary speech engine currently relies on an internet connection (Google Speech Recognition API). 
3. **No Destructive Actions Without Confirmation:** Jarvis is designed to ask for confirmation before executing potentially destructive commands (e.g., shutting down the PC or sending messages).
4. **Mac/Linux Incompatibility:** Jarvis is built heavily upon native Windows APIs (`win32gui`, `win32api`, `ctypes.windll`) and is exclusively tailored for Windows 10/11.

---

## 🛠 Help & Rules

If you are ever unsure of what Jarvis can do, simply ask:
* `"Help me"`
* `"What are your capabilities?"`
* `"List commands"`

Jarvis will automatically open this document to provide you with the exact rules and regulations of its command structure.

---

*Designed for seamless productivity and maximum efficiency.*

# 🤖 Jarvis AI Assistant

A CPU-efficient AI voice assistant built using Python that supports wake-word activation, local LLM responses, and system control commands.

---

## 🚀 Features

* 🎤 Speech-to-Text input (voice commands)
* 🧠 AI responses using local LLM (TinyLlama via Ollama)
* 🔊 Text-to-Speech output
* 🟡 Wake word activation ("Jarvis")
* ⚡ Fast command execution (open apps, browser, etc.)
* 💻 System control (shutdown, restart, time, apps)
* 🔁 Event-driven architecture (Idle → Active → Sleep)
* 🖥️ Runs on CPU (no GPU required)

---

## 🧠 How It Works

1. Assistant stays in **Idle mode**
2. Listens for wake word: **"Jarvis"**
3. Activates and listens to user input
4. Processes command:

   * ⚡ Direct command → executes instantly
   * 🧠 Otherwise → sends to LLM
5. Responds using voice output
6. Returns to idle on "sleep"

---

## 🏗️ Project Structure

```
ai-voice-assistant/
│
├── main.py          # Main controller (state management)
├── stt.py           # Speech-to-text
├── tts.py           # Text-to-speech
├── llm.py           # LLM interaction (Ollama)
├── utils.py         # Command handling
├── wake_word.py     # Wake word detection
```

---

## ⚙️ Tech Stack

* Python
* SpeechRecognition
* pyttsx3
* Ollama (TinyLlama)
* subprocess
* webbrowser / os

---

## ▶️ How to Run

```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate

# Install dependencies
pip install speechrecognition pyttsx3 pyaudio

# Run assistant
python main.py
```

---

## 🔥 Example Commands

* "Jarvis" → activates assistant
* "Open YouTube"
* "Open Google"
* "What time is it?"
* "Shutdown PC"
* "Sleep" → return to idle

---

## ⚠️ Notes

* Uses microphone input — ensure permissions are enabled
* Some commands (shutdown/restart) affect your system — use carefully
* Ollama must be running locally

---

## 🚀 Future Improvements

* 🧠 Memory (context awareness)
* ⚡ Faster wake word detection (Porcupine)
* 🖥️ GUI interface (Streamlit / React)
* 🔌 STM32 hardware integration
* 🎯 Fully background system (tray app)

---

## 📌 Author

**Pranav Karande**

---

## ⭐ If you like this project

Give it a star ⭐ and feel free to contribute!

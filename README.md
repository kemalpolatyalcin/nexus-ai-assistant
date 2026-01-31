# 🎙️ NEXUS AI - Intelligent Voice Automation System

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI](https://img.shields.io/badge/Model-Gemini%201.5%20Flash-orange)

## 📖 Overview
**NEXUS** is a modular, voice-activated automation assistant designed to bridge the gap between natural language processing (NLP) and system-level control. Built with **Python** and powered by **Google's Gemini LLM**, it functions as a "hands-free" interface for complex workflows.

Unlike standard voice assistants, NEXUS features a **transparent, sci-fi inspired HUD** (Heads-Up Display) and is engineered for **low-latency execution** of system commands, clipboard analysis, and real-time information retrieval.

## ✨ Core Architecture

### 🧠 Cognitive Engine (The Brain)
- **LLM Integration:** Utilizes `google.generativeai` (Gemini 1.5) for context-aware reasoning.
- **Context Handling:** Maintains short-term memory of the conversation for fluid interactions.
- **Clipboard Analysis:** Can read, analyze, and summarize clipboard content instantly upon command.

### 🗣️ Voice I/O (The Interface)
- **Neural TTS:** Implements `edge-tts` for natural, human-like speech synthesis.
- **Adaptive Listening:** Uses `SpeechRecognition` with dynamic noise threshold adjustment for varied environments.
- **Asynchronous Processing:** Non-blocking audio feedback loop using `asyncio` and `threading`.

### 💻 System Control (The Hands)
- **Automation:** Executes shell commands, launches applications (VS Code, Terminal), and manages system states.
- **Cross-Platform:** Designed with compatibility for Windows and macOS environments.

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Core Logic** | Python 3.10+ |
| **AI Model** | Google Gemini 1.5 Flash |
| **GUI Framework** | CustomTkinter (Modern UI) |
| **Speech-to-Text** | Google Speech Recognition |
| **Text-to-Speech** | Edge-TTS (Neural) |
| **Audio Engine** | Pygame Mixer |

## 🚀 Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/kemalpolatyalcin/nexus-ai-assistant.git](https://github.com/kemalpolatyalcin/nexus-ai-assistant.git)
    cd nexus-ai-assistant
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration:**
    Create a `.env` file in the root directory and add your API key:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```

4.  **Run the System:**
    ```bash
    python main.py
    ```

## 🖥️ Usage Examples
- *"Nexus, open VS Code and start a new project."*
- *"Analyze the text in my clipboard."*
- *"System status report."*

## 👨‍💻 Author
**Kemal Polat Yalcin**
- *IT Student @ EMU*
- *Focus: AI Automation & Human-Computer Interaction*

---
*Disclaimer: This project is an open-source prototype demonstrating LLM integration in desktop automation.*

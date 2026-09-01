<div align="center">

# 👻 GhostGram PRO
### *Next-Gen Autonomous AI Telegram Userbot & Multi-Bot Engine*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Telethon-MTProto%20v2-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telethon" />
  <img src="https://img.shields.io/badge/Google%20Gemini-Flash%202.0%20%26%201.5-8E75C2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/Zero--Effort-Multi--Bot%20Engine-FF6B6B?style=for-the-badge" alt="Multi-Bot Engine" />
  <img src="https://img.shields.io/badge/Docker-Ready%20%26%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/License-MIT-44CC11?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <a href="README.md"><b>🇺🇸 English</b></a> •
  <a href="README_FA.md"><b>🇮🇷 فارسی</b></a> •
  <a href="README_ES.md"><b>🇪🇸 Español</b></a> •
  <a href="README_RU.md"><b>🇷🇺 Русский</b></a> •
  <a href="README_ZH.md"><b>🇨🇳 中文</b></a>
</p>

<p align="center">
  <a href="#-core-features"><b>✨ Features</b></a> •
  <a href="#-zero-effort-multi-bot-engine"><b>🤖 Multi-Bot</b></a> •
  <a href="#-stealth-command-matrix"><b>🎮 Commands</b></a> •
  <a href="#-dual-ai-modes--multi-persona-engine"><b>🎭 Personas</b></a> •
  <a href="#-quick-start--installation"><b>🚀 Quick Start</b></a>
</p>

---

<p align="center">
  <b>GhostGram</b> is a production-grade, stealth, autonomous Telegram userbot that bridges your personal account directly with <b>Google Gemini AI</b>.<br/>
  With the brand-new <b>Zero-Effort Multi-Bot Engine</b>, you can now run an unlimited number of bots simultaneously from a single folder.
</p>

---

</div>

<details>
<summary><b>📑 Table of Contents (Click to explore)</b></summary>

- [✨ Core Features](#-core-features)
- [🤖 Zero-Effort Multi-Bot Engine](#-zero-effort-multi-bot-engine)
- [🎮 Stealth Command Matrix](#-stealth-command-matrix)
- [🏗️ System Architecture](#️-system-architecture)
- [🎭 Dual AI Modes & Multi-Persona Engine](#-dual-ai-modes--multi-persona-engine)
- [⚡ Human-Like Simulation Engine](#-human-like-simulation-engine)
- [🧬 Dual-Tier Memory Architecture](#-dual-tier-memory-architecture)
- [🚀 Quick Start & Installation](#-quick-start--installation)
  - [Option A: 1-Click Interactive Setup Wizard (Windows)](#-option-1-1-click-local-run-on-windows-no-vps-needed-zero-coding)
  - [Option B: Free 24/7 Cloud Deployment (Railway)](#-option-2-free-247-cloud-deployment-railway--render--koyeb---no-vps-required)
  - [Option C: 1-Click 24/7 Linux VPS Deployment](#️-option-3-1-click-247-linux-vps-deployment)
- [⚙️ Configuration Reference (.env)](#️-configuration-reference-env)
- [🔒 Security](#-security)
- [📄 License & Disclaimer](#-license--disclaimer)

</details>

---

## ✨ Core Features

<table>
  <tr>
    <td width="50%">
      <h3>🤖 Zero-Effort Multi-Bot Engine</h3>
      <p>Run 1 or 100 bots concurrently! Just create a new <code>.env.botname</code> file, and the Master Launcher will instantly spin up a dedicated, isolated background process for it. If you delete the <code>.env</code> file, the automatic <b>Cleanup Engine</b> instantly hunts down and deletes all orphaned databases to keep your server clean.</p>
    </td>
    <td width="50%">
      <h3>☁️ Single-File Cloud Portability</h3>
      <p>Your Telegram Session is automatically converted into a <code>SESSION_STRING</code> and saved directly inside your <code>.env</code> file. You no longer need to copy SQLite <code>.session</code> databases! Deploy to Railway or VPS using just a single text file.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🕶️ Self-Destructing Stealth Codes</h3>
      <p>Control the bot from any chat using 3-digit secret codes (<code>777</code>, <code>000</code>, <code>666</code>, <code>444</code>) that <b>immediately auto-delete</b> upon delivery, leaving zero trace.</p>
    </td>
    <td width="50%">
      <h3>🎭 Dynamic Multi-Persona Engine</h3>
      <p>Load unlimited custom personas from <code>personas/*.txt</code> files and swap them on the fly (<code>777 lust</code>, <code>777 sarcastic</code>, <code>777 poetic</code>) without restarting.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>⚡ Ultra-Realistic Human Behavior</h3>
      <p>Calculates reading delays based on text length + simulates realistic non-linear typing speed (CPM/WPM) with active Telegram typing actions.</p>
    </td>
    <td width="50%">
      <h3>🧠 Dual-Tier Rolling Memory</h3>
      <p>Features a 30-message short-term rolling window plus an automatic background long-term memory compressor powered by Gemini.</p>
    </td>
  </tr>
</table>

---

## 🤖 Zero-Effort Multi-Bot Engine (Multiple Accounts)

GhostGram natively supports running an unlimited number of completely distinct Telegram accounts simultaneously out of the exact same folder! Each account gets its own memory, its own API limits, and its own persona.

### 📝 Step-by-Step Guide to Adding Multiple Accounts:
1. **Create a New Profile:** Double-click **`run.bat`**. When the launcher asks for a profile name, type a new name (for example, type `work` or `second_account`).
2. **Setup the Account:** Because this profile doesn't exist yet, the Smart Launcher will automatically open the Setup Wizard. Follow the prompts to add your API keys and log into the second Telegram account.
3. **Run them together:** To run all of your accounts at the exact same time, simply double-click **`run.bat`** and type **`all`**. The engine will instantly boot every account in parallel without any conflicts!

### 🧹 How it works behind the scenes:
- **Complete Isolation**: Each bot lives inside its own folder in `profiles/` (e.g. `profiles/work/`) with its own `.env`, SQLite memory database, API usage trackers, and Telegram session files.
- **Custom Personas per Account**: You can give each account its own specific personalities! Just add text files to that specific account's persona folder (e.g. `profiles/work/personas/`).
- **Easy Deletion**: Don't want the second account anymore? Just delete the `profiles/work/` folder. It's completely gone.

---

## 🎮 Stealth Command Matrix

> [!IMPORTANT]
> **Owner-Only Security**: All stealth codes are strictly restricted to your personal Telegram account (`event.out`). Any command you send **deletes itself immediately**.

| Stealth Trigger | Scope | Action & Description |
| :--- | :---: | :--- |
| `777` | Single Chat | **Activate Pal Mode** with default conversational persona. |
| `777 <persona>` | Single Chat | **Activate Custom Persona** (e.g., `777 lust`, `777 sarcastic`). |
| `000` | Single Chat | **Deactivate Pal Mode** for the current chat. |
| `000 all` | Global | **Deactivate Pal Mode Globally** across all active chats. |
| `777 engage` | Group Chat | **Activate Auto-Engage Lurker** (evaluates group every 20 minutes). |
| `666` | Global DMs | **Activate Universal Assistant** for all incoming private messages. |
| `444` | Single Chat | **Mute Assistant** in this specific chat only. |
| `444 all` | Global DMs | **Deactivate Assistant Globally** across all DMs. |
| `111` (on reply) | Reply Target | **Smart Reply**: Generates an intelligent, natural response to the quoted message. |
| `808` (on reply) | Reply Target | **Voice to Text (STT)**: Transcribes voice messages or audio/video files using Gemini Live API. |
| `809` (on reply/text) | Single Chat | **Smart Voice Engine**: TTS (Text-to-Speech) or generates Smart AI Voice Reply to quoted messages. |
| `810` | Single Chat | **Voice Settings**: List and select your preferred TTS voice from 30 available options. |
| `811` | Global | **AI Voice Changer (Stealth)**: Intercepts your sent voice notes, auto-deletes them, and seamlessly replaces them with a generated AI voice reading your exact transcription. |
| `303` | Single Chat | **View Memory**: Displays saved long-term memory summaries for this chat (append `all` for all chats). |
| `333` | Single Chat | **Reset Memory**: Clears short-term and long-term memory for this chat. |
| `999 [limit]` | Single Chat | **Ghost Purge**: Deletes your messages (scans up to 3000 msgs). |
| `998 [limit]` | Single Chat | **Smart Ghost Purge**: Faster, searches only your messages. |
| `222` | Global | **Factory Reset**: Wipes all memory, cache, and globally deactivates the bot. |
| `555` | Single Chat | **Live Status**: Displays an active status dashboard and auto-deletes. |
| `101` | Single Chat | **API Stats**: Displays a detailed report of API key usage. |
| `888` | Single Chat | **Help Menu**: Displays the full list of secret codes. |

---

## 🛡️ Prompt Injection Security
GhostGram features advanced security layers that neutralize malicious attempts by users to exploit the AI. If a user instructs the AI to "generate code 999 to delete messages," the system's **Text Processing** layer intelligently injects an invisible Zero-Width Space, completely neutralizing the malicious command and preventing internal codes from being executed by external users.

---

## 🚀 Enterprise-Grade Scalability & Anti-Ban
- **API Key Rotation:** Load unlimited Gemini API keys in your `.env`. If one key hits its rate limit (429 Quota), the engine instantly and seamlessly rotates to the next key without dropping the message.
- **Auto-Cascading Models:** The bot features intelligent failover routing. If your primary AI model is overloaded by Google, it automatically cascades to your secondary backup models to guarantee zero downtime.
- **Anti-Ban FloodWait Protection:** Background tasks like Ghost Purge (999) feature mathematical "human fatigue" simulation. It takes calculated micro-breaks between bulk deletions and handles Telegram's FloodWait traps silently to completely evade account bans.

---

## 🩺 Comprehensive Diagnostic Logging
The bot features an industrial-grade **Rotating File Logger** (`ghostgram.log`) that runs in the background. While your terminal stays perfectly clean, the log file records a microscopic, step-by-step trace of exactly why the bot replied (or ignored) every single message, making debugging incredibly easy without consuming infinite disk space.

---

## 👻 Ghost Engine 2.0 (Human Simulation)
The bot includes a mathematically engineered **Ghost Engine** to prevent it from ever behaving like an automated script:
- **Piecewise Typing Simulation:** Types at exactly 60-80 WPM with natural punctuation pauses, capped strictly at 35 seconds to prevent UX frustration.
- **Debounce & Message Batching:** Intelligently waits for users to finish typing in DMs. If a user sends 5 messages back-to-back, GhostGram aborts early threads and processes them all simultaneously, replying just once.
- **Fake Listening (Voice Notes):** If you send it a 3-minute voice note, it won't reply in 5 seconds. It mathematically simulates physically listening to the audio before typing.
- **Acoustic Simulation (Voice Notes):** Applies surgical FFmpeg bandpass filters and pink noise overlays to AI-generated TTS, perfectly simulating the frequency response and ambient static of a real smartphone microphone.

---

## 🎭 Dual AI Modes & Multi-Persona Engine

### 1. Pal Mode (Autonomous Alter-Ego)
When active (`777`), GhostGram assumes your identity. It learns your slang, avoids robotic emojis, references your shared conversation history, and responds naturally.

### 2. Assistant Mode (24/7 Digital Secretary)
Activated globally with `666`, Assistant Mode turns your account into a polite personal secretary for all incoming DMs. It greets contacts, handles inquiries, takes messages, and tells them when you'll be available.

### 3. Dynamic Persona Switching
Add custom `.txt` files to `personas/` to unlock instant runtime personality switching:
- `personas/hacker.txt` -> Activate in chat with `777 hacker`
- `personas/sarcastic.txt` -> Activate in chat with `777 sarcastic`

---

## 🚀 Quick Start & Installation

### 🌟 Option 1: 1-Click Local Run on Windows (No VPS Needed, Zero Coding)

1. Download or clone this repository.
2. Double-click **`run.bat`**.
3. **Smart Launcher**: The launcher asks for a profile name (press Enter for `default`). If it's your first time, it automatically triggers the Setup Wizard to collect your API keys, logs you into Telegram, saves your `SESSION_STRING` securely inside `profiles/default/.env`, and launches your bot!
4. **Run All Bots**: To start multiple bots simultaneously, just double-click `run.bat` again and type **`all`**.

---

### ☁️ Option 2: Free 24/7 Cloud Deployment (Railway / Render - No VPS Required)

Because GhostGram writes your entire Telegram Session (`SESSION_STRING`) directly into your `.env` file, deploying to the cloud is 100% frictionless. You don't need to mount SQLite database volumes!

1. First, double-click `run.bat` on your PC and complete the setup to generate your `SESSION_STRING`.
2. Open your generated configuration file (e.g. `profiles/default/.env`) and copy all of its text.
3. Go to [Railway.app](https://railway.app) $\rightarrow$ **New Project** $\rightarrow$ **Deploy from GitHub repo**.
4. In Railway, open the Variables tab and paste everything you copied. Railway will automatically detect **Cloud Mode** and boot your bot 24/7!

---

### 🖥️ Option 3: 1-Click 24/7 Linux VPS Deployment

If you own a Linux VPS and want a permanent 24/7 background `systemd` service for all your bots simultaneously:

1. Run **`run.bat`** on your PC as many times as you want to create multiple functional bot profiles (e.g., `work`, `test`).
2. Double-click **`deploy.bat`** on Windows.
3. The deployment script will ask for your VPS IP address and SSH credentials (saving them centrally in your default profile).
4. **Magic Deployment**: It instantly packages your source code and all your `profiles/`, uploads them securely over SSH, builds a Python virtual environment on your VPS, and registers a permanent background system service!
5. **Auto-Sync**: Anytime you add a new profile or change a persona, simply double-click `deploy.bat` again. It will magically sync your changes to the server in seconds!

---

## ⚙️ Configuration Reference (.env)

```ini
API_ID=2040
API_HASH=b18441a1ff607e10a989891a5462e627
PHONE_NUMBER=+1234567890
OWNER_ID=123456789

# 👤 Personal Identity (Supports Persian/Farsi perfectly)
OWNER_FIRST_NAME=Your First Name / نام شما
OWNER_LAST_NAME=Your Last Name / نام خانوادگی
OWNER_BIO=دانشجو و برنامه‌نویس
OWNER_WEBSITE=yourwebsite.com
OWNER_SERVICES=مشاوره، برنامه‌نویسی و طراحی پروژه
OWNER_INTERESTS=موسیقی، کتاب، تکنولوژی و گفتگو

# 🤖 AI Engine Settings
GEMINI_API_KEYS=your_key_1,your_key_2
GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20"
GEMINI_TTS_MODEL="gemini-3.1-flash-tts-preview"
GEMINI_STT_MODEL="models/gemini-3.5-transcribe-live"

# 🧠 Memory & Processing Tuning
SHORT_TERM_MEMORY_LIMIT=30
LONG_TERM_SUMMARY_INTERVAL=30
MAX_LONG_TERM_SUMMARY_CHARS=600
MAX_MESSAGE_SEGMENT_CHARS=200

# ⚡ Human Simulation Engine (Ghost Engine 2.0)
TYPING_SPEED_CPS=18.0
MIN_TYPING_DELAY=1.5
MAX_TYPING_DELAY=7.0

# ☁️ System Settings
SESSION_NAME=teleagent_session
SESSION_STRING=1ApW... # Generated automatically by the Setup Wizard
VPS_IP=127.0.0.1
SSH_USER=root
SSH_PORT=22
```

---

## 🔒 Security

> [!CAUTION]
> **Never publish your `.env` files to public repositories!** They contain your private `SESSION_STRING` which gives full access to your Telegram account.

---

## 📄 License & Disclaimer

This project is licensed under the **MIT License**.

> [!NOTE]
> **Disclaimer**: This software is intended for personal productivity, educational, and research purposes. Use responsibly and in accordance with Telegram's Terms of Service.

---

<div align="center">
Made with ❤️ for the open-source community.
</div>
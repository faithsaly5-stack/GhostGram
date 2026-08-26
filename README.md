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
  <a href="README.md"><b>English</b></a> •
  <a href="README_FA.md"><b>فارسی</b></a>
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

## 🤖 Zero-Effort Multi-Bot Engine

Managing multiple Telegram bots (e.g., a Work bot, a Personal bot, and a Test bot) used to require complicated setups. **Not anymore.** GhostGram features a containerized architecture!

1. **Add a Bot:** Double click `setup.bat` and enter a new profile name (e.g., `work`). It automatically creates an isolated folder at `profiles/work/`.
2. **Remove a Bot:** Simply delete the `profiles/work/` folder!
3. **Start All Bots:** Double-click `run.bat` and type `all` to run every bot profile simultaneously without conflicts!

The **Master Launcher** handles everything:
- **Complete Isolation**: Each bot lives inside its own folder in `profiles/` with its own `.env`, SQLite memory database, API usage trackers, and Telegram session files.
- **Customization**: You can even have custom Personas just for specific bots by adding text files to `profiles/botname/personas/`!

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
| `333` | Single Chat | **Reset Memory**: Clears short-term and long-term memory for this chat. |
| `999` | Single Chat | **Ghost Purge All**: Deletes every message sent by you in this chat. |
| `555` | Single Chat | **Live Status**: Displays an active status dashboard and auto-deletes. |

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
2. Double-click **`setup.bat`** to create a profile.
3. **Setup Wizard**: It will ask for your profile name (leave blank for the default bot). It then asks for your API keys.
4. **Login**: Type `Y` to log into Telegram right in the terminal. Your `SESSION_STRING` will be permanently injected into your profile's `.env` file!
5. **Start the Bot**: Double-click **`run.bat`** to start your bot. If you have multiple profiles, type **`all`** to launch them all concurrently in the same terminal!

---

### ☁️ Option 2: Free 24/7 Cloud Deployment (Railway / Render / Koyeb - No VPS Required)

Because GhostGram writes your entire Telegram Session (`SESSION_STRING`) directly into your `.env` file, deploying to the cloud is 100% frictionless. You don't need to mount SQLite database volumes!

1. Set up your bot locally using `run.bat` on your PC first (this generates your `SESSION_STRING` inside your `.env` file).
2. Go to [Railway.app](https://railway.app) $\rightarrow$ **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. In Railway, open the Variables tab and copy-paste every line from your `.env` file directly into Railway's variable editor.
4. Railway will automatically detect **Cloud Mode**, see your variables, and boot your bot flawlessly 24/7!

---

### 🖥️ Option 3: 1-Click 24/7 Linux VPS Deployment

If you own a Linux VPS and want a background `systemd` service for all your bots simultaneously:

1. Use **`setup.bat`** to create as many fully functional bot profiles as you want locally. Ensure you logged into Telegram for each of them so they have a `SESSION_STRING`.
2. Double-click **`deploy.bat`** on Windows.
3. It will launch the **VPS Setup Wizard** to ask for your VPS IP Address and save it centrally to `profiles/default/.env`.
4. The deployment engine automatically packages your source code and all your `profiles/`, uploads them securely over SSH, builds a Python virtual environment on your VPS, and registers a permanent systemd service!
5. **Auto-Sync**: Anytime you add, delete, or modify bot profiles on your PC, simply double-click `deploy.bat` again and it will instantly mirror those changes to your VPS.

---

## ⚙️ Configuration Reference (.env)

```ini
API_ID=2040
API_HASH=b18441a1ff607e10a989891a5462e627
PHONE_NUMBER=+1234567890
OWNER_ID=123456789

# 📝 EDIT THESE VALUES IN YOUR TEXT EDITOR (Supports Persian/Farsi perfectly)
OWNER_NAME=Your Name / نام شما
OWNER_BIO=دانشجو و برنامه‌نویس
OWNER_WEBSITE=yourwebsite.com
OWNER_SERVICES=مشاوره، برنامه‌نویسی و طراحی پروژه
OWNER_INTERESTS=موسیقی، کتاب، تکنولوژی و گفتگو

GEMINI_API_KEYS=your_key_1,your_key_2
GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20"

SESSION_NAME=teleagent_session
SESSION_STRING=1ApW... # Generated automatically by the Setup Wizard

# ☁️ Deployment Settings (Optional)
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
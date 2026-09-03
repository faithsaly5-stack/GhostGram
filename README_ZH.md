<div align="center">

# 👻 GhostGram PRO
### *下一代自主 AI Telegram 用户机器人与隐形智能助手*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/Telethon-MTProto%20v2-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telethon" />
  <img src="https://img.shields.io/badge/Google%20Gemini-Flash%202.0%20%26%201.5-8E75C2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Google Gemini" />
  <img src="https://img.shields.io/badge/Docker-Ready%20%26%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Systemd-24%2F7%20Background%20Service-E95420?style=for-the-badge&logo=ubuntu&logoColor=white" alt="Systemd" />
  <img src="https://img.shields.io/badge/Stealth-Zero%20Trace-000000?style=for-the-badge&logo=ghostery&logoColor=white" alt="Stealth Mode" />
  <img src="https://img.shields.io/badge/License-MIT-44CC11?style=for-the-badge" alt="License" />
</p>

<p align="center">
  <a href="README.md"><b>English</b></a> •
  <a href="README_FA.md"><b>فارسی</b></a> •
  <a href="README_ZH.md"><b>中文 (简体)</b></a> •
  <a href="README_RU.md"><b>Русский</b></a> •
  <a href="README_ES.md"><b>Español</b></a>
</p>

---

<p align="center">
  <b>GhostGram</b> 是一个生产级的 Telegram 隐形自主 AI 用户机器人（Userbot），直接将您的个人账户与 <b>Google Gemini AI</b> 连接。<br/>
  它能够自然流畅地进行多语言对话，支持可动态切换的丰富人设（Personas），模拟逼真的人类阅读与打字延迟，具备双层滚动长期记忆，并通过自动销毁的隐形 3 位数字指令进行全权操控，不留任何痕迹。
</p>

---

</div>

## 📑 目录
- [✨ 核心功能](#-核心功能)
- [🎮 隐形指令矩阵 (Secret Codes)](#-隐形指令矩阵-secret-codes)
- [🎭 双 AI 模式与人设引擎](#-双-ai-模式与人设引擎)
- [⚡ 人类行为模拟引擎 (防风控与逼真交互)](#-人类行为模拟引擎-防风控与逼真交互)
- [🧠 双层记忆架构 (短期 + 滚动长期记忆)](#-双层记忆架构-短期--滚动长期记忆)
- [🧹 999 隐形幽灵清理 (Ghost Purge)](#-999-隐形幽灵清理-ghost-purge)
- [🚀 快速安装与多平台部署](#-快速安装与多平台部署)
  - [🌟 方法一：Windows 一键启动（无需代码/无需 VPS）](#-方法一windows-一键启动无需代码无需-vps)
  - [💻 方法二：本地终端手动运行 (CLI)](#-方法二本地终端手动运行-cli)
  - [☁️ 方法三：免费 24/7 云端托管 (Railway / Render - 零成本免 VPS)](#️-方法三免费-247-云端托管-railway--render---零成本免-vps)
  - [🖥️ 方法四：一键部署至 Linux VPS (Systemd 守护进程)](#️-方法四一键部署至-linux-vps-systemd-守护进程)
  - [🐳 方法五：Docker & Docker Compose 运行](#-方法五docker--docker-compose-运行)
- [⚙️ 环境变量配置 (.env)](#️-环境变量配置-env)
- [📁 项目架构](#-项目架构)
- [🛡️ 安全与隐私说明](#️-安全与隐私说明)

---

## ✨ 核心功能

1. **零痕迹隐形控制 (Zero-Trace Stealth Engine)**:
   - 使用 3 位数字指令（`777`, `000`, `666`, `444`, `555`, `999` 等）进行控制。
   - 发送后**立即物理删除**触发消息，群成员与对方完全无法察觉。
   - 全面支持中文、波斯/阿拉伯数字（如 `۰۰۰`、`۷۷۷`）及多余空格自动修正。

2. **双 AI 运营模式**:
   - **👥 伙伴自驾模式 (Pal Autopilot - `777`)**: 指定群聊或私聊由 AI 接管代聊，深度扮演特定人设。
   - **💼 全局私聊助理 (Universal Assistant - `666`)**: 礼貌专业的个人助理，自动接待所有私聊咨询。

3. **🕵️ 自动隐身潜伏互动 (Auto-Engage / Lurker - `777 engage`)**:
   - AI 在指定群聊中潜伏观察，根据活跃度与设定时间间隔，自然挑选有趣话题主动插话。

4. **⚡ 拟真打字与阅读模拟 (Human Simulator)**:
   - 动态计算阅读时间与打字速度（CPS），实时显示 Telegram 原生 `typing...` 状态。

5. **🧠 双层记忆引擎 (Dual-Tier Rolling Memory)**:
   - 自动维护 30 条精准短期上下文，并在后台定期自动浓缩沉淀长期关键记忆摘要。

6. **🧹 999 幽灵清理 (Ghost Purge)**:
   - 一键撤回删除自己在当前聊天中发送的所有历史消息，不留痕迹。

---

## 🎮 隐形指令矩阵 (Secret Codes)

> 💡 **所有指令均在发送后瞬间自毁**，仅您自己的账号能触发。

| 指令 | 适用范围 | 说明与功能 |
| :--- | :---: | :--- |
| `777` | 当前会话 | **开启伙伴模式**（默认人设）。 |
| `777 <人设名>` | 当前会话 | **开启指定人设**（例如 `777 sarcastic` 或 `777 academic`）。 |
| `777 engage [分钟]` | 当前会话 | **开启潜伏互动**（每隔 N 分钟智能评估并自然插话，默认 20 分钟）。 |
| `777 engage off` | 当前会话 | **关闭当前会话的潜伏互动**。 |
| `777 engage off all` | 全局生效 | **关闭所有群聊的潜伏互动**。 |
| `000` | 当前会话 | **关闭伙伴代聊模式**（立即进入静默）。 |
| `000 all` | 全局生效 | **关闭所有会话中的伙伴代聊模式**。 |
| `666` | 全局私聊 | **开启全天候私聊助理**（自动接待新老私聊联系人）。 |
| `444` | 当前会话 | **暂停当前私聊助理**（其他联系人仍受保护）。 |
| `444 all` | 全局私聊 | **完全关闭全局私聊助理**。 |
| `111 <指令/提示词>` | 当前会话/回复 | **指定 AI 即时发言**（可回复某条消息让 AI 根据指示代答）。 |
| `808` | 回复 | **语音转文字 (STT)**: 快速将语音或视频转换为文字。 |
| `809` | 当前会话/回复 | **智能语音回复**: 根据指令生成智能 AI 语音并发送。 |
| `810` | 当前会话 | **语音设置**: 从 30 种不同声音中选择并保存您最喜欢的语音。 |
| `811` | 全局生效 | **AI 变声器 (隐身)**: 拦截您发送的语音记录，自动删除并用 AI 语音无缝替换。 |
| `303` | 当前会话 | **查看记忆**: 显示此聊天的长期记忆摘要（添加 `all` 查看所有）。 |
| `333` | 当前会话 | **重置记忆**: 清除此聊天的所有短期和长期记忆历史。 |
| `555` | 当前会话 | **查看状态面板**（4秒后自动销毁）。 |
| `999 [数量]` | 当前会话 | **幽灵清理**（撤回自己发送的消息，最多回溯 3000 条）。 |
| `998 [数量]` | 当前会话 | **智能幽灵清理**（更快，仅搜索并撤回自己发送的消息）。 |
| `222` | 全局生效 | **恢复出厂设置**: 清除所有记忆并全局停用机器人。 |
| `101` | 当前会话 | **API 统计**: 显示 API 密钥使用的详细报告。 |
| `888` | 当前会话 | **查看帮助菜单**。 |

---

## 🚀 企业级可扩展性与防封禁机制
- **API密钥轮换与冷却 (Cooldown):** 在您的 `.env` 中加载无限制的 Gemini API 密钥。如果一个密钥达到其速率限制 (429 Quota)，引擎会立即轮换到下一个密钥。它还使用 `GEMINI_RPM_COOLDOWN_SECONDS` 在本地暂停操作以严格遵守 API 配额。
- **模型自动级联:** 机器人具有智能故障转移路由。如果您的主要 AI 模型被 Google 服务器过载，它将自动级联到您的辅助备用模型，确保零停机时间。
- **防封禁 FloodWait 保护:** 像幽灵清理（999）这样的后台任务具有数学“人类疲劳”模拟功能。它在批量删除之间进行有计划的微小休息，并默默处理 Telegram 的 FloodWait 陷阱，从而彻底规避账号封禁风险。

---

## 🩺 全面诊断日志记录
该机器人具有在后台运行的工业级 **旋转文件记录器** (`ghostgram.log`)。在您的终端保持完全干净的同时，日志文件会显微镜般地一步步记录机器人为何回复（或忽略）每条消息的具体原因，从而在不消耗无限磁盘空间的情况下使调试变得异常简单。

---

## 👻 Ghost Engine 2.0 (拟人化引擎)
机器人包含一个经过数学计算的 **Ghost Engine**，以防止其表现得像一个自动脚本：
- **打字模拟:** 以 60-80 WPM 的速度打字，并带有自然的标点停顿，打字时间严格限制在 35 秒以内。
- **消息合并 (防抖):** 在私聊中智能等待用户完成打字。如果用户连续发送 5 条消息，GhostGram 会合并它们并仅回复一次。
- **模拟倾听 (语音消息):** 如果您发送一段 3 分钟的语音消息，它不会在 5 秒内回复，而是通过数学计算模拟听完音频的时间。
- **声学模拟 (语音消息):** 对 AI 生成的语音应用 FFmpeg 带通滤波器和粉红噪声覆盖，完美模拟真实智能手机麦克风的频率响应和环境底噪。

---

## 🎭 双 AI 模式与人设引擎

GhostGram 自带 13+ 种精心打磨的预设人设文件（位于 `personas/` 目录）：

- `normal.txt`: 温暖、真实、口语化的日常好友。
- `academic.txt`: 严谨、专业、引用权威的学者。
- `sarcastic.txt`: 幽默、反讽、机智的毒舌好友。
- `angry.txt`: 暴躁、不耐烦但讲逻辑的直性子。
- `poetic.txt`: 优雅深邃的文艺诗人。
- `drunk.txt`: 迷离搞怪的微醺状态。
- `assistant.txt`: 礼貌高效的商务与个人助理。

> **✨ 创建自定人设：** 只需在 `personas/` 文件夹内新建文本文件（例如 `coder.txt`），即可通过 `777 coder` 随时调用！

### 独立角色 (隔离身份)
如果您想创建一个完全脱离您主要身份的角色（这意味着它不会继承 `normal.txt` 中的任何规则、您的名字或简介），只需在其 `.txt` 文件中的任何位置添加 `[STANDALONE]` 标签即可。引擎会立即将其识别为完全隔离，并从最终提示中删除该标签。

---

## 🚀 快速安装与多平台部署

### 🌟 方法一：Windows 一键启动（无需代码/无需 VPS）
如果您使用的是 Windows 个人电脑，只想简单运行：

1. 下载或克隆本项目。
2. 双击运行 **`run.bat`**。
3. 首次运行时，脚本会自动检测 Python 环境、自动安装依赖库，并启动交互式设置向导让您输入 API Key 和个人简介。
4. **完成！** 今后只要想使用机器人，双击 **`run.bat`** 即可。

---

### 💻 方法二：本地终端手动运行 (CLI)

```bash
# 1. 克隆代码库
git clone https://github.com/faithsaly5-stack/GhostGram.git
cd GhostGram

# 2. 创建并激活 Python 虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行交互向导生成配置（或手动编辑 .env）
python setup.py

# 5. Telegram 账号登录认证
python login.py

# 6. 启动 GhostGram
python main.py
```

---

### ☁️ 方法三：免费 24/7 云端托管 (Railway / Render - 零成本免 VPS)
无需购买服务器或让个人电脑开机，即可在云端免费 24 小时运行 GhostGram：

#### 🔑 第一步：生成会话秘钥字符串 (SESSION_STRING)
由于云端服务器为无头环境（Headless），启动时无法交互输入短信验证码，需在本地先生成一次：
1. 在本地电脑双击 `run.bat` 或运行 `python login.py`。
2. 输入手机号与 Telegram 登录验证码。
3. 登录成功后，终端会打印出一段以 `1Ap...` 开头的 **`SESSION_STRING`**，将其复制保存。

---

#### 🚀 第二步：部署至 [Railway.app](https://railway.app) (强烈推荐)
1. Fork 本代码库到您的 GitHub 账号。
2. 登录 Railway.app ➡️ 点击 **New Project** ➡️ 选择 **Deploy from GitHub repo** ➡️ 选中 `GhostGram`。
3. 在 Railway 项目设置的 **Variables** 选项卡中添加以下环境变量：
   - `API_ID`: 您的 Telegram API ID
   - `API_HASH`: 您的 Telegram API Hash
   - `PHONE_NUMBER`: 您的 Telegram 手机号（带国家区号）
   - `SESSION_STRING`: 第一步中复制的 Session String
   - `GEMINI_API_KEYS`: 您的 Google Gemini API Key
   - `OWNER_ID`: 您的 Telegram 数字用户 ID
   - `OWNER_NAME`: 您的名字
   - `OWNER_BIO`: 您的职业/简介
4. Railway 将自动使用内置 Dockerfile 完成构建并启动，实现 24 小时永不掉线！

---

#### 🚀 第三步：或者部署至 [Render.com](https://render.com)
1. 登录 Render.com ➡️ 点击 **New +** ➡️ 选择 **Background Worker**。
2. 连接您的 GitHub 代码库。
3. 环境选择 **Docker**（或 **Python 3**，Build 命令填 `pip install -r requirements.txt`，Start 命令填 `python main.py`）。
4. 在 **Environment Variables** 选项卡中填入各项参数及 `SESSION_STRING`。
5. 点击 **Deploy** 即可！

---

### 🖥️ 方法四：一键部署至 Linux VPS (Systemd 守护进程)
如果您拥有 Linux VPS，希望机器人作为系统服务开机自启、奔溃自动重启：

1. 在本地 `.env` 文件中填入 VPS 连接信息：
   ```env
   VPS_IP=your.vps.ip.here
   SSH_USER=root
   SSH_PORT=22
   ```
2. 双击运行 **`deploy.bat`**（Windows）或在 Linux 下执行 `./deploy.sh`。
3. 脚本将自动打包上传源码、安装 Python 虚拟环境及依赖、生成 `ghostgram.service` 服务并启动实时日志监控。

---

### 🐳 方法五：Docker & Docker Compose 运行

```bash
# 后台构建并启动容器
docker compose up -d --build

# 实时查看日志
docker compose logs -f
```

---

## ⚙️ 环境变量配置 (.env)

```ini
# ==========================================
# 🔑 TELEGRAM 认证凭据 (来自 my.telegram.org)
# ==========================================
API_ID=12345678
API_HASH=abcdef0123456789abcdef0123456789
PHONE_NUMBER=+1234567890
OWNER_ID=123456789

# ==========================================
# 👤 用户身份与人设动态插值参数
# ==========================================
OWNER_FIRST_NAME=YourFirstName
OWNER_LAST_NAME=YourLastName
OWNER_BIO=计算机科学研究生 & AI 开发者
OWNER_WEBSITE=yourwebsite.com
OWNER_SERVICES=AI 开发、网站建设、咨询
OWNER_INTERESTS=音乐、科技、摄影、阅读

# ==========================================
# 🤖 GOOGLE GEMINI API 引擎设置
# ==========================================
GEMINI_API_KEYS=your_key_1,your_key_2
GEMINI_MODELS="gemini-3.8-flash:5:20,gemini-3.7-flash:5:20,gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3-flash-preview:5:20,gemini-3.5-flash-lite:15:500,gemini-3.1-flash-lite:15:500"
GEMINI_TTS_MODELS="gemini-3.1-flash-tts-preview"
GEMINI_STT_MODEL="models/gemini-3.5-transcribe-live"

# 🎙️ 媒体与音频设置
# TTS_NOISE_LEVEL: 机器人声音中添加的模拟粉红噪音/静电的强度，使其听起来像真实的麦克风。
# 单位: 振幅 (例如，0.012 = 轻微静电，0 = 清晰，0.05 = 嘈杂环境)
TTS_NOISE_LEVEL=0.012
# TTS_HIGHPASS / TTS_LOWPASS: 应用于模拟智能手机麦克风频率响应的音频 EQ 滤波器。
# 单位: 赫兹 (Hz)
TTS_HIGHPASS=200
TTS_LOWPASS=4000
# TTS_BITRATE: 生成的 OGG 音频文件的压缩质量。
# 单位: 比特率字符串 (例如，32k = 标准语音消息，64k = 高质量)
TTS_BITRATE=32k
# TTS_DEFAULT_VOICE_INDEX: 从 TTS_VOICES 列表中使用的默认 AI 声音编号（基于 1 索引）。
# 单位: 整数 (例如，6 = Aoede)
TTS_DEFAULT_VOICE_INDEX=6
# TTS_VOICES: 可用的 Gemini TTS 声音名称列表。
# 单位: 逗号分隔的字符串
TTS_VOICES=Achernar, Achird, Algenib, Algieba, Alnilam, Aoede, Autonoe, Callirrhoe, Charon, Despina, Enceladus, Erinome, Fenrir, Gacrux, Iapetus, Kore, Laomedeia, Leda, Orus, Puck, Pulcherrima, Rasalgethi, Sadachbia, Sadaltager, Schedar, Sulafat, Umbriel, Vindemiatrix, Zephyr, Zubenelgenubi
# STT_INITIAL_TIMEOUT_SECONDS: 机器人等待 AI 开始分析大型接收音频文件的时间。
# 单位: 秒 (例如，45.0)
STT_INITIAL_TIMEOUT_SECONDS=45.0
# STT_STREAMING_TIMEOUT_SECONDS: AI 转换音频时流式文本块之间的超时。
# 单位: 秒 (例如，25.0)
STT_STREAMING_TIMEOUT_SECONDS=25.0

# ==========================================
# 🧠 内存与处理调优
# ==========================================
# SHORT_TERM_MEMORY_LIMIT: 扫描您最近发送的消息数量，以防止重复说话。
SHORT_TERM_MEMORY_LIMIT=30
# LONG_TERM_SUMMARY_INTERVAL: 经过多少条消息后，AI 触发长期记忆压缩摘要。
LONG_TERM_SUMMARY_INTERVAL=30
# LONG_TERM_SUMMARY_SCAN_LIMIT: 在长期记忆摘要压缩扫描期间获取的最大近期消息数。
LONG_TERM_SUMMARY_SCAN_LIMIT=100
# MAX_LONG_TERM_SUMMARY_CHARS: 长期摘要记录在旧部分被截断前允许的最大字符数。
MAX_LONG_TERM_SUMMARY_CHARS=600
# MAX_MESSAGE_SEGMENT_CHARS: 如果消息超过此限制，AI 会将其拆分（保持像人类一样的短句）。
MAX_MESSAGE_SEGMENT_CHARS=200

# ==========================================
# ⚡ 拟人化引擎设置 (Ghost Engine 2.0)
# ==========================================
TYPING_SPEED_CPS=18.0
MIN_TYPING_DELAY=1.5
MAX_TYPING_DELAY=7.0
# MAX_DEBOUNCE_WAIT_SECONDS: 引擎在强制回复前等待用户停止输入的最大时间。
MAX_DEBOUNCE_WAIT_SECONDS=45.0
# MAX_VOICE_LISTEN_DELAY_SECONDS: “收听”输入语音笔记时的最大模拟延迟。
MAX_VOICE_LISTEN_DELAY_SECONDS=25.0

# ==========================================
# ⚙️ 高级系统调优
# ==========================================
# 🤖 AI 限制与连接
# GEMINI_MAX_CHARS: 每次请求发送给 AI 的最大字符数（防止崩溃）。
GEMINI_MAX_CHARS=50000
# GEMINI_MAX_ATTEMPTS: 如果一个模型失败，机器人尝试切换到其他模型的次数。
GEMINI_MAX_ATTEMPTS=20
# GEMINI_TIMEOUT_SECONDS: 切换到下一个 AI 模型前的严格超时时间（秒）。
GEMINI_TIMEOUT_SECONDS=35.0
# GEMINI_RPM_COOLDOWN_SECONDS: How long an API key cools down when hitting Google's requests-per-minute limit.
# Unit: Seconds (e.g., 15)
GEMINI_RPM_COOLDOWN_SECONDS=15

# 🗄️ 系统与媒体
# LOG_MAX_BYTES: 日志文件轮转前的最大大小 (5242880 = 5MB)。
LOG_MAX_BYTES=5242880
# LOG_BACKUP_COUNT: 保留的旧日志文件数量。
LOG_BACKUP_COUNT=3
# FFMPEG_TIMEOUT_SECONDS: 等待语音笔记转换为文本的最长时间。
FFMPEG_TIMEOUT_SECONDS=120

# ⚡ 行为与自动化
# AUTO_ENGAGE_INTERVAL_MINUTES: Ghost Lurker 参与前所需的用户不活动分钟数。
AUTO_ENGAGE_INTERVAL_MINUTES=30
# AUTO_ENGAGE_DEFAULT_DURATION_MINUTES: 自动触发时的默认参与持续时间。
AUTO_ENGAGE_DEFAULT_DURATION_MINUTES=20
# AUTO_ENGAGE_LOOP_INTERVAL_SECONDS: 自动参与主循环的检查间隔（秒）。
AUTO_ENGAGE_LOOP_INTERVAL_SECONDS=60
# FATAL_ERROR_RETRY_SECONDS: 如果循环遇到致命错误，机器人的重试等待时间。
FATAL_ERROR_RETRY_SECONDS=60
# GHOST_PURGE_SCAN_LIMIT: 批量清除消息时向后扫描的最大消息数。
GHOST_PURGE_SCAN_LIMIT=3000
# AI_VOICE_COOLDOWN_SECONDS: 变声器命令的防垃圾冷却时间。
AI_VOICE_COOLDOWN_SECONDS=15

# ==========================================
# ☁️ 系统与 VPS 自动化部署设置
# ==========================================
SESSION_NAME=teleagent_session
# SESSION_STRING= (可选，用于 Railway/Render 等云端无头部署)
VPS_IP=123.45.67.89
SSH_USER=root
SSH_PORT=22
```

---

## 🛡️ 安全与隐私说明

- **零数据外泄**: 您的 API Key、手机号、Session 文件均只保存在本地 `.env` 及 session 中，`.gitignore` 与构建发布脚本已作多重隔离，**绝不会推送到 GitHub**。
- **隐形自毁机制**: 所有 3 位数字管理指令在触发后均被 Telegram 原生 Revoke 彻底物理擦除。
- **纯个人使用**: 本项目仅供学习与个人助理使用，请遵守 Telegram 官方服务条款及当地法规。

---

<div align="center">
  <b>GhostGram PRO</b> • <i>由 Google Gemini 与 Telethon 强力驱动</i>
</div>

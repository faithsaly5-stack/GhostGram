import os

files = ['README_ZH.md', 'README_RU.md', 'README_ES.md', 'README_FA.md']

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    # 1. Update config strings
    content = content.replace('GEMINI_TTS_MODEL="gemini-3.1-flash-tts-preview"', 'GEMINI_TTS_MODELS="gemini-3.1-flash-tts-preview"')
    content = content.replace('GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20"', 'GEMINI_MODELS="gemini-3.8-flash:5:20,gemini-3.7-flash:5:20,gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3-flash-preview:5:20"')
    content = content.replace('GEMINI_MODELS="gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3-flash-preview:5:20"', 'GEMINI_MODELS="gemini-3.8-flash:5:20,gemini-3.7-flash:5:20,gemini-3.6-flash:5:20,gemini-3.5-flash:5:20,gemini-3-flash-preview:5:20"')
    
    # 2. Update RPM Cooldown in .env
    content = content.replace('GEMINI_TIMEOUT_SECONDS=25.0', 'GEMINI_TIMEOUT_SECONDS=25.0\n# GEMINI_RPM_COOLDOWN_SECONDS: How long an API key cools down when hitting Google\'s requests-per-minute limit.\n# Unit: Seconds (e.g., 15)\nGEMINI_RPM_COOLDOWN_SECONDS=15')
    
    # 3. Update Cooldown text in Scalability section & inject Standalone Personas
    if f == 'README_ZH.md':
        content = content.replace('- **API 密钥轮换:** 在您的 `.env` 文件中加载无限制的 Gemini API 密钥。如果一个密钥触发频率限制（429 报错），引擎会立即无缝切换到下一个密钥，绝不丢失消息。', '- **API密钥轮换与冷却 (Cooldown):** 在您的 `.env` 中加载无限制的 Gemini API 密钥。如果一个密钥达到其速率限制 (429 Quota)，引擎会立即轮换到下一个密钥。它还使用 `GEMINI_RPM_COOLDOWN_SECONDS` 在本地暂停操作以严格遵守 API 配额。')
        
        persona = "\n\n### 独立角色 (隔离身份)\n如果您想创建一个完全脱离您主要身份的角色（这意味着它不会继承 `normal.txt` 中的任何规则、您的名字或简介），只需在其 `.txt` 文件中的任何位置添加 `[STANDALONE]` 标签即可。引擎会立即将其识别为完全隔离，并从最终提示中删除该标签。"
        content = content.replace("> **✨ 创建自定人设：** 只需在 `personas/` 文件夹内新建文本文件（例如 `coder.txt`），即可通过 `777 coder` 随时调用！", "> **✨ 创建自定人设：** 只需在 `personas/` 文件夹内新建文本文件（例如 `coder.txt`），即可通过 `777 coder` 随时调用！" + persona)
        
    elif f == 'README_RU.md':
        content = content.replace('- **Ротация API-ключей:** Загрузите неограниченное количество API-ключей Gemini в ваш `.env`. Если один ключ исчерпывает свой лимит (ошибка 429), движок мгновенно переключается на следующий ключ, не теряя сообщение.', '- **Ротация API Ключей и Охлаждение:** Загружайте неограниченное количество API-ключей Gemini в ваш `.env`. Если один ключ исчерпывает свой лимит (429 Quota), система мгновенно переключается на следующий. Также используется `GEMINI_RPM_COOLDOWN_SECONDS` для локальной приостановки операций.')
        
        persona = "\n\n### Автономные Персонажи (Изолированная Идентичность)\nЕсли вы хотите создать персонажа, полностью отделенного от вашей основной идентичности (то есть он не будет наследовать правила, ваше имя или вашу биографию из `normal.txt`), просто добавьте тег `[STANDALONE]` в любом месте его `.txt` файла. Механизм мгновенно распознает его как полностью изолированный и удалит этот тег из итогового промпта."
        content = content.replace("> **✨ Добавление своего персонажа:** Просто создайте `.txt` файл в папке `personas/` (например, `streamer.txt`) и активируйте его командой `777 streamer`!", "> **✨ Добавление своего персонажа:** Просто создайте `.txt` файл в папке `personas/` (например, `streamer.txt`) и активируйте его командой `777 streamer`!" + persona)
        
    elif f == 'README_ES.md':
        content = content.replace('- **Rotación de Claves API:** Cargue claves API de Gemini ilimitadas en su `.env`. Si una clave alcanza su límite (Cuota 429), el motor rota de forma instantánea y fluida a la siguiente clave sin perder el mensaje.', '- **Rotación de Claves API y Enfriamiento:** Carga claves API de Gemini ilimitadas en tu `.env`. Si una clave alcanza su límite de cuota (429), el motor rota instantáneamente a la siguiente. También utiliza `GEMINI_RPM_COOLDOWN_SECONDS` para pausar operaciones localmente y evadir baneos.')
        
        persona = "\n\n### Personas Independientes (Identidad Aislada)\nSi deseas crear una persona que esté completamente separada de tu identidad principal (es decir, que no herede reglas, tu nombre ni tu biografía de `normal.txt`), simplemente agrega la etiqueta `[STANDALONE]` en cualquier parte de su archivo `.txt`. El motor lo reconocerá instantáneamente como completamente aislado y eliminará la etiqueta del prompt final."
        content = content.replace("> **✨ Crea tu propia personalidad:** Solo añade un archivo `.txt` en la carpeta `personas/` (ej: `gamer.txt`) y úsalo con `777 gamer`.", "> **✨ Crea tu propia personalidad:** Solo añade un archivo `.txt` en la carpeta `personas/` (ej: `gamer.txt`) y úsalo con `777 gamer`." + persona)

    elif f == 'README_FA.md':
        content = content.replace('- **چرخش کلید API:** تعداد نامحدودی کلید API جمنای را در فایل `.env` خود بارگذاری کنید. اگر یک کلید به محدودیت خود برسد (خطای 429)، موتور به صورت آنی و بدون از دست رفتن پیام به کلید بعدی سوئیچ می‌کند.', '- **چرخش کلیدهای API و Cooldown:** هر تعداد کلید API که می‌خواهید در `.env` قرار دهید. اگر یکی به لیمیت برسد (429 Quota)، انجین فوراً به کلید بعدی سوییچ می‌کند. همچنین از `GEMINI_RPM_COOLDOWN_SECONDS` برای توقف موقت عملیات و رعایت لیمیت‌ها استفاده می‌کند.')
        
        persona = "\n\n## 🎭 موتور چند پرسونایی (Personas)\n\n### پرسونا‌های مستقل (هویت ایزوله)\nاگر می‌خواهید پرسونایی بسازید که کاملاً از هویت اصلی شما جدا باشد (یعنی قوانین، نام یا بیوگرافی شما را از `normal.txt` به ارث نبرد)، کافیست تگ `[STANDALONE]` را در هر کجای فایل `.txt` آن قرار دهید. موتور بلافاصله آن را به عنوان یک هویت کاملاً ایزوله شناسایی کرده و تگ را از پرامپت نهایی حذف می‌کند.\n\n"
        content = content.replace('## 🚀 راه‌اندازی سریع و نصب', persona + '## 🚀 راه‌اندازی سریع و نصب')
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

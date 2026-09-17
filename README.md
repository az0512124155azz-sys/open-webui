# Open WebUI Custom Fork v1 🚀

**A Production-Ready AI Interface with Enhanced Features, Local Model Support & Bionic Integration**

![GitHub stars](https://img.shields.io/github/stars/az0512124155azz-sys/open-webui?style=social)
![GitHub forks](https://img.shields.io/github/forks/az0512124155azz-sys/open-webui?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/az0512124155azz-sys/open-webui?style=social)

> This is a **custom fork** of [Open WebUI](https://github.com/open-webui/open-webui) with production-ready enhancements, local model optimization, and integration with **Bionic AI model repository**.


---

## 🚀 התקנה ב-Windows בלחיצה אחת

**אין צורך להבין Python או פקודות מסובכות.**

### 1. הורד את קובץ ההפעלה

👉 **[הורד OpenWebUI-Setup.bat](https://github.com/az0512124155azz-sys/open-webui/raw/feature/custom-fork-v1/OpenWebUI-Setup.bat)**

(אם הדפדפן מציג טקסט במקום הורדה: לחיצה ימנית על הקישור → **Save link as...** / שמור קישור בשם)

### 2. פתח את הקובץ

לחץ פעמיים על `OpenWebUI-Setup.bat`.

הקובץ יעשה לבד:

1. הורדה/עדכון של הפרויקט  
2. בדיקת Node.js ו-Python  
3. התקנת חבילות (לפני הורדות כבדות ישאל **YES** להמשיך או **NO** להורדה ידנית ואז **Enter**)  
4. הפעלת האתר

### 3. פתח בדפדפן

**http://localhost:8080**

### דרישות חד-פעמיות במחשב

| תוכנה | קישור |
|--------|--------|
| **Node.js 22** (לא 24) | https://nodejs.org/en/download |
| **Python 3.11 או 3.12** | https://www.python.org/downloads/ |
| **Git** (רק אם הפרויקט עדיין לא אצלך) | https://git-scm.com/download/win |

### הפעלה חוזרת אחרי ההתקנה

👉 **[הורד START_WINDOWS.bat](https://github.com/az0512124155azz-sys/open-webui/raw/feature/custom-fork-v1/START_WINDOWS.bat)**  
או מתוך תיקיית הפרויקט: לחיצה כפולה על `START_WINDOWS.bat`.

---

## 🚀 One-Click Windows Setup (English)

👉 **[Download OpenWebUI-Setup.bat](https://github.com/az0512124155azz-sys/open-webui/raw/feature/custom-fork-v1/OpenWebUI-Setup.bat)**

Double-click the file. It clones/updates the repo, installs dependencies (asks before large downloads), and starts **http://localhost:8080**.

Once: [Node.js 22](https://nodejs.org/en/download), [Python 3.11+](https://www.python.org/downloads/), [Git](https://git-scm.com/download/win) if needed.

Later: **[START_WINDOWS.bat](https://github.com/az0512124155azz-sys/open-webui/raw/feature/custom-fork-v1/START_WINDOWS.bat)**

---

## ✨ What's New in This Fork?

### Core Enhancements

- **🔧 Ollama Performance Optimization**
  - `OLLAMA_FLASH_ATTENTION=1` support for accelerated inference
  - `OLLAMA_NUM_PARALLEL=2` configuration for concurrent request handling
  - `OLLAMA_KEEP_ALIVE=-1` for persistent model caching
  - Per-request `keep_alive` parameter tuning

- **🌍 Automatic Hebrew ↔ English Translation**
  - Built-in language detection and real-time translation
  - Local LibreTranslate fallback for offline environments
  - Ollama-powered translation backup
  - Per-user translation preferences
  - Code block, URL, and path protection from translation

- **🗂️ Smart Chat Memory Management**
  - Linked memory deletion when chats are removed
  - `source_chat_id` tracking for memory provenance
  - Pre-deletion confirmation with memory count
  - Legacy compatibility mode

- **📁 Extended File Handling**
  - Multi-format file preview (PDF, DOCX, XLSX, PPTX, images, video, audio)
  - 3D model rendering (STL, OBJ)
  - STL export from 3D previews
  - Automatic file type detection and optimal viewer selection

- **🎨 3D Model Preview & Interaction**
  - Interactive STL viewer with rotation, zoom, and pan
  - OBJ format support
  - Real-time triangle count display
  - Export models to STL format
  - Touch-friendly gesture controls

### Advanced AI Features (Planned)

- **Smart Model Router** - Intelligent model selection based on task type
- **Automatic Model Fallback** - Graceful degradation when models fail
- **Local Model Benchmark** - Performance metrics for local models
- **Context Optimizer** - Smart context reduction for long conversations
- **Compare Models Side-by-Side** - A/B testing interface
- **Plugin System** - Extensible architecture for custom integrations
- **Skills System** - Reusable AI prompts and workflows
- **Session Snapshots** - Save and restore chat snapshots
- **Temporary Chats** - Private ephemeral conversations
- **Global Search** - Full-text search across chats and documents

---

## 🌐 Bionic Model Integration

This fork includes **native support for Bionic AI models** - a curated collection of open-source models optimized for production use.

### Supported Model Sources

1. **Ollama Models** (Default)
2. **Bionic AI Repository**
3. **LM Studio**
4. **vLLM**
5. **OpenAI-Compatible APIs**

---

## 🚀 Quick Start

### Windows (easiest)

Use **[OpenWebUI-Setup.bat](https://github.com/az0512124155azz-sys/open-webui/raw/feature/custom-fork-v1/OpenWebUI-Setup.bat)** above.

### Docker

```bash
docker run -d -p 3000:8080 --name open-webui --restart always ghcr.io/az0512124155azz-sys/open-webui:latest
```

### From source

```bash
git clone -b feature/custom-fork-v1 https://github.com/az0512124155azz-sys/open-webui.git
cd open-webui
# Windows: INSTALL_WINDOWS.bat or START_WINDOWS.bat
```

---

## 📄 License

This project maintains the original [Open WebUI License](LICENSE) with custom enhancements.

**Made with ❤️ for the open-source AI community**

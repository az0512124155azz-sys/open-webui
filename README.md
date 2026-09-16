# Open WebUI Custom Fork v1 🚀

**A Production-Ready AI Interface with Enhanced Features, Local Model Support & Bionic Integration**

![GitHub stars](https://img.shields.io/github/stars/az0512124155azz-sys/open-webui?style=social)
![GitHub forks](https://img.shields.io/github/forks/az0512124155azz-sys/open-webui?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/az0512124155azz-sys/open-webui?style=social)

> This is a **custom fork** of [Open WebUI](https://github.com/open-webui/open-webui) with production-ready enhancements, local model optimization, and integration with **Bionic AI model repository**.

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
   - Public model registry
   - Local model hosting
   - Custom model serving

2. **Bionic AI Repository**
   - Curated model collection
   - Pre-optimized for inference
   - Direct download integration

3. **LM Studio**
   - GGUF format models
   - Local inference engine

4. **vLLM**
   - High-throughput serving
   - Production deployments

5. **OpenAI-Compatible APIs**
   - GroqCloud
   - Mistral API
   - OpenRouter
   - Custom endpoints

### Downloading Models from Bionic

```bash
# Example: Download a model from Bionic
# Models are automatically cached and managed

# Using Ollama with Bionic models
ollama pull bionic/mistral-7b-instruct
ollama pull bionic/neural-chat-7b
ollama pull bionic/dolphin-2.6-mixtral-8x7b
```

**Bionic Popular Models:**

- Mistral 7B Instruct
- Neural Chat 7B
- Dolphin 2.6 Mixtral 8x7B
- Llama 2 Chat 70B (quantized)
- Phi-2
- Zephyr 7B

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# With Ollama and optional GPU support
docker run -d \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_FLASH_ATTENTION=1 \
  -e OLLAMA_NUM_PARALLEL=2 \
  -v open-webui:/app/backend/data \
  --add-host=host.docker.internal:host-gateway \
  --name open-webui \
  --restart always \
  ghcr.io/az0512124155azz-sys/open-webui:latest
```

### Option 2: Python pip

```bash
# Python 3.11+ required
pip install open-webui
open-webui serve
```

### Option 3: Docker Compose

```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - '11434:11434'
    volumes:
      - ollama:/root/.ollama
    environment:
      - OLLAMA_FLASH_ATTENTION=1
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_KEEP_ALIVE=-1

  open-webui:
    image: ghcr.io/az0512124155azz-sys/open-webui:latest
    ports:
      - '3000:8080'
    volumes:
      - open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_FLASH_ATTENTION=1
      - OLLAMA_NUM_PARALLEL=2
    depends_on:
      - ollama
    restart: always

volumes:
  ollama:
  open-webui:
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434           # Ollama server URL
OLLAMA_FLASH_ATTENTION=1                        # Enable Flash Attention 2 optimization
OLLAMA_NUM_PARALLEL=2                           # Number of parallel request handlers
OLLAMA_KEEP_ALIVE=-1                            # Keep model loaded (-1 = forever)

# Translation Configuration
LIBRETRANSLATE_BASE_URL=http://localhost:5000   # LibreTranslate server (optional)
OLLAMA_TRANSLATION_MODEL=mistral                # Fallback translation model in Ollama
TRANSLATION_ENABLED=true                        # Enable auto-translation (default)

# OpenAI Configuration (optional)
OPENAI_API_KEY=sk-...                           # OpenAI API key for hybrid usage
OPENAI_BASE_URL=https://api.openai.com/v1       # OpenAI API endpoint
```

### Ollama Performance Tuning

```bash
# Start Ollama with optimizations
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_KEEP_ALIVE=-1

ollama serve
```

---

## 🌟 Feature Highlights

### 3D Model Viewing

- ✅ STL and OBJ format support
- ✅ Interactive rotation, zoom, and pan
- ✅ Real-time triangle count
- ✅ STL export capability
- ✅ Mobile-friendly touch gestures

### File Support

- ✅ Images (PNG, JPG, JPEG, GIF, WebP, BMP, AVIF, SVG)
- ✅ Videos (MP4, WebM, MOV, OGV)
- ✅ Audio (MP3, WAV, OGG, FLAC, AAC, OPUS)
- ✅ Documents (PDF, DOCX, XLSX, PPTX)
- ✅ Code (Python, JavaScript, TypeScript, Java, C++, etc.)
- ✅ Data (JSON, CSV, TSV, SQL)
- ✅ Markup (Markdown, HTML, XML, YAML)
- ✅ 3D Models (STL, OBJ)

### Translation Features

- ✅ Automatic language detection
- ✅ Hebrew ↔ English translation
- ✅ Code block protection
- ✅ URL and path protection
- ✅ Per-user preferences
- ✅ Offline LibreTranslate support

---

## 📦 Bionic Model Examples

### Pull and Run Models

```bash
# Text generation models
ollama pull bionic/mistral-7b-instruct
ollama pull bionic/neural-chat-7b
ollama pull bionic/dolphin-mixtral-8x7b

# Code-specialized models
ollama pull bionic/deepseek-coder-33b
ollama pull bionic/wizardcoder-15b

# Small efficient models
ollama pull bionic/phi-2
ollama pull bionic/orca-mini-7b

# Run a model
ollama run bionic/mistral-7b-instruct
```

### Model Comparison

| Model              | Size | Speed | Quality   | Best For                     |
| ------------------ | ---- | ----- | --------- | ---------------------------- |
| Phi-2              | 2.7B | ⚡⚡⚡   | ★★★       | Light tasks, edge devices    |
| Mistral-7B         | 7B   | ⚡⚡    | ★★★★      | General purpose, balanced    |
| Neural Chat-7B     | 7B   | ⚡⚡    | ★★★★      | Conversational AI            |
| Dolphin-Mixtral    | 45B  | ⚡     | ★★★★★     | Heavy computation, accuracy  |
| Deepseek Coder-33B | 33B  | ⚡     | ★★★★★     | Code generation              |

---

## 🔐 Security & Privacy

✅ **Completely Local** - Models run on your machine, data never leaves your network
✅ **No Telemetry** - Zero tracking or usage monitoring
✅ **Open Source** - Full source code transparency
✅ **Encryption Ready** - Support for encrypted SQLite database
✅ **RBAC** - Role-based access control for multi-user setups

---

## 🛠️ Development

### Build from Source

```bash
git clone https://github.com/az0512124155azz-sys/open-webui.git
cd open-webui
git checkout feature/custom-fork-v1

# Install dependencies
npm ci

# Development server
npm run dev

# Production build
npm run build

# Run checks
npm run check
npm run format
npm run i18n:parse
```

### Running Tests

```bash
npm run test:frontend
```

### Formatting & Linting

```bash
npm run format          # Auto-format code
npm run lint            # Check code quality
npm run check           # TypeScript checks
```

---

## 💻 System Requirements

### Minimum

- **CPU**: Intel i3 / AMD Ryzen 3 (or equivalent)
- **RAM**: 8 GB (16 GB recommended for larger models)
- **Storage**: 50 GB SSD (depends on models)
- **OS**: Linux, macOS, or Windows (via WSL2)

### Recommended

- **CPU**: Intel i7 / AMD Ryzen 7
- **GPU**: NVIDIA RTX 3080+ or AMD RX 6800+ (for acceleration)
- **RAM**: 32 GB
- **Storage**: 200 GB+ SSD

### GPU Support

```bash
# NVIDIA CUDA
docker run -d \
  -p 3000:8080 \
  --gpus all \
  -v open-webui:/app/backend/data \
  ghcr.io/az0512124155azz-sys/open-webui:cuda

# AMD ROCm
docker run -d \
  -p 3000:8080 \
  --device=/dev/kfd \
  --device=/dev/dri \
  -v open-webui:/app/backend/data \
  ghcr.io/az0512124155azz-sys/open-webui:rocm
```

---

## 🐛 Troubleshooting

### Model Not Loading

```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Check Open WebUI logs
docker logs open-webui

# Restart services
docker restart open-webui
```

### Translation Not Working

```bash
# Check LibreTranslate (if using)
curl http://localhost:5000/detect

# Enable Ollama fallback
# Add fallback model in settings
```

### Memory Issues

```bash
# Increase Docker memory
docker run -m 16g ...  # 16 GB limit

# Reduce model context
# In settings: Lower "max_tokens" for responses
```

---

## 📚 Documentation

- [Original Open WebUI Docs](https://docs.openwebui.com/)
- [Bionic AI Models](https://bionic.ai/models)
- [Ollama Documentation](https://ollama.ai/)
- [LibreTranslate Docs](https://libretranslate.de/)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project maintains the original [Open WebUI License](LICENSE) with custom enhancements. See [LICENSE](LICENSE) for details.

The original Open WebUI project is by [Timothy Jaeryang Baek](https://github.com/tjbck).

---

## 💬 Support & Community

- 🐛 **Issues**: [GitHub Issues](https://github.com/az0512124155azz-sys/open-webui/issues)
- 💬 **Discord**: [Open WebUI Community](https://discord.gg/5rJgQTnV4s)
- 🌐 **Website**: [Open WebUI](https://openwebui.com/)

---

## 🚀 Roadmap

### Phase 1: Stability (Current)

- ✅ Ollama optimization
- ✅ Hebrew translation
- ✅ 3D model support
- ✅ File preview enhancements
- 🔄 CI/CD fixes

### Phase 2: Intelligence

- 🔧 Smart Model Router
- 🔧 Automatic fallback
- 🔧 Context optimization
- 🔧 Plugin system
- 🔧 Skills framework

### Phase 3: Enterprise

- 🔧 Advanced RBAC
- 🔧 Audit logging
- 🔧 Multi-node scaling
- 🔧 Enterprise SSO
- 🔧 Compliance reporting

---

**Made with ❤️ for the open-source AI community**

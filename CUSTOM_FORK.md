# Custom Open WebUI Fork v1

This branch keeps Open WebUI's existing architecture and adds a focused set of local-first features: Ollama performance controls, automatic Hebrew/English translation, chat-scoped memory privacy, a cleaner chat layout, richer file previews, and local 3D/STL workflows.

## Quick start

Requirements:

- Docker Desktop / Docker Engine with Compose v2
- 8 GB RAM minimum; 16 GB+ recommended for local models
- Optional NVIDIA or AMD GPU supported by Ollama

```bash
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:3000`.

The default Compose stack starts:

- **Open WebUI** on port `3000`
- **Ollama** on the internal Docker network
- **LibreTranslate** on `127.0.0.1:5000` with persistent language models

The LibreTranslate port is bound to localhost by default so it is not exposed to other machines on the network.

## NVIDIA / AMD

The base Compose file contains the Ollama performance defaults. Use the existing GPU overlays for the matching platform:

```bash
# NVIDIA
docker compose -f docker-compose.yaml -f docker-compose.gpu.yaml up -d --build

# AMD / ROCm
docker compose -f docker-compose.yaml -f docker-compose.amdgpu.yaml up -d --build
```

Default local-inference settings:

```env
OLLAMA_KEEP_ALIVE=-1
OLLAMA_FLASH_ATTENTION=1
OLLAMA_NUM_PARALLEL=2
```

`OLLAMA_KEEP_ALIVE` is also applied to supported Ollama requests at runtime. Flash Attention and parallelism are Ollama server-process settings, so changing them in the admin UI requires restarting an externally managed Ollama server. Managed Compose deployments pick them up on restart.

## Ollama diagnostics

Admin settings expose local Ollama performance controls and loaded-model diagnostics. Diagnostics use Ollama's `/api/ps` API and show the model expiry / `Until` state. With `keep_alive=-1`, models should remain loaded until explicitly unloaded or the Ollama process restarts.

## Automatic Hebrew ↔ English translation

The fork installs the global `automatic_hebrew_translation` Filter Function. It is globally available but disabled per user by default.

Open **Settings → Interface → Translation** and enable it. Available engines:

- **LibreTranslate** — default local service at `http://libretranslate:5000`
- **Ollama** — local model fallback / alternative, default `qwen2.5:3b`

The filter detects message language, translates Hebrew prompts to English before inference, and translates English assistant output back to Hebrew. Code fences, inline code, URLs, and file paths are protected. Long messages are chunked and translated concurrently.

### Offline behavior

LibreTranslate is included in Docker Compose with persistent model storage and English/Hebrew language loading. Once the images and language data are present locally, translation does not require a cloud translation API.

## Chat memory privacy

Memories created from a conversation now carry `source_chat_id`. Existing memories are backfilled from their previous chat metadata when possible.

Open **Settings → Data Controls → Privacy** and enable **Delete linked memories with chat** to make chat deletion also remove only the memories created from that chat. Both SQL rows and vector entries are removed. Memories from other conversations and manually-created memories remain untouched.

The backend also exposes a chat-scoped memory count endpoint and a strict delete-with-memories endpoint for clients that need an explicit privacy workflow.

## Interface design

`static/custom.css` provides a restrained GPT-style visual layer without changing Open WebUI branding or product identifiers. It keeps the main conversation width focused, reduces card/border noise, improves sidebar selection states, and preserves mobile and dark-mode behavior.

## File previews

Uploaded files open in the enhanced local preview modal. Existing Open WebUI preview capabilities are reused for:

- images, audio and video
- PDF
- DOCX, XLS/XLSX and PPTX
- CSV/TSV
- Markdown, HTML, JSON, SVG, notebooks and source code
- SQLite databases
- plain text and logs

Unknown binary formats still expose a direct download action instead of failing the chat UI.

## 3D preview and STL export

`.stl` and `.obj` files receive an interactive dependency-free 3D preview. Drag to rotate and use the wheel/trackpad to zoom. The viewer parses both ASCII and binary STL plus common OBJ polygon faces locally in the browser.

The **Export STL** action converts the currently loaded mesh to ASCII STL. This also allows an OBJ result to be downloaded as STL without uploading the geometry to another service.

Generated terminal artifacts use the same 3D viewer when an STL/OBJ file is displayed inline.

## Downloads

File cards expose a direct authenticated download action. The enhanced preview modal also always includes **Download**, including for file types that cannot be previewed. Generated terminal artifacts keep their original download action as well.

## Updating this fork

Before syncing a newer upstream Open WebUI release:

1. Back up the Open WebUI data volume and database.
2. Keep the custom branch separate from `main` while resolving upstream changes.
3. Pay special attention to the router compatibility wrappers (`ollama_legacy.py`, `chats_legacy.py`, `memories_legacy.py`).
4. Run the frontend type check, unit tests, backend checks used by upstream, and the custom smoke script.
5. Rebuild all Compose services so server-level Ollama and LibreTranslate settings are applied.

## Validation

Frontend checks:

```bash
npm run check
npm run test:frontend -- --run
npm run build
```

Compose / service smoke test:

```bash
bash scripts/custom-fork-smoke.sh
```

The smoke script validates Compose configuration, Open WebUI health, Ollama availability, and both Hebrew→English and English→Hebrew LibreTranslate calls when those services are reachable.

## Troubleshooting

**Translation says the local service is unavailable**  
Check `docker compose ps libretranslate` and `docker compose logs libretranslate`. The first start can take longer while language packages are initialized.

**A model still unloads**  
Verify the running Ollama server was restarted with `OLLAMA_KEEP_ALIVE=-1`. External Ollama processes do not inherit environment changes made inside Open WebUI.

**3D preview is empty**  
Confirm the file is a valid STL or OBJ mesh with triangle/polygon faces. Very large meshes can take longer to draw because preview is intentionally dependency-free and local.

**A file has no preview**  
Use **Download**. Unsupported binary formats are preserved and downloadable even when no browser renderer exists.

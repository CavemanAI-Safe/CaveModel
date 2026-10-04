# CaveManAI ModelCreate Vault

A lightweight browser-based tool for rapidly building and deploying Ollama Modelfiles. Form-fillable parameters, live preview, and direct `ollama create` integration — no CLI workflow required.

## Quick Start

```bash
cd ModelCreate
python3 server.py
```

Open **http://localhost:8700** in your browser.

Custom port:
```bash
python3 server.py 9000
```

## UI Layout

### Left Gutter — Control Panel

| Section | Description |
|---|---|
| **Model Identity** | Set the model name (target for `ollama create`) and select a base model (FROM). The dropdown auto-populates from your local `ollama list`; switch to manual entry for any model not yet pulled. |
| **Parameters** | Temperature, top_p, top_k, num_ctx, num_predict, repeat_penalty. Leave any field blank to omit. |
| **Stop Sequences** | Add or remove `PARAMETER stop` entries dynamically. |
| **System Context / Persona** | Full-text multiline editor for the SYSTEM block. |
| **Template** | Optional Go-template override. |
| **RAW Modelfile Override** | Paste an existing Modelfile verbatim — bypasses the form entirely. |

### Right Working Area — Preview & Actions

- **Modelfile Preview** — live-generated output, updates as you type
- **Download Modelfile** — saves the file to your downloads folder
- **Copy to Clipboard** — one-click copy
- **Create Model (ollama)** — sends the Modelfile to the server, which runs `ollama create <name> -f <file>` and streams the result

## API Endpoints

The server exposes a minimal JSON API:

| Method | Path | Body | Description |
|---|---|---|---|
| `GET` | `/api/base-models` | — | Returns `{"models": ["..."]}` from `ollama list` |
| `POST` | `/api/create` | `{"name": "...", "modelfile": "..."}` | Creates the model via `ollama create`. Returns `{"success": bool, "output": "..."}` |
| `POST` | `/api/save` | `{"name": "...", "content": "..."}` | Saves Modelfile to `exports/<name>/Modelfile` on disk |

## File Structure

```
ModelCreate/
├── index.html          # Main application UI
├── server.py           # Local server (Python 3.10+, stdlib only)
├── Modelfile           # Example Modelfile (EagleEye agent)
├── CAVE_UI_1.xml       # Layout reference
└── exports/            # Created by server on first run
    └── <model-name>/
        └── Modelfile
```

## Requirements

- Python 3.10+
- Ollama installed and running (`ollama serve` or the desktop app)
- No pip packages required — pure stdlib

## Notes

- Base model dropdown refreshes each time the server starts.
- The `Create Model` button validates both the model name and Modelfile content before dispatching.
- Models created via this tool appear immediately in `ollama list`.
- Exported Modelfiles land in `exports/<model-name>/Modelfile` alongside the app.

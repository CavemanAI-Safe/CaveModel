#!/usr/bin/env python3
"""
CaveManAI ModelCreate Vault — lightweight local server.
Serves the UI + exposes endpoints so the browser can talk to Ollama directly.

Usage:
    python3 server.py          # defaults to port 8700
    python3 server.py 9000     # custom port
"""

import json, os, subprocess, sys, tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = BASE_DIR / "exports"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8700


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/base-models":
            self._api_base_models()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/create":
            self._api_create()
        elif parsed.path == "/api/save":
            self._api_save()
        else:
            self._json_response(404, {"error": "Not found"})

    # ------------------------------------------------------------------
    # GET /api/base-models
    # ------------------------------------------------------------------
    def _api_base_models(self):
        try:
            out = subprocess.check_output(
                ["ollama", "list"], stderr=subprocess.STDOUT, text=True
            )
            models = []
            for line in out.strip().splitlines()[1:]:
                name = line.split()[0] if line.strip() else None
                if name:
                    models.append(name)
            self._json_response(200, {"models": models})
        except FileNotFoundError:
            self._json_response(
                200, {"models": [], "warning": "ollama binary not found"}
            )
        except subprocess.CalledProcessError as e:
            self._json_response(
                200, {"models": [], "warning": e.output or str(e)}
            )

    # ------------------------------------------------------------------
    # POST /api/create   { "name": "...", "modelfile": "..." }
    # ------------------------------------------------------------------
    def _api_create(self):
        body = self._read_json()
        if not body:
            return

        name = body.get("name", "").strip()
        modelfile = body.get("modelfile", "").strip()

        if not name or not modelfile:
            self._json_response(
                400, {"success": False, "error": "name and modelfile required"}
            )
            return

        # Write temp Modelfile
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix="Modelfile",
            prefix="caveman_",
            dir=str(EXPORTS_DIR),
            delete=False,
        )
        tmp.write(modelfile)
        tmp.write("\n")
        tmp.close()

        try:
            result = subprocess.run(
                ["ollama", "create", name, "-f", tmp.name],
                capture_output=True,
                text=True,
                timeout=600,
            )
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            success = result.returncode == 0
            self._json_response(
                200,
                {
                    "success": success,
                    "output": output.strip(),
                    "error": None if success else f"exit code {result.returncode}",
                },
            )
        except subprocess.TimeoutExpired:
            self._json_response(
                200, {"success": False, "error": "timeout (600s)"}
            )
        except FileNotFoundError:
            self._json_response(
                200, {"success": False, "error": "ollama binary not found"}
            )
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # POST /api/save   { "name": "...", "content": "..." }
    # ------------------------------------------------------------------
    def _api_save(self):
        body = self._read_json()
        if not body:
            return

        name = body.get("name", "model").strip()
        content = body.get("content", "")
        if not name:
            name = "model"

        model_dir = EXPORTS_DIR / name
        model_dir.mkdir(parents=True, exist_ok=True)
        modelfile_path = model_dir / "Modelfile"
        modelfile_path.write_text(content, encoding="utf-8")

        self._json_response(
            200,
            {
                "success": True,
                "path": str(modelfile_path),
                "message": f"Modelfile saved to {modelfile_path}",
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._json_response(400, {"error": "invalid JSON"})
            return None

    def _json_response(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[CaveManAI ModelCreate] {args[0]} {args[1]}\n")


# ------------------------------------------------------------------
if __name__ == "__main__":
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"CaveManAI ModelCreate Vault  —  http://localhost:{PORT}", flush=True)
    print(f"Exports directory:  {EXPORTS_DIR}", flush=True)
    print("Press Ctrl+C to stop.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] CaveManAI Vault shutting down.")
        server.server_close()

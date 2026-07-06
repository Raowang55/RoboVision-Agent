"""Background server launcher for RoboVision-Agent."""
from app.main import build_ui, custom_css
from app.main import preload_embedding_model
from app.utils.logging_config import setup_logging
import gradio as gr
import threading
import time

setup_logging()

demo = build_ui()

# Preload embedding model for RAG (synchronous, takes ~5s)
import logging
logger = logging.getLogger(__name__)
logger.info("Preloading embedding model...")
preload_embedding_model()

demo.launch(
    server_name="127.0.0.1",
    server_port=7861,
    css=custom_css,
    share=False,
    show_error=True,
    prevent_thread_lock=True,
)
logger.info("Server started on http://127.0.0.1:7861")

# ---- /health endpoint (lightweight, no extra dependencies) ----
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

_START_TIME = time.time()

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({
                "status": "ok",
                "uptime_seconds": round(time.time() - _START_TIME, 1),
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass  # silence request logs

_health_server = HTTPServer(("127.0.0.1", 7862), _HealthHandler)
_health_thread = threading.Thread(target=_health_server.serve_forever, daemon=True)
_health_thread.start()
logger.info("Health endpoint started on http://127.0.0.1:7862/health")

# Keep alive indefinitely
try:
    while True:
        time.sleep(3600)
except KeyboardInterrupt:
    logger.info("Server stopped.")

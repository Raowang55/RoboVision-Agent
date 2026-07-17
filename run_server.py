"""Single-process launcher for the RoboVision Gradio application."""

from __future__ import annotations

import logging
import os

from app.config import GRADIO_TEMP_DIR, SERVER_HOST, SERVER_PORT, ensure_runtime_dirs
from app.utils.logging_config import setup_logging
from app.utils.ultralytics_patch import patch_ultralytics


def main() -> None:
    ensure_runtime_dirs()
    os.environ["GRADIO_TEMP_DIR"] = str(GRADIO_TEMP_DIR)
    patch_ultralytics()
    setup_logging()

    from app.main import _find_free_port, build_ui

    logger = logging.getLogger(__name__)
    port = _find_free_port(SERVER_PORT)
    logger.info("Starting RoboVision Agent on http://%s:%s", SERVER_HOST, port)
    build_ui().launch(
        server_name=SERVER_HOST,
        server_port=port,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()

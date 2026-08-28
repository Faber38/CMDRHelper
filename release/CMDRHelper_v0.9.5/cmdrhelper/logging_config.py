from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_MAX_BYTES = 2 * 1024 * 1024
LOG_BACKUP_COUNT = 3


def log_folder() -> Path:
    folder = Path(__file__).resolve().parent.parent / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def configure_logging(level=logging.INFO) -> Path:
    log_file = log_folder() / "cmdrhelper.log"

    root = logging.getLogger()
    root.setLevel(level)

    # Bei erneutem Aufruf keinen zweiten CMDRHelper-Dateihandler anlegen.
    for handler in root.handlers:
        if getattr(handler, "_cmdrhelper_file_handler", False):
            return log_file

    handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler._cmdrhelper_file_handler = True
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s "
            "[%(threadName)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    return log_file

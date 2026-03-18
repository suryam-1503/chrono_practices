import logging
from pathlib import Path

# Global log file path
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "automation.log"


def setup_logger(name=__name__):

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Stop logs propagating to Prefect root logger
    logger.propagate = False

    if not logger.handlers:

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
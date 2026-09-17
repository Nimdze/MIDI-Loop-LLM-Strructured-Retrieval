import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the package logger cleanly."""
    logger = logging.getLogger("midi_analyzer_tagger")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)

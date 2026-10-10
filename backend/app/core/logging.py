import logging


def configure_logging(level: str) -> None:
    """Send app logs to stderr at `level` (e.g. "INFO"). Shared by the API and the CLI."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

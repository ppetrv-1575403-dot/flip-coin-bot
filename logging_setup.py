import logging


def setup_logging() -> logging.Logger:
    """Настраивает логирование явно, при вызове из main() — а не как side-effect импорта."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("coin_bot")

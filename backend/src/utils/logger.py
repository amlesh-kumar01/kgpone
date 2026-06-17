import logging
import sys

def setup_logger(name: str = "KgpOne") -> logging.Logger:
    logger = logging.getLogger(name)
    
    # If the logger already has handlers, assume it's already configured to avoid duplicate logs
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Global instance for easy import
logger = setup_logger()

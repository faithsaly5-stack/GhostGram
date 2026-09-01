import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger():
    # Create logger
    logger = logging.getLogger("GhostGram")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate logs if called multiple times
    if logger.handlers:
        return logger

    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create file handler
    log_file = os.path.join(Config.PROFILE_DIR, "ghostgram.log")
    try:
        # 5 MB max per file, keeping 3 backup files (total 20 MB max history per profile)
        fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"⚠️ Could not set up file logger at {log_file}: {e}")

    return logger

logger = setup_logger()

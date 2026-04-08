"""日志配置"""
import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """配置日志: 控制台 + 文件(5MB滚动, 保留7个)"""
    # 日志目录: exe同级/log, 或 backend/log
    if getattr(sys, 'frozen', False):
        log_dir = Path(os.path.dirname(sys.executable)) / "log"
    else:
        log_dir = Path(__file__).resolve().parent.parent.parent / "log"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "etf_radar.log"

    # 根日志
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    # 文件: 5MB滚动, 保留7个备份
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_handler)

    # 降低第三方库日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"日志文件: {log_file}")

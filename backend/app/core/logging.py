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
    # 根日志 + 控制台（优先保证控制台可用）
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console)

    # 日志目录: 优先用 run.py 设置的环境变量，兜底用代码目录
    base = os.environ.get("ETF_BASE_DIR")
    if base:
        log_dir = Path(base) / "log"
    else:
        log_dir = Path(__file__).resolve().parent.parent.parent / "log"

    # 文件 handler: 失败时降级为仅控制台
    try:
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "etf_radar.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root.addHandler(file_handler)
        logging.info(f"日志文件: {log_file}")
    except OSError as e:
        logging.warning(f"无法创建日志文件({e}), 仅输出到控制台。请将程序移到非系统目录(如D盘)后重试")

    # 降低第三方库日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

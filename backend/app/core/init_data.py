"""首次启动初始化"""
import gzip
import shutil
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS, DATA_DIR
from app.models.models import ETFFund

logger = logging.getLogger(__name__)

MAIN_DB = DATA_DIR / "etf.db"


def _find_seed_gz() -> Path:
    candidates = [
        DATA_DIR / "seed.db.gz",
        Path(__file__).resolve().parent.parent.parent / "data" / "seed.db.gz",
    ]
    if getattr(sys, 'frozen', False):
        candidates.insert(0, Path(sys._MEIPASS) / "data" / "seed.db.gz")
    for p in candidates:
        if p.exists():
            return p
    return None


def init_seed_data():
    seed = _find_seed_gz()
    if not MAIN_DB.exists() and seed:
        with gzip.open(seed, "rb") as f_in, open(MAIN_DB, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        logger.info("从 seed.db.gz 恢复预置数据")
        return

    db: Session = SessionLocal()
    try:
        count = db.query(ETFFund).count()
        if count == 0:
            for item in DEFAULT_ETFS:
                db.add(ETFFund(**item))
            db.commit()
            logger.info(f"写入 {len(DEFAULT_ETFS)} 只默认ETF")
        else:
            logger.info(f"etf_fund 已有 {count} 条记录")
    finally:
        db.close()

"""首次启动初始化"""
import gzip
import shutil
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS, DATA_DIR
from app.models.models import ETFFund

MAIN_DB = DATA_DIR / "etf.db"


def _find_seed_gz() -> Path:
    """查找 seed.db.gz（兼容开发模式和 exe 模式）"""
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
        print(f"[init] 从 seed.db.gz 恢复预置数据")
        return

    db: Session = SessionLocal()
    try:
        count = db.query(ETFFund).count()
        if count == 0:
            for item in DEFAULT_ETFS:
                db.add(ETFFund(**item))
            db.commit()
            print(f"[init] 写入 {len(DEFAULT_ETFS)} 只默认ETF")
        else:
            print(f"[init] etf_fund 已有 {count} 条记录")
    finally:
        db.close()

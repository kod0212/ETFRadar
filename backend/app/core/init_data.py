"""首次启动初始化"""
import gzip
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS, DATA_DIR
from app.models.models import ETFFund

SEED_GZ = DATA_DIR / "seed.db.gz"
MAIN_DB = DATA_DIR / "etf.db"


def init_seed_data():
    if not MAIN_DB.exists() and SEED_GZ.exists():
        with gzip.open(SEED_GZ, "rb") as f_in, open(MAIN_DB, "wb") as f_out:
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

"""首次启动初始化"""
import shutil
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS, DATA_DIR
from app.models.models import ETFFund

SEED_DB = DATA_DIR / "seed.db"
MAIN_DB = DATA_DIR / "etf.db"


def init_seed_data():
    # 如果主数据库不存在但种子数据库存在，直接复制
    if not MAIN_DB.exists() and SEED_DB.exists():
        shutil.copy2(SEED_DB, MAIN_DB)
        print(f"[init] 从 seed.db 恢复预置数据")
        return

    # 否则检查是否需要写入默认ETF
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

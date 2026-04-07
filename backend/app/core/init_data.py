"""首次启动初始化种子数据"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS
from app.models.models import ETFFund


def init_seed_data():
    db: Session = SessionLocal()
    try:
        count = db.query(ETFFund).count()
        if count == 0:
            for item in DEFAULT_ETFS:
                db.add(ETFFund(**item))
            db.commit()
            print(f"[init] 写入 {len(DEFAULT_ETFS)} 只默认ETF")
        else:
            print(f"[init] etf_fund 已有 {count} 条记录，跳过种子数据")
    finally:
        db.close()

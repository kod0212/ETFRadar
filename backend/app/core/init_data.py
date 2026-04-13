"""首次启动初始化 + 版本升级合并"""
import gzip
import shutil
import sys
import logging
import sqlite3
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import DEFAULT_ETFS, DATA_DIR, VERSION
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

    if not MAIN_DB.exists():
        # 全新安装：直接从seed恢复
        if seed:
            with gzip.open(seed, "rb") as f_in, open(MAIN_DB, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            logger.info("全新安装: 从 seed.db.gz 恢复预置数据")
        return

    # 已有数据库：检查是否需要升级
    if seed:
        _merge_upgrade(seed)

    # 确保有默认ETF
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


def _merge_upgrade(seed_gz: Path):
    """
    合并升级：用seed中的新数据更新现有数据库，保留用户数据
    - 更新 etf_dict（新ETF、新名称、新标签规则）
    - 更新 etf_fund.sys_tags（系统标签刷新）
    - 补入新的 etf_share 数据（seed中有但本地没有的）
    - 保留用户的 etf_fund（追踪列表）和 tags（自定义标签）
    """
    import tempfile, os

    # 解压seed到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        with gzip.open(seed_gz, "rb") as f_in, open(tmp.name, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        main_conn = sqlite3.connect(str(MAIN_DB))
        seed_conn = sqlite3.connect(tmp.name)

        # 1. 更新 etf_dict（全量替换，seed的更新更全）
        seed_dicts = seed_conn.execute("SELECT code, name, market, index_name, auto_tags FROM etf_dict").fetchall()
        if seed_dicts:
            # 确保表有auto_tags列
            try:
                main_conn.execute("ALTER TABLE etf_dict ADD COLUMN auto_tags TEXT")
            except:
                pass
            for row in seed_dicts:
                main_conn.execute(
                    "INSERT OR REPLACE INTO etf_dict (code, name, market, index_name, auto_tags) VALUES (?,?,?,?,?)",
                    row
                )
            logger.info(f"升级: 更新 etf_dict {len(seed_dicts)} 条")

        # 2. 刷新 etf_fund.sys_tags（保留用户的tags不动）
        try:
            main_conn.execute("ALTER TABLE etf_fund ADD COLUMN sys_tags TEXT")
        except:
            pass
        main_conn.execute("""
            UPDATE etf_fund SET
                sys_tags = (SELECT auto_tags FROM etf_dict WHERE etf_dict.code = etf_fund.code),
                name = (SELECT name FROM etf_dict WHERE etf_dict.code = etf_fund.code)
            WHERE code IN (SELECT code FROM etf_dict)
        """)
        logger.info("升级: 刷新 etf_fund 系统标签和名称")

        # 3. 补入seed中有但本地没有的etf_share数据
        main_max = main_conn.execute("SELECT MAX(trade_date) FROM etf_share").fetchone()[0]
        seed_max = seed_conn.execute("SELECT MAX(trade_date) FROM etf_share").fetchone()[0]

        if seed_max and (not main_max or seed_max > main_max):
            # seed有更新的数据，补入
            if main_max:
                new_rows = seed_conn.execute(
                    "SELECT fund_code, trade_date, price, total_market_cap, shares, change_shares, source FROM etf_share WHERE trade_date > ?",
                    (main_max,)
                ).fetchall()
            else:
                new_rows = seed_conn.execute(
                    "SELECT fund_code, trade_date, price, total_market_cap, shares, change_shares, source FROM etf_share"
                ).fetchall()

            for row in new_rows:
                try:
                    main_conn.execute(
                        "INSERT OR IGNORE INTO etf_share (fund_code, trade_date, price, total_market_cap, shares, change_shares, source) VALUES (?,?,?,?,?,?,?)",
                        row
                    )
                except:
                    pass
            main_conn.commit()
            logger.info(f"升级: 补入 {len(new_rows)} 条份额数据 (seed到{seed_max})")
        else:
            logger.info("升级: 份额数据已是最新，无需补入")

        main_conn.commit()
        main_conn.close()
        seed_conn.close()
    finally:
        os.unlink(tmp.name)

"""给所有ETF补全价格和市值"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from app.services.collector import _fetch_sina_kline
from app.core.database import SessionLocal, init_db
from app.models.models import ETFShare, ETFDict
from sqlalchemy import text

init_db()
db = SessionLocal()

# 获取所有有份额但缺价格的ETF代码
codes = [r[0] for r in db.execute(
    text("SELECT DISTINCT fund_code FROM etf_share WHERE price IS NULL")
).fetchall()]
print(f"需要补价格的ETF: {len(codes)} 只")

# 从字典表获取市场信息
dict_map = {d.code: d.market for d in db.query(ETFDict).all()}
print(f"字典表: {len(dict_map)} 只")

# 没在字典表里的，按代码猜市场(5/1开头=sh, 其他=sz)
def guess_market(code):
    if code in dict_map:
        return dict_map[code]
    return "sh" if code.startswith(("5", "1")) else "sz"

total_updated = 0
failed = []

for i, code in enumerate(codes):
    market = guess_market(code)
    try:
        klines = _fetch_sina_kline(code, market, 400)
        if not klines:
            failed.append(code)
            continue
        price_map = {k["day"]: k["close"] for k in klines}

        rows = db.query(ETFShare).filter(
            ETFShare.fund_code == code,
            ETFShare.price == None
        ).all()

        updated = 0
        for row in rows:
            price = price_map.get(row.trade_date.isoformat())
            if price:
                row.price = price
                row.total_market_cap = round(row.shares * price, 2) if row.shares else None
                updated += 1

        db.commit()
        total_updated += updated

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(codes)}] 已补 {total_updated} 条价格")

    except Exception as e:
        db.rollback()
        failed.append(code)

    time.sleep(0.2)

print(f"\n补价格完成: {total_updated} 条")
if failed:
    print(f"失败: {len(failed)} 只 (可能已退市)")

db.close()

# 更新seed
import gzip, shutil
db_path = os.path.join(os.path.dirname(__file__), "..", "data", "etf.db")
gz_path = os.path.join(os.path.dirname(__file__), "..", "data", "seed.db.gz")
with open(db_path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
    shutil.copyfileobj(f_in, f_out)
print(f"seed.db.gz 已更新")
print("\n done")

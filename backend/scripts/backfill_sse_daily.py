"""上交所ETF每日精确份额回补 - 保存全部ETF"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time, json
from datetime import date
from app.services.collector import fetch_sse_shares_by_date, _fetch_sina_kline, _calc_change_shares
from app.core.database import SessionLocal, init_db
from app.models.models import ETFFund, ETFShare

init_db()
db = SessionLocal()

# 用一只已知ETF获取交易日列表
prices_510300 = _fetch_sina_kline("510300", "sh", 365)
trade_dates = sorted([dp["day"] for dp in prices_510300])
print(f"交易日: {trade_dates[0]} ~ {trade_dates[-1]}, 共 {len(trade_dates)} 天")

# 1. 逐日获取上交所全部ETF份额（约8分钟）
print("\n开始逐日获取上交所全部ETF份额...")
daily_sse = {}  # {date_str: {code: shares_yi}}
for i, dt_str in enumerate(trade_dates):
    dt_fmt = dt_str.replace("-", "")
    data = fetch_sse_shares_by_date(dt_fmt)
    if data:
        daily_sse[dt_str] = data
    print(f"  [{i+1}/{len(trade_dates)}] {dt_str}: {len(data) if data else 0} 只")
    time.sleep(0.3)

print(f"\n获取完成: {len(daily_sse)} 天有数据")

# 保存原始数据到JSON（备份，避免重复请求）
cache_file = os.path.join(os.path.dirname(__file__), "..", "data", "sse_daily_cache.json")
with open(cache_file, "w") as f:
    json.dump(daily_sse, f)
print(f"已缓存到 {cache_file}")

# 2. 收集所有出现过的上交所ETF代码
all_sh_codes = set()
for shares_map in daily_sse.values():
    all_sh_codes.update(shares_map.keys())
print(f"\n上交所ETF总数: {len(all_sh_codes)} 只")

# 3. 获取每只ETF的价格（只处理已追踪的，其他只存份额不存价格）
tracked = {f.code: f for f in db.query(ETFFund).filter(ETFFund.market == "sh").all()}
print(f"已追踪上交所ETF: {list(tracked.keys())}")

# 获取已追踪ETF的价格
prices_map = {}
for code in tracked:
    prices = _fetch_sina_kline(code, "sh", 365)
    prices_map[code] = {dp["day"]: dp["close"] for dp in prices}

# 4. 删除旧的上交所数据
deleted = db.query(ETFShare).filter(ETFShare.fund_code.in_(all_sh_codes)).delete(synchronize_session=False)
db.commit()
print(f"删除旧数据: {deleted} 条")

# 5. 写入全部上交所ETF数据
total_count = 0
for code in sorted(all_sh_codes):
    count = 0
    for dt_str in trade_dates:
        shares = daily_sse.get(dt_str, {}).get(code)
        if shares is None:
            continue
        price = prices_map.get(code, {}).get(dt_str)  # 未追踪的ETF没有价格
        mcap = round(shares * price, 2) if price else None
        db.add(ETFShare(
            fund_code=code, trade_date=date.fromisoformat(dt_str),
            price=price, total_market_cap=mcap,
            shares=round(shares, 4), change_shares=None, source="sse_daily",
        ))
        count += 1
    if count > 0:
        total_count += count
    if count > 200:  # 只打印数据较多的
        print(f"  {code}: {count} 条")
    # 每50只ETF提交一次
    if total_count % 5000 < count:
        db.commit()

db.commit()
print(f"\n写入完成: {len(all_sh_codes)} 只ETF, {total_count} 条记录")

# 6. 补算已追踪ETF的change_shares
_calc_change_shares(db)
db.close()
print("\n✅ 上交所全部ETF每日精确份额回补完成")

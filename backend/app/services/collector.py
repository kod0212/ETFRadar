"""数据采集服务"""
import requests
import json
import re
import time
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import ETFFund, ETFShare, CollectLog


def fetch_etf_realtime(codes: list[dict]) -> list[dict]:
    """腾讯财经接口批量获取ETF实时数据(含总市值→份额)"""
    query = ",".join(f"{c['market']}{c['code']}" for c in codes)
    url = f"https://qt.gtimg.cn/q={query}"
    resp = requests.get(url, timeout=15)
    resp.encoding = "gbk"

    results = []
    for line in resp.text.strip().split(";"):
        line = line.strip()
        if not line or "~" not in line:
            continue
        fields = line.split("~")
        if len(fields) < 48:
            continue
        code = fields[2]
        name = fields[1]
        price = float(fields[3]) if fields[3] else 0
        total_mcap = float(fields[45]) if fields[45] else 0
        shares = round(total_mcap / price, 4) if price > 0 else 0
        results.append({
            "code": code, "name": name, "price": price,
            "total_market_cap": total_mcap, "shares": shares,
        })
    return results


def fetch_sse_shares() -> dict:
    """从AKShare获取上交所ETF当日份额(份)"""
    try:
        import akshare as ak
        df = ak.fund_etf_scale_sse()
        result = {}
        for _, row in df.iterrows():
            code = str(row["基金代码"]).strip()
            shares = float(row["基金份额"]) / 1e8  # 份→亿份
            result[code] = shares
        return result
    except Exception:
        return {}


def fetch_szse_shares() -> dict:
    """从AKShare获取深交所ETF当日份额(份)"""
    try:
        import akshare as ak
        df = ak.fund_scale_daily_szse()
        result = {}
        for _, row in df.iterrows():
            code = str(row["基金代码"]).strip()
            shares = float(row["基金份额"]) / 1e8  # 份→亿份
            result[code] = shares
        return result
    except Exception:
        return {}


def collect_today(db: Session = None) -> dict:
    """
    采集当天全部活跃ETF数据:
    1. 腾讯接口获取价格和市值
    2. 上交所/深交所接口获取精确份额
    3. 如果交易所份额获取失败，用市值/价格计算
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        if not funds:
            return {"status": "skipped", "message": "无活跃ETF"}

        # 1. 腾讯获取价格和市值
        codes = [{"code": f.code, "market": f.market} for f in funds]
        realtime = fetch_etf_realtime(codes)
        realtime_map = {item["code"]: item for item in realtime}

        # 2. 交易所获取精确份额
        sse_shares = fetch_sse_shares()
        szse_shares = fetch_szse_shares()
        exchange_shares = {**sse_shares, **szse_shares}

        today = date.today()
        count = 0

        for fund in funds:
            item = realtime_map.get(fund.code)
            if not item:
                continue

            # 优先用交易所份额，否则用市值/价格
            shares = exchange_shares.get(fund.code, item["shares"])
            mcap = round(shares * item["price"], 2) if shares and item["price"] else item["total_market_cap"]

            prev = db.query(ETFShare).filter(
                ETFShare.fund_code == fund.code,
                ETFShare.trade_date < today
            ).order_by(ETFShare.trade_date.desc()).first()
            change = round(shares - prev.shares, 4) if prev and prev.shares and shares else None

            source = "exchange" if fund.code in exchange_shares else "tencent"

            existing = db.query(ETFShare).filter(
                ETFShare.fund_code == fund.code,
                ETFShare.trade_date == today
            ).first()
            if existing:
                existing.price = item["price"]
                existing.total_market_cap = mcap
                existing.shares = shares
                existing.change_shares = change
                existing.source = source
                existing.created_at = datetime.now()
            else:
                db.add(ETFShare(
                    fund_code=fund.code, trade_date=today,
                    price=item["price"], total_market_cap=mcap,
                    shares=shares, change_shares=change, source=source,
                ))
            count += 1

        log = CollectLog(trade_date=today, status="success", fund_count=count,
                         message=f"采集 {count} 只ETF (交易所份额: {len(exchange_shares)} 只)")
        db.add(log)
        db.commit()
        return {"status": "success", "fund_count": count, "trade_date": str(today)}
    except Exception as e:
        db.rollback()
        log = CollectLog(trade_date=date.today(), status="failed", fund_count=0, message=str(e))
        db.add(log)
        db.commit()
        return {"status": "failed", "message": str(e)}
    finally:
        if own_session:
            db.close()


def backfill_history(days: int = 365):
    """
    回补历史数据:
    1. 从东方财富获取季度精确份额(用于插值)
    2. 从新浪获取每日价格
    3. 线性插值得到每日近似份额
    """
    db = SessionLocal()
    try:
        existing_count = db.query(ETFShare).count()
        if existing_count > 1:
            print(f"[backfill] etf_share 已有 {existing_count} 条数据，跳过")
            return

        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        if not funds:
            return

        for fund in funds:
            try:
                quarterly = _fetch_quarterly_shares(fund.code)
                if not quarterly:
                    print(f"[backfill] {fund.code} 无季度份额数据，跳过")
                    continue

                daily_prices = _fetch_sina_kline(fund.code, fund.market, days)
                if not daily_prices:
                    print(f"[backfill] {fund.code} 无历史价格，跳过")
                    continue

                records = []
                for dp in daily_prices:
                    trade_dt = date.fromisoformat(dp["day"])
                    price = dp["close"]
                    shares = _interpolate_shares(trade_dt, quarterly)
                    mcap = round(shares * price, 2) if shares else None

                    records.append(ETFShare(
                        fund_code=fund.code, trade_date=trade_dt,
                        price=price, total_market_cap=mcap,
                        shares=round(shares, 4) if shares else None,
                        change_shares=None, source="backfill",
                    ))

                for r in records:
                    existing = db.query(ETFShare).filter(
                        ETFShare.fund_code == r.fund_code,
                        ETFShare.trade_date == r.trade_date
                    ).first()
                    if not existing:
                        db.add(r)
                db.commit()
                print(f"[backfill] {fund.code} {fund.name}: {len(records)} 条")
                time.sleep(0.5)
            except Exception as e:
                db.rollback()
                print(f"[backfill] {fund.code} 失败: {e}")
                time.sleep(1)

        _calc_change_shares(db)
        print("[backfill] 历史数据回补完成")
    finally:
        db.close()


def _fetch_quarterly_shares(fund_code: str) -> list[dict]:
    """从东方财富获取季度份额数据"""
    url = f"https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=gmbd&mode=0&code={fund_code}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://fundf10.eastmoney.com/gmbd_{fund_code}.html",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    tds = re.findall(r'<td[^>]*>(.*?)</td>', resp.text)
    clean = [re.sub(r'<[^>]+>', '', c).strip() for c in tds]

    result = []
    for i in range(0, len(clean), 6):
        row = clean[i:i+6]
        if len(row) >= 4:
            try:
                dt = date.fromisoformat(row[0])
                shares = float(row[3].replace(',', ''))
                result.append({"date": dt, "shares": shares})
            except (ValueError, IndexError):
                continue
    result.sort(key=lambda x: x["date"])
    return result


def _interpolate_shares(target_date: date, quarterly: list[dict]) -> float:
    """用季度份额数据线性插值"""
    if not quarterly:
        return 0
    if target_date <= quarterly[0]["date"]:
        return quarterly[0]["shares"]
    if target_date >= quarterly[-1]["date"]:
        return quarterly[-1]["shares"]

    for i in range(len(quarterly) - 1):
        q1, q2 = quarterly[i], quarterly[i + 1]
        if q1["date"] <= target_date <= q2["date"]:
            total_days = (q2["date"] - q1["date"]).days
            elapsed = (target_date - q1["date"]).days
            if total_days == 0:
                return q1["shares"]
            return q1["shares"] + (q2["shares"] - q1["shares"]) * elapsed / total_days

    return quarterly[-1]["shares"]


def _fetch_sina_kline(code: str, market: str, datalen: int = 365) -> list[dict]:
    """新浪财经历史日K线"""
    symbol = f"{market}{code}"
    url = (
        f"https://quotes.sina.cn/cn/api/jsonp_v2.php/=/"
        f"CN_MarketDataService.getKLineData?symbol={symbol}"
        f"&scale=240&ma=no&datalen={datalen}"
    )
    resp = requests.get(url, timeout=15)
    match = re.search(r'=\((.*)\)', resp.text, re.DOTALL)
    if not match:
        return []
    data = json.loads(match.group(1))
    return [{"day": d["day"], "close": float(d["close"])} for d in data]


def _calc_change_shares(db: Session):
    """补算所有缺失的 change_shares"""
    funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
    for fund in funds:
        rows = db.query(ETFShare).filter(
            ETFShare.fund_code == fund.code,
            ETFShare.shares.isnot(None),
        ).order_by(ETFShare.trade_date).all()
        for i in range(1, len(rows)):
            if rows[i].change_shares is None and rows[i].shares and rows[i-1].shares:
                rows[i].change_shares = round(rows[i].shares - rows[i-1].shares, 4)
    db.commit()

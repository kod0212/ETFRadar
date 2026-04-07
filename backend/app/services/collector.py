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
    resp = requests.get(f"https://qt.gtimg.cn/q={query}", timeout=15)
    resp.encoding = "gbk"
    results = []
    for line in resp.text.strip().split(";"):
        line = line.strip()
        if not line or "~" not in line:
            continue
        fields = line.split("~")
        if len(fields) < 48:
            continue
        price = float(fields[3]) if fields[3] else 0
        total_mcap = float(fields[45]) if fields[45] else 0
        results.append({
            "code": fields[2], "name": fields[1], "price": price,
            "total_market_cap": total_mcap,
            "shares": round(total_mcap / price, 4) if price > 0 else 0,
        })
    return results


def fetch_sse_shares_by_date(dt: str) -> dict:
    """
    上交所ETF份额(按日期), dt格式: 20260403
    返回 {code: shares_yi, ...}
    """
    import akshare as ak
    try:
        df = ak.fund_etf_scale_sse(date=dt)
        result = {}
        for _, row in df.iterrows():
            code = str(row["基金代码"]).strip()
            result[code] = round(float(row["基金份额"]) / 1e8, 4)  # 份→亿份
        return result
    except Exception:
        return {}


def fetch_szse_shares() -> dict:
    """深交所ETF当日份额"""
    import akshare as ak
    try:
        df = ak.fund_scale_daily_szse()
        return {str(row["基金代码"]).strip(): round(float(row["基金份额"]) / 1e8, 4)
                for _, row in df.iterrows()}
    except Exception:
        return {}


def collect_today(db: Session = None) -> dict:
    """采集当天: 腾讯价格 + 交易所精确份额"""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        if not funds:
            return {"status": "skipped", "message": "无活跃ETF"}

        codes = [{"code": f.code, "market": f.market} for f in funds]
        realtime = {item["code"]: item for item in fetch_etf_realtime(codes)}

        today_str = date.today().strftime("%Y%m%d")
        exchange_shares = {**fetch_sse_shares_by_date(today_str), **fetch_szse_shares()}

        today = date.today()
        count = 0
        for fund in funds:
            item = realtime.get(fund.code)
            if not item:
                continue
            shares = exchange_shares.get(fund.code, item["shares"])
            mcap = round(shares * item["price"], 2) if shares and item["price"] else item["total_market_cap"]
            source = "exchange" if fund.code in exchange_shares else "tencent"

            prev = db.query(ETFShare).filter(
                ETFShare.fund_code == fund.code, ETFShare.trade_date < today
            ).order_by(ETFShare.trade_date.desc()).first()
            change = round(shares - prev.shares, 4) if prev and prev.shares and shares else None

            existing = db.query(ETFShare).filter(
                ETFShare.fund_code == fund.code, ETFShare.trade_date == today
            ).first()
            if existing:
                existing.price, existing.total_market_cap = item["price"], mcap
                existing.shares, existing.change_shares = shares, change
                existing.source, existing.created_at = source, datetime.now()
            else:
                db.add(ETFShare(
                    fund_code=fund.code, trade_date=today, price=item["price"],
                    total_market_cap=mcap, shares=shares, change_shares=change, source=source,
                ))
            count += 1

        db.add(CollectLog(trade_date=today, status="success", fund_count=count,
                          message=f"采集 {count} 只ETF"))
        db.commit()
        return {"status": "success", "fund_count": count, "trade_date": str(today)}
    except Exception as e:
        db.rollback()
        db.add(CollectLog(trade_date=date.today(), status="failed", fund_count=0, message=str(e)))
        db.commit()
        return {"status": "failed", "message": str(e)}
    finally:
        if own_session:
            db.close()


def backfill_history():
    """
    回补历史数据: 上交所每周精确份额 + 新浪每日价格
    上交所接口支持按日期查询历史份额(每次返回全部ETF)
    策略: 每周采样1次份额(周五), 配合每日价格, 份额在两次采样间线性插值
    """
    db = SessionLocal()
    try:
        if db.query(ETFShare).count() > 1:
            print("[backfill] etf_share 已有数据，跳过")
            return

        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        if not funds:
            return

        # 1. 获取每周五的上交所精确份额(约52周)
        print("[backfill] 获取上交所历史份额...")
        sample_dates = _get_weekly_dates(365)
        sse_history = {}  # {date_str: {code: shares_yi}}
        for dt_str in sample_dates:
            data = fetch_sse_shares_by_date(dt_str)
            if data:
                sse_history[dt_str] = data
                print(f"  {dt_str}: {len(data)} 只ETF")
            time.sleep(0.5)

        if not sse_history:
            print("[backfill] 无上交所历史数据")
            return

        # 2. 对每只ETF: 获取每日价格 + 插值份额
        for fund in funds:
            try:
                # 新浪每日价格
                prices = _fetch_sina_kline(fund.code, fund.market, 365)
                if not prices:
                    continue

                # 构建该ETF的份额时间序列(采样点)
                share_points = []
                for dt_str, shares_map in sorted(sse_history.items()):
                    if fund.code in shares_map:
                        share_points.append({
                            "date": date(int(dt_str[:4]), int(dt_str[4:6]), int(dt_str[6:])),
                            "shares": shares_map[fund.code],
                        })

                if not share_points:
                    print(f"[backfill] {fund.code} 无份额数据，跳过")
                    continue

                # 每日记录: 价格来自新浪, 份额在采样点间插值
                records = []
                for dp in prices:
                    trade_dt = date.fromisoformat(dp["day"])
                    price = dp["close"]
                    shares = _interpolate(trade_dt, share_points)
                    records.append(ETFShare(
                        fund_code=fund.code, trade_date=trade_dt, price=price,
                        total_market_cap=round(shares * price, 2),
                        shares=round(shares, 4), change_shares=None, source="backfill",
                    ))

                for r in records:
                    if not db.query(ETFShare).filter(
                        ETFShare.fund_code == r.fund_code, ETFShare.trade_date == r.trade_date
                    ).first():
                        db.add(r)
                db.commit()
                print(f"[backfill] {fund.code} {fund.name}: {len(records)} 条 (份额采样点: {len(share_points)})")
            except Exception as e:
                db.rollback()
                print(f"[backfill] {fund.code} 失败: {e}")

        _calc_change_shares(db)
        print("[backfill] 历史数据回补完成")
    finally:
        db.close()


def _get_weekly_dates(days: int) -> list[str]:
    """生成过去N天内每周五的日期列表"""
    result = []
    d = date.today()
    end = d - timedelta(days=days)
    while d > end:
        # 找到最近的周五 (weekday=4)
        offset = (d.weekday() - 4) % 7
        friday = d - timedelta(days=offset)
        dt_str = friday.strftime("%Y%m%d")
        if dt_str not in result:
            result.append(dt_str)
        d -= timedelta(days=7)
    return sorted(result)


def _interpolate(target: date, points: list[dict]) -> float:
    """线性插值"""
    if not points:
        return 0
    if target <= points[0]["date"]:
        return points[0]["shares"]
    if target >= points[-1]["date"]:
        return points[-1]["shares"]
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        if p1["date"] <= target <= p2["date"]:
            total = (p2["date"] - p1["date"]).days
            elapsed = (target - p1["date"]).days
            if total == 0:
                return p1["shares"]
            return p1["shares"] + (p2["shares"] - p1["shares"]) * elapsed / total
    return points[-1]["shares"]


def _fetch_sina_kline(code: str, market: str, datalen: int = 365) -> list[dict]:
    """新浪财经历史日K线"""
    symbol = f"{market}{code}"
    url = (f"https://quotes.sina.cn/cn/api/jsonp_v2.php/=/"
           f"CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=no&datalen={datalen}")
    resp = requests.get(url, timeout=15)
    match = re.search(r'=\((.*)\)', resp.text, re.DOTALL)
    if not match:
        return []
    return [{"day": d["day"], "close": float(d["close"])} for d in json.loads(match.group(1))]


def _calc_change_shares(db: Session):
    """补算 change_shares"""
    for fund in db.query(ETFFund).filter(ETFFund.is_active == True).all():
        rows = db.query(ETFShare).filter(
            ETFShare.fund_code == fund.code, ETFShare.shares.isnot(None),
        ).order_by(ETFShare.trade_date).all()
        for i in range(1, len(rows)):
            if rows[i].change_shares is None and rows[i].shares and rows[i - 1].shares:
                rows[i].change_shares = round(rows[i].shares - rows[i - 1].shares, 4)
    db.commit()

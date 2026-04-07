"""数据采集服务"""
import requests
import time
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.models import ETFFund, ETFShare, CollectLog


def fetch_etf_realtime(codes: list[dict]) -> list[dict]:
    """腾讯财经接口批量获取ETF实时数据"""
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


def collect_today(db: Session = None) -> dict:
    """采集当天全部活跃ETF数据并写入DB"""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        if not funds:
            return {"status": "skipped", "message": "无活跃ETF"}

        codes = [{"code": f.code, "market": f.market} for f in funds]
        data = fetch_etf_realtime(codes)
        today = date.today()
        count = 0

        for item in data:
            prev = db.query(ETFShare).filter(
                ETFShare.fund_code == item["code"],
                ETFShare.trade_date < today
            ).order_by(ETFShare.trade_date.desc()).first()
            change = round(item["shares"] - prev.shares, 4) if prev and prev.shares else None

            existing = db.query(ETFShare).filter(
                ETFShare.fund_code == item["code"],
                ETFShare.trade_date == today
            ).first()
            if existing:
                existing.price = item["price"]
                existing.total_market_cap = item["total_market_cap"]
                existing.shares = item["shares"]
                existing.change_shares = change
                existing.source = "tencent"
                existing.created_at = datetime.now()
            else:
                db.add(ETFShare(
                    fund_code=item["code"], trade_date=today,
                    price=item["price"], total_market_cap=item["total_market_cap"],
                    shares=item["shares"], change_shares=change, source="tencent",
                ))
            count += 1

        log = CollectLog(trade_date=today, status="success", fund_count=count,
                         message=f"采集 {count} 只ETF")
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


def backfill_history(days: int = 90):
    """
    回补历史数据:
    1. 先用腾讯接口获取当前份额(作为基准)
    2. 用AKShare获取历史价格
    3. 假设份额短期不变, 用基准份额 * 历史价格/当前价格 近似历史市值
       份额本身直接用基准值(ETF份额短期变化较小, 足够看趋势)
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

        # 1. 获取当前实时数据作为基准
        codes = [{"code": f.code, "market": f.market} for f in funds]
        realtime = fetch_etf_realtime(codes)
        baseline = {item["code"]: item for item in realtime}

        # 2. 用新浪财经回补历史价格 (不限流)
        for fund in funds:
            base = baseline.get(fund.code)
            if not base or base["price"] <= 0:
                print(f"[backfill] {fund.code} 无基准数据，跳过")
                continue

            try:
                hist = _fetch_sina_kline(fund.code, fund.market, days)
                if not hist:
                    continue

                records = []
                base_price = base["price"]
                base_mcap = base["total_market_cap"]

                for item in hist:
                    hist_price = item["close"]
                    est_mcap = round(base_mcap * hist_price / base_price, 2)
                    est_shares = round(est_mcap / hist_price, 4) if hist_price > 0 else None

                    from datetime import date as date_type
                    trade_dt = date_type.fromisoformat(item["day"])
                    records.append(ETFShare(
                        fund_code=fund.code,
                        trade_date=trade_dt,
                        price=hist_price,
                        total_market_cap=est_mcap,
                        shares=est_shares,
                        change_shares=None,
                        source="backfill",
                    ))

                # 批量写入
                for r in records:
                    existing = db.query(ETFShare).filter(
                        ETFShare.fund_code == r.fund_code,
                        ETFShare.trade_date == r.trade_date
                    ).first()
                    if not existing:
                        db.add(r)
                db.commit()
                print(f"[backfill] {fund.code} {fund.name}: {len(records)} 条")
                time.sleep(1)
            except Exception as e:
                db.rollback()
                print(f"[backfill] {fund.code} 失败: {e}")
                time.sleep(2)

        # 3. 补算 change_shares
        _calc_change_shares(db)
        print("[backfill] 历史数据回补完成")
    finally:
        db.close()


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


def _fetch_sina_kline(code: str, market: str, datalen: int = 90) -> list[dict]:
    """新浪财经历史日K线"""
    import json, re
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

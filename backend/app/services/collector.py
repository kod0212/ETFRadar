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
            # 查前一日份额算变化
            prev = db.query(ETFShare).filter(
                ETFShare.fund_code == item["code"],
                ETFShare.trade_date < today
            ).order_by(ETFShare.trade_date.desc()).first()
            change = round(item["shares"] - prev.shares, 4) if prev and prev.shares else None

            # upsert
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


def backfill_history(days: int = 60):
    """用AKShare回补历史行情数据（仅etf_share表为空时执行）"""
    db = SessionLocal()
    try:
        if db.query(ETFShare).count() > 0:
            print("[backfill] etf_share 已有数据，跳过历史回补")
            return

        import akshare as ak
        funds = db.query(ETFFund).filter(ETFFund.is_active == True).all()
        end = date.today().strftime("%Y%m%d")
        start = (date.today() - timedelta(days=days)).strftime("%Y%m%d")

        for fund in funds:
            try:
                df = ak.fund_etf_hist_em(
                    symbol=fund.code, period="daily",
                    start_date=start, end_date=end, adjust=""
                )
                for _, row in df.iterrows():
                    db.add(ETFShare(
                        fund_code=fund.code,
                        trade_date=row["日期"],
                        price=row["收盘"],
                        total_market_cap=None,
                        shares=None,
                        change_shares=None,
                        source="akshare",
                    ))
                db.commit()
                print(f"[backfill] {fund.code} {fund.name}: {len(df)} 条")
                time.sleep(1)  # 避免限流
            except Exception as e:
                db.rollback()
                print(f"[backfill] {fund.code} 失败: {e}")
                time.sleep(2)
    finally:
        db.close()

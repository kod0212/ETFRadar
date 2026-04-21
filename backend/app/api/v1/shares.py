"""API 路由 - 份额数据查询"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
from app.api.deps import get_db
from app.models.models import ETFShare, ETFFund
from app.schemas.share import ShareOut, ShareSummary, TrendPoint
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/shares", tags=["份额数据"])


@router.get("", response_model=ApiResponse)
def query_shares(
    code: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = Query(default=500, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(ETFShare)
    if code:
        q = q.filter(ETFShare.fund_code == code)
    if start:
        q = q.filter(ETFShare.trade_date >= start)
    if end:
        q = q.filter(ETFShare.trade_date <= end)
    rows = q.order_by(ETFShare.trade_date.desc(), ETFShare.fund_code).limit(limit).all()
    return ApiResponse(data=[ShareOut.model_validate(r) for r in rows])


@router.get("/latest", response_model=ApiResponse)
def latest_shares(db: Session = Depends(get_db)):
    """每只追踪ETF各自的最新一条记录"""
    from sqlalchemy import and_

    # 子查询：每只ETF的最新日期
    sub = db.query(
        ETFShare.fund_code,
        func.max(ETFShare.trade_date).label("max_date"),
    ).group_by(ETFShare.fund_code).subquery()

    # 一次查出所有最新记录
    funds = {f.code: f for f in db.query(ETFFund).all()}
    if not funds:
        return ApiResponse(data=[])

    rows = db.query(ETFShare).join(
        sub, and_(ETFShare.fund_code == sub.c.fund_code, ETFShare.trade_date == sub.c.max_date)
    ).filter(ETFShare.fund_code.in_(funds.keys())).all()

    data = []
    for row in rows:
        fund = funds.get(row.fund_code)
        if not fund:
            continue
        d = ShareOut.model_validate(row).model_dump()
        d["name"] = fund.name
        d["group_tag"] = fund.group_tag
        d["sys_tags"] = fund.sys_tags
        d["tags"] = fund.tags
        data.append(d)
    return ApiResponse(data=data)


@router.get("/summary", response_model=ApiResponse)
def shares_summary(
    group: Optional[str] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if not start:
        start = date.today() - timedelta(days=365)
    if not end:
        end = date.today()

    q = db.query(
        ETFFund.group_tag,
        ETFShare.trade_date,
        func.sum(ETFShare.shares).label("total_shares"),
    ).join(ETFFund, ETFShare.fund_code == ETFFund.code).filter(
        ETFShare.trade_date >= start,
        ETFShare.trade_date <= end,
        ETFShare.shares.isnot(None),
    )
    if group:
        q = q.filter(ETFFund.group_tag == group)
    rows = q.group_by(ETFFund.group_tag, ETFShare.trade_date).order_by(
        ETFShare.trade_date
    ).all()
    data = [ShareSummary(group_tag=r[0], trade_date=r[1], total_shares=round(r[2], 2)) for r in rows]
    return ApiResponse(data=data)


@router.get("/trend", response_model=ApiResponse)
def shares_trend(
    code: Optional[str] = None,
    codes: Optional[str] = Query(default=None, description="多个代码逗号分隔"),
    metric: str = Query(default="market_cap", description="market_cap 或 shares"),
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if not start:
        start = date.today() - timedelta(days=365)
    if not end:
        end = date.today()

    col = ETFShare.total_market_cap if metric == "market_cap" else ETFShare.shares

    if code:
        rows = db.query(ETFShare.trade_date, col).filter(
            ETFShare.fund_code == code,
            ETFShare.trade_date >= start,
            ETFShare.trade_date <= end,
            col.isnot(None),
        ).order_by(ETFShare.trade_date).all()
        data = [TrendPoint(trade_date=r[0], value=round(r[1], 2)) for r in rows]
    elif codes:
        code_list = [c.strip() for c in codes.split(",") if c.strip()]
        rows = db.query(
            ETFShare.trade_date,
            func.sum(col).label("total"),
            func.count(ETFShare.fund_code).label("cnt"),
        ).filter(
            ETFShare.fund_code.in_(code_list),
            ETFShare.trade_date >= start,
            ETFShare.trade_date <= end,
            col.isnot(None),
        ).group_by(ETFShare.trade_date).order_by(ETFShare.trade_date).all()
        # 只保留所有ETF都有数据的日期
        data = [TrendPoint(trade_date=r[0], value=round(r[1], 2))
                for r in rows if r[2] == len(code_list)]
    else:
        return ApiResponse(code=400, message="需要指定 code 或 codes 参数")

    return ApiResponse(data=data)

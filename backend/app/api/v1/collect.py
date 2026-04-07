"""API 路由 - 采集控制"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.api.deps import get_db
from app.models.models import CollectLog, ETFShare
from app.services.collector import incremental_update
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/collect", tags=["采集控制"])


@router.post("/trigger", response_model=ApiResponse)
def trigger_collect(db: Session = Depends(get_db)):
    result = incremental_update(db)
    return ApiResponse(data=result)


@router.get("/status", response_model=ApiResponse)
def collect_status(db: Session = Depends(get_db)):
    # 数据库最新日期
    max_date = db.query(func.max(ETFShare.trade_date)).scalar()
    logs = db.query(CollectLog).order_by(CollectLog.created_at.desc()).limit(10).all()
    data = {
        "latest_date": str(max_date) if max_date else None,
        "today": str(date.today()),
        "is_up_to_date": str(max_date) == str(date.today()) if max_date else False,
        "logs": [
            {"trade_date": str(l.trade_date), "status": l.status,
             "fund_count": l.fund_count, "message": l.message,
             "created_at": str(l.created_at)}
            for l in logs
        ],
    }
    return ApiResponse(data=data)

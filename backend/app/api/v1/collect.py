"""API 路由 - 采集控制"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.models import CollectLog
from app.services.collector import collect_today
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/collect", tags=["采集控制"])


@router.post("/trigger", response_model=ApiResponse)
def trigger_collect(db: Session = Depends(get_db)):
    result = collect_today(db)
    return ApiResponse(data=result)


@router.get("/status", response_model=ApiResponse)
def collect_status(db: Session = Depends(get_db)):
    logs = db.query(CollectLog).order_by(CollectLog.created_at.desc()).limit(10).all()
    data = [
        {"trade_date": str(l.trade_date), "status": l.status,
         "fund_count": l.fund_count, "message": l.message,
         "created_at": str(l.created_at)}
        for l in logs
    ]
    return ApiResponse(data=data)

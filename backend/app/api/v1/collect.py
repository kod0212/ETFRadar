import logging
logger = logging.getLogger(__name__)
"""API 路由 - 采集控制"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.api.deps import get_db
from app.models.models import CollectLog, ETFShare
from app.services.collector import incremental_update, get_update_status
from app.core.config import VERSION
from app.core.updater import check_update, do_update, get_progress
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/collect", tags=["采集控制"])


@router.post("/trigger", response_model=ApiResponse)
def trigger_collect(force: bool = False, db: Session = Depends(get_db)):
    """触发增量更新。force=true 跳过冷却（手动触发用）"""
    result = incremental_update(db, force=force)
    return ApiResponse(data=result)


@router.get("/status", response_model=ApiResponse)
def collect_status(db: Session = Depends(get_db)):
    # 数据库最新日期
    max_date = db.query(func.max(ETFShare.trade_date)).scalar()
    logs = db.query(CollectLog).order_by(CollectLog.created_at.desc()).limit(10).all()
    data = {
        "version": VERSION,
        "latest_date": str(max_date) if max_date else None,
        "today": str(date.today()),
        "is_up_to_date": str(max_date) == str(date.today()) if max_date else False,
        "update": get_update_status(),
        "logs": [
            {"trade_date": str(l.trade_date), "status": l.status,
             "fund_count": l.fund_count, "message": l.message,
             "created_at": str(l.created_at)}
            for l in logs
        ],
    }
    return ApiResponse(data=data)


@router.get("/check_update", response_model=ApiResponse)
def api_check_update():
    """检查是否有新版本"""
    info = check_update()
    if info:
        return ApiResponse(data={"has_update": True, **info})
    return ApiResponse(data={"has_update": False, "version": VERSION})


@router.post("/do_update", response_model=ApiResponse)
def api_do_update():
    """触发热更新"""
    info = check_update()
    if not info:
        return ApiResponse(data={"status": "up_to_date"})
    if info.get("update_type") == "cold":
        return ApiResponse(data={"status": "cold", "message": "此版本需要下载完整包", **info})
    do_update(info)
    return ApiResponse(data={"status": "started"})


@router.get("/update_progress", response_model=ApiResponse)
def api_update_progress():
    """获取更新进度"""
    return ApiResponse(data=get_progress())

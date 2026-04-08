"""API 路由 - ETF管理"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import requests
from app.api.deps import get_db
from app.models.models import ETFFund, ETFShare
from app.schemas.fund import FundCreate, FundUpdate, FundOut
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/funds", tags=["ETF管理"])


@router.get("/lookup", response_model=ApiResponse)
def lookup_fund(code: str = Query(..., description="6位基金代码"), db: Session = Depends(get_db)):
    """根据代码查询ETF信息（优先本地字典，回退腾讯接口）"""
    # 检查是否已追踪
    existing = db.query(ETFFund).filter(ETFFund.code == code).first()
    if existing:
        return ApiResponse(code=400, message=f"{code} 已在追踪列表中")

    # 1. 优先查本地字典表
    from app.models.models import ETFDict
    dict_entry = db.query(ETFDict).filter(ETFDict.code == code).first()
    if dict_entry:
        info = {"code": code, "name": dict_entry.name, "market": dict_entry.market}
    else:
        # 2. 回退腾讯接口
        info = _lookup_from_tencent(code)
        if not info:
            return ApiResponse(code=404, message=f"未找到基金 {code}")

    # 检查预置份额数据
    has_data = db.query(ETFShare).filter(ETFShare.fund_code == code).count()
    info["has_history"] = has_data > 0
    info["history_count"] = has_data
    return ApiResponse(data=info)


def _lookup_from_tencent(code: str) -> dict:
    for market in ["sh", "sz"]:
        try:
            resp = requests.get(f"https://qt.gtimg.cn/q={market}{code}", timeout=5)
            resp.encoding = "gbk"
            for line in resp.text.strip().split(";"):
                if "~" not in line:
                    continue
                fields = line.split("~")
                if len(fields) > 3 and fields[2] == code and fields[1]:
                    return {"code": code, "name": fields[1], "market": market}
        except Exception:
            continue
    return None


@router.get("", response_model=ApiResponse)
def list_funds(group_tag: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(ETFFund)
    if group_tag:
        q = q.filter(ETFFund.group_tag == group_tag)
    funds = q.order_by(ETFFund.code).all()
    return ApiResponse(data=[FundOut.model_validate(f) for f in funds])


@router.post("", response_model=ApiResponse)
def create_fund(body: FundCreate, db: Session = Depends(get_db)):
    if db.query(ETFFund).filter(ETFFund.code == body.code).first():
        raise HTTPException(400, f"ETF {body.code} 已存在")
    fund = ETFFund(**body.model_dump())
    db.add(fund)
    db.commit()
    db.refresh(fund)
    return ApiResponse(data=FundOut.model_validate(fund))


@router.put("/{code}", response_model=ApiResponse)
def update_fund(code: str, body: FundUpdate, db: Session = Depends(get_db)):
    fund = db.query(ETFFund).filter(ETFFund.code == code).first()
    if not fund:
        raise HTTPException(404, f"ETF {code} 不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(fund, k, v)
    db.commit()
    db.refresh(fund)
    return ApiResponse(data=FundOut.model_validate(fund))


@router.delete("/{code}", response_model=ApiResponse)
def delete_fund(code: str, db: Session = Depends(get_db)):
    fund = db.query(ETFFund).filter(ETFFund.code == code).first()
    if not fund:
        raise HTTPException(404, f"ETF {code} 不存在")
    db.delete(fund)
    db.commit()
    return ApiResponse(message=f"ETF {code} 已删除")

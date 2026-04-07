"""API 路由 - ETF管理"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.api.deps import get_db
from app.models.models import ETFFund
from app.schemas.fund import FundCreate, FundUpdate, FundOut
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/funds", tags=["ETF管理"])


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

from pydantic import BaseModel
from typing import Optional
from datetime import date


class ShareOut(BaseModel):
    fund_code: str
    trade_date: date
    price: Optional[float]
    total_market_cap: Optional[float]
    shares: Optional[float]
    change_shares: Optional[float]
    source: Optional[str]

    class Config:
        from_attributes = True


class ShareSummary(BaseModel):
    group_tag: str
    trade_date: date
    total_shares: float


class TrendPoint(BaseModel):
    trade_date: date
    value: float

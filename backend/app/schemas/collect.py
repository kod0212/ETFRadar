from pydantic import BaseModel
from typing import Optional
from datetime import date


class CollectResult(BaseModel):
    trade_date: date
    status: str
    fund_count: int
    message: Optional[str]

    class Config:
        from_attributes = True

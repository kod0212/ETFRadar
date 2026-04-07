from pydantic import BaseModel
from typing import Optional


class FundCreate(BaseModel):
    code: str
    name: str
    market: str  # sh / sz
    index_name: Optional[str] = None
    group_tag: Optional[str] = None


class FundUpdate(BaseModel):
    name: Optional[str] = None
    index_name: Optional[str] = None
    group_tag: Optional[str] = None
    is_active: Optional[bool] = None


class FundOut(BaseModel):
    code: str
    name: str
    market: str
    index_name: Optional[str]
    group_tag: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

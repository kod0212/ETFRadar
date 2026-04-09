"""SQLAlchemy ORM 模型"""
from sqlalchemy import Column, String, Float, Boolean, Integer, Date, DateTime, UniqueConstraint, Text
from datetime import datetime
from app.core.database import Base


class ETFFund(Base):
    __tablename__ = "etf_fund"

    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    market = Column(String(2), nullable=False)  # sh / sz
    index_name = Column(String(50))
    group_tag = Column(String(50))
    tags = Column(String(200))  # 用户自定义标签,逗号分隔
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ETFShare(Base):
    __tablename__ = "etf_share"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    price = Column(Float)
    total_market_cap = Column(Float)  # 亿元
    shares = Column(Float)  # 亿份
    change_shares = Column(Float)  # 份额变化(亿份)
    source = Column(String(20), default="tencent")
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("fund_code", "trade_date", name="uq_fund_date"),
    )


class ETFDict(Base):
    """ETF字典表 - 全部ETF代码和名称"""
    __tablename__ = "etf_dict"

    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    market = Column(String(2), nullable=False)
    index_name = Column(String(50))  # 跟踪指数/分组


class CollectLog(Base):
    __tablename__ = "collect_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False)
    status = Column(String(20))  # success / failed / partial
    fund_count = Column(Integer)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

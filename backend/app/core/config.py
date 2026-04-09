"""应用配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# exe 模式下数据目录在 exe 同级，否则在 backend/data
if os.environ.get("ETF_DATA_DIR"):
    DATA_DIR = Path(os.environ["ETF_DATA_DIR"])
else:
    DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'etf.db'}"

# 默认追踪的ETF列表
DEFAULT_ETFS = [
    {"code": "510300", "name": "华泰柏瑞沪深300ETF", "market": "sh", "index_name": "沪深300", "group_tag": "沪深300"},
    {"code": "510310", "name": "易方达沪深300ETF", "market": "sh", "index_name": "沪深300", "group_tag": "沪深300"},
    {"code": "159919", "name": "嘉实沪深300ETF", "market": "sz", "index_name": "沪深300", "group_tag": "沪深300"},
    {"code": "510330", "name": "华夏沪深300ETF", "market": "sh", "index_name": "沪深300", "group_tag": "沪深300"},
    {"code": "510500", "name": "南方中证500ETF", "market": "sh", "index_name": "中证500", "group_tag": "中证500"},
    {"code": "510050", "name": "华夏上证50ETF", "market": "sh", "index_name": "上证50", "group_tag": "上证50"},
    {"code": "159915", "name": "易方达创业板ETF", "market": "sz", "index_name": "创业板", "group_tag": "创业板"},
]

COLLECT_HOUR = 16
COLLECT_MINUTE = 5

VERSION = "1.0.1"

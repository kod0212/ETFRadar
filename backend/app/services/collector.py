"""数据采集服务 - 腾讯财经接口"""
import requests
from datetime import date


def fetch_etf_realtime(codes: list[dict]) -> list[dict]:
    """
    通过腾讯财经接口批量获取ETF实时数据

    Args:
        codes: [{"code": "510300", "market": "sh"}, ...]

    Returns:
        [{"code", "name", "price", "total_market_cap", "shares"}, ...]
    """
    query = ",".join(f"{c['market']}{c['code']}" for c in codes)
    url = f"https://qt.gtimg.cn/q={query}"
    resp = requests.get(url, timeout=15)
    resp.encoding = "gbk"

    results = []
    for line in resp.text.strip().split(";"):
        line = line.strip()
        if not line or "~" not in line:
            continue
        fields = line.split("~")
        if len(fields) < 48:
            continue

        code = fields[2]
        name = fields[1]
        price = float(fields[3]) if fields[3] else 0
        total_mcap = float(fields[45]) if fields[45] else 0  # 总市值(亿)
        shares = round(total_mcap / price, 4) if price > 0 else 0  # 份额(亿份)

        results.append({
            "code": code,
            "name": name,
            "price": price,
            "total_market_cap": total_mcap,
            "shares": shares,
        })
    return results

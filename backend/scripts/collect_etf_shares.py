"""
ETF数据采集验证脚本
验证各数据源能否稳定获取ETF份额/规模数据

验证结论 (2026-04-07):
======================
✅ AKShare fund_etf_hist_em  - ETF日线行情(价格/成交量/换手率), 可用, 数据来自东方财富
✅ 东方财富 push2 行情接口     - 可获取总市值(f116), 总市值/价格=份额, 有频率限制
✅ 东方财富 pingzhongdata     - 季度规模数据(Data_fluctuationScale), 粒度为季度
✅ 东方财富 ETF列表接口        - 可获取全部1415只ETF列表
✅ AKShare fund_open_fund_info_em - 单位净值走势, 可用
⚠️ 天天基金 FundSize API      - 对ETF(场内基金)返回404, 仅支持场外基金
⚠️ 东方财富 push2 接口        - 短时间频繁请求会被限流(RemoteDisconnected)

推荐数据采集方案:
  1. 每日份额 = 总市值 / 最新价 (通过东方财富行情接口, 控制请求频率)
  2. 历史行情用 AKShare fund_etf_hist_em
  3. 季度规模用 pingzhongdata Data_fluctuationScale 做校准
"""
import requests
import json
import time


TARGET_ETFS = [
    {"code": "510300", "name": "华泰柏瑞沪深300ETF", "secid": "1.510300"},
    {"code": "510310", "name": "易方达沪深300ETF", "secid": "1.510310"},
    {"code": "159919", "name": "嘉实沪深300ETF", "secid": "0.159919"},
    {"code": "510330", "name": "华夏沪深300ETF", "secid": "1.510330"},
    {"code": "510500", "name": "南方中证500ETF", "secid": "1.510500"},
    {"code": "510050", "name": "华夏上证50ETF", "secid": "1.510050"},
    {"code": "159915", "name": "易方达创业板ETF", "secid": "0.159915"},
]


def get_etf_shares_from_market_cap(secid: str) -> dict:
    """通过总市值/价格计算ETF份额"""
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {"secid": secid, "fields": "f57,f58,f43,f116,f117"}
    resp = requests.get(url, params=params, timeout=15)
    d = resp.json().get("data", {})
    price = d.get("f43", 0) / 1000
    mcap = d.get("f116", 0)
    shares_yi = mcap / price / 1e8 if price > 0 else 0
    return {
        "code": d.get("f57"),
        "name": d.get("f58"),
        "price": price,
        "market_cap_yi": round(mcap / 1e8, 2),
        "shares_yi": round(shares_yi, 2),
    }


def get_quarterly_scale(fund_code: str) -> list:
    """从东方财富pingzhongdata获取季度规模数据"""
    import re
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    resp = requests.get(url, headers=headers, timeout=10)
    match = re.search(r"var Data_fluctuationScale\s*=\s*(\{.*?\});", resp.text, re.DOTALL)
    if not match:
        return []
    data = json.loads(match.group(1))
    result = []
    for date, item in zip(data.get("categories", []), data.get("series", [])):
        result.append({"date": date, "scale_yi": item["y"], "mom": item["mom"]})
    return result


def get_etf_hist(symbol: str, start: str, end: str):
    """AKShare获取ETF日线行情"""
    import akshare as ak
    return ak.fund_etf_hist_em(symbol=symbol, period="daily",
                                start_date=start, end_date=end, adjust="")


if __name__ == "__main__":
    print("🔍 ETF数据源验证\n")

    # 测试1: AKShare ETF日线行情
    print("=" * 50)
    print("1. AKShare fund_etf_hist_em")
    print("=" * 50)
    try:
        df = get_etf_hist("510300", "20260401", "20260407")
        print(f"✅ 返回 {len(df)} 条, 字段: {list(df.columns)}")
        print(df.tail(3).to_string(index=False))
    except Exception as e:
        print(f"❌ {e}")
    print()

    time.sleep(2)

    # 测试2: 季度规模数据
    print("=" * 50)
    print("2. 东方财富 pingzhongdata 季度规模")
    print("=" * 50)
    try:
        scale = get_quarterly_scale("510300")
        print(f"✅ 返回 {len(scale)} 条季度数据:")
        for s in scale:
            print(f"  {s['date']}  规模: {s['scale_yi']}亿元  环比: {s['mom']}")
    except Exception as e:
        print(f"❌ {e}")
    print()

    time.sleep(2)

    # 测试3: 实时市值->份额
    print("=" * 50)
    print("3. 东方财富行情接口 (市值->份额)")
    print("=" * 50)
    try:
        result = get_etf_shares_from_market_cap("1.510300")
        print(f"✅ {result['code']} {result['name']}")
        print(f"   价格: {result['price']:.3f}元")
        print(f"   总市值: {result['market_cap_yi']}亿元")
        print(f"   估算份额: {result['shares_yi']}亿份")
    except Exception as e:
        print(f"❌ {e}")

    print("\n🏁 验证完成")

# ==========================================
# tools/us_stock.py
# yfinance 기반 미국 주식 종가 수집
# @tool 데코레이터로 LangChain Tool Calling 지원
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import yfinance as yf
from langchain.tools import tool


US_SECTOR_ETF = {
    "AI 반도체"  : "SOXX",
    "기술주"     : "XLK",
    "헬스케어"   : "XLV",
    "에너지"     : "XLE",
    "금융"       : "XLF",
    "소비재"     : "XLY",
    "필수소비재"  : "XLP",
    "산업재"     : "XLI",
    "유틸리티"   : "XLU",
    "부동산/리츠" : "XLRE",
    "소재"       : "XLB",
    "통신"       : "XLC",
}


@tool
def get_us_stock_price(tickers_json: str) -> str:
    """
    미국 주식 종목의 최근 종가를 수집합니다.
    Args:
        tickers_json: JSON 배열 문자열 (예: '["AAPL", "NVDA", "VOO"]')
    Returns:
        종목별 종가 정보 JSON 문자열
    """
    tickers = json.loads(tickers_json)
    result  = {}

    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(period="5d")

            if hist.empty:
                result[ticker] = {"error": "데이터 없음", "close": None}
                continue

            latest      = hist.iloc[-1]
            latest_date = hist.index[-1].strftime("%Y-%m-%d")

            try:
                name = t.info.get("longName") or t.info.get("shortName") or ticker
            except Exception:
                name = ticker

            result[ticker] = {
                "name"  : name,
                "close" : round(float(latest["Close"]), 2),
                "open"  : round(float(latest["Open"]), 2),
                "high"  : round(float(latest["High"]), 2),
                "low"   : round(float(latest["Low"]), 2),
                "volume": int(latest["Volume"]),
                "date"  : latest_date,
                "source": "Yahoo Finance (yfinance)",
            }

        except Exception as e:
            result[ticker] = {"error": str(e), "close": None}

    return json.dumps(result, ensure_ascii=False)


@tool
def get_us_sector_trend(period_weeks: int = 4) -> str:
    """
    미국 섹터 ETF 기반 섹터 트렌드를 수집합니다.
    Args:
        period_weeks: 분석 기간 (주, 기본값 4)
    Returns:
        섹터별 트렌드 정보 JSON 문자열
    """
    period_str = f"{period_weeks * 7}d"
    result     = {}

    for sector_name, etf_ticker in US_SECTOR_ETF.items():
        try:
            t    = yf.Ticker(etf_ticker)
            hist = t.history(period=period_str)

            if hist.empty or len(hist) < 2:
                result[sector_name] = {"error": "데이터 없음", "trend": "NEUTRAL"}
                continue

            start_price = float(hist.iloc[0]["Close"])
            end_price   = float(hist.iloc[-1]["Close"])
            change_pct  = round((end_price - start_price) / start_price * 100, 2)

            if change_pct >= 5.0:
                trend = "UPTREND"
            elif change_pct <= -5.0:
                trend = "DOWNTREND"
            else:
                trend = "NEUTRAL"

            result[sector_name] = {
                "etf_ticker"  : etf_ticker,
                "change_pct"  : change_pct,
                "trend"       : trend,
                "start_price" : round(start_price, 2),
                "end_price"   : round(end_price, 2),
                "period_weeks": period_weeks,
                "market"      : "US",
                "source"      : f"Yahoo Finance ETF ({etf_ticker})",
            }

        except Exception as e:
            result[sector_name] = {"error": str(e), "trend": "NEUTRAL"}

    return json.dumps(result, ensure_ascii=False)


# 기존 함수 방식도 유지
def get_us_stock_price_direct(tickers: list) -> dict:
    return json.loads(get_us_stock_price.invoke(json.dumps(tickers)))

def get_us_sector_trend_direct(period_weeks: int = 4) -> dict:
    return json.loads(get_us_sector_trend.invoke(period_weeks))


if __name__ == "__main__":
    print("=== @tool 기반 미국 주식 종가 조회 ===")
    result = get_us_stock_price.invoke('["AAPL", "NVDA", "VOO"]')
    print(result)

    print("\n=== @tool 기반 미국 섹터 트렌드 조회 ===")
    result = get_us_sector_trend.invoke(4)
    data   = json.loads(result)
    for sector, info in data.items():
        if "error" not in info:
            print(f"  {sector:12s}: {info.get('change_pct', 'N/A'):>+6.2f}%  [{info.get('trend')}]")
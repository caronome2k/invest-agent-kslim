# ==========================================
# tools/kr_stock.py
# pykrx 기반 한국 주식 종가 수집
# @tool 데코레이터로 LangChain Tool Calling 지원
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pykrx import stock
from datetime import datetime, timedelta
from langchain.tools import tool
import yfinance as yf


def _get_recent_trading_date(days_back: int = 7) -> tuple:
    today   = datetime.today()
    from_dt = (today - timedelta(days=days_back)).strftime("%Y%m%d")
    to_dt   = today.strftime("%Y%m%d")
    return from_dt, to_dt


@tool
def get_kr_stock_price(tickers_json: str) -> str:
    """
    한국 주식 종목의 최근 종가를 수집합니다.
    Args:
        tickers_json: JSON 배열 문자열 (예: '["005930", "000660"]')
    Returns:
        종목별 종가 정보 JSON 문자열
    """
    tickers = json.loads(tickers_json)
    from_dt, to_dt = _get_recent_trading_date()
    result = {}

    for ticker in tickers:
        try:
            df = stock.get_market_ohlcv_by_date(from_dt, to_dt, ticker)
            if df.empty:
                result[ticker] = {"error": "데이터 없음", "close": None}
                continue

            latest      = df.iloc[-1]
            latest_date = df.index[-1].strftime("%Y-%m-%d")

            try:
                name = stock.get_market_ticker_name(ticker)
            except Exception:
                name = ticker

            result[ticker] = {
                "name"  : name,
                "close" : float(latest["종가"]),
                "open"  : float(latest["시가"]),
                "high"  : float(latest["고가"]),
                "low"   : float(latest["저가"]),
                "volume": int(latest["거래량"]),
                "date"  : latest_date,
                "source": "KRX (pykrx)",
            }

        except Exception as e:
            result[ticker] = {"error": str(e), "close": None}

    return json.dumps(result, ensure_ascii=False)


# 한국 섹터 대표 ETF
KR_SECTOR_ETF = {
    "KOSPI 전체"     : "069500.KS",
    "반도체/IT"      : "091160.KS",
    "바이오/헬스케어" : "143860.KS",
    "2차전지"        : "305720.KS",
    "금융"           : "091170.KS",
    "소비재"         : "228790.KS",
    "KOSDAQ 전체"    : "229200.KS",
}


@tool
def get_kr_sector_index(period_weeks: int = 4) -> str:
    """
    한국 섹터 ETF 기반 섹터 트렌드를 수집합니다.
    Args:
        period_weeks: 분석 기간 (주, 기본값 4)
    Returns:
        섹터별 트렌드 정보 JSON 문자열
    """
    period_str = f"{period_weeks * 7}d"
    result     = {}

    for sector_name, etf_ticker in KR_SECTOR_ETF.items():
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
                "change_pct"  : change_pct,
                "trend"       : trend,
                "start_price" : round(start_price, 0),
                "end_price"   : round(end_price, 0),
                "period_weeks": period_weeks,
                "market"      : "KR",
                "source"      : f"KRX ETF yfinance ({etf_ticker})",
            }

        except Exception as e:
            result[sector_name] = {"error": str(e), "trend": "NEUTRAL"}

    return json.dumps(result, ensure_ascii=False)


# 기존 함수 방식도 유지 (다른 모듈에서 직접 호출용)
def get_kr_stock_price_direct(tickers: list) -> dict:
    return json.loads(get_kr_stock_price.invoke(json.dumps(tickers)))

def get_kr_sector_index_direct(period_weeks: int = 4) -> dict:
    return json.loads(get_kr_sector_index.invoke(period_weeks))


if __name__ == "__main__":
    print("=== @tool 기반 한국 주식 종가 조회 ===")
    result = get_kr_stock_price.invoke('["005930", "000660"]')
    print(result)

    print("\n=== @tool 기반 한국 섹터 트렌드 조회 ===")
    result = get_kr_sector_index.invoke(4)
    data   = json.loads(result)
    for sector, info in data.items():
        if "error" not in info:
            print(f"  {sector:15s}: {info.get('change_pct', 'N/A'):>+6.2f}%  [{info.get('trend')}]")
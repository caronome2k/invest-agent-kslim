# ==========================================
# tools/kr_stock.py
# pykrx 기반 한국 주식 종가 수집
# 섹터 트렌드는 yfinance KRX ETF 기반으로 대체
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pykrx import stock
from datetime import datetime, timedelta
import yfinance as yf


def _get_recent_trading_date(days_back: int = 7) -> tuple:
    """최근 거래일 범위 반환"""
    today   = datetime.today()
    from_dt = (today - timedelta(days=days_back)).strftime("%Y%m%d")
    to_dt   = today.strftime("%Y%m%d")
    return from_dt, to_dt


def get_kr_stock_price(tickers: list) -> dict:
    """
    한국 주식 종목의 최근 종가를 수집합니다. (pykrx)
    """
    from_dt, to_dt = _get_recent_trading_date()
    result = {}

    for ticker in tickers:
        try:
            df = stock.get_market_ohlcv_by_date(from_dt, to_dt, ticker)
            if df.empty:
                result[ticker] = {"error": "데이터 없음", "close": None, "date": None}
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
            result[ticker] = {"error": str(e), "close": None, "date": None}

    return result


# 한국 섹터 대표 ETF (yfinance 티커)
KR_SECTOR_ETF = {
    "KOSPI 전체"  : "069500.KS",   # KODEX 200
    "반도체/IT"   : "091160.KS",   # KODEX 반도체
    "바이오/헬스케어": "143860.KS", # KOSEF 헬스케어
    "2차전지"     : "305720.KS",   # KODEX 2차전지산업
    "금융"        : "091170.KS",   # KODEX 은행
    "소비재"      : "228790.KS",   # KODEX 소비재
    "KOSDAQ 전체" : "229200.KS",   # KODEX 코스닥150
}


def get_kr_sector_index(period_weeks: int = 4) -> dict:
    """
    한국 섹터 ETF 기반 섹터 트렌드를 수집합니다. (yfinance)
    pykrx get_index_ohlcv_by_date 로그인 문제로 yfinance ETF로 대체
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

    return result


# ------------------------------------------
# 동작 확인용
# ------------------------------------------
if __name__ == "__main__":
    print("=== 한국 주식 종가 조회 ===")
    prices = get_kr_stock_price(["005930", "000660"])
    for ticker, data in prices.items():
        print(f"  {ticker}: {data}")

    print("\n=== 한국 섹터 트렌드 조회 (4주) ===")
    sectors = get_kr_sector_index(period_weeks=4)
    for sector, data in sectors.items():
        if "error" in data:
            print(f"  {sector:15s}: 오류 - {data['error']}")
        else:
            print(f"  {sector:15s}: {data.get('change_pct', 'N/A'):>+6.2f}%  [{data.get('trend')}]")
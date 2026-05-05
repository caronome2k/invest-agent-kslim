# ==========================================
# tools/us_stock.py
# yfinance 기반 미국 주식 종가 수집
# ==========================================

import yfinance as yf
from datetime import datetime, timedelta


# 미국 섹터 ETF 코드 매핑
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


def get_us_stock_price(tickers: list[str]) -> dict:
    """
    미국 주식 종목의 최근 종가를 수집합니다.

    Args:
        tickers: 티커 리스트 (예: ["AAPL", "NVDA", "VOO"])

    Returns:
        {
            "AAPL": {"name": "Apple Inc.", "close": 189.5, "date": "2025-04-28"},
            ...
        }
    """
    result = {}

    for ticker in tickers:
        try:
            t    = yf.Ticker(ticker)
            hist = t.history(period="5d")   # 최근 5거래일 (주말 대비 여유)

            if hist.empty:
                result[ticker] = {"error": "데이터 없음", "close": None, "date": None}
                continue

            latest      = hist.iloc[-1]
            latest_date = hist.index[-1].strftime("%Y-%m-%d")

            # 종목명 조회
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
            result[ticker] = {"error": str(e), "close": None, "date": None}

    return result


def get_us_sector_trend(period_weeks: int = 4) -> dict:
    """
    미국 섹터 ETF 기반 섹터 트렌드를 수집합니다.

    Args:
        period_weeks: 분석 기간 (주)

    Returns:
        {
            "AI 반도체": {"change_pct": 18.2, "trend": "UPTREND", ...},
            ...
        }
    """
    period_str = f"{period_weeks * 7}d"
    result     = {}

    for sector_name, etf_ticker in US_SECTOR_ETF.items():
        try:
            t    = yf.Ticker(etf_ticker)
            hist = t.history(period=period_str)

            if hist.empty or len(hist) < 2:
                continue

            start_price = float(hist.iloc[0]["Close"])
            end_price   = float(hist.iloc[-1]["Close"])
            change_pct  = round((end_price - start_price) / start_price * 100, 2)

            # 트렌드 분류
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

    return result


# ------------------------------------------
# 동작 확인용
# ------------------------------------------
if __name__ == "__main__":
    print("=== 미국 주식 종가 조회 ===")
    prices = get_us_stock_price(["AAPL", "NVDA", "VOO"])
    for ticker, data in prices.items():
        print(f"  {ticker}: {data}")

    print("\n=== 미국 섹터 트렌드 조회 (4주) ===")
    sectors = get_us_sector_trend(period_weeks=4)
    for sector, data in sectors.items():
        print(f"  {sector:12s}: {data.get('change_pct', 'N/A'):>6}%  [{data.get('trend', 'N/A')}]")

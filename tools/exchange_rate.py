# ==========================================
# tools/exchange_rate.py
# yfinance 기반 USD/KRW 환율 수집
# pykrx get_exchange_rate_ohlcv_by_date 미지원으로 yfinance 대체
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
from datetime import datetime


def get_exchange_rate() -> dict:
    """
    yfinance 기반 USD/KRW 환율 수집
    티커: USDKRW=X (Yahoo Finance 환율 티커)

    Returns:
        {
            "USD_KRW"     : 1382.0,
            "prev_USD_KRW": 1387.0,
            "change"      : -5.0,
            "change_dir"  : "▼",
            "date"        : "2025-04-28",
            "source"      : "Yahoo Finance"
        }
    """
    try:
        ticker = yf.Ticker("USDKRW=X")
        hist   = ticker.history(period="5d")   # 최근 5거래일

        if hist.empty:
            raise ValueError("환율 데이터를 가져올 수 없습니다.")

        latest      = hist.iloc[-1]
        prev        = hist.iloc[-2] if len(hist) >= 2 else latest
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        usd_krw      = round(float(latest["Close"]), 2)
        prev_usd_krw = round(float(prev["Close"]), 2)
        change       = round(usd_krw - prev_usd_krw, 2)

        return {
            "USD_KRW"     : usd_krw,
            "prev_USD_KRW": prev_usd_krw,
            "change"      : change,
            "change_dir"  : "▲" if change > 0 else ("▼" if change < 0 else "-"),
            "date"        : latest_date,
            "source"      : "Yahoo Finance (USDKRW=X)",
        }

    except Exception as e:
        return {
            "USD_KRW"     : 1350.0,
            "prev_USD_KRW": 1350.0,
            "change"      : 0.0,
            "change_dir"  : "-",
            "date"        : datetime.today().strftime("%Y-%m-%d"),
            "source"      : "FALLBACK",
            "error"       : str(e),
        }


def convert_usd_to_krw(usd_amount: float, rate: float) -> float:
    """USD 금액을 KRW로 환산합니다."""
    return round(usd_amount * rate, 0)


def calc_fx_impact(
    us_invest_krw: float,
    total_invest_krw: float,
    prev_rate: float,
    curr_rate: float,
) -> float:
    """
    환율 변동이 전체 포트폴리오 수익률에 미치는 영향 계산 (%)
    """
    if total_invest_krw == 0 or prev_rate == 0:
        return 0.0
    fx_effect = (curr_rate - prev_rate) / prev_rate * 100
    us_weight = us_invest_krw / total_invest_krw
    return round(fx_effect * us_weight, 2)


# ------------------------------------------
# 동작 확인용
# ------------------------------------------
if __name__ == "__main__":
    print("=== USD/KRW 환율 조회 ===")
    rate = get_exchange_rate()
    for key, value in rate.items():
        print(f"  {key:15s}: {value}")

    print("\n=== USD → KRW 환산 예시 ===")
    usd = 1000.0
    krw = convert_usd_to_krw(usd, rate["USD_KRW"])
    print(f"  ${usd:,.2f} → {krw:,.0f}원  (환율: {rate['USD_KRW']})")
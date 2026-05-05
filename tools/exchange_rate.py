# ==========================================
# tools/exchange_rate.py
# yfinance 기반 USD/KRW 환율 수집
# @tool 데코레이터로 LangChain Tool Calling 지원
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import yfinance as yf
from datetime import datetime
from langchain.tools import tool


@tool
def get_exchange_rate(dummy: str = "") -> str:
    """
    USD/KRW 환율을 수집합니다. (Yahoo Finance USDKRW=X)
    Args:
        dummy: 사용하지 않음 (tool 인터페이스 호환용)
    Returns:
        환율 정보 JSON 문자열
    """
    try:
        ticker = yf.Ticker("USDKRW=X")
        hist   = ticker.history(period="5d")

        if hist.empty:
            raise ValueError("환율 데이터를 가져올 수 없습니다.")

        latest      = hist.iloc[-1]
        prev        = hist.iloc[-2] if len(hist) >= 2 else latest
        latest_date = hist.index[-1].strftime("%Y-%m-%d")

        usd_krw      = round(float(latest["Close"]), 2)
        prev_usd_krw = round(float(prev["Close"]), 2)
        change       = round(usd_krw - prev_usd_krw, 2)

        result = {
            "USD_KRW"     : usd_krw,
            "prev_USD_KRW": prev_usd_krw,
            "change"      : change,
            "change_dir"  : "▲" if change > 0 else ("▼" if change < 0 else "-"),
            "date"        : latest_date,
            "source"      : "Yahoo Finance (USDKRW=X)",
        }

    except Exception as e:
        result = {
            "USD_KRW"     : 1350.0,
            "prev_USD_KRW": 1350.0,
            "change"      : 0.0,
            "change_dir"  : "-",
            "date"        : datetime.today().strftime("%Y-%m-%d"),
            "source"      : "FALLBACK",
            "error"       : str(e),
        }

    return json.dumps(result, ensure_ascii=False)


def convert_usd_to_krw(usd_amount: float, rate: float) -> float:
    """USD 금액을 KRW로 환산합니다."""
    return round(usd_amount * rate, 0)


def calc_fx_impact(
    us_invest_krw   : float,
    total_invest_krw: float,
    prev_rate       : float,
    curr_rate       : float,
) -> float:
    """환율 변동이 전체 포트폴리오 수익률에 미치는 영향 계산 (%)"""
    if total_invest_krw == 0 or prev_rate == 0:
        return 0.0
    fx_effect = (curr_rate - prev_rate) / prev_rate * 100
    us_weight = us_invest_krw / total_invest_krw
    return round(fx_effect * us_weight, 2)


# 기존 함수 방식도 유지
def get_exchange_rate_direct() -> dict:
    return json.loads(get_exchange_rate.invoke(""))


if __name__ == "__main__":
    print("=== @tool 기반 환율 조회 ===")
    result = get_exchange_rate.invoke("")
    data   = json.loads(result)
    for key, value in data.items():
        print(f"  {key:15s}: {value}")
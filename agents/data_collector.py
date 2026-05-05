# ==========================================
# agents/data_collector.py
# 데이터 수집 Agent
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import PortfolioState
from tools.kr_stock import get_kr_stock_price
from tools.us_stock import get_us_stock_price
from tools.exchange_rate import get_exchange_rate
from utils.parser import get_kr_tickers, get_us_tickers


def data_collector_node(state: PortfolioState) -> PortfolioState:
    holdings = state.get("holdings", [])

    if not holdings:
        state["error_log"].append("[data_collector] 보유 종목 없음")
        return state

    kr_tickers = get_kr_tickers(holdings)
    us_tickers = get_us_tickers(holdings)
    market_data = {}

    if kr_tickers:
        try:
            market_data["KR"] = get_kr_stock_price(kr_tickers)
        except Exception as e:
            state["error_log"].append(f"[data_collector] 한국 주식 수집 오류: {str(e)}")
            market_data["KR"] = {}

    if us_tickers:
        try:
            market_data["US"] = get_us_stock_price(us_tickers)
        except Exception as e:
            state["error_log"].append(f"[data_collector] 미국 주식 수집 오류: {str(e)}")
            market_data["US"] = {}

    try:
        exchange_rate = get_exchange_rate()
    except Exception as e:
        state["error_log"].append(f"[data_collector] 환율 수집 오류: {str(e)}")
        exchange_rate = {"USD_KRW": 1350.0, "source": "FALLBACK"}

    state["market_data"]   = market_data
    state["exchange_rate"] = exchange_rate
    return state


if __name__ == "__main__":
    from agents.state import create_initial_state

    sample_holdings = [
        {"ticker": "005930", "name": "삼성전자",   "market": "KOSPI",  "sector": "반도체",
         "quantity": 50, "avg_price": 71000,  "currency": "KRW", "buy_date": "2023-03-15", "memo": None},
        {"ticker": "AAPL",   "name": "Apple Inc.", "market": "NASDAQ", "sector": "기술주",
         "quantity": 10, "avg_price": 178.5,  "currency": "USD", "buy_date": "2023-01-10", "memo": None},
    ]

    state  = create_initial_state(user_input="브리핑", holdings=sample_holdings)
    result = data_collector_node(state)

    print("=== 데이터 수집 결과 ===")
    print(f"환율: {result['exchange_rate']}")
    print(f"\n한국 주식:")
    for ticker, data in result["market_data"].get("KR", {}).items():
        print(f"  {ticker}: {data}")
    print(f"\n미국 주식:")
    for ticker, data in result["market_data"].get("US", {}).items():
        print(f"  {ticker}: {data}")
    if result["error_log"]:
        print(f"\n오류: {result['error_log']}")
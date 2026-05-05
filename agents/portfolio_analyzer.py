# ==========================================
# agents/portfolio_analyzer.py
# 포트폴리오 분석 Agent
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import PortfolioState, HoldingAnalysis
from tools.exchange_rate import convert_usd_to_krw


def portfolio_analyzer_node(state: PortfolioState) -> PortfolioState:
    holdings      = state.get("holdings", [])
    market_data   = state.get("market_data", {})
    exchange_rate = state.get("exchange_rate", {})
    usd_krw       = exchange_rate.get("USD_KRW", 1350.0)

    holdings_analysis = []
    total_invest_krw  = 0.0
    total_eval_krw    = 0.0
    us_invest_krw     = 0.0

    for holding in holdings:
        ticker    = holding["ticker"]
        currency  = holding["currency"]
        qty       = holding["quantity"]
        avg_price = holding["avg_price"]

        if currency == "KRW":
            price_data        = market_data.get("KR", {}).get(ticker, {})
            current_price     = price_data.get("close") or avg_price
            current_price_krw = current_price
            avg_price_krw     = avg_price
        else:
            price_data        = market_data.get("US", {}).get(ticker, {})
            current_price     = price_data.get("close") or avg_price
            current_price_krw = convert_usd_to_krw(current_price, usd_krw)
            avg_price_krw     = convert_usd_to_krw(avg_price, usd_krw)

        eval_amount_krw   = current_price_krw * qty
        invest_amount_krw = avg_price_krw * qty
        return_pct        = round(
            (eval_amount_krw - invest_amount_krw) / invest_amount_krw * 100, 2
        ) if invest_amount_krw > 0 else 0.0

        analysis = {
            "ticker"            : ticker,
            "name"              : holding["name"],
            "market"            : holding["market"],
            "sector"            : holding["sector"],
            "current_price"     : current_price,
            "current_price_krw" : current_price_krw,
            "avg_price"         : avg_price,
            "avg_price_krw"     : avg_price_krw,
            "quantity"          : qty,
            "eval_amount_krw"   : eval_amount_krw,
            "invest_amount_krw" : invest_amount_krw,
            "return_pct"        : return_pct,
            "sector_trend"      : "NEUTRAL",
            "currency"          : currency,
        }
        holdings_analysis.append(analysis)
        total_invest_krw += invest_amount_krw
        total_eval_krw   += eval_amount_krw
        if currency == "USD":
            us_invest_krw += invest_amount_krw

    total_return_pct = round(
        (total_eval_krw - total_invest_krw) / total_invest_krw * 100, 2
    ) if total_invest_krw > 0 else 0.0

    prev_usd_krw  = exchange_rate.get("prev_USD_KRW", usd_krw)
    fx_change_pct = (usd_krw - prev_usd_krw) / prev_usd_krw * 100 if prev_usd_krw > 0 else 0.0
    us_weight     = us_invest_krw / total_invest_krw if total_invest_krw > 0 else 0.0
    fx_return_pct = round(total_return_pct + fx_change_pct * us_weight, 2)

    state["holdings_analysis"] = holdings_analysis
    state["total_invest_krw"]  = total_invest_krw
    state["total_eval_krw"]    = total_eval_krw
    state["total_return_pct"]  = total_return_pct
    state["fx_return_pct"]     = fx_return_pct
    return state


if __name__ == "__main__":
    from agents.state import create_initial_state
    from agents.data_collector import data_collector_node

    sample_holdings = [
        {"ticker": "005930", "name": "삼성전자",   "market": "KOSPI",  "sector": "반도체",
         "quantity": 50, "avg_price": 71000, "currency": "KRW", "buy_date": "2023-03-15", "memo": None},
        {"ticker": "AAPL",   "name": "Apple Inc.", "market": "NASDAQ", "sector": "기술주",
         "quantity": 10, "avg_price": 178.5, "currency": "USD", "buy_date": "2023-01-10", "memo": None},
    ]

    state  = create_initial_state(user_input="브리핑", holdings=sample_holdings)
    state  = data_collector_node(state)
    result = portfolio_analyzer_node(state)

    print("=== 포트폴리오 분석 결과 ===")
    print(f"총 투자 원금    : {result['total_invest_krw']:>15,.0f} 원")
    print(f"총 평가 금액    : {result['total_eval_krw']:>15,.0f} 원")
    print(f"전체 수익률     : {result['total_return_pct']:>+.2f}%")
    print(f"환율 조정 수익률: {result['fx_return_pct']:>+.2f}%")
    print(f"\n종목별 분석:")
    for h in result["holdings_analysis"]:
        print(f"  {h['ticker']:8s} {h['name']:15s} 수익률: {h['return_pct']:>+.2f}%")
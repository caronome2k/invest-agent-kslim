# ==========================================
# agents/data_collector.py
# 데이터 수집 Agent
# @tool + bind_tools + create_react_agent 기반 Tool Calling
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from agents.state import PortfolioState
from config import get_llm
from tools.kr_stock import get_kr_stock_price, get_kr_sector_index
from tools.us_stock import get_us_stock_price, get_us_sector_trend
from tools.exchange_rate import get_exchange_rate
from utils.parser import get_kr_tickers, get_us_tickers


# Tool 목록 정의
DATA_COLLECTION_TOOLS = [
    get_kr_stock_price,
    get_us_stock_price,
    get_exchange_rate,
    get_kr_sector_index,
    get_us_sector_trend,
]


def data_collector_node(state: PortfolioState) -> PortfolioState:
    """
    데이터 수집 Agent 노드
    - @tool + bind_tools 기반 Tool Calling으로 데이터 수집
    - ReAct 방식으로 LLM이 필요한 Tool을 능동적으로 선택/실행
    """
    holdings   = state.get("holdings", [])
    if not holdings:
        state["error_log"].append("[data_collector] 보유 종목 없음")
        return state

    kr_tickers = get_kr_tickers(holdings)
    us_tickers = get_us_tickers(holdings)

    # ------------------------------------------
    # Tool Calling 방식으로 데이터 수집
    # LLM이 필요한 Tool을 판단하여 능동적으로 호출
    # ------------------------------------------
    try:
        llm        = get_llm("gpt4o_mini")
        react_agent = create_react_agent(llm, DATA_COLLECTION_TOOLS)

        prompt = f"""다음 작업을 순서대로 수행하세요:

1. 한국 주식 종가 조회: {json.dumps(kr_tickers)}
2. 미국 주식 종가 조회: {json.dumps(us_tickers)}
3. USD/KRW 환율 조회

각 도구를 호출하여 데이터를 수집하세요.
"""
        response = react_agent.invoke({"messages": [HumanMessage(content=prompt)]})

        # Tool 실행 결과 추출
        market_data   = {}
        exchange_rate = {}

        for msg in response["messages"]:
            # ToolMessage에서 결과 추출
            if hasattr(msg, "name") and hasattr(msg, "content"):
                try:
                    data = json.loads(msg.content)
                    if msg.name == "get_kr_stock_price":
                        market_data["KR"] = data
                    elif msg.name == "get_us_stock_price":
                        market_data["US"] = data
                    elif msg.name == "get_exchange_rate":
                        exchange_rate = data
                except (json.JSONDecodeError, Exception):
                    continue

        # Tool Calling 결과가 없으면 직접 호출로 폴백
        if not market_data.get("KR") and kr_tickers:
            from tools.kr_stock import get_kr_stock_price_direct
            market_data["KR"] = get_kr_stock_price_direct(kr_tickers)

        if not market_data.get("US") and us_tickers:
            from tools.us_stock import get_us_stock_price_direct
            market_data["US"] = get_us_stock_price_direct(us_tickers)

        if not exchange_rate:
            from tools.exchange_rate import get_exchange_rate_direct
            exchange_rate = get_exchange_rate_direct()

    except Exception as e:
        state["error_log"].append(f"[data_collector] Tool Calling 오류: {str(e)}, 직접 호출로 폴백")

        # 폴백: 직접 함수 호출
        from tools.kr_stock import get_kr_stock_price_direct
        from tools.us_stock import get_us_stock_price_direct
        from tools.exchange_rate import get_exchange_rate_direct

        market_data   = {}
        exchange_rate = {}

        if kr_tickers:
            try:
                market_data["KR"] = get_kr_stock_price_direct(kr_tickers)
            except Exception as e2:
                state["error_log"].append(f"[data_collector] 한국 주식 폴백 오류: {str(e2)}")
                market_data["KR"] = {}

        if us_tickers:
            try:
                market_data["US"] = get_us_stock_price_direct(us_tickers)
            except Exception as e2:
                state["error_log"].append(f"[data_collector] 미국 주식 폴백 오류: {str(e2)}")
                market_data["US"] = {}

        try:
            exchange_rate = get_exchange_rate_direct()
        except Exception as e2:
            state["error_log"].append(f"[data_collector] 환율 폴백 오류: {str(e2)}")
            exchange_rate = {"USD_KRW": 1350.0, "source": "FALLBACK"}

    state["market_data"]   = market_data
    state["exchange_rate"] = exchange_rate
    return state


if __name__ == "__main__":
    from agents.state import create_initial_state
    from utils.parser import parse_portfolio

    root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portfolio = parse_portfolio(os.path.join(root, "portfolio.txt"))

    state  = create_initial_state(
        user_input = "브리핑",
        holdings   = portfolio["holdings"],
    )
    result = data_collector_node(state)

    print("=== Tool Calling 기반 데이터 수집 결과 ===")
    print(f"환율: {result['exchange_rate']}")
    print(f"\n한국 주식:")
    for ticker, data in result["market_data"].get("KR", {}).items():
        print(f"  {ticker}: {data.get('close', 'N/A')}")
    print(f"\n미국 주식:")
    for ticker, data in result["market_data"].get("US", {}).items():
        print(f"  {ticker}: {data.get('close', 'N/A')}")
    if result["error_log"]:
        print(f"\n오류: {result['error_log']}")
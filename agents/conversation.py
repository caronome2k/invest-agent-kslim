# ==========================================
# agents/conversation.py
# 대화 Agent
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.state import PortfolioState
from config import get_llm


SYSTEM_PROMPT_BASE = """당신은 개인 투자자의 포트폴리오를 관리하는 AI 투자 어드바이저입니다.
아래 규칙을 반드시 따르세요:
1. 레버리지 상품과 펀드는 절대 추천하지 마세요.
2. 투자 추천 시 반드시 근거와 리스크를 함께 제시하세요.
3. 사용자의 포트폴리오 현황을 기반으로 맥락 있는 답변을 하세요.
4. 확실하지 않은 정보는 추측하지 말고 모른다고 답하세요.

{portfolio_context}
"""


def _build_portfolio_context(state: PortfolioState) -> str:
    """포트폴리오 컨텍스트 문자열 생성"""
    lines = ["[현재 포트폴리오 현황]"]

    rate = state.get("exchange_rate", {})
    if rate:
        lines.append(f"현재 환율: {rate.get('USD_KRW', 'N/A'):,.0f}원")

    total_return = state.get("total_return_pct", 0)
    if total_return:
        lines.append(f"전체 수익률: {total_return:+.2f}%")

    holdings = state.get("holdings_analysis", [])
    if holdings:
        lines.append("\n보유 종목:")
        for h in holdings:
            lines.append(
                f"  - {h['name']}({h['ticker']}): 수익률 {h['return_pct']:+.2f}%, "
                f"섹터 {h['sector']} [{h['sector_trend']}]"
            )

    sector_trends = state.get("sector_trends", [])
    if sector_trends:
        uptrend   = [s["sector"] for s in sector_trends if s["trend"] == "UPTREND"]
        downtrend = [s["sector"] for s in sector_trends if s["trend"] == "DOWNTREND"]
        if uptrend:
            lines.append(f"\n상승 섹터: {', '.join(uptrend)}")
        if downtrend:
            lines.append(f"하락 섹터: {', '.join(downtrend)}")

    return "\n".join(lines)


def conversation_node(state: PortfolioState) -> PortfolioState:
    user_input = state.get("user_input", "")

    try:
        llm = get_llm("gpt4o")

        portfolio_context = _build_portfolio_context(state)
        system_prompt     = SYSTEM_PROMPT_BASE.format(portfolio_context=portfolio_context)

        messages = [SystemMessage(content=system_prompt)]

        for chat in state.get("chat_history", []):
            if chat["role"] == "user":
                messages.append(HumanMessage(content=chat["content"]))
            elif chat["role"] == "assistant":
                messages.append(AIMessage(content=chat["content"]))

        messages.append(HumanMessage(content=user_input))

        response = llm.invoke(messages)
        answer   = response.content.strip()

        state["chat_history"] += [
            {"role": "user",      "content": user_input},
            {"role": "assistant", "content": answer},
        ]
        state["final_report"] = answer

    except Exception as e:
        error_msg = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        state["error_log"].append(f"[conversation] {str(e)}")
        state["final_report"] = error_msg
        state["chat_history"] += [
            {"role": "user",      "content": user_input},
            {"role": "assistant", "content": error_msg},
        ]

    return state


if __name__ == "__main__":
    from agents.state import create_initial_state

    sample_holdings = [
        {"ticker": "005930", "name": "삼성전자", "market": "KOSPI", "sector": "반도체",
         "quantity": 50, "avg_price": 71000, "currency": "KRW", "buy_date": "2023-03-15", "memo": None},
        {"ticker": "NVDA", "name": "Nvidia Corp.", "market": "NASDAQ", "sector": "AI 반도체",
         "quantity": 5, "avg_price": 550.0, "currency": "USD", "buy_date": "2023-06-01", "memo": None},
    ]

    state  = create_initial_state(
        user_input    = "삼성전자 지금 팔아야 해?",
        holdings      = sample_holdings,
        investor_name = "홍길동",
    )
    result = conversation_node(state)
    print("=== 대화 Agent 응답 ===")
    print(result["final_report"])
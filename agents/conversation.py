# ==========================================
# agents/conversation.py
# 대화 Agent - 포트폴리오 컨텍스트 유지
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from agents.state import PortfolioState
from config import get_llm
from prompts.conversation_prompt import build_conversation_system_prompt


def conversation_node(state: PortfolioState) -> PortfolioState:
    user_input = state.get("user_input", "")

    try:
        llm = get_llm("gpt4o")

        # prompts 모듈에서 CoT + Few-shot 포함 프롬프트 로드
        system_prompt = build_conversation_system_prompt(
            holdings_analysis = state.get("holdings_analysis", []),
            sector_trends     = state.get("sector_trends", []),
            exchange_rate     = state.get("exchange_rate", {}),
            total_return_pct  = state.get("total_return_pct", 0.0),
        )

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
    from utils.parser import parse_portfolio

    root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portfolio = parse_portfolio(os.path.join(root, "portfolio.txt"))

    state = create_initial_state(
        user_input    = "삼성전자 지금 팔아야 해?",
        holdings      = portfolio["holdings"],
        investor_name = portfolio["investor_name"],
    )
    result = conversation_node(state)
    print("=== 대화 Agent 응답 ===")
    print(result["final_report"])
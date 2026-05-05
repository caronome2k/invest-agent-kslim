# ==========================================
# agents/supervisor.py
# Supervisor Agent - 요청 분류 및 라우팅
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.state import PortfolioState
from config import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from prompts.supervisor_prompt import get_supervisor_prompt

ROUTE_KEYWORDS = {
    "daily_briefing": ["브리핑", "오늘", "현황", "포트폴리오 보여", "수익률 보여", "전체 보여"],
    "sector_analysis": ["섹터", "트렌드", "업종", "시장 분석"],
    "recommendation": ["추천", "매수", "매도", "팔아", "사야", "투자금", "배분", "리밸런싱"],
    "conversation": [],
}


def _keyword_route(user_input: str) -> str:
    for route, keywords in ROUTE_KEYWORDS.items():
        if route == "conversation":
            continue
        for kw in keywords:
            if kw in user_input:
                return route
    return "conversation"


def supervisor_node(state: PortfolioState) -> PortfolioState:
    user_input = state["user_input"]
    route = _keyword_route(user_input)

    if route == "conversation":
        try:
            llm = get_llm("gpt4o_mini")

            # prompts 모듈에서 Few-shot 포함 프롬프트 로드
            system_prompt = get_supervisor_prompt()

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
            response  = llm.invoke(messages)
            llm_route = response.content.strip().lower()
            if llm_route in ROUTE_KEYWORDS:
                route = llm_route
        except Exception as e:
            state["error_log"].append(f"[supervisor] LLM 라우팅 오류: {str(e)}")
            route = "conversation"

    state["route"] = route
    return state


def route_after_supervisor(state: PortfolioState) -> str:
    route = state.get("route", "conversation")
    if route in ("daily_briefing", "recommendation"):
        return "full_pipeline"
    elif route == "sector_analysis":
        return "sector_only"
    else:
        return "conversation"


if __name__ == "__main__":
    from agents.state import create_initial_state

    test_inputs = [
        "오늘 포트폴리오 브리핑 보여줘",
        "섹터 트렌드 분석해줘",
        "지금 매도 추천 있어?",
        "삼성전자 어떻게 생각해?",
        "ETF가 뭐야?",
    ]
    for user_input in test_inputs:
        state  = create_initial_state(user_input=user_input)
        result = supervisor_node(state)
        print(f"  입력: {user_input}")
        print(f"  라우팅: {result['route']}\n")
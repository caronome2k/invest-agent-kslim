# ==========================================
# agents/supervisor.py
# Supervisor Agent - 요청 분류 및 라우팅
# ==========================================

from agents.state import PortfolioState
from config import get_llm
from langchain_core.messages import HumanMessage, SystemMessage


# 라우팅 키워드 정의
ROUTE_KEYWORDS = {
    "daily_briefing": [
        "브리핑", "오늘", "현황", "포트폴리오 보여", "수익률 보여", "전체 보여"
    ],
    "sector_analysis": [
        "섹터", "트렌드", "업종", "시장", "상승", "하락"
    ],
    "recommendation": [
        "추천", "매수", "매도", "팔아", "사야", "투자금", "배분", "리밸런싱"
    ],
    "conversation": [],   # 위 키워드에 해당하지 않는 경우
}


def _keyword_route(user_input: str) -> str:
    """키워드 기반 1차 라우팅"""
    for route, keywords in ROUTE_KEYWORDS.items():
        if route == "conversation":
            continue
        for kw in keywords:
            if kw in user_input:
                return route
    return "conversation"


def supervisor_node(state: PortfolioState) -> PortfolioState:
    """
    Supervisor Agent 노드
    - 사용자 입력을 분석하여 실행 경로(route)를 결정합니다.
    - 1차: 키워드 기반 빠른 분류
    - 2차: LLM 기반 정밀 분류 (키워드로 판단 불가 시)
    """
    user_input = state["user_input"]

    # 1차: 키워드 기반 라우팅
    route = _keyword_route(user_input)

    # 2차: 키워드로 판단 불가 시 LLM 라우팅
    if route == "conversation":
        try:
            llm = get_llm("gpt4o_mini")   # 라우팅은 mini 모델로 비용 절감

            system_prompt = """당신은 투자 서비스의 요청 분류기입니다.
사용자 입력을 분석하여 아래 4가지 중 하나로만 답하세요. 다른 말은 하지 마세요.

- daily_briefing  : 포트폴리오 전체 현황, 수익률 조회 요청
- sector_analysis : 섹터/업종 트렌드 분석 요청
- recommendation  : 매수/매도/투자금 배분 추천 요청
- conversation    : 특정 종목 질문, 일반 투자 질의, 기타"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]

            response = llm.invoke(messages)
            llm_route = response.content.strip().lower()

            if llm_route in ROUTE_KEYWORDS:
                route = llm_route

        except Exception as e:
            state["error_log"].append(f"[supervisor] LLM 라우팅 오류: {str(e)}")
            route = "conversation"

    state["route"] = route
    return state


def route_after_supervisor(state: PortfolioState) -> str:
    """
    LangGraph conditional_edge 함수
    Supervisor가 결정한 route 값을 반환합니다.
    """
    route = state.get("route", "conversation")

    # daily_briefing / recommendation 은 전체 파이프라인 실행
    if route in ("daily_briefing", "recommendation"):
        return "full_pipeline"
    elif route == "sector_analysis":
        return "sector_only"
    else:
        return "conversation"


# ------------------------------------------
# 동작 확인용
# ------------------------------------------
if __name__ == "__main__":
    from agents.state import create_initial_state

    test_inputs = [
        "오늘 포트폴리오 브리핑 보여줘",
        "섹터 트렌드 분석해줘",
        "지금 매도 추천 있어?",
        "삼성전자 어떻게 생각해?",
    ]

    for user_input in test_inputs:
        state = create_initial_state(user_input=user_input)
        result = supervisor_node(state)
        print(f"  입력: {user_input}")
        print(f"  라우팅: {result['route']}\n")
# ==========================================
# agents/graph.py
# LangGraph StateGraph 전체 흐름 연결
# MemorySaver Checkpointer 기반 멀티턴 대화 유지
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agents.state import PortfolioState, create_initial_state
from agents.supervisor import supervisor_node, route_after_supervisor
from agents.data_collector import data_collector_node
from agents.portfolio_analyzer import portfolio_analyzer_node
from agents.sector_analyzer import sector_analyzer_node
from agents.recommender import recommender_node
from agents.report_generator import report_generator_node
from agents.conversation import conversation_node
from rag.retriever import enrich_state_with_rag


def rag_enricher_node(state: PortfolioState) -> PortfolioState:
    """RAG 컨텍스트 보강 노드"""
    return enrich_state_with_rag(state)


def build_graph() -> StateGraph:
    """
    LangGraph StateGraph 구성
    MemorySaver Checkpointer로 세션별 상태 영속화

    실행 경로:
    [full_pipeline]  supervisor → data_collector → portfolio_analyzer
                     → sector_analyzer → rag_enricher → recommender
                     → report_generator
    [sector_only]    supervisor → data_collector → sector_analyzer
                     → report_generator
    [conversation]   supervisor → conversation
    """
    graph = StateGraph(PortfolioState)

    # 노드 등록
    graph.add_node("supervisor",         supervisor_node)
    graph.add_node("data_collector",     data_collector_node)
    graph.add_node("portfolio_analyzer", portfolio_analyzer_node)
    graph.add_node("sector_analyzer",    sector_analyzer_node)
    graph.add_node("rag_enricher",       rag_enricher_node)
    graph.add_node("recommender",        recommender_node)
    graph.add_node("report_generator",   report_generator_node)
    graph.add_node("conversation",       conversation_node)

    # 진입점
    graph.set_entry_point("supervisor")

    # Supervisor → 조건부 분기
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "full_pipeline": "data_collector",
            "sector_only"  : "data_collector",
            "conversation" : "conversation",
        }
    )

    graph.add_edge("data_collector",     "portfolio_analyzer")
    graph.add_edge("portfolio_analyzer", "sector_analyzer")

    graph.add_conditional_edges(
        "sector_analyzer",
        lambda state: "rag_enricher"
            if state.get("route") in ("daily_briefing", "recommendation")
            else "report_generator",
        {
            "rag_enricher"    : "rag_enricher",
            "report_generator": "report_generator",
        }
    )

    graph.add_edge("rag_enricher",     "recommender")
    graph.add_edge("recommender",      "report_generator")
    graph.add_edge("report_generator", END)
    graph.add_edge("conversation",     END)

    # MemorySaver Checkpointer 적용
    # thread_id 기반으로 세션별 상태 영속화
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# 전역 그래프 인스턴스 (싱글턴)
_graph = None

def get_graph():
    """그래프 인스턴스 반환 (최초 1회만 빌드)"""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_graph(
    user_input   : str,
    portfolio    : dict,
    period_weeks : int  = 4,
    chat_history : list = None,
    session_id   : str  = "default",
) -> PortfolioState:
    """
    그래프 실행 메인 함수

    Args:
        user_input   : 사용자 입력 메시지
        portfolio    : parse_portfolio() 결과
        period_weeks : 섹터 분석 기간 (주)
        chat_history : 이전 대화 히스토리
        session_id   : 세션 ID (Checkpointer thread_id)

    Returns:
        최종 PortfolioState
    """
    graph = get_graph()

    initial_state = create_initial_state(
        user_input      = user_input,
        holdings        = portfolio["holdings"],
        monthly_deposit = portfolio["monthly_deposit"],
        investor_name   = portfolio["investor_name"],
        period_weeks    = period_weeks,
    )

    if chat_history:
        initial_state["chat_history"] = chat_history

    # Checkpointer thread_id로 세션별 상태 관리
    config = {"configurable": {"thread_id": session_id}}
    result = graph.invoke(initial_state, config=config)
    return result


if __name__ == "__main__":
    from utils.parser import parse_portfolio

    root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath  = os.path.join(root, "portfolio.txt")
    portfolio = parse_portfolio(filepath)

    print("=" * 60)
    print(" 그래프 실행 테스트 (Tool Calling + Checkpointer)")
    print("=" * 60)

    print("\n[테스트 1] Daily 브리핑")
    result = run_graph(
        user_input = "오늘 브리핑 보여줘",
        portfolio  = portfolio,
        session_id = "test_session",
    )
    print(result["final_report"])

    if result["error_log"]:
        print(f"\n[오류 로그]")
        for err in result["error_log"]:
            print(f"  {err}")
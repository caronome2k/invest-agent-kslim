# ==========================================
# rag/retriever.py
# RAG 검색 체인 구성
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vectorstore import get_vectorstore
from agents.state import PortfolioState


def search_sector_context(
    sector_names: list[str],
    market: str = "ALL",
    k: int = 5,
) -> str:
    """
    섹터명 기반으로 관련 문서를 검색합니다.

    Args:
        sector_names : 검색할 섹터명 리스트
        market       : "KR" / "US" / "ALL"
        k            : 검색 결과 수

    Returns:
        검색된 문서 내용을 합친 컨텍스트 문자열
    """
    try:
        vs      = get_vectorstore()
        query   = " ".join(sector_names) + " 섹터 트렌드 동향 분석"
        results = vs.similarity_search(query, k=k)

        # 마켓 필터링
        if market != "ALL":
            results = [
                doc for doc in results
                if doc.metadata.get("market") in (market, "ALL")
            ]

        if not results:
            return ""

        context_parts = []
        for doc in results:
            source = doc.metadata.get("source", "Unknown")
            sector = doc.metadata.get("sector", "")
            date   = doc.metadata.get("date", "")
            context_parts.append(
                f"[출처: {source} | 섹터: {sector} | 날짜: {date}]\n{doc.page_content}"
            )

        return "\n\n".join(context_parts)

    except Exception as e:
        print(f"[retriever] 검색 오류: {e}")
        return ""


def search_ticker_context(ticker: str, name: str, k: int = 3) -> str:
    """
    특정 종목 관련 문서를 검색합니다.
    """
    try:
        vs      = get_vectorstore()
        query   = f"{name} {ticker} 주식 분석 전망"
        results = vs.similarity_search(query, k=k)

        if not results:
            return ""

        context_parts = []
        for doc in results:
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[출처: {source}]\n{doc.page_content}")

        return "\n\n".join(context_parts)

    except Exception as e:
        print(f"[retriever] 종목 검색 오류: {e}")
        return ""


def enrich_state_with_rag(state: PortfolioState) -> PortfolioState:
    """
    State의 섹터 분석 결과를 기반으로 RAG 컨텍스트를 보강합니다.
    recommender_node 실행 전에 호출됩니다.
    """
    sector_trends = state.get("sector_trends", [])

    # UPTREND / DOWNTREND 섹터만 검색 대상으로
    target_sectors = [
        s["sector"] for s in sector_trends
        if s["trend"] in ("UPTREND", "DOWNTREND")
    ]

    if not target_sectors:
        state["rag_context"] = ""
        return state

    context = search_sector_context(
        sector_names = target_sectors,
        market       = "ALL",
        k            = 5,
    )

    state["rag_context"] = context
    return state


if __name__ == "__main__":
    print("=== RAG 검색 테스트 ===")

    print("\n[섹터 컨텍스트 검색]")
    context = search_sector_context(["AI 반도체", "기술주"], market="US", k=3)
    if context:
        print(context[:300] + "...")
    else:
        print("  검색 결과 없음 (벡터 저장소 먼저 빌드 필요)")
        print("  → python rag/vectorstore.py 실행 후 재시도")
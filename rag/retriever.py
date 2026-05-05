# ==========================================
# rag/retriever.py
# RAG 검색 체인 구성
# Retriever-Reranker 2단계 검색 적용
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vectorstore import get_vectorstore
from agents.state import PortfolioState


def _rerank_documents(docs: list, query: str) -> list:
    """
    Reranker: 검색된 문서를 쿼리 관련도 기준으로 재정렬합니다.
    - 쿼리 키워드 포함 빈도로 점수 계산
    - 높은 점수 순으로 정렬
    """
    query_terms = set(query.lower().split())

    def score(doc) -> float:
        content    = doc.page_content.lower()
        # 키워드 매칭 점수
        term_score = sum(1 for term in query_terms if term in content)
        # 섹터 메타데이터 보너스
        sector     = doc.metadata.get("sector", "").lower()
        sector_bonus = sum(2 for term in query_terms if term in sector)
        return term_score + sector_bonus

    return sorted(docs, key=score, reverse=True)


def search_sector_context(
    sector_names : list,
    market       : str = "ALL",
    k            : int = 5,
) -> str:
    """
    2단계 Retriever-Reranker 기반 섹터 컨텍스트 검색

    1단계 (Retriever): MMR 검색으로 관련성 높고 다양한 문서 검색
    2단계 (Reranker) : 키워드 매칭 점수로 재정렬 후 상위 k개 선택

    Args:
        sector_names : 검색할 섹터명 리스트
        market       : "KR" / "US" / "ALL"
        k            : 최종 반환 문서 수

    Returns:
        검색된 문서 내용을 합친 컨텍스트 문자열
    """
    try:
        vs    = get_vectorstore()
        query = " ".join(sector_names) + " 섹터 트렌드 동향 분석"

        # ------------------------------------------
        # 1단계: Retriever
        # MMR(Maximal Marginal Relevance) 검색
        # - fetch_k: 후보 문서를 k*3배 더 많이 가져옴
        # - lambda_mult: 관련성(1.0) vs 다양성(0.0) 균형
        # ------------------------------------------
        fetch_k  = k * 3
        candidates = vs.max_marginal_relevance_search(
            query,
            k         = fetch_k,
            fetch_k   = fetch_k * 2,
            lambda_mult = 0.7,      # 관련성 70% + 다양성 30%
        )

        # 마켓 필터링 (메타데이터 기반 선제 필터)
        if market != "ALL":
            candidates = [
                doc for doc in candidates
                if doc.metadata.get("market") in (market, "ALL")
            ]

        if not candidates:
            return ""

        # ------------------------------------------
        # 2단계: Reranker
        # 키워드 매칭 점수로 재정렬 후 상위 k개 선택
        # ------------------------------------------
        reranked = _rerank_documents(candidates, query)
        final    = reranked[:k]

        # 컨텍스트 문자열 구성
        context_parts = []
        for doc in final:
            source = doc.metadata.get("source", "Unknown")
            sector = doc.metadata.get("sector", "")
            date   = doc.metadata.get("date", "")
            market_label = doc.metadata.get("market", "")
            context_parts.append(
                f"[출처: {source} | 섹터: {sector} | 시장: {market_label} | 날짜: {date}]\n"
                f"{doc.page_content}"
            )

        return "\n\n".join(context_parts)

    except Exception as e:
        print(f"[retriever] 검색 오류: {e}")
        return ""


def search_ticker_context(ticker: str, name: str, k: int = 3) -> str:
    """
    2단계 Retriever-Reranker 기반 종목 컨텍스트 검색

    Args:
        ticker : 종목 코드 또는 티커
        name   : 종목명
        k      : 최종 반환 문서 수
    """
    try:
        vs    = get_vectorstore()
        query = f"{name} {ticker} 주식 분석 전망 섹터"

        # 1단계: MMR 검색
        candidates = vs.max_marginal_relevance_search(
            query,
            k           = k * 3,
            fetch_k     = k * 6,
            lambda_mult = 0.6,
        )

        if not candidates:
            return ""

        # 2단계: Reranker
        reranked = _rerank_documents(candidates, query)
        final    = reranked[:k]

        context_parts = []
        for doc in final:
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

    - UPTREND / DOWNTREND 섹터만 검색 대상으로 선정
    - 한국/미국 시장별로 분리 검색 후 통합
    """
    sector_trends = state.get("sector_trends", [])

    # UPTREND / DOWNTREND 섹터만 검색 (NEUTRAL 제외)
    kr_targets = [
        s["sector"] for s in sector_trends
        if s["trend"] in ("UPTREND", "DOWNTREND") and s["market"] == "KR"
    ]
    us_targets = [
        s["sector"] for s in sector_trends
        if s["trend"] in ("UPTREND", "DOWNTREND") and s["market"] == "US"
    ]

    contexts = []

    # 한국 섹터 검색
    if kr_targets:
        kr_context = search_sector_context(
            sector_names = kr_targets,
            market       = "KR",
            k            = 3,
        )
        if kr_context:
            contexts.append(f"[한국 시장 관련 리포트]\n{kr_context}")

    # 미국 섹터 검색
    if us_targets:
        us_context = search_sector_context(
            sector_names = us_targets,
            market       = "US",
            k            = 3,
        )
        if us_context:
            contexts.append(f"[미국 시장 관련 리포트]\n{us_context}")

    state["rag_context"] = "\n\n".join(contexts)
    return state


# ------------------------------------------
# 동작 확인용
# ------------------------------------------
if __name__ == "__main__":
    print("=== RAG Retriever-Reranker 테스트 ===")

    print("\n[1단계] 섹터 컨텍스트 검색 (US, AI 반도체)")
    context = search_sector_context(["AI 반도체", "기술주"], market="US", k=3)
    if context:
        print(context[:400] + "...")
    else:
        print("  검색 결과 없음 → python rag/vectorstore.py 먼저 실행")

    print("\n[2단계] 종목 컨텍스트 검색 (NVDA)")
    ticker_ctx = search_ticker_context("NVDA", "Nvidia Corp.", k=2)
    if ticker_ctx:
        print(ticker_ctx[:300] + "...")
    else:
        print("  검색 결과 없음")
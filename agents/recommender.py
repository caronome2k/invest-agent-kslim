# ==========================================
# agents/recommender.py
# 매매 추천 Agent - Structured Output 적용
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from agents.state import PortfolioState
from config import get_llm
from prompts.recommendation_prompt import build_recommendation_prompt


# ------------------------------------------
# Structured Output 스키마
# ------------------------------------------
class TradeAction(BaseModel):
    ticker      : str   = Field(description="종목코드 또는 티커")
    name        : str   = Field(description="종목명")
    action      : Literal["BUY", "SELL", "HOLD"] = Field(description="추천 액션")
    reason      : str   = Field(description="추천 사유 (3문장 이내)")
    source      : str   = Field(description="근거 데이터 출처")
    risk_warning: str   = Field(description="리스크 경고")
    confidence  : float = Field(description="추천 신뢰도 0.0~1.0", ge=0.0, le=1.0)


class AllocationSuggestion(BaseModel):
    ticker    : str   = Field(description="종목코드 또는 티커")
    name      : str   = Field(description="종목명")
    amount_krw: int   = Field(description="배분 금액 (원)")
    ratio_pct : float = Field(description="비중 (%)")
    reason    : str   = Field(description="배분 사유")


class RecommendationOutput(BaseModel):
    recommendations: List[TradeAction]          = Field(description="매매 추천 리스트")
    allocation     : List[AllocationSuggestion] = Field(description="월 투자금 배분 가이드")
    market_summary : str                        = Field(description="시장 전체 요약 (3문장 이내)")


def recommender_node(state: PortfolioState) -> PortfolioState:
    try:
        llm            = get_llm("gpt4o")
        structured_llm = llm.with_structured_output(RecommendationOutput)

        # prompts 모듈에서 CoT + Few-shot 포함 프롬프트 로드
        prompt = build_recommendation_prompt(
            holdings_analysis = state.get("holdings_analysis", []),
            sector_trends     = state.get("sector_trends", []),
            exchange_rate     = state.get("exchange_rate", {}),
            monthly_deposit   = state.get("monthly_deposit", 1500000),
            rag_context       = state.get("rag_context", ""),
            analysis_date     = state.get("analysis_date", ""),
        )

        messages = [
            SystemMessage(content=prompt["system"]),
            HumanMessage(content=prompt["user"]),
        ]

        output: RecommendationOutput = structured_llm.invoke(messages)

        state["recommendations"] = [
            {"ticker": r.ticker, "name": r.name, "action": r.action,
             "reason": r.reason, "source": r.source,
             "risk_warning": r.risk_warning, "confidence": r.confidence}
            for r in output.recommendations
        ]
        state["allocation"] = [
            {"ticker": a.ticker, "name": a.name, "amount_krw": a.amount_krw,
             "ratio_pct": a.ratio_pct, "reason": a.reason}
            for a in output.allocation
        ]

    except Exception as e:
        state["error_log"].append(f"[recommender] 추천 생성 오류: {str(e)}")
        state["recommendations"] = []
        state["allocation"]      = []

    return state


if __name__ == "__main__":
    from agents.state import create_initial_state
    from agents.data_collector import data_collector_node
    from agents.portfolio_analyzer import portfolio_analyzer_node
    from agents.sector_analyzer import sector_analyzer_node
    from utils.parser import parse_portfolio

    root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    portfolio = parse_portfolio(os.path.join(root, "portfolio.txt"))

    state = create_initial_state(
        user_input      = "매매 추천해줘",
        holdings        = portfolio["holdings"],
        monthly_deposit = portfolio["monthly_deposit"],
    )
    state = data_collector_node(state)
    state = portfolio_analyzer_node(state)
    state = sector_analyzer_node(state)
    state = recommender_node(state)

    print("=== 매매 추천 결과 ===")
    for r in state["recommendations"]:
        print(f"\n  [{r['action']}] {r['name']} ({r['ticker']})")
        print(f"    사유   : {r['reason']}")
        print(f"    출처   : {r['source']}")
        print(f"    리스크 : {r['risk_warning']}")

    print("\n=== 월 투자금 배분 ===")
    for a in state["allocation"]:
        print(f"  {a['name']:20s}: {a['amount_krw']:>8,}원 ({a['ratio_pct']}%)")
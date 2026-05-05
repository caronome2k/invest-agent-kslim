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


def _build_prompt(state: PortfolioState) -> tuple[str, str]:
    """추천 프롬프트 생성"""

    # 보유 종목 요약
    holdings_summary = "\n".join([
        f"  - {h['name']}({h['ticker']}): 수익률 {h['return_pct']:+.2f}%, "
        f"섹터 {h['sector']} [{h['sector_trend']}]"
        for h in state.get("holdings_analysis", [])
    ])

    # 섹터 트렌드 요약
    uptrend   = [s["sector"] for s in state.get("sector_trends", []) if s["trend"] == "UPTREND"]
    downtrend = [s["sector"] for s in state.get("sector_trends", []) if s["trend"] == "DOWNTREND"]

    exchange_rate   = state.get("exchange_rate", {})
    monthly_deposit = state.get("monthly_deposit", 1500000)
    rag_context     = state.get("rag_context", "")

    system_prompt = """당신은 전문 투자 어드바이저입니다.
아래 규칙을 반드시 따르세요:
1. 레버리지 상품과 펀드는 절대 추천하지 마세요.
2. 모든 추천에 근거 데이터 출처를 명시하세요.
3. 리스크 경고를 반드시 포함하세요.
4. 분할 매수/매도를 기본 원칙으로 하세요.
5. 월 정기 투자금 배분 시 총액을 초과하지 마세요."""

    user_prompt = f"""다음 정보를 바탕으로 매매 추천 리포트를 작성하세요.

[보유 종목 현황]
{holdings_summary}

[섹터 트렌드]
상승 섹터: {', '.join(uptrend) if uptrend else '없음'}
하락 섹터: {', '.join(downtrend) if downtrend else '없음'}

[환율 정보]
현재 환율: {exchange_rate.get('USD_KRW', 'N/A'):,.0f}원
전일 대비: {exchange_rate.get('change_dir', '-')}{abs(exchange_rate.get('change', 0)):.0f}원

[월 정기 투자금]
{monthly_deposit:,}원

{f'[참고 리포트]{chr(10)}{rag_context}' if rag_context else ''}
"""
    return system_prompt, user_prompt


def recommender_node(state: PortfolioState) -> PortfolioState:
    try:
        llm            = get_llm("gpt4o")
        structured_llm = llm.with_structured_output(RecommendationOutput)

        system_prompt, user_prompt = _build_prompt(state)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
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

    sample_holdings = [
        {"ticker": "005930", "name": "삼성전자",        "market": "KOSPI",  "sector": "반도체",
         "quantity": 50, "avg_price": 71000,  "currency": "KRW", "buy_date": "2023-03-15", "memo": None},
        {"ticker": "000990", "name": "LG에너지솔루션",  "market": "KOSPI",  "sector": "2차전지",
         "quantity": 10, "avg_price": 395000, "currency": "KRW", "buy_date": "2023-09-01", "memo": None},
        {"ticker": "NVDA",   "name": "Nvidia Corp.",    "market": "NASDAQ", "sector": "AI 반도체",
         "quantity": 5,  "avg_price": 550.0,  "currency": "USD", "buy_date": "2023-06-01", "memo": None},
        {"ticker": "VOO",    "name": "Vanguard S&P500", "market": "NYSE",   "sector": "ETF-미국전체",
         "quantity": 5,  "avg_price": 410.0,  "currency": "USD", "buy_date": "2022-11-20", "memo": None},
    ]

    state = create_initial_state(user_input="매매 추천해줘", holdings=sample_holdings, monthly_deposit=1500000)
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
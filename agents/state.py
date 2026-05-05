# ==========================================
# agents/state.py
# LangGraph Agent 간 공유 State 정의
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import TypedDict, List, Optional, Annotated
import operator


class HoldingItem(TypedDict):
    ticker:         str
    name:           str
    market:         str
    sector:         str
    quantity:       int
    avg_price:      float
    currency:       str
    buy_date:       str
    memo:           Optional[str]


class HoldingAnalysis(TypedDict):
    ticker:             str
    name:               str
    market:             str
    sector:             str
    current_price:      float
    current_price_krw:  float
    avg_price:          float
    avg_price_krw:      float
    quantity:           int
    eval_amount_krw:    float
    invest_amount_krw:  float
    return_pct:         float
    sector_trend:       str
    currency:           str


class SectorTrend(TypedDict):
    sector:         str
    market:         str
    change_pct:     float
    trend:          str
    period_weeks:   int
    source:         str


class TradeRecommendation(TypedDict):
    ticker:         str
    name:           str
    action:         str
    reason:         str
    source:         str
    risk_warning:   str
    confidence:     float


class AllocationItem(TypedDict):
    ticker:         str
    name:           str
    amount_krw:     int
    ratio_pct:      float
    reason:         str


class PortfolioState(TypedDict):
    user_input:         str
    route:              str
    holdings:           List[HoldingItem]
    monthly_deposit:    int
    investor_name:      str
    market_data:        dict
    exchange_rate:      dict
    holdings_analysis:  List[HoldingAnalysis]
    total_invest_krw:   float
    total_eval_krw:     float
    total_return_pct:   float
    fx_return_pct:      float
    sector_trends:      List[SectorTrend]
    rag_context:        str
    recommendations:    List[TradeRecommendation]
    allocation:         List[AllocationItem]
    final_report:       str
    chat_history:       Annotated[List[dict], operator.add]
    analysis_date:      str
    period_weeks:       int
    error_log:          Annotated[List[str], operator.add]


def create_initial_state(
    user_input: str,
    holdings: List[HoldingItem] = None,
    monthly_deposit: int = 1500000,
    investor_name: str = "",
    period_weeks: int = 4,
) -> PortfolioState:
    from datetime import datetime
    return PortfolioState(
        user_input          = user_input,
        route               = "",
        holdings            = holdings or [],
        monthly_deposit     = monthly_deposit,
        investor_name       = investor_name,
        market_data         = {},
        exchange_rate       = {},
        holdings_analysis   = [],
        total_invest_krw    = 0.0,
        total_eval_krw      = 0.0,
        total_return_pct    = 0.0,
        fx_return_pct       = 0.0,
        sector_trends       = [],
        rag_context         = "",
        recommendations     = [],
        allocation          = [],
        final_report        = "",
        chat_history        = [],
        analysis_date       = datetime.today().strftime("%Y-%m-%d"),
        period_weeks        = period_weeks,
        error_log           = [],
    )


if __name__ == "__main__":
    state = create_initial_state(
        user_input      = "오늘 포트폴리오 브리핑 보여줘",
        investor_name   = "홍길동",
        monthly_deposit = 1500000,
        period_weeks    = 4,
    )
    print("[state] 초기 State 생성 완료")
    for key, value in state.items():
        print(f"  {key:20s}: {value}")
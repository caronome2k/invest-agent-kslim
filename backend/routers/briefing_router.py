# ==========================================
# backend/routers/briefing_router.py
# Daily 브리핑 라우터
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Query, HTTPException
from agents.graph import run_graph
from backend.routers.portfolio_router import get_portfolio

router = APIRouter()


@router.get("/daily")
def get_daily_briefing(
    period_weeks: int = Query(default=4, ge=1, le=12, description="섹터 분석 기간 (주)")
):
    """
    Daily 브리핑을 실행합니다.
    - 보유 종목 종가 수집
    - 포트폴리오 수익률 계산
    - 섹터 트렌드 분석
    - 리포트 생성
    """
    try:
        portfolio = get_portfolio()
        result    = run_graph(
            user_input   = "오늘 브리핑 보여줘",
            portfolio    = portfolio,
            period_weeks = period_weeks,
        )

        return {
            "status"          : "success",
            "analysis_date"   : result["analysis_date"],
            "exchange_rate"   : result["exchange_rate"],
            "total_invest_krw": result["total_invest_krw"],
            "total_eval_krw"  : result["total_eval_krw"],
            "total_return_pct": result["total_return_pct"],
            "fx_return_pct"   : result["fx_return_pct"],
            "holdings_analysis": result["holdings_analysis"],
            "final_report"    : result["final_report"],
            "error_log"       : result["error_log"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
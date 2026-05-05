# ==========================================
# backend/routers/recommendation_router.py
# 매매 추천 라우터
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Query, HTTPException
from agents.graph import run_graph
from backend.routers.portfolio_router import get_portfolio

router = APIRouter()


@router.get("")
def get_recommendation(
    period_weeks: int = Query(default=4, ge=1, le=12, description="섹터 분석 기간 (주)")
):
    """
    매매 추천 및 월 투자금 배분 가이드를 생성합니다.
    - 섹터 트렌드 기반 매도/매수 추천
    - 월 정기 투자금 배분 가이드
    - RAG 기반 근거 보강
    """
    try:
        portfolio = get_portfolio()
        result    = run_graph(
            user_input   = "매매 추천해줘",
            portfolio    = portfolio,
            period_weeks = period_weeks,
        )

        return {
            "status"         : "success",
            "analysis_date"  : result["analysis_date"],
            "exchange_rate"  : result["exchange_rate"],
            "recommendations": result["recommendations"],
            "allocation"     : result["allocation"],
            "monthly_deposit": result["monthly_deposit"],
            "final_report"   : result["final_report"],
            "error_log"      : result["error_log"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
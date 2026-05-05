# ==========================================
# backend/routers/sector_router.py
# 섹터 트렌드 분석 라우터
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Query, HTTPException
from agents.graph import run_graph
from backend.routers.portfolio_router import get_portfolio

router = APIRouter()


@router.get("/analysis")
def get_sector_analysis(
    period_weeks: int = Query(default=4, ge=1, le=12, description="섹터 분석 기간 (주)")
):
    """
    한국/미국 섹터 트렌드를 분석합니다.
    """
    try:
        portfolio = get_portfolio()
        result    = run_graph(
            user_input   = "섹터 트렌드 분석해줘",
            portfolio    = portfolio,
            period_weeks = period_weeks,
        )

        # 한국/미국 섹터 분리
        kr_sectors = [s for s in result["sector_trends"] if s["market"] == "KR"]
        us_sectors = [s for s in result["sector_trends"] if s["market"] == "US"]

        return {
            "status"       : "success",
            "analysis_date": result["analysis_date"],
            "period_weeks" : period_weeks,
            "kr_sectors"   : sorted(kr_sectors, key=lambda x: x["change_pct"], reverse=True),
            "us_sectors"   : sorted(us_sectors, key=lambda x: x["change_pct"], reverse=True),
            "final_report" : result["final_report"],
            "error_log"    : result["error_log"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
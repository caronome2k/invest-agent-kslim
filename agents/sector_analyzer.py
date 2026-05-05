# ==========================================
# agents/sector_analyzer.py
# 섹터 분석 Agent
# @tool 기반 함수의 _direct 버전 사용
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from agents.state import PortfolioState, SectorTrend
from tools.kr_stock import get_kr_sector_index
from tools.us_stock import get_us_sector_trend


def sector_analyzer_node(state: PortfolioState) -> PortfolioState:
    """
    섹터 분석 Agent 노드
    - 한국/미국 섹터별 트렌드를 수집합니다
    - 보유 종목의 sector_trend 필드를 업데이트합니다 (A2A)
    """
    period_weeks  = state.get("period_weeks", 4)
    sector_trends = []

    # 한국 섹터 트렌드 수집
    try:
        # @tool 함수는 .invoke()로 호출 (딕셔너리로 전달)
        kr_result  = get_kr_sector_index.invoke({"period_weeks": period_weeks})
        kr_sectors = json.loads(kr_result)

        for sector_name, data in kr_sectors.items():
            if "error" in data:
                continue
            sector_trends.append({
                "sector"      : sector_name,
                "market"      : "KR",
                "change_pct"  : data["change_pct"],
                "trend"       : data["trend"],
                "period_weeks": period_weeks,
                "source"      : data["source"],
            })
    except Exception as e:
        state["error_log"].append(f"[sector_analyzer] 한국 섹터 수집 오류: {str(e)}")

    # 미국 섹터 트렌드 수집
    try:
        # @tool 함수는 .invoke()로 호출 (딕셔너리로 전달)
        us_result  = get_us_sector_trend.invoke({"period_weeks": period_weeks})
        us_sectors = json.loads(us_result)

        for sector_name, data in us_sectors.items():
            if "error" in data:
                continue
            sector_trends.append({
                "sector"      : sector_name,
                "market"      : "US",
                "change_pct"  : data["change_pct"],
                "trend"       : data["trend"],
                "period_weeks": period_weeks,
                "source"      : data["source"],
            })
    except Exception as e:
        state["error_log"].append(f"[sector_analyzer] 미국 섹터 수집 오류: {str(e)}")

    state["sector_trends"] = sector_trends

    # A2A: 보유 종목 sector_trend 업데이트
    sector_map       = {s["sector"]: s["trend"] for s in sector_trends}
    updated_holdings = []
    for h in state.get("holdings_analysis", []):
        h["sector_trend"] = sector_map.get(h.get("sector", ""), "NEUTRAL")
        updated_holdings.append(h)
    state["holdings_analysis"] = updated_holdings

    return state


if __name__ == "__main__":
    from agents.state import create_initial_state

    state  = create_initial_state(user_input="섹터 분석", period_weeks=4)
    result = sector_analyzer_node(state)

    print("=== 섹터 트렌드 분석 결과 ===")
    print(f"\n[한국 시장]")
    for s in result["sector_trends"]:
        if s["market"] == "KR":
            print(f"  {s['sector']:15s}: {s['change_pct']:>+6.2f}%  [{s['trend']}]")
    print(f"\n[미국 시장]")
    for s in result["sector_trends"]:
        if s["market"] == "US":
            print(f"  {s['sector']:15s}: {s['change_pct']:>+6.2f}%  [{s['trend']}]")
    if result["error_log"]:
        print(f"\n[오류 로그]")
        for err in result["error_log"]:
            print(f"  {err}")
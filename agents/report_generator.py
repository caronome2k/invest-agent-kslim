# ==========================================
# agents/report_generator.py
# 리포트 생성 Agent
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from agents.state import PortfolioState

TREND_EMOJI  = {"UPTREND": "▲", "DOWNTREND": "▼", "NEUTRAL": "→"}
ACTION_EMOJI = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}


def report_generator_node(state: PortfolioState) -> PortfolioState:
    route = state.get("route", "daily_briefing")
    if route == "sector_analysis":
        report = _build_sector_report(state)
    elif route == "recommendation":
        report = _build_recommendation_report(state)
    else:
        report = _build_daily_briefing(state)
    state["final_report"] = report
    return state


def _build_daily_briefing(state: PortfolioState) -> str:
    rate          = state.get("exchange_rate", {})
    analysis_date = state.get("analysis_date", datetime.today().strftime("%Y-%m-%d"))
    lines = []
    lines.append("=" * 60)
    lines.append(f" 📊 개인 투자 추천 Agent | Daily 브리핑")
    lines.append(f" 기준일: {analysis_date}  |  환율: {rate.get('USD_KRW', 'N/A'):,.0f}원 "
                 f"(전일比 {rate.get('change_dir', '-')}{abs(rate.get('change', 0)):.0f}원)")
    lines.append("=" * 60)
    lines.append("\n[포트폴리오 요약]")
    lines.append(f"  총 투자 원금   : {state.get('total_invest_krw', 0):>15,.0f} 원")
    lines.append(f"  현재 평가금액  : {state.get('total_eval_krw', 0):>15,.0f} 원")
    lines.append(f"  전체 수익률    : {state.get('total_return_pct', 0):>+.2f}%")
    lines.append(f"  환율 조정 수익 : {state.get('fx_return_pct', 0):>+.2f}%")
    lines.append("\n[종목별 현황]")
    lines.append(f"  {'티커':<8} {'종목명':<18} {'현재가':>12} {'수익률':>8} {'섹터트렌드'}")
    lines.append("  " + "-" * 60)
    for h in state.get("holdings_analysis", []):
        price_str  = (f"{h['current_price']:>10,.0f}원"
                      if h["currency"] == "KRW"
                      else f"${h['current_price']:>9,.2f}")
        trend_mark = TREND_EMOJI.get(h["sector_trend"], "→")
        lines.append(
            f"  {h['ticker']:<8} {h['name']:<18} {price_str} "
            f"  {h['return_pct']:>+.1f}%  {trend_mark} {h['sector_trend']}"
        )
    downtrend = [h for h in state.get("holdings_analysis", []) if h["sector_trend"] == "DOWNTREND"]
    if downtrend:
        lines.append(f"\n  ⚠️  DOWNTREND 섹터 노출 종목 {len(downtrend)}개 감지")
    lines.append("=" * 60)
    return "\n".join(lines)


def _build_sector_report(state: PortfolioState) -> str:
    period_weeks  = state.get("period_weeks", 4)
    analysis_date = state.get("analysis_date", "")
    lines = []
    lines.append("=" * 60)
    lines.append(f" 📡 섹터 트렌드 분석 | 최근 {period_weeks}주 기준 | {analysis_date}")
    lines.append("=" * 60)
    for market_label, market_code in [("한국 시장", "KR"), ("미국 시장", "US")]:
        lines.append(f"\n[{market_label}]")
        lines.append(f"  {'섹터':<15} {'변동률':>8}   {'트렌드'}")
        lines.append("  " + "-" * 35)
        sectors = [s for s in state.get("sector_trends", []) if s["market"] == market_code]
        for s in sorted(sectors, key=lambda x: x["change_pct"], reverse=True):
            mark = TREND_EMOJI.get(s["trend"], "→")
            lines.append(f"  {s['sector']:<15} {s['change_pct']:>+7.2f}%   {mark} {s['trend']}")
    downtrend = [h for h in state.get("holdings_analysis", []) if h["sector_trend"] == "DOWNTREND"]
    if downtrend:
        lines.append("\n[⚠️  내 포트폴리오 DOWNTREND 노출 종목]")
        for h in downtrend:
            lines.append(f"  {h['ticker']} {h['name']} ({h['sector']})")
    lines.append("=" * 60)
    return "\n".join(lines)


def _build_recommendation_report(state: PortfolioState) -> str:
    analysis_date = state.get("analysis_date", "")
    rate          = state.get("exchange_rate", {})
    lines = []
    lines.append("=" * 60)
    lines.append(f" 💡 매매 추천 리포트 | {analysis_date}")
    lines.append(f" 기준 환율: {rate.get('USD_KRW', 'N/A'):,.0f}원")
    lines.append("=" * 60)
    recommendations = state.get("recommendations", [])
    if not recommendations:
        lines.append("\n  추천 데이터가 없습니다.")
    else:
        for r in recommendations:
            emoji = ACTION_EMOJI.get(r["action"], "⚪")
            lines.append(f"\n{emoji} [{r['action']}] {r['name']} ({r['ticker']})")
            lines.append(f"  사유   : {r['reason']}")
            lines.append(f"  출처   : {r['source']}")
            lines.append(f"  리스크 : {r['risk_warning']}")
            lines.append(f"  신뢰도 : {r['confidence'] * 100:.0f}%")
    lines.append(f"\n[💰 월 투자금 배분 가이드] {state.get('monthly_deposit', 0):,}원")
    lines.append(f"  {'종목명':<20} {'금액':>10}   {'비중':>6}   사유")
    lines.append("  " + "-" * 55)
    for a in state.get("allocation", []):
        lines.append(
            f"  {a['name']:<20} {a['amount_krw']:>10,}원  {a['ratio_pct']:>5.1f}%  {a['reason']}"
        )
    lines.append("=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    from agents.state import create_initial_state
    from agents.data_collector import data_collector_node
    from agents.portfolio_analyzer import portfolio_analyzer_node
    from agents.sector_analyzer import sector_analyzer_node
    from utils.parser import parse_portfolio

    # portfolio.txt 에서 실제 데이터 로드
    root      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath  = os.path.join(root, "portfolio.txt")
    portfolio = parse_portfolio(filepath)

    state = create_initial_state(
        user_input      = "브리핑",
        holdings        = portfolio["holdings"],
        monthly_deposit = portfolio["monthly_deposit"],
        investor_name   = portfolio["investor_name"],
    )
    state = data_collector_node(state)
    state = portfolio_analyzer_node(state)
    state = sector_analyzer_node(state)
    state["route"] = "daily_briefing"
    result = report_generator_node(state)
    print(result["final_report"])
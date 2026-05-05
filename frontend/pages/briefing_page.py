# ==========================================
# frontend/pages/briefing_page.py
# Daily 브리핑 탭
# ==========================================

import streamlit as st
import pandas as pd
from agents.graph import run_graph


def render(portfolio: dict, period_weeks: int):
    """Daily 브리핑 탭 렌더링"""

    st.subheader("📈 Daily 브리핑")

    if st.button("🔄 브리핑 실행", key="btn_briefing", type="primary"):
        with st.spinner("데이터 수집 및 분석 중..."):
            result = run_graph(
                user_input   = "오늘 브리핑 보여줘",
                portfolio    = portfolio,
                period_weeks = period_weeks,
            )
            st.session_state.last_result = result

    result = st.session_state.get("last_result")
    if not result:
        st.info("브리핑 실행 버튼을 눌러주세요.")
        return

    # 요약 카드
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 투자 원금",   f"{result['total_invest_krw']:,.0f}원")
    col2.metric("현재 평가금액",  f"{result['total_eval_krw']:,.0f}원")
    col3.metric("전체 수익률",    f"{result['total_return_pct']:+.2f}%")
    col4.metric("환율 조정 수익", f"{result['fx_return_pct']:+.2f}%")

    # 환율 정보
    rate = result.get("exchange_rate", {})
    if rate:
        st.caption(
            f"💱 환율: {rate.get('USD_KRW', 0):,.0f}원 "
            f"(전일比 {rate.get('change_dir','')}{abs(rate.get('change', 0)):.0f}원) "
            f"| 기준일: {result.get('analysis_date', '')}"
        )

    st.divider()

    # 종목별 현황 테이블
    st.subheader("종목별 현황")
    trend_map = {"UPTREND": "▲ 상승", "DOWNTREND": "▼ 하락", "NEUTRAL": "→ 중립"}

    holdings_data = []
    for h in result.get("holdings_analysis", []):
        price_str = (
            f"{h['current_price']:,.0f}원"
            if h["currency"] == "KRW"
            else f"${h['current_price']:,.2f}"
        )
        holdings_data.append({
            "티커"      : h["ticker"],
            "종목명"    : h["name"],
            "시장"      : h["market"],
            "섹터"      : h["sector"],
            "현재가"    : price_str,
            "수익률"    : f"{h['return_pct']:+.2f}%",
            "섹터트렌드": trend_map.get(h["sector_trend"], "→ 중립"),
        })

    if holdings_data:
        df = pd.DataFrame(holdings_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # DOWNTREND 경고
    downtrend = [
        h for h in result.get("holdings_analysis", [])
        if h["sector_trend"] == "DOWNTREND"
    ]
    if downtrend:
        st.warning(f"⚠️ DOWNTREND 섹터 노출 종목 {len(downtrend)}개 감지: "
                   f"{', '.join([h['name'] for h in downtrend])}")

    # 전체 리포트
    with st.expander("📄 전체 리포트 보기"):
        st.code(result["final_report"], language=None)

    # 오류 로그
    if result.get("error_log"):
        with st.expander("⚠️ 오류 로그"):
            for err in result["error_log"]:
                st.warning(err)
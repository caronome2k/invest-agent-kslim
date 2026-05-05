# ==========================================
# frontend/pages/sector_page.py
# 섹터 트렌드 탭
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
from agents.graph import run_graph


def render(portfolio: dict, period_weeks: int):
    """섹터 트렌드 탭 렌더링"""

    st.subheader("📡 섹터 트렌드 분석")

    if st.button("🔄 섹터 분석 실행", key="btn_sector", type="primary"):
        with st.spinner("섹터 트렌드 분석 중..."):
            result = run_graph(
                user_input   = "섹터 트렌드 분석해줘",
                portfolio    = portfolio,
                period_weeks = period_weeks,
            )
            st.session_state.sector_result = result

    result = st.session_state.get("sector_result")
    if not result:
        st.info("섹터 분석 실행 버튼을 눌러주세요.")
        return

    sector_trends = result.get("sector_trends", [])
    if not sector_trends:
        st.warning("섹터 데이터가 없습니다.")
        return

    col1, col2 = st.columns(2)

    # 한국 섹터
    with col1:
        st.subheader("🇰🇷 한국 시장")
        kr_sectors = [s for s in sector_trends if s["market"] == "KR"]
        if kr_sectors:
            kr_df = pd.DataFrame(kr_sectors).sort_values("change_pct", ascending=True)
            fig   = px.bar(
                kr_df,
                x     = "change_pct",
                y     = "sector",
                orientation           = "h",
                color                 = "change_pct",
                color_continuous_scale    = ["red", "lightgray", "green"],
                color_continuous_midpoint = 0,
                labels = {"change_pct": "변동률 (%)", "sector": "섹터"},
                title  = f"한국 섹터 변동률 (최근 {period_weeks}주)",
            )
            fig.add_vline(x=5,  line_dash="dash", line_color="green", annotation_text="UPTREND (+5%)")
            fig.add_vline(x=-5, line_dash="dash", line_color="red",   annotation_text="DOWNTREND (-5%)")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

            # 트렌드 뱃지
            for s in sorted(kr_sectors, key=lambda x: x["change_pct"], reverse=True):
                badge = {"UPTREND": "🟢", "DOWNTREND": "🔴", "NEUTRAL": "🟡"}.get(s["trend"], "🟡")
                st.write(f"{badge} **{s['sector']}**: {s['change_pct']:+.2f}%")
        else:
            st.info("한국 섹터 데이터 없음")

    # 미국 섹터
    with col2:
        st.subheader("🇺🇸 미국 시장")
        us_sectors = [s for s in sector_trends if s["market"] == "US"]
        if us_sectors:
            us_df = pd.DataFrame(us_sectors).sort_values("change_pct", ascending=True)
            fig   = px.bar(
                us_df,
                x     = "change_pct",
                y     = "sector",
                orientation           = "h",
                color                 = "change_pct",
                color_continuous_scale    = ["red", "lightgray", "green"],
                color_continuous_midpoint = 0,
                labels = {"change_pct": "변동률 (%)", "sector": "섹터"},
                title  = f"미국 섹터 변동률 (최근 {period_weeks}주)",
            )
            fig.add_vline(x=5,  line_dash="dash", line_color="green", annotation_text="UPTREND (+5%)")
            fig.add_vline(x=-5, line_dash="dash", line_color="red",   annotation_text="DOWNTREND (-5%)")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

            for s in sorted(us_sectors, key=lambda x: x["change_pct"], reverse=True):
                badge = {"UPTREND": "🟢", "DOWNTREND": "🔴", "NEUTRAL": "🟡"}.get(s["trend"], "🟡")
                st.write(f"{badge} **{s['sector']}**: {s['change_pct']:+.2f}%")
        else:
            st.info("미국 섹터 데이터 없음")

    st.divider()

    # 내 포트폴리오 섹터 노출 현황
    holdings = result.get("holdings_analysis", [])
    if holdings:
        st.subheader("📋 내 포트폴리오 섹터 노출")
        exposure_data = []
        for h in holdings:
            badge = {"UPTREND": "🟢", "DOWNTREND": "🔴", "NEUTRAL": "🟡"}.get(h["sector_trend"], "🟡")
            exposure_data.append({
                "티커"      : h["ticker"],
                "종목명"    : h["name"],
                "섹터"      : h["sector"],
                "트렌드"    : f"{badge} {h['sector_trend']}",
            })
        df = pd.DataFrame(exposure_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # 전체 리포트
    with st.expander("📄 전체 리포트 보기"):
        st.code(result["final_report"], language=None)
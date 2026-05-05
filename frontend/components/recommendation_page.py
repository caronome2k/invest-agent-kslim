# ==========================================
# frontend/pages/recommendation_page.py
# 매매 추천 탭
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
from agents.graph import run_graph


def render(portfolio: dict, period_weeks: int):
    """매매 추천 탭 렌더링"""

    st.subheader("💡 매매 추천")

    if st.button("🔄 매매 추천 실행", key="btn_rec", type="primary"):
        with st.spinner("매매 추천 생성 중... (약 30초 소요)"):
            result = run_graph(
                user_input   = "매매 추천해줘",
                portfolio    = portfolio,
                period_weeks = period_weeks,
            )
            st.session_state.rec_result = result

    result = st.session_state.get("rec_result")
    if not result:
        st.info("매매 추천 실행 버튼을 눌러주세요.")
        return

    # 환율 정보
    rate = result.get("exchange_rate", {})
    if rate:
        st.caption(
            f"💱 기준 환율: {rate.get('USD_KRW', 0):,.0f}원 "
            f"| 기준일: {result.get('analysis_date', '')}"
        )

    st.divider()

    # 매매 추천 카드
    ACTION_EMOJI = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
    recommendations = result.get("recommendations", [])

    if not recommendations:
        st.info("추천 데이터가 없습니다.")
    else:
        st.subheader(f"매매 추천 ({len(recommendations)}건)")

        # SELL 먼저 표시
        for action_type in ["SELL", "BUY", "HOLD"]:
            filtered = [r for r in recommendations if r["action"] == action_type]
            for r in filtered:
                emoji = ACTION_EMOJI.get(r["action"], "⚪")
                with st.expander(
                    f"{emoji} [{r['action']}] {r['name']} ({r['ticker']})",
                    expanded = (action_type in ("SELL", "BUY"))
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**📝 사유**")
                        st.write(r["reason"])
                        st.write(f"**📌 출처**: {r['source']}")
                    with col2:
                        st.warning(f"⚠️ **리스크**: {r['risk_warning']}")
                        st.progress(
                            r["confidence"],
                            text=f"신뢰도: {r['confidence']*100:.0f}%"
                        )

    st.divider()

    # 월 투자금 배분
    monthly_deposit = result.get("monthly_deposit", 0)
    allocation      = result.get("allocation", [])

    st.subheader(f"💰 월 투자금 배분 가이드 ({monthly_deposit:,}원)")

    if not allocation:
        st.info("배분 데이터가 없습니다.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            alloc_df = pd.DataFrame(allocation)
            fig = px.pie(
                alloc_df,
                values = "amount_krw",
                names  = "name",
                title  = "투자금 배분 비중",
                hole   = 0.3,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            for a in allocation:
                st.write(f"**{a['name']}** ({a['ticker']})")
                st.write(f"💵 {a['amount_krw']:,}원 ({a['ratio_pct']}%)")
                st.caption(f"사유: {a['reason']}")
                st.divider()

    # 전체 리포트
    with st.expander("📄 전체 리포트 보기"):
        st.code(result["final_report"], language=None)

    # 오류 로그
    if result.get("error_log"):
        with st.expander("⚠️ 오류 로그"):
            for err in result["error_log"]:
                st.warning(err)
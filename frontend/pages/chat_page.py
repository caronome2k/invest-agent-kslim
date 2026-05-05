# ==========================================
# frontend/pages/chat_page.py
# 대화 질의 탭
# ==========================================

import streamlit as st
from agents.graph import run_graph


def render(portfolio: dict, period_weeks: int):
    """대화 질의 탭 렌더링"""

    st.subheader("💬 대화형 질의")
    st.caption("포트폴리오 컨텍스트를 유지하며 투자 관련 질문에 답변합니다.")

    # 빠른 질문 버튼
    st.write("**빠른 질문:**")
    col1, col2, col3 = st.columns(3)
    quick_input = None
    if col1.button("📊 전체 수익률은?"):
        quick_input = "내 전체 포트폴리오 수익률은 어때?"
    if col2.button("💱 환율 영향은?"):
        quick_input = "환율이 내 포트폴리오에 미치는 영향은?"
    if col3.button("🔍 리밸런싱 필요해?"):
        quick_input = "지금 리밸런싱이 필요할까?"

    st.divider()

    # 대화 히스토리 출력
    chat_history = st.session_state.get("chat_history", [])
    for chat in chat_history:
        if chat["role"] == "user":
            st.chat_message("user").write(chat["content"])
        else:
            st.chat_message("assistant").write(chat["content"])

    # 빠른 질문 또는 직접 입력 처리
    user_input = st.chat_input("질문을 입력하세요 (예: 삼성전자 지금 팔아야 해?)")
    user_input = quick_input or user_input

    if user_input:
        st.chat_message("user").write(user_input)

        with st.spinner("답변 생성 중..."):
            result = run_graph(
                user_input   = user_input,
                portfolio    = portfolio,
                chat_history = chat_history,
            )

        answer = result["final_report"]
        st.chat_message("assistant").write(answer)

        # 히스토리 업데이트
        st.session_state.chat_history = result["chat_history"]
        st.session_state.last_result  = result
        st.rerun()

    # 대화 초기화 버튼
    if chat_history:
        st.divider()
        if st.button("🗑️ 대화 초기화", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
# ==========================================
# frontend/app.py
# Streamlit 앱 진입점
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.parser import parse_portfolio
from frontend.pages import briefing_page, sector_page, recommendation_page, chat_page

# ------------------------------------------
# 페이지 기본 설정
# ------------------------------------------
st.set_page_config(
    page_title            = "개인 투자 추천 Agent",
    page_icon             = "📊",
    layout                = "wide",
    initial_sidebar_state = "expanded",
)

# ------------------------------------------
# 세션 상태 초기화
# ------------------------------------------
if "portfolio"    not in st.session_state: st.session_state.portfolio    = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "period_weeks" not in st.session_state: st.session_state.period_weeks = 4
if "last_result"  not in st.session_state: st.session_state.last_result  = None
if "sector_result"not in st.session_state: st.session_state.sector_result= None
if "rec_result"   not in st.session_state: st.session_state.rec_result   = None

# ------------------------------------------
# 사이드바
# ------------------------------------------
with st.sidebar:
    st.title("📊 투자 추천 Agent")
    st.divider()

    # 포트폴리오 업로드
    st.subheader("📁 포트폴리오 업로드")
    uploaded = st.file_uploader("portfolio.txt", type=["txt"])

    if uploaded:
        import tempfile
        contents = uploaded.read()
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        try:
            portfolio = parse_portfolio(tmp_path)
            st.session_state.portfolio = portfolio
            os.unlink(tmp_path)
            st.success(f"✅ {len(portfolio['holdings'])}개 종목 등록 완료")
        except Exception as e:
            st.error(f"파싱 오류: {e}")

    # 기본 portfolio.txt 자동 로드
    if st.session_state.portfolio is None:
        root     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(root, "portfolio.txt")
        if os.path.exists(filepath):
            try:
                st.session_state.portfolio = parse_portfolio(filepath)
                st.info("📂 기본 portfolio.txt 로드됨")
            except Exception:
                pass

    # 포트폴리오 요약
    if st.session_state.portfolio:
        p = st.session_state.portfolio
        st.divider()
        st.subheader("📋 포트폴리오 현황")
        col1, col2 = st.columns(2)
        col1.metric("총 종목 수", f"{len(p['holdings'])}개")
        col2.metric("월 투자금",  f"{p['monthly_deposit']:,}원")
        kr = len([h for h in p["holdings"] if h["currency"] == "KRW"])
        us = len([h for h in p["holdings"] if h["currency"] == "USD"])
        col1.metric("한국 종목", f"{kr}개")
        col2.metric("미국 종목", f"{us}개")

    st.divider()

    # 분석 기간 설정
    st.subheader("⚙️ 설정")
    st.session_state.period_weeks = st.selectbox(
        "섹터 분석 기간",
        options      = [2, 4, 8, 12],
        index        = 1,
        format_func  = lambda x: f"{x}주",
    )

    # 환율 정보
    if st.session_state.last_result:
        rate = st.session_state.last_result.get("exchange_rate", {})
        if rate:
            st.divider()
            st.subheader("💱 환율")
            st.metric(
                "USD/KRW",
                f"{rate.get('USD_KRW', 0):,.0f}원",
                f"{rate.get('change_dir','')}{abs(rate.get('change', 0)):.0f}원",
            )

# ------------------------------------------
# 메인 화면
# ------------------------------------------
st.title("📊 개인 투자 추천 Agent")

if st.session_state.portfolio is None:
    st.warning("⬅️ 왼쪽 사이드바에서 portfolio.txt 를 업로드해주세요.")
    st.stop()

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Daily 브리핑",
    "📡 섹터 트렌드",
    "💡 매매 추천",
    "💬 대화 질의",
])

with tab1:
    briefing_page.render(
        portfolio    = st.session_state.portfolio,
        period_weeks = st.session_state.period_weeks,
    )

with tab2:
    sector_page.render(
        portfolio    = st.session_state.portfolio,
        period_weeks = st.session_state.period_weeks,
    )

with tab3:
    recommendation_page.render(
        portfolio    = st.session_state.portfolio,
        period_weeks = st.session_state.period_weeks,
    )

with tab4:
    chat_page.render(
        portfolio    = st.session_state.portfolio,
        period_weeks = st.session_state.period_weeks,
    )
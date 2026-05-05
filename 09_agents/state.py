# ==========================================
# agents/state.py
# LangGraph Agent 간 공유 State 정의
# ==========================================

from typing import TypedDict, List, Optional, Annotated
import operator


# ------------------------------------------
# 보유 종목 단위 구조
# ------------------------------------------
class HoldingItem(TypedDict):
    ticker:         str         # 종목코드 또는 티커 (예: 005930, AAPL)
    name:           str         # 종목명
    market:         str         # KOSPI / KOSDAQ / NASDAQ / NYSE
    sector:         str         # 섹터명
    quantity:       int         # 보유 수량
    avg_price:      float       # 평균 매입가
    currency:       str         # KRW / USD
    buy_date:       str         # 최초 매입일 (YYYY-MM-DD)
    memo:           Optional[str]  # 메모 (선택)


# ------------------------------------------
# 종목별 시세 + 수익률 구조
# ------------------------------------------
class HoldingAnalysis(TypedDict):
    ticker:             str
    name:               str
    market:             str
    sector:             str
    current_price:      float       # 현재가 (원화 또는 달러)
    current_price_krw:  float       # 원화 환산 현재가
    avg_price:          float       # 평균 매입가
    avg_price_krw:      float       # 원화 환산 매입가
    quantity:           int
    eval_amount_krw:    float       # 평가금액 (원화)
    invest_amount_krw:  float       # 투자원금 (원화)
    return_pct:         float       # 수익률 (%)
    sector_trend:       str         # UPTREND / DOWNTREND / NEUTRAL
    currency:           str


# ------------------------------------------
# 섹터 트렌드 구조
# ------------------------------------------
class SectorTrend(TypedDict):
    sector:         str         # 섹터명
    market:         str         # KR / US
    change_pct:     float       # 기간 변동률 (%)
    trend:          str         # UPTREND / DOWNTREND / NEUTRAL
    period_weeks:   int         # 분석 기간 (주)
    source:         str         # 데이터 출처


# ------------------------------------------
# 매매 추천 단위 구조
# ------------------------------------------
class TradeRecommendation(TypedDict):
    ticker:         str
    name:           str
    action:         str         # BUY / SELL / HOLD
    reason:         str         # 추천 사유 (3문장 이내)
    source:         str         # 근거 데이터 출처
    risk_warning:   str         # 리스크 경고
    confidence:     float       # 추천 신뢰도 0.0 ~ 1.0


# ------------------------------------------
# 월 투자금 배분 단위 구조
# ------------------------------------------
class AllocationItem(TypedDict):
    ticker:         str
    name:           str
    amount_krw:     int         # 배분 금액 (원화)
    ratio_pct:      float       # 비중 (%)
    reason:         str         # 배분 사유


# ------------------------------------------
# LangGraph 공유 State 정의
# ==========================================
# Annotated[List, operator.add] 는
# 여러 Agent가 리스트에 항목을 추가할 때
# 덮어쓰지 않고 누적(append)되도록 처리
# ------------------------------------------
class PortfolioState(TypedDict):

    # 사용자 입력
    user_input:         str                         # 사용자 메시지
    route:              str                         # 실행 경로 (supervisor 결정)

    # 포트폴리오 원본 (portfolio.txt 파싱 결과)
    holdings:           List[HoldingItem]           # 보유 종목 리스트
    monthly_deposit:    int                         # 월 정기 투자금 (원)
    investor_name:      str                         # 투자자명

    # 데이터 수집 Agent 결과
    market_data:        dict                        # 종가 원시 데이터 (KR/US)
    exchange_rate:      dict                        # 환율 정보

    # 포트폴리오 분석 Agent 결과
    holdings_analysis:  List[HoldingAnalysis]       # 종목별 수익률 분석
    total_invest_krw:   float                       # 총 투자 원금 (원)
    total_eval_krw:     float                       # 총 평가금액 (원)
    total_return_pct:   float                       # 전체 수익률 (%)
    fx_return_pct:      float                       # 환율 조정 수익률 (%)

    # 섹터 분석 Agent 결과
    sector_trends:      List[SectorTrend]           # 섹터별 트렌드

    # RAG 검색 결과
    rag_context:        str                         # 검색된 섹터 리포트 컨텍스트

    # 매매 추천 Agent 결과
    recommendations:    List[TradeRecommendation]   # 매매 추천 리스트
    allocation:         List[AllocationItem]        # 월 투자금 배분 가이드

    # 리포트 생성 Agent 결과
    final_report:       str                         # 최종 출력 텍스트

    # 대화 Agent
    chat_history:       Annotated[List[dict], operator.add]  # 대화 히스토리 누적

    # 메타
    analysis_date:      str                         # 분석 기준일 (YYYY-MM-DD)
    period_weeks:       int                         # 섹터 분석 기간 (주)
    error_log:          Annotated[List[str], operator.add]   # 오류 로그 누적


# ------------------------------------------
# State 초기값 생성 헬퍼
# ------------------------------------------
def create_initial_state(
    user_input: str,
    holdings: List[HoldingItem] = None,
    monthly_deposit: int = 1500000,
    investor_name: str = "",
    period_weeks: int = 4,
) -> PortfolioState:
    from datetime import datetime

    return PortfolioState(
        # 사용자 입력
        user_input      = user_input,
        route           = "",

        # 포트폴리오
        holdings        = holdings or [],
        monthly_deposit = monthly_deposit,
        investor_name   = investor_name,

        # 데이터 수집
        market_data     = {},
        exchange_rate   = {},

        # 포트폴리오 분석
        holdings_analysis   = [],
        total_invest_krw    = 0.0,
        total_eval_krw      = 0.0,
        total_return_pct    = 0.0,
        fx_return_pct       = 0.0,

        # 섹터 분석
        sector_trends   = [],

        # RAG
        rag_context     = "",

        # 추천
        recommendations = [],
        allocation      = [],

        # 리포트
        final_report    = "",

        # 대화
        chat_history    = [],

        # 메타
        analysis_date   = datetime.today().strftime("%Y-%m-%d"),
        period_weeks    = period_weeks,
        error_log       = [],
    )


# ------------------------------------------
# 동작 확인용
# python agents/state.py 로 직접 실행
# ------------------------------------------
if __name__ == "__main__":
    state = create_initial_state(
        user_input      = "오늘 포트폴리오 브리핑 보여줘",
        investor_name   = "홍길동",
        monthly_deposit = 1500000,
        period_weeks    = 4,
    )
    print("[state] 초기 State 생성 완료")
    for key, value in state.items():
        print(f"  {key:20s}: {value}")
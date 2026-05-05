# ==========================================
# prompts/recommendation_prompt.py
# 매매 추천 Agent 프롬프트
# CoT + Few-shot 기반 추천 생성
# ==========================================

RECOMMENDATION_SYSTEM_PROMPT = """당신은 전문 투자 어드바이저입니다.

[CoT - 매매 추천 절차]
추천을 생성할 때 반드시 아래 순서로 사고하세요:

1단계 - 포트폴리오 현황 파악
   → 보유 종목별 수익률과 섹터 트렌드를 확인합니다.
   → DOWNTREND 섹터 노출 종목을 우선 식별합니다.

2단계 - 매도 후보 선별
   → DOWNTREND 섹터 + 현재 수익 구간 → 매도 검토
   → DOWNTREND 섹터 + 손실 구간     → 손절 또는 보유 검토
   → 수익률이 과도하게 높은 종목     → 부분 차익실현 검토

3단계 - 매수 후보 선별
   → UPTREND 섹터 중 포트폴리오 비중 부족 종목 식별
   → 현재 보유하지 않은 UPTREND 섹터 종목 검토
   → ETF를 통한 분산 투자 고려

4단계 - 월 투자금 배분
   → UPTREND 섹터 비중을 높이는 방향으로 배분
   → 총액({monthly_deposit}원)을 초과하지 않도록 배분
   → 한/미 시장 균형과 환율 영향을 고려

5단계 - 리스크 검토
   → 모든 추천에 리스크 경고를 포함합니다.
   → 분할 매수/매도를 기본 원칙으로 합니다.

[필수 규칙]
- 레버리지 상품과 펀드는 절대 추천하지 마세요.
- 모든 추천에 근거 데이터 출처를 명시하세요.
- 추천 사유는 3문장 이내로 작성하세요.

[Few-shot 예시]

입력 상황:
- LG에너지솔루션 (2차전지 섹터, DOWNTREND -13.2%, 수익률 +4.1%)
- NVDA (AI 반도체 섹터, UPTREND +18.2%, 미보유)

출력 예시:
SELL - LG에너지솔루션
사유: 2차전지 섹터가 4주간 -13.2% 하락하며 DOWNTREND 진입.
     현재 수익률 +4.1% 구간에서 수익 실현이 유리.
     섹터 반등 신호 확인 후 재진입 검토 권장.
출처: KRX ETF (305720.KS)
리스크: 단기 반등 가능성 존재, 분할 매도 권장

BUY - NVDA
사유: AI 반도체 섹터 4주간 +18.2% 상승, UPTREND 지속 중.
     포트폴리오 내 AI 반도체 비중 부족 상태.
     장기 AI 인프라 수요 증가 추세 지속 전망.
출처: Yahoo Finance SOXX ETF
리스크: 고밸류에이션 부담, 분할 매수 권장
"""

RECOMMENDATION_USER_TEMPLATE = """다음 정보를 바탕으로 매매 추천 리포트를 작성하세요.

[보유 종목 현황]
{holdings_summary}

[섹터 트렌드]
상승 섹터 (UPTREND) : {uptrend_sectors}
하락 섹터 (DOWNTREND): {downtrend_sectors}
중립 섹터 (NEUTRAL) : {neutral_sectors}

[환율 정보]
현재 환율: {usd_krw:,.0f}원 (전일比 {change_dir}{change_abs:.0f}원)

[월 정기 투자금]
{monthly_deposit:,}원

{rag_section}

위 CoT 절차에 따라 단계별로 분석하고 매매 추천을 생성하세요.
"""


def build_recommendation_prompt(
    holdings_analysis : list,
    sector_trends     : list,
    exchange_rate     : dict,
    monthly_deposit   : int,
    rag_context       : str = "",
    analysis_date     : str = "",
) -> dict:

    # 보유 종목 요약
    holdings_summary = "\n".join([
        f"  - {h['name']}({h['ticker']}): 수익률 {h['return_pct']:+.2f}%, "
        f"섹터 {h['sector']} [{h['sector_trend']}]"
        for h in holdings_analysis
    ]) or "  데이터 없음"

    # 섹터 분류
    uptrend   = [s["sector"] for s in sector_trends if s["trend"] == "UPTREND"]
    downtrend = [s["sector"] for s in sector_trends if s["trend"] == "DOWNTREND"]
    neutral   = [s["sector"] for s in sector_trends if s["trend"] == "NEUTRAL"]

    # RAG 섹션
    rag_section = f"[참고 리포트]\n{rag_context}" if rag_context else ""

    system_prompt = RECOMMENDATION_SYSTEM_PROMPT.format(
        monthly_deposit = monthly_deposit,
    )

    user_prompt = RECOMMENDATION_USER_TEMPLATE.format(
        holdings_summary  = holdings_summary,
        uptrend_sectors   = ", ".join(uptrend)   or "없음",
        downtrend_sectors = ", ".join(downtrend) or "없음",
        neutral_sectors   = ", ".join(neutral)   or "없음",
        usd_krw           = exchange_rate.get("USD_KRW", 0),
        change_dir        = exchange_rate.get("change_dir", "-"),
        change_abs        = abs(exchange_rate.get("change", 0)),
        monthly_deposit   = monthly_deposit,
        rag_section       = rag_section,
    )

    return {"system": system_prompt, "user": user_prompt}
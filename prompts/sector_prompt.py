# ==========================================
# prompts/sector_prompt.py
# 섹터 분석 Agent 프롬프트
# CoT 기반 단계별 분류 구조
# ==========================================

SECTOR_ANALYSIS_SYSTEM_PROMPT = """당신은 한국과 미국 주식 시장을 담당하는 전문 섹터 애널리스트입니다.

[CoT - 섹터 트렌드 분류 절차]
섹터 트렌드를 분류할 때 반드시 아래 순서로 사고하세요:

1단계 - 데이터 확인
   → 지정된 기간의 섹터 지수/ETF 변동률을 확인합니다.
   → 데이터가 누락된 섹터는 NEUTRAL로 처리합니다.

2단계 - 트렌드 분류 기준 적용
   → 변동률 +5% 이상  : UPTREND  (상승 추세)
   → 변동률 -5% 이하  : DOWNTREND (하락 추세)
   → -5% ~ +5% 사이  : NEUTRAL  (중립)

3단계 - 지속성 판단
   → 단순 변동이 아닌 추세의 지속성을 고려합니다.
   → 급등/급락 직후라면 NEUTRAL에 가깝게 판단합니다.

4단계 - 보유 종목 매핑
   → 사용자의 보유 종목이 속한 섹터 트렌드를 확인합니다.
   → DOWNTREND 섹터 노출 종목을 우선 식별합니다.

5단계 - 결과 출력
   → 섹터명, 변동률, 트렌드, 데이터 출처를 명시합니다.

[주의사항]
- 레버리지 상품과 펀드는 절대 추천하지 마세요.
- 분석 시 사용한 데이터 출처와 기간을 반드시 명시하세요.
- 확실하지 않은 정보는 추측하지 마세요.
"""

SECTOR_ANALYSIS_USER_TEMPLATE = """아래 섹터 데이터를 분석하여 트렌드를 분류하세요.

분석 기간: {period_weeks}주
기준일: {analysis_date}

[한국 섹터 데이터]
{kr_sector_data}

[미국 섹터 데이터]
{us_sector_data}

[내 보유 종목 섹터]
{holdings_sectors}

위 CoT 절차에 따라 단계별로 분석하고 최종 결과를 제시하세요.
"""


def get_sector_analysis_prompt(
    period_weeks    : int,
    analysis_date   : str,
    kr_sector_data  : str,
    us_sector_data  : str,
    holdings_sectors: str,
) -> dict:
    return {
        "system": SECTOR_ANALYSIS_SYSTEM_PROMPT,
        "user"  : SECTOR_ANALYSIS_USER_TEMPLATE.format(
            period_weeks     = period_weeks,
            analysis_date    = analysis_date,
            kr_sector_data   = kr_sector_data,
            us_sector_data   = us_sector_data,
            holdings_sectors = holdings_sectors,
        )
    }
# ==========================================
# rag/loader.py
# 문서 로딩 및 청킹
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import requests
from datetime import datetime
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size    = 500,
    chunk_overlap = 50,
    separators    = ["\n\n", "\n", ".", " "],
)

US_SECTOR_ETF = {
    "AI 반도체" : "SOXX",
    "기술주"    : "XLK",
    "헬스케어"  : "XLV",
    "에너지"    : "XLE",
    "금융"      : "XLF",
    "소비재"    : "XLY",
    "부동산/리츠": "XLRE",
}


def load_us_sector_news(max_per_sector: int = 5) -> list:
    """yfinance 기반 미국 섹터 ETF 뉴스 수집"""
    documents = []

    for sector_name, etf_ticker in US_SECTOR_ETF.items():
        try:
            t    = yf.Ticker(etf_ticker)
            news = t.news or []
            count = 0

            for article in news:
                if count >= max_per_sector:
                    break
                title   = article.get("title", "")
                summary = article.get("summary", "") or article.get("description", "")
                if not title:
                    continue

                content = f"[{sector_name} 섹터 뉴스]\n제목: {title}\n내용: {summary}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "source" : f"Yahoo Finance News ({etf_ticker})",
                        "sector" : sector_name,
                        "market" : "US",
                        "type"   : "news",
                        "date"   : datetime.today().strftime("%Y-%m-%d"),
                    }
                )
                documents.append(doc)
                count += 1

        except Exception as e:
            print(f"[loader] {sector_name} 뉴스 수집 오류: {e}")

    return documents


def load_glossary_documents() -> list:
    """투자 용어 사전 문서 로딩 (없으면 자동 생성)"""
    root         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    glossary_dir = os.path.join(root, "data", "documents", "glossary")
    os.makedirs(glossary_dir, exist_ok=True)

    default_path = os.path.join(glossary_dir, "investment_glossary.txt")
    if not os.path.exists(default_path):
        _create_default_glossary(default_path)

    documents = []
    for filename in os.listdir(glossary_dir):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(glossary_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            doc = Document(
                page_content=content,
                metadata={
                    "source": filename,
                    "sector": "일반",
                    "market": "ALL",
                    "type"  : "glossary",
                    "date"  : datetime.today().strftime("%Y-%m-%d"),
                }
            )
            documents.append(doc)
        except Exception as e:
            print(f"[loader] 용어 사전 로딩 오류: {e}")

    return documents


def _create_default_glossary(filepath: str):
    """기본 투자 용어 사전 파일 생성"""
    content = """# 투자 용어 사전

## 섹터 트렌드 분류 기준
- UPTREND: 최근 4주간 섹터 지수 변동률 +5% 이상
- DOWNTREND: 최근 4주간 섹터 지수 변동률 -5% 이하
- NEUTRAL: -5% ~ +5% 범위

## 주요 투자 지표
- 수익률: (현재가 - 매입가) / 매입가 × 100
- 환율 효과: 원화 약세 시 미국 주식 원화 환산 수익률 상승
- 포트폴리오 수익률: 전체 평가금액 / 전체 투자원금 × 100

## 리밸런싱 원칙
- 하락 섹터 보유 종목은 수익 구간에서 매도 검토
- 상승 섹터 비중이 낮으면 월 투자금으로 보완
- 분할 매수/매도 원칙 준수

## 주요 미국 섹터 ETF
- SOXX: iShares 반도체 ETF (AI 반도체 섹터 대표)
- XLK: Technology Select Sector SPDR (기술주)
- XLV: Health Care Select Sector SPDR (헬스케어)
- XLE: Energy Select Sector SPDR (에너지)
- XLF: Financial Select Sector SPDR (금융)
- VOO: Vanguard S&P 500 ETF (미국 전체 시장)

## 주요 한국 섹터 ETF
- KODEX 반도체 (091160): 국내 반도체 대표 ETF
- KODEX 2차전지산업 (305720): 2차전지 섹터 대표
- KODEX 200 (069500): KOSPI 200 추종
- KODEX 코스닥150 (229200): KOSDAQ 150 추종

## 환율과 투자
- 원화 약세(환율 상승): 미국 주식 원화 환산 수익률 증가
- 원화 강세(환율 하락): 미국 주식 원화 환산 수익률 감소
- 환율 1% 변동 시 미국 주식 비중만큼 포트폴리오 수익률 영향
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[loader] 기본 용어 사전 생성: {filepath}")


def load_all_documents() -> list:
    """모든 문서를 수집하고 청킹하여 반환"""
    print("[loader] 문서 수집 시작...")
    all_docs = []

    us_news = load_us_sector_news()
    print(f"[loader] 미국 섹터 뉴스: {len(us_news)}건")
    all_docs.extend(us_news)

    glossary = load_glossary_documents()
    print(f"[loader] 투자 용어 사전: {len(glossary)}건")
    all_docs.extend(glossary)

    chunks = TEXT_SPLITTER.split_documents(all_docs)
    print(f"[loader] 총 청크 수: {len(chunks)}개")
    return chunks


if __name__ == "__main__":
    chunks = load_all_documents()
    print(f"\n=== 샘플 청크 (처음 3개) ===")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n[청크 {i+1}]")
        print(f"  내용  : {chunk.page_content[:100]}...")
        print(f"  메타  : {chunk.metadata}")
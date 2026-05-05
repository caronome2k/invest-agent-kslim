# ==========================================
# utils/parser.py
# portfolio.txt 파싱 유틸
# ==========================================

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_portfolio(filepath: str) -> dict:
    """
    portfolio.txt 파일을 읽어 포트폴리오 정보를 반환합니다.

    Returns:
        {
            "investor_name"  : "홍길동",
            "monthly_deposit": 1500000,
            "base_currency"  : "KRW",
            "holdings"       : [dict, ...]
        }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"포트폴리오 파일을 찾을 수 없습니다: {filepath}")

    result = {
        "investor_name"  : "",
        "monthly_deposit": 1500000,
        "base_currency"  : "KRW",
        "holdings"       : [],
    }

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 빈 줄 또는 주석 스킵
            if not line or line.startswith("#"):
                continue

            # 메타 정보 파싱
            if "=" in line and "|" not in line:
                key, _, value = line.partition("=")
                key   = key.strip()
                value = value.strip()

                if key == "INVESTOR_NAME":
                    result["investor_name"] = value
                elif key == "MONTHLY_DEPOSIT":
                    result["monthly_deposit"] = int(value)
                elif key == "BASE_CURRENCY":
                    result["base_currency"] = value
                continue

            # 종목 데이터 파싱 (| 구분자)
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 7:
                    continue

                market = parts[2].upper()

                # 한국 주식 (KOSPI / KOSDAQ)
                if market in ("KOSPI", "KOSDAQ"):
                    holding = {
                        "ticker"   : parts[0],
                        "name"     : parts[1],
                        "market"   : market,
                        "sector"   : parts[3],
                        "quantity" : int(parts[4]),
                        "avg_price": float(parts[5]),
                        "currency" : "KRW",
                        "buy_date" : parts[6],
                        "memo"     : parts[7] if len(parts) > 7 else None,
                    }
                    result["holdings"].append(holding)

                # 미국 주식 (NASDAQ / NYSE)
                elif market in ("NASDAQ", "NYSE"):
                    holding = {
                        "ticker"   : parts[0],
                        "name"     : parts[1],
                        "market"   : market,
                        "sector"   : parts[3],
                        "quantity" : int(parts[4]),
                        "avg_price": float(parts[5]),
                        "currency" : "USD",
                        "buy_date" : parts[6],
                        "memo"     : parts[7] if len(parts) > 7 else None,
                    }
                    result["holdings"].append(holding)

    return result


def get_kr_tickers(holdings: list) -> list:
    """한국 종목 티커 리스트만 추출"""
    return [h["ticker"] for h in holdings if h["currency"] == "KRW"]


def get_us_tickers(holdings: list) -> list:
    """미국 종목 티커 리스트만 추출"""
    return [h["ticker"] for h in holdings if h["currency"] == "USD"]


# ------------------------------------------
# 동작 확인용
# python utils/parser.py 로 실행
# ------------------------------------------
if __name__ == "__main__":
    # 루트 기준 portfolio.txt 경로
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(root, "portfolio.txt")

    portfolio = parse_portfolio(filepath)
    print(f"[parser] 투자자         : {portfolio['investor_name']}")
    print(f"[parser] 월 투자금      : {portfolio['monthly_deposit']:,}원")
    print(f"[parser] 총 보유 종목   : {len(portfolio['holdings'])}개")

    kr = get_kr_tickers(portfolio["holdings"])
    us = get_us_tickers(portfolio["holdings"])
    print(f"[parser] 한국 종목      : {kr}")
    print(f"[parser] 미국 종목      : {us}")
# tools/exchange_rate.py
from pykrx import stock
from datetime import datetime, timedelta

def get_exchange_rate() -> dict:
    today = datetime.today()
    
    # 주말/공휴일 대비 최근 5거래일 중 가장 최근 데이터 사용
    from_date = (today - timedelta(days=7)).strftime("%Y%m%d")
    to_date = today.strftime("%Y%m%d")
    
    df = stock.get_exchange_rate_ohlcv_by_date(from_date, to_date, "USD")
    
    if df.empty:
        raise ValueError("환율 데이터를 가져올 수 없습니다.")
    
    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) >= 2 else latest
    
    return {
        "USD_KRW"     : float(latest["종가"]),
        "prev_USD_KRW": float(prev["종가"]),
        "change"      : round(float(latest["종가"]) - float(prev["종가"]), 2),
        "date"        : df.index[-1].strftime("%Y-%m-%d"),
        "source"      : "KRX"
    }
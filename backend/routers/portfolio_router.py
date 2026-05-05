# ==========================================
# backend/routers/portfolio_router.py
# 포트폴리오 업로드 라우터
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.parser import parse_portfolio
import tempfile

router = APIRouter()

# 세션 포트폴리오 저장 (메모리)
_portfolio_store = {}


@router.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    portfolio.txt 파일을 업로드하고 파싱합니다.
    """
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="txt 파일만 업로드 가능합니다.")

    try:
        # 임시 파일에 저장 후 파싱
        contents = await file.read()
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", delete=False
        ) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        portfolio = parse_portfolio(tmp_path)
        os.unlink(tmp_path)

        # 메모리에 저장
        _portfolio_store["current"] = portfolio

        return {
            "status"        : "success",
            "investor_name" : portfolio["investor_name"],
            "monthly_deposit": portfolio["monthly_deposit"],
            "total_holdings": len(portfolio["holdings"]),
            "kr_holdings"   : len([h for h in portfolio["holdings"] if h["currency"] == "KRW"]),
            "us_holdings"   : len([h for h in portfolio["holdings"] if h["currency"] == "USD"]),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current")
def get_current_portfolio():
    """현재 등록된 포트폴리오를 반환합니다."""
    portfolio = _portfolio_store.get("current")
    if not portfolio:
        raise HTTPException(status_code=404, detail="등록된 포트폴리오가 없습니다.")
    return portfolio


def get_portfolio() -> dict:
    """다른 라우터에서 포트폴리오를 가져올 때 사용"""
    portfolio = _portfolio_store.get("current")
    if not portfolio:
        # portfolio.txt 기본 경로에서 로드 시도
        root     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        filepath = os.path.join(root, "portfolio.txt")
        if os.path.exists(filepath):
            portfolio = parse_portfolio(filepath)
            _portfolio_store["current"] = portfolio
        else:
            raise HTTPException(status_code=404, detail="포트폴리오를 먼저 업로드해주세요.")
    return portfolio
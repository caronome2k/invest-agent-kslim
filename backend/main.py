# ==========================================
# backend/main.py
# FastAPI 앱 진입점
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    portfolio_router,
    briefing_router,
    sector_router,
    recommendation_router,
    chat_router,
)

app = FastAPI(
    title       = "개인 투자 추천 Agent API",
    description = "LangGraph 기반 Multi-Agent 투자 추천 서비스",
    version     = "1.0.0",
)

# CORS 설정 (Streamlit 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# 라우터 등록
app.include_router(portfolio_router.router,      prefix="/portfolio",     tags=["Portfolio"])
app.include_router(briefing_router.router,       prefix="/briefing",      tags=["Briefing"])
app.include_router(sector_router.router,         prefix="/sector",        tags=["Sector"])
app.include_router(recommendation_router.router, prefix="/recommendation", tags=["Recommendation"])
app.include_router(chat_router.router,           prefix="/chat",          tags=["Chat"])


@app.get("/")
def root():
    return {"message": "개인 투자 추천 Agent API 서버 정상 동작 중"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ------------------------------------------
# 실행: uvicorn backend.main:app --reload
# ------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
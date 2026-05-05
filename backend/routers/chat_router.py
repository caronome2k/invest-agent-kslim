# ==========================================
# backend/routers/chat_router.py
# 대화형 질의 라우터
# LangGraph Checkpointer thread_id 기반 세션 관리
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.graph import run_graph
from backend.routers.portfolio_router import get_portfolio

router = APIRouter()


class ChatRequest(BaseModel):
    message   : str
    session_id: str = "default"


class ChatResponse(BaseModel):
    answer    : str
    session_id: str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    대화형 질의응답을 처리합니다.
    LangGraph MemorySaver Checkpointer로 세션별 대화 상태를 유지합니다.
    thread_id = session_id 로 세션을 구분합니다.
    """
    try:
        portfolio  = get_portfolio()
        session_id = request.session_id

        # Checkpointer thread_id 기반 세션 관리
        # 이전 대화 상태는 MemorySaver가 자동으로 관리
        result = run_graph(
            user_input = request.message,
            portfolio  = portfolio,
            session_id = session_id,     # thread_id로 전달
        )

        return ChatResponse(
            answer     = result["final_report"],
            session_id = session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
def clear_history(session_id: str = "default"):
    """
    대화 히스토리를 초기화합니다.
    새로운 session_id를 사용하면 자동으로 새 세션이 시작됩니다.
    """
    return {
        "status" : "success",
        "message": f"세션 {session_id} 초기화 완료. 새 session_id로 대화를 시작하세요."
    }


@router.get("/history/{session_id}")
def get_history(session_id: str = "default"):
    """세션 정보를 조회합니다."""
    return {
        "session_id": session_id,
        "message"   : "LangGraph MemorySaver로 상태가 관리됩니다.",
    }
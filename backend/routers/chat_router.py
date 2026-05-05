# ==========================================
# backend/routers/chat_router.py
# 대화형 질의 라우터
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.graph import run_graph
from backend.routers.portfolio_router import get_portfolio

router = APIRouter()

# 세션 대화 히스토리 (메모리)
_chat_history_store = {}


class ChatRequest(BaseModel):
    message    : str
    session_id : str = "default"


class ChatResponse(BaseModel):
    answer     : str
    session_id : str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    대화형 질의응답을 처리합니다.
    포트폴리오 컨텍스트를 유지하며 답변합니다.
    """
    try:
        portfolio    = get_portfolio()
        session_id   = request.session_id
        chat_history = _chat_history_store.get(session_id, [])

        result = run_graph(
            user_input   = request.message,
            portfolio    = portfolio,
            chat_history = chat_history,
        )

        # 대화 히스토리 업데이트
        _chat_history_store[session_id] = result["chat_history"]

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
    """대화 히스토리를 초기화합니다."""
    _chat_history_store.pop(session_id, None)
    return {"status": "success", "message": f"세션 {session_id} 히스토리 초기화 완료"}


@router.get("/history/{session_id}")
def get_history(session_id: str = "default"):
    """대화 히스토리를 조회합니다."""
    history = _chat_history_store.get(session_id, [])
    return {"session_id": session_id, "history": history}
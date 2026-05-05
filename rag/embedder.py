# ==========================================
# rag/embedder.py
# 임베딩 생성
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_embeddings
from langchain_core.documents import Document


def get_embedding_model():
    """임베딩 모델 반환"""
    return get_embeddings("large")


def embed_documents(chunks: list[Document]) -> tuple:
    """
    문서 청크를 임베딩합니다.

    Returns:
        (chunks, embedding_model) 튜플
    """
    embedding_model = get_embedding_model()
    print(f"[embedder] 임베딩 모델: {type(embedding_model).__name__}")
    print(f"[embedder] 임베딩 대상: {len(chunks)}개 청크")
    return chunks, embedding_model


if __name__ == "__main__":
    from rag.loader import load_all_documents

    chunks = load_all_documents()
    docs, model = embed_documents(chunks)
    print(f"[embedder] 임베딩 준비 완료: {len(docs)}개 청크")
    print(f"[embedder] 모델: {type(model).__name__}")
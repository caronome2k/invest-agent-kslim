# ==========================================
# rag/vectorstore.py
# FAISS 벡터 저장소 관리
# ==========================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import get_embeddings, get_service_config


def get_vectorstore_path() -> str:
    """벡터 저장소 경로 반환"""
    config = get_service_config()
    path   = config["vectorstore_path"]
    os.makedirs(path, exist_ok=True)
    return path


def build_vectorstore(chunks: list[Document]) -> FAISS:
    """
    문서 청크로 FAISS 벡터 저장소를 생성하고 저장합니다.
    """
    embeddings = get_embeddings("large")
    path       = get_vectorstore_path()

    print(f"[vectorstore] 벡터 저장소 생성 중... ({len(chunks)}개 청크)")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(path)
    print(f"[vectorstore] 저장 완료: {path}")

    return vectorstore


def load_vectorstore() -> FAISS:
    """
    저장된 FAISS 벡터 저장소를 로드합니다.
    없으면 자동으로 새로 빌드합니다.
    """
    embeddings = get_embeddings("large")
    path       = get_vectorstore_path()
    index_path = os.path.join(path, "index.faiss")

    if os.path.exists(index_path):
        print(f"[vectorstore] 기존 벡터 저장소 로드: {path}")
        return FAISS.load_local(
            path,
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        print("[vectorstore] 벡터 저장소 없음 → 새로 빌드")
        from rag.loader import load_all_documents
        chunks = load_all_documents()
        return build_vectorstore(chunks)


def rebuild_vectorstore() -> FAISS:
    """벡터 저장소를 강제로 재빌드합니다."""
    from rag.loader import load_all_documents
    chunks = load_all_documents()
    return build_vectorstore(chunks)


# 전역 벡터 저장소 인스턴스 (싱글턴)
_vectorstore = None

def get_vectorstore() -> FAISS:
    """벡터 저장소 싱글턴 반환"""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = load_vectorstore()
    return _vectorstore


if __name__ == "__main__":
    print("=== 벡터 저장소 빌드 테스트 ===")
    vs = rebuild_vectorstore()

    print("\n=== 검색 테스트 ===")
    results = vs.similarity_search("AI 반도체 섹터 트렌드", k=3)
    for i, doc in enumerate(results):
        print(f"\n[결과 {i+1}]")
        print(f"  내용  : {doc.page_content[:100]}...")
        print(f"  메타  : {doc.metadata}")
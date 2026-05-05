# llm_factory.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings

load_dotenv()


def get_llm(model="gpt4o"):
    """
    ENV_MODE 에 따라 OpenAI 또는 Azure OpenAI LLM 반환

    Args:
        model: "gpt4o" | "gpt4o_mini"

    Returns:
        ChatOpenAI 또는 AzureChatOpenAI 인스턴스
    """
    deploy_map = {
        "gpt4o"     : os.getenv("AOAI_DEPLOY_GPT4O"),
        "gpt4o_mini": os.getenv("AOAI_DEPLOY_GPT4O_MINI"),
    }
    deployment = deploy_map.get(model)
    if not deployment:
        raise ValueError(f"지원하지 않는 모델: {model}. 사용 가능: {list(deploy_map.keys())}")

    if os.getenv("ENV_MODE") == "azure":
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_API_KEY"),
            azure_deployment=deployment,
            api_version="2024-08-01-preview",
        )
    else:
        return ChatOpenAI(
            api_key=os.getenv("AOAI_API_KEY"),
            model=deployment,
        )


def get_embeddings(model="large"):
    """
    ENV_MODE 에 따라 OpenAI 또는 Azure OpenAI Embeddings 반환

    Args:
        model: "large" | "small" | "ada"

    Returns:
        OpenAIEmbeddings 또는 AzureOpenAIEmbeddings 인스턴스
    """
    deploy_map = {
        "large": os.getenv("AOAI_DEPLOY_EMBED_3_LARGE"),
        "small": os.getenv("AOAI_DEPLOY_EMBED_3_SMALL"),
        "ada"  : os.getenv("AOAI_DEPLOY_EMBED_ADA"),
    }
    deployment = deploy_map.get(model)
    if not deployment:
        raise ValueError(f"지원하지 않는 모델: {model}. 사용 가능: {list(deploy_map.keys())}")

    if os.getenv("ENV_MODE") == "azure":
        return AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_API_KEY"),
            azure_deployment=deployment,
            api_version="2024-08-01-preview",
        )
    else:
        return OpenAIEmbeddings(
            api_key=os.getenv("AOAI_API_KEY"),
            model=deployment,
        )


# ------------------------------------------
# 단위 테스트
# ------------------------------------------
if __name__ == "__main__":
    import sys

    env_mode = os.getenv("ENV_MODE", "local")
    print(f"\n{'='*50}")
    print(f"  LLM Factory 단위 테스트 (ENV_MODE: {env_mode})")
    print(f"{'='*50}\n")

    all_passed = True

    # 테스트 1 - gpt4o LLM 연결
    print("[테스트 1] gpt4o LLM 연결 확인...")
    try:
        llm = get_llm("gpt4o")
        response = llm.invoke("안녕하세요. '테스트 성공'이라고만 답해주세요.")
        print(f"  ✅ 성공: {response.content}")
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        all_passed = False

    # 테스트 2 - gpt4o_mini LLM 연결
    print("\n[테스트 2] gpt4o_mini LLM 연결 확인...")
    try:
        llm = get_llm("gpt4o_mini")
        response = llm.invoke("안녕하세요. '테스트 성공'이라고만 답해주세요.")
        print(f"  ✅ 성공: {response.content}")
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        all_passed = False

    # 테스트 3 - Embeddings 연결
    print("\n[테스트 3] Embeddings 연결 확인...")
    try:
        embeddings = get_embeddings("large")
        vector = embeddings.embed_query("테스트 문장입니다.")
        print(f"  ✅ 성공: 벡터 차원 = {len(vector)}")
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        all_passed = False

    # 테스트 4 - 잘못된 모델명 예외처리
    print("\n[테스트 4] 잘못된 모델명 예외처리 확인...")
    try:
        get_llm("invalid_model")
        print("  ❌ 실패: 예외가 발생해야 합니다.")
        all_passed = False
    except ValueError as e:
        print(f"  ✅ 성공: {e}")

    # 최종 결과
    print(f"\n{'='*50}")
    print(f"  최종 결과: {'✅ 전체 통과' if all_passed else '❌ 일부 실패'}")
    print(f"{'='*50}\n")

    sys.exit(0 if all_passed else 1)
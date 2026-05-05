# ==========================================
# config.py
# LLM / Embedding 환경 전환 유틸
# ENV_MODE=local  → OpenAI 직접 사용
# ENV_MODE=azure  → Azure OpenAI 사용
# ==========================================

import os
from dotenv import load_dotenv

load_dotenv()

ENV_MODE = os.getenv("ENV_MODE", "local")


# ------------------------------------------
# LLM 클라이언트 반환
# model: "gpt4o" | "gpt4o_mini"
# ------------------------------------------
def get_llm(model: str = "gpt4o", temperature: float = 0.1):
    if ENV_MODE == "azure":
        from langchain_openai import AzureChatOpenAI

        deploy = (
            os.getenv("AOAI_DEPLOY_GPT4O")
            if model == "gpt4o"
            else os.getenv("AOAI_DEPLOY_GPT4O_MINI")
        )
        return AzureChatOpenAI(
            azure_deployment=deploy,
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_API_KEY"),
            api_version="2024-02-01",
            temperature=temperature,
        )
    else:
        from langchain_openai import ChatOpenAI

        model_name = (
            os.getenv("OPENAI_DEPLOY_GPT4O")
            if model == "gpt4o"
            else os.getenv("OPENAI_DEPLOY_GPT4O_MINI")
        )
        return ChatOpenAI(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=temperature,
        )


# ------------------------------------------
# Embedding 클라이언트 반환
# model: "large" | "small"
# ------------------------------------------
def get_embeddings(model: str = "large"):
    if ENV_MODE == "azure":
        from langchain_openai import AzureOpenAIEmbeddings

        deploy = (
            os.getenv("AOAI_DEPLOY_EMBED_3_LARGE")
            if model == "large"
            else os.getenv("AOAI_DEPLOY_EMBED_3_SMALL")
        )
        return AzureOpenAIEmbeddings(
            azure_deployment=deploy,
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_API_KEY"),
            api_version="2024-02-01",
        )
    else:
        from langchain_openai import OpenAIEmbeddings

        model_name = (
            os.getenv("OPENAI_DEPLOY_EMBED_3_LARGE")
            if model == "large"
            else os.getenv("OPENAI_DEPLOY_EMBED_3_SMALL")
        )
        return OpenAIEmbeddings(
            model=model_name,
            api_key=os.getenv("OPENAI_API_KEY"),
        )


# ------------------------------------------
# 서비스 설정값 반환
# ------------------------------------------
def get_service_config() -> dict:
    return {
        "analysis_period_weeks": int(os.getenv("ANALYSIS_PERIOD_WEEKS", 4)),
        "monthly_deposit_krw":   int(os.getenv("MONTHLY_DEPOSIT_KRW", 1500000)),
        "vectorstore_path":      os.getenv("VECTORSTORE_PATH", "./data/vectorstore"),
        "history_path":          os.getenv("HISTORY_PATH", "./data/history"),
        "env_mode":              ENV_MODE,
    }


# ------------------------------------------
# 환경 확인용 (디버그 목적)
# python config.py 로 직접 실행 시에만 동작
# ------------------------------------------
if __name__ == "__main__":
    print(f"[config] ENV_MODE       : {ENV_MODE}")
    print(f"[config] service config : {get_service_config()}")

    llm = get_llm("gpt4o")
    print(f"[config] LLM            : {type(llm).__name__}")

    embeddings = get_embeddings("large")
    print(f"[config] Embeddings     : {type(embeddings).__name__}")
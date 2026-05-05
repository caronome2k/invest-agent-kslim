# llm_factory.py 같은 파일로 분리
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, AzureChatOpenAI

load_dotenv()

def get_llm(model="gpt4o"):
    deploy_map = {
        "gpt4o": os.getenv("AOAI_DEPLOY_GPT4O"),
        "gpt4o_mini": os.getenv("AOAI_DEPLOY_GPT4O_MINI"),
    }
    deployment = deploy_map[model]

    if os.getenv("USE_AZURE") == "true":
        return AzureChatOpenAI(
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
            api_key=os.getenv("AOAI_API_KEY"),
            azure_deployment=deployment,
            api_version="2024-08-01-preview"
        )
    else:
        return ChatOpenAI(
            api_key=os.getenv("AOAI_API_KEY"),
            model=deployment
        )
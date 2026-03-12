import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from zai import ZhipuAiClient

load_dotenv()

# DeepSeek官方 api
deepseek_reasoner = init_chat_model(
    model = "deepseek-reasoner",
    model_provider="deepseek",
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    base_url = os.getenv("DEEPSEEK_BASE_URL")
)

deepseek_chat = init_chat_model(
    model = "deepseek-chat",
    model_provider="deepseek",
    api_key = os.getenv("DEEPSEEK_API_KEY"),
    base_url = os.getenv("DEEPSEEK_BASE_URL")
)

# 智谱官方 api
zhipuai_client = ZhipuAiClient(
    api_key = os.getenv("ZHIPU_API_KEY")
)
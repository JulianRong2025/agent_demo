from langchain.agents import create_agent

from agent.my_llm import deepseek_chat
from agent.tools.tool_demo1 import web_search
from agent.tools.tool_demo2 import MyWebSearchTool


web_search2= MyWebSearchTool()

agent2 = create_agent(
    model=deepseek_chat,
    # tools=[web_search],
    tools=[web_search2],
    system_prompt="你是一个智能助手，尽可能调用工具回答用户的问题",
)
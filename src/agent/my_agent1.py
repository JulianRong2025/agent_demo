from langchain.agents import create_agent

from agent.my_llm import deepseek_chat

def send_email(to: str, subject: str, body: str):
    """发送邮件"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    return f"邮件已发送至 {to}"

agent1 = create_agent(
    model=deepseek_chat,
    tools=[send_email],
    system_prompt="你是一个邮件助手。请始终使用 send_email 工具。",
)

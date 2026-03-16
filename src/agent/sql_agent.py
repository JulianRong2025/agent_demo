from typing import List

from langchain.agents import create_agent
from langchain.tools import BaseTool

from agent.my_llm import deepseek_chat

from agent.utils.db_utils import MySQLDatabaseManager
from agent.tools.sql_tool import ListTablesTool, TableSchemaTool, SQLQueryTool, SQLQueryCheckerTool

import os
from dotenv import load_dotenv
load_dotenv()

def get_tools(host: str, port: int, username: str, password: str, database: str) -> List[BaseTool]:
    # 构建连接字符串
    connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    db_manager = MySQLDatabaseManager(connection_string)
    return [
        ListTablesTool(db_manager=db_manager),
        TableSchemaTool(db_manager=db_manager),
        SQLQueryTool(db_manager=db_manager),
        SQLQueryCheckerTool(db_manager=db_manager)
    ]

tools = get_tools(
    host="localhost",
    port=3306,
    username="root",
    password=os.getenv("DB_PASSWORD", ""),
    database="mysql"
)

system_prompt = """
你是一个专门设计用于与 SQL 数据库交互的 AI 智能体。

给定一个输入问题，你需要按照以下步骤操作：
1.创建一个语法正确的{dialect}查询语句
2.执行查询并查看结果
3.根据查询结果生成最终答案

除非用户明确指定要获取的具体示例数量，否则始终将查询结果限制为最多{top_k}条。

你可以通过相关列对结果进行排序，以返回数据库中最有意义的示例。
永远不要查询特定表的所有列，只获取与问题相关的列。

在执行查询之前，你必须仔细检查查询语句。如果在执行查询时遇到错误，请重写查询并再次尝试。

绝对不要对数据库执行任何数据操作语言（DML）语句（如 INSERT，UPDATE，DELETE，DROP 等）

开始处理问题时，你应该始终先查看数据库中有哪些表可以查询。不要跳过这一步骤。

然后，你应该查询最相关表的模式结构信息。
""".format(
    dialect="MySQL", # 数据库方言，如 MySQL，SQLite，PostgreSQL 等
    top_k=5)

agent = create_agent(
    model=deepseek_chat,
    tools=tools,
    system_prompt=system_prompt
)
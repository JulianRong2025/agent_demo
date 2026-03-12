from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, create_model
from agent.my_llm import zhipuai_client

# 工具参数的第一种写法需要定义这个类
# class SearchArgs(BaseModel):    #类：数据模型类（静态）
#     query:str = Field(description='需要进行互联网查询的信息。')

class MyWebSearchTool(BaseTool):
    name :str = "web_search2"   #定义工具的名字

    description: str = "使用这个工具可以进行网络搜索"

    # #工具参数描述的第一种写法
    # args_schema : Type[BaseModel]= SearchArgs   #工具的参数描述

    #工具参数描述的第二种写法
    def __init__(self):
        super().__init__()
        self.args_schema = create_model(
            "SearchInput",   #动态数据模型类的名字，随便取的
            query = (str, Field(description='需要进行互联网查询的信息。'))
        )   #动态创建数据模型类

    # _run表示run 是一个私有函数，只能在内部调用
    def _run(self, query: str) -> str:
        try:
            response = zhipuai_client.web_search.web_search(
                search_engine='search_std',
                search_query=query,
            )
            if response.search_result:
                return "\n\n".join([d.content for d in response.search_result])  #搜索结果是一个列表，里面有很多结果，将其转成非列表
            return "没有搜索到结果"
        except Exception as e:
            print(e)
            return f"没有搜索到结果"
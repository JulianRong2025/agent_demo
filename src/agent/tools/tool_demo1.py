from langchain_core.tools import tool
from agent.my_llm import zhipuai_client
# from pydantic import BaseModel, Field

@tool('my_web_search', parse_docstring=True)
def web_search(query: str) -> str:
    """互联网搜索的工具，可以搜索所有公开的信息。

    Args:
        query:需要进行互联网查询的信息。

    Returns:
        返回搜索的结果信息，该信息是一个文本字符串。
    """
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

# 第二种写法
# class SearchArgs(BaseModel):
#     query:str = Field(description='需要进行互联网查询的信息。')


# @tool('web_search2', args_schema=SearchArgs, description='互联网搜索的工具，可以搜索所有公开的信息。', parse_docstring=True)
# def web_search2(query: str) -> str:
    
#     pass

if __name__ == '__main__':
    print(web_search.name)
    print(web_search.description)
    print(web_search.args)
    print(web_search.args_schema.model_json_schema())  #工具的参数的 json schema（描述 json 字符串）

    result = web_search.invoke({'query':"讲讲MacBook Neo的配置"})
    print(result)

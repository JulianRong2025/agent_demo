from typing import List, Optional

from langchain_core.tools import BaseTool
from pydantic import Field, create_model
from agent.utils.log_utils import log
from agent.utils.db_utils import MySQLDatabaseManager

class ListTablesTool(BaseTool):
    """列出数据库中的表及其描述信息"""

    name :str = "sql_db_list_tables"   #定义工具的名字
    description: str = "使用这个工具可以列出数据库中的表及其描述信息。当需要了解数据库中有哪些表以及表的用途时使用此工具。"

    # 数据库管理器实例
    db_manager: MySQLDatabaseManager

    def _run(self) -> str:
        try:
            tables_info = self.db_manager.get_tables_with_comments()
            
            result = f"数据库中一共有 {len(tables_info)} 张表：\n\n"
            for i, table_info in enumerate(tables_info):
                table_name = table_info['table_name']
                table_comment = table_info['table_comment']

                # 处理空描述的情况
                if not table_comment or table_comment.isspace():
                    description_display = "(无描述)"
                else:
                    description_display = table_comment

                result += f"{i+1}. 表名： {table_name}\n    描述： {description_display}\n"
            
            return result

        except Exception as e:
            log.exception(e)
            return f"获取表信息失败： {str(e)}"
        
    async def _arun(self) -> str:
        """异步执行工具"""
        return self._run()

class TableSchemaTool(BaseTool):
    """获取指定表的模式信息"""

    name :str = "sql_db_schema"   #定义工具的名字
    description: str = "使用这个工具可以获取指定表的模式信息，包括列定义、主键、外键等。输入应为英文逗号分隔的表名列表。如果输入为空，则获取所有表的模式信息。"

    # 数据库管理器实例
    db_manager: MySQLDatabaseManager

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.db_manager = db_manager
        self.args_schema = create_model(
            "TableSchemaToolArgs",   #动态数据模型类的名字，随便取的
            table_names = (Optional[str], Field(default=None, description='逗号分隔的表名列表，例如："default_roles,func"'))
        )   #动态创建数据模型类

    def _run(self, table_names: Optional[str] = None) -> str:
        """返回表结构信息"""
        try:
            table_list = None
            if table_names:
                table_list = [name.strip() for name in table_names.split(',') if name.strip()]
            schema_info = self.db_manager.get_table_schema(table_list)
            return schema_info if schema_info else "没有找到匹配的表"

        except Exception as e:
            log.exception(e)
            return f"获取表模式失败： {str(e)}" 

    async def _arun(self, table_names: Optional[str] = None) -> str:
        """异步执行工具"""
        return self._run(table_names)

class SQLQueryTool(BaseTool):
    """执行SQL查询并返回结果"""

    name :str = "sql_db_query"   #定义工具的名字
    description: str = "使用这个工具可以执行SQL查询并返回结果。输入应为SQL查询语句。请确保查询语句是安全的，并且只执行SELECT语句以避免修改数据库。"

    # 数据库管理器实例
    db_manager: MySQLDatabaseManager

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.db_manager = db_manager
        self.args_schema = create_model(
            "SQLQueryToolArgs",   #动态数据模型类的名字，随便取的
            query = (str, Field(description='有效的SQL查询语句'))
        )   #动态创建数据模型类

    def _run(self, query: str) -> str:
        """执行工具逻辑"""
        try:
            result = self.db_manager.execute_query(query)
            return result
        except Exception as e:
            log.exception(e)
            return f"执行查询失败： {str(e)}" 

    async def _arun(self, query: str) -> str:
        """异步执行工具"""
        return self._run(query)

class SQLQueryCheckerTool(BaseTool):
    """验证SQL查询的语法和安全性"""

    name :str = "sql_db_query_checker"   #定义工具的名字
    description: str = "使用这个工具可以验证SQL查询的语法和安全性。输入应为SQL查询语句。工具将检查查询是否为SELECT语句，并且不包含任何可能修改数据库的操作（如INSERT、UPDATE、DELETE等）。"

    # 数据库管理器实例
    db_manager: MySQLDatabaseManager

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.db_manager = db_manager
        self.args_schema = create_model(
            "SQLQueryCheckerToolArgs",   #动态数据模型类的名字，随便取的
            query = (str, Field(description='要验证的SQL查询语句'))
        )   #动态创建数据模型类

    def _run(self, query: str) -> str:
        """执行工具逻辑"""
        try:
            validation_result = self.db_manager.validate_query(query)
            return validation_result
        except Exception as e:
            log.exception(e)
            return f"验证查询失败： {str(e)}" 

    async def _arun(self, query: str) -> str:
        """异步执行工具"""
        return self._run(query)

if __name__ == "__main__":
    # 测试工具
    import os
    from dotenv import load_dotenv
    load_dotenv()
    # 配置数据库连接信息
    password = os.getenv("DB_PASSWORD", "")  # 从环境变量中获取数据库密码，默认为空字符串
    username = "root"
    host = "localhost"
    port = 3306
    database = "mysql"
    # 构建数据库连接字符串
    connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    manager = MySQLDatabaseManager(connection_string)
    # # 测试第一个工具
    # tool = ListTablesTool(db_manager=manager)
    # print(tool.invoke({}))

    # # 测试第二个工具
    # tool = TableSchemaTool(db_manager=manager)
    # print(tool.invoke({"table_names": ["db","func"]}))

    # # 测试第三个工具
    # tool = SQLQueryTool(db_manager=manager)
    # print(tool.invoke({'query': 'select * from db'}))

    # 测试第四个工具
    tool = SQLQueryCheckerTool(db_manager=manager)
    print(tool.invoke({'query': 'select count(*) from db'}))

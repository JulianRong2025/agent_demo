# 一个写项目常用的数据库工具类，不是智能体的工具
import json
from typing import List, Optional


from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from agent.utils.log_utils import log


class MySQLDatabaseManager:
    """MySQL数据库管理器，负责数据库连接和基本操作"""

    def __init__(self, connection_string: str):
        """
        初始化 MySQL 数据库连接

        Arg:
            connection_string: MySQL连接字符串, 格式为：
                mysql+pymysql://username:password@host:port/database
        """
        # 数据库引擎：数据库连接池+执行器，可以执行数据库的各种操作
        # pool_size=5, pool_recycle=3600是数据库连接池的相关参数
        self.engine = create_engine(connection_string, pool_size=5, pool_recycle=3600)
        
    def get_table_names(self) -> list[str]:
        """获取数据库中所有的表名"""
        try:
            # 创建一个inspector（数据库映射）对象，用于获取数据库的元数据（除了表内的内容，其他都有的数据）
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except Exception as e:
            log.exception(e)
            raise ValueError(f"获取表名失败： {str(e)}")

    def get_tables_with_comments(self) -> List[dict]:
        """获取数据库中所有表的名字和注释
        
        Retruns:
            List[dict]:一个字典列表，每个字典包含'table_name'和'comment'两个键，分别对应表名和注释。
        """
        try:
            # 构建查询语句，从 INFORMATION_SCHEMA.TABLES 中获取表名和注释
            query = text("""
                            SELECT TABLE_NAME, TABLE_COMMENT
                            FROM INFORMATION_SCHEMA.TABLES
                            WHERE TABLE_SCHEMA = DATABASE()
                                AND TABLE_TYPE = 'BASE TABLE'
                            ORDER BY TABLE_NAME
                         """)
            
            with self.engine.connect() as connection:
                result = connection.execute(query)
                # 将查询结果转换为包含表名和注释的字典列表，便于后续处理
                tables_info = [{'table_name':row[0], 'table_comment':row[1]} for row in result]
                return tables_info
            
        except SQLAlchemyError as e:
            log.exception(e)
            raise ValueError(f"获取表名和注释失败： {str(e)}")

    def get_table_schema(self, table_name: Optional[List[str]] = None) -> str:
        """获取指定表的模式信息（列名、数据类型等,包含字段注释）
        
        Args:
            table_name: 可选参数，指定要获取模式信息的表名。如果为None
                        则获取所有表的模式信息.
        """
        try:
            inspector = inspect(self.engine)
            schema_info = []

            tables_to_process = table_name if table_name else self.get_table_names()

            for table_name in tables_to_process:
                # 获取表的列信息，包括列名、数据类型、是否可空、默认值和注释等
                columns = inspector.get_columns(table_name)
                # 使用get_pk_constraint代替已弃用的 get_primary_keys 方法来获取主键列的信息
                pk_constraint = inspector.get_pk_constraint(table_name)
                primary_keys = pk_constraint.get('constrained_columns', []) if pk_constraint else []
                foreign_keys = inspector.get_foreign_keys(table_name)
                indexes = inspector.get_indexes(table_name)

                # 构建表模式描述
                table_schema = f"表名: {table_name}\n"
                table_schema += "列信息:\n"

                for column in columns:
                    # 检查该列是否为主键
                    pk_indicator = " (主键)" if column['name'] in primary_keys else ""
                    # 获取列的注释信息，如果没有则使用‘无注释‘
                    comment = column.get('comment', '无注释')
                    table_schema += f"  - {column['name']}:{str(column['type'])}{pk_indicator} [注释: {comment}]\n"

                if foreign_keys:
                    table_schema += "外键约束:\n" 
                    for fk in foreign_keys:
                        table_schema += f"  - 列: {fk['constrained_columns']} -> 参照表: {fk['referred_table']} (参照列: {fk['referred_columns']})\n"

                if indexes:
                    table_schema += "索引:\n"
                    for index in indexes:
                        if not index['name'].startswith('sqlite_'):
                            table_schema += f"  - 索引名: {index['name']} (列: {index['column_names']}, 唯一: {index['unique']})\n"

                schema_info.append(table_schema)
            
            return "\n".join(schema_info) if schema_info else "没有找到匹配的表"
            
        except Exception as e:
            log.exception(e)
            raise ValueError(f"获取表模式失败： {str(e)}")
    
    def execute_query(self, query: str) -> str:
        """执行SQL查询并返回结果
        
        Args:
            query: 要执行的SQL查询语句。
        """
        # 安全检查：防止数据修改操作
        forbidden_keywords = ['insert', 'update', 'delete', 'drop', 'alter', 'create', 'grant', 'truncate']
        query_lower = query.lower().strip()

        # 检查查询语句是否以SELECT开头，并且不包含任何禁止的关键词
        if not query_lower.startswith(('select', 'with')) and any(
                keyword in query_lower for keyword in forbidden_keywords):
            raise ValueError("仅允许执行SELECT和WITH查询，禁止执行数据修改操作。")
          
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                # 获取查询结果的列名
                columns = result.keys()
                # 获取数据（限制返回行数防止内存溢出）
                rows = result.fetchmany(100)  # 可以根据需要调整返回的行数

                if not rows:
                    return "查询成功，但没有返回任何数据。"
                
                # 格式化结果
                result_data = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        # 处理无法序列化的数据类型
                        try:
                            # 尝试 json 序列化来检测是否可序列化
                            if row[i] is not None:
                                json.dumps(row[i])
                            row_dict[col] = row[i]
                        except (TypeError, ValueError):
                            row_dict[col] = str(row[i])  # 将无法序列化的值转换为字符串
                    result_data.append(row_dict)
                
                return json.dumps(result_data, ensure_ascii=False, indent=2)
                                
        except SQLAlchemyError as e:
            log.exception(e)
            raise ValueError(f"执行查询失败： {str(e)}")
        
    # def validate_query(self, query: str) -> bool:
    #     """验证SQL查询的合法性，确保它是一个安全的SELECT查询
        
    #     Args:
    #         query: 要验证的SQL查询语句。
    #     """
    #     # 基本语法检查
    #     if not query or not query.strip():
    #         return "错误：查询不能为空"
        
    #     # 检查是否以SELECT或WITH开头
    #     query_lower = query.lower().strip()
    #     if not query_lower.startswith(('select', 'with')):
    #         return "错误：查询必须以SELECT或WITH开头"
        
    #     # 尝试解析查询（不实际执行）
    #     try:
    #         with self.engine.connect() as connection:
    #             # 使用 SQLAlchemy 的 text() 函数来解析查询语句，EXPLAIN 语句可以检查查询的语法和安全性，而不执行查询
    #             parsed_query = text(query)
    #             # 尝试编译查询以检查语法
    #             compiled = parsed_query.compile(compile_kwargs={"literal_binds": True})
    #             return "查询语法看起来正确"
    #     except Exception as e:
    #         log.exception(e)
    #         return f"查询语法错误或不安全： {str(e)}"

    def validate_query(self, query: str) -> str:
        """
        验证SQL查询的合法性，确保它是一个安全的SELECT查询

        Args:
            query: 要验证的SQL查询语句。
        """
        if not query or not query.strip():
            return "错误：查询不能为空"
    
        query_lower = query.lower().strip()
        if not query_lower.startswith(('select', 'with')):
            return "错误：查询必须以SELECT或WITH开头，其他操作可能被限制"

        try:
            with self.engine.connect() as connection:
                # 根据数据库方言构建 explain 查询
                # 这里以 mysql 为例，其他数据库请参考其 explain 语法进行调整
                if self.engine.dialect.name == 'mysql':
                    explain_query = text(f"EXPLAIN {query}")
                else:
                    # 对于其他数据库，可能需要不同的 explain 语法，这里只是一个示例
                    explain_query = text(f"EXPLAIN {query}")
            
                # 执行 explain 查询来验证语法和安全性
                connection.execute(explain_query)
                return "SQL 查询语法正确，已通过数据库 EXPLAIN 验证" 

        except Exception as e:
            log.exception(e)
            return f"查询语法错误或不安全： {str(e)}"
     
if __name__ == '__main__':
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

    query = os.getenv("DB_TEST_QUERY", "SELECT 1 AS ok;")
    print(manager.validate_query(query))


    

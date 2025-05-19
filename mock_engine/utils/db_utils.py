import logging
import pymysql
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MysqlDBUtil:
    """MySQL数据库工具类"""

    def __init__(self, host: str, user: str, password: str, port: int = 3306):
        """
        初始化数据库连接
        
        Args:
            host: 主机地址
            user: 用户名
            password: 密码
            port: 端口号
        """
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.conn = None
        self.cursor = None

    def connect_db(self) -> Dict[str, str]:
        """
        连接数据库
        
        Returns:
            连接结果字典
        """
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                charset='utf8mb4'
            )
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            return {'msg': '连接成功！'}
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return {'msg': str(e)}

    def execute_sql(self, sql: str, params: Optional[list] = None) -> Dict[str, Any]:
        """
        执行SQL语句
        Args:
            sql: SQL语句
            params: 参数列表（可选）
        Returns:
            执行结果字典
        """
        try:
            if not self.conn or not self.cursor:
                self.connect_db()
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            if sql.strip().upper().startswith('SELECT'):
                result = self.cursor.fetchall()
                return {'msg': '执行成功！', 'data': result}
            else:
                self.conn.commit()
                return {'msg': '执行成功！', 'affected_rows': self.cursor.rowcount}
        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            return {'msg': str(e)}
        finally:
            self.close()

    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

def execute_sqls(sql: str, env: str = None, db_config: Optional[Dict[str, Any]] = None, params: Optional[list] = None) -> Dict[str, Any]:
    """
    执行SQL语句的便捷函数
    Args:
        sql: SQL语句
        env: 环境名称（可选）
        db_config: 数据库配置字典，包含 host, user, password, port 等配置项
        params: 参数列表（可选）
    Returns:
        执行结果字典
    """
    try:
        # 如果没有传入配置，使用默认配置
        if db_config is None:
            db_config = {
                'host': '127.0.0.1',
                'user': 'root',
                'password': '123456',
                'port': 3306
            }
        db_util = MysqlDBUtil(**db_config)
        return db_util.execute_sql(sql, params)
    except Exception as e:
        logger.error(f"SQL执行失败: {str(e)}")
        return {'msg': str(e)} 
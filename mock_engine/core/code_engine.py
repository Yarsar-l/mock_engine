import sys
import logging
from io import StringIO
from typing import Dict, Optional, Tuple, Any, Union

logger = logging.getLogger(__name__)

class CodeEngine:
    """代码模式引擎（支持动态逻辑）"""

    def __init__(self, code: Optional[str] = None, request: Optional[Dict] = None, config: Optional[Dict] = None, debug: bool = False):
        """
        初始化代码引擎
        
        Args:
            code: 用户提交的Python代码
            request: 请求数据字典，包含headers、body和query
            config: 配置字典（可包含db_config等）
            debug: 是否启用调试模式
        """
        self.code = code or ""
        self.debug = debug
        self.context = {
            'HEADERS': request.get('headers', {}) if request else {},
            'BODY': request.get('body', {}) if request else {},
            'QUERY': request.get('query', {}) if request else {},
            'SET_RESPONSE': lambda data: self.context['RESPONSE'].update(data=data),
            "GET_RESPONSE": lambda: self.context['RESPONSE']['data'],
            'RESPONSE': {'status': 200, 'data': {}},
            'SETSTATUS': lambda code: self.context['RESPONSE'].update(status=code),
            'EXECUTE_SQL': self._execute_sql,
            'SEND_REQUEST': self._send_request,
            'print': self._debug_print if debug else print
        }
        if config and 'db_config' in config:
            self.context['db_config'] = config['db_config']
        self.stdout = StringIO()
        self.debug_output = []

    def _debug_print(self, *args, **kwargs):
        """调试输出"""
        if self.debug:
            output = ' '.join(str(arg) for arg in args)
            logger.debug(output)
            self.debug_output.append(output)

    def _execute_sql(self, sql: str, params: Optional[list] = None, db_config: Optional[Dict] = None) -> Dict:
        """
        执行SQL语句
        Args:
            sql: SQL语句
            params: 参数列表（可选）
            db_config: 数据库配置（可选）
        Returns:
            执行结果字典
        """
        try:
            if self.debug:
                self._debug_print(f"执行SQL: {sql}")
            if db_config is None:
                db_config = self.context.get('db_config')
            from ..utils.db_utils import execute_sqls
            result = execute_sqls(sql, db_config=db_config, params=params)
            if self.debug:
                self._debug_print(f"SQL执行结果: {result}")
            return result
        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            return {"error": str(e)}

    def _send_request(
        self,
        method: str,
        path: str = None,
        base_url: str = 'http://127.0.0.1:8000/mock/',
        headers: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        发送HTTP请求
        """
        try:
            if self.debug:
                self._debug_print(f"发送请求: {method} {path}")
                self._debug_print(f"请求头: {headers}")
                self._debug_print(f"请求数据: {data}")
            from ..utils.http_utils import send_mock_request
            # 判断 path 是否为完整 URL
            if path and (path.startswith('http://') or path.startswith('https://')):
                result = send_mock_request(method=method, url=path, headers=headers, data=data, **kwargs)
            else:
                result = send_mock_request(method=method, path=path, base_url=base_url, headers=headers, data=data, **kwargs)
            if self.debug:
                self._debug_print(f"请求结果: {result}")
            return result
        except Exception as e:
            logger.error(f"请求发送失败: {str(e)}")
            return {"error": str(e)}

    def ASSERT(self, actual, op, expected, msg=None):
        import re
        result = None
        if op == "==":
            result = actual == expected
        elif op == "!=":
            result = actual != expected
        elif op == ">":
            result = actual > expected
        elif op == "<":
            result = actual < expected
        elif op == ">=":
            result = actual >= expected
        elif op == "<=":
            result = actual <= expected
        elif op == "contains":
            result = expected in actual
        elif op == "not_contains":
            result = expected not in actual
        elif op == "regex":
            result = re.search(expected, actual) is not None
        elif op == "startswith":
            result = str(actual).startswith(str(expected))
        elif op == "endswith":
            result = str(actual).endswith(str(expected))
        else:
            raise ValueError(f"不支持的断言操作符: {op}")
        if not result:
            raise AssertionError(msg or f"断言失败: {actual} {op} {expected}")

    def execute(self, code: str, context: dict = None) -> dict:
        """
        执行Python代码
        
        Args:
            code: 要执行的Python代码
            context: 上下文变量
            
        Returns:
            dict: 执行结果
        """
        self._debug_print("开始执行代码")
        self._debug_print(f"代码内容:\n{code}")
        
        if context:
            self._debug_print(f"上下文变量: {context}")
            self.context.update(context)
            
        # 用于存储状态码
        status_code_holder = {'value': 200}
        def set_status_code(code):
            status_code_holder['value'] = code
            if self.debug:
                self._debug_print(f"设置响应状态码: {code}")
        def get_status_code():
            if self.debug:
                self._debug_print(f"获取响应状态码: {status_code_holder['value']}")
            return status_code_holder['value']
        
        # 创建执行环境
        local_vars = {}
        global_vars = {
            'print': self._capture_print,
            'sql_execute': self._execute_sql,
            'http_request': (lambda *args, **kwargs: __import__('mock_engine.utils.http_utils', fromlist=['request']).request(*args, debug_callback=self._debug_print, **kwargs)) if self.debug else __import__('mock_engine.utils.http_utils', fromlist=['request']).request,
            'get_context': self.get_context,
            'set_context': self.set_context,
            'get_request_data': self._get_request_data,
            'ASSERT': self.ASSERT,
            'set_status_code': set_status_code,
            'get_status_code': get_status_code
        }
        
        try:
            # 执行代码
            exec(code, global_vars, local_vars)
            self._debug_print("代码执行完成")
            
            # 获取结果
            result = {
                'data': local_vars.get('result', None),
                'status_code': status_code_holder['value'],
                'stdout': self.stdout.getvalue()
            }
            
            if self.debug:
                result['debug_output'] = self.debug_output
            
            self._debug_print(f"执行结果: {result}")
            return result
            
        except Exception as e:
            self._debug_print(f"执行出错: {str(e)}")
            result = {
                'error': str(e),
                'status_code': 500,
                'stdout': self.stdout.getvalue()
            }
            
            if self.debug:
                result['debug_output'] = self.debug_output
                
            return result

    def add_context(self, name: str, value: Any):
        """
        添加自定义上下文变量
        
        Args:
            name: 变量名
            value: 变量值
        """
        self.context[name] = value
        if self.debug:
            self._debug_print(f"添加上下文变量: {name} = {value}")

    def get_context(self, name: str) -> Any:
        """
        获取上下文变量
        
        Args:
            name: 变量名
            
        Returns:
            变量值
        """
        value = self.context.get(name)
        if self.debug:
            self._debug_print(f"获取上下文变量: {name} = {value}")
        return value

    def _capture_print(self, *args, **kwargs):
        print_str = ' '.join(str(arg) for arg in args)
        self.stdout.write(print_str + '\n')
        if self.debug:
            self.debug_output.append(f"print: {print_str}")

    def _make_http_request(self, *args, **kwargs):
        return self._send_request(*args, **kwargs)

    def set_context(self, name: str, value: Any):
        """
        设置上下文变量
        """
        self.context[name] = value
        if self.debug:
            self._debug_print(f"设置上下文变量: {name} = {value}")

    def _get_request_data(self, data_type: str, key_path: str = None, default=None):
        """统一的请求数据访问方法"""
        if data_type == 'header':
            data = self.context.get('HEADERS', {})
        elif data_type == 'body':
            data = self.context.get('BODY', {})
        elif data_type == 'query':
            data = self.context.get('QUERY', {})
        else:
            return default

        if key_path is None:
            return data

        keys = key_path.split('.')
        value = data
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default 
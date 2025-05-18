import re
import json
import logging
import sys
from io import StringIO
from typing import Any, Dict, Optional, Union, Tuple, List
from functools import wraps
from faker import Faker
from jsonpath_ng import parse as jsonpath_parse

logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    模板引擎类，用于处理响应模板中的变量表达式和自定义方法调用。
    
    主要功能：
    1. 支持请求头数据访问 (@request_header.xxx)
    2. 支持请求体数据访问 (@request_body.xxx)
    3. 支持Faker方法调用 (@faker.xxx 或 @xxx)
    4. 支持自定义方法调用 (@custom_method)
    5. 支持嵌套数据访问 (user.address.city)
    6. 支持调试模式，输出方法执行过程
    7. 支持断言功能，验证数据
    """

    def __init__(self, template: Optional[Union[Dict, str]] = None, request: Optional[Dict] = None, debug: bool = False):
        """
        初始化模板引擎
        
        Args:
            template: 响应模板，可以是字典或JSON字符串
            request: 请求数据字典，包含headers、body和query
            debug: 是否启用调试模式
        """
        self.template = json.dumps(template) if isinstance(template, dict) else (template or "{}")
        self.fake = Faker(locale='zh_CN')
        self.request = request or {}
        self.custom_methods = {}
        self.debug = debug
        self.debug_output = []
        self._init_builtin_methods()
        self._debug_print("模板引擎初始化完成")

    def _debug_print(self, message: str):
        """调试输出"""
        if self.debug:
            self.debug_output.append(message)
            logger.debug(message)

    def _init_builtin_methods(self):
        """初始化内置方法"""
        self.custom_methods['request_header'] = self._get_request_header
        self.custom_methods['request_body'] = self._get_request_body
        self.custom_methods['faker'] = self._call_faker_method
        self.custom_methods['get_request_data'] = self._get_request_data

    def register_method(self, name: str = None):
        """
        注册自定义方法的装饰器
        
        Args:
            name: 方法名，如果不提供则使用函数名
        """
        def decorator(func):
            method_name = name or func.__name__
            @wraps(func)
            def wrapper(*args, **kwargs):
                self._debug_print(f"执行方法: {method_name}")
                self._debug_print(f"参数: args={args}, kwargs={kwargs}")
                result = func(*args, **kwargs)
                self._debug_print(f"结果: {result}")
                return result
                
            self.custom_methods[method_name] = wrapper
            self._debug_print(f"注册自定义方法: {method_name}")
            return wrapper
        return decorator

    def register_script(self, name: str, script: str):
        """
        注册自定义脚本方法
        
        Args:
            name: 方法名
            script: Python脚本代码
        """
        try:
            script_namespace = {
                'request_header': self._get_request_header,
                'request_body': self._get_request_body,
                'faker': self._call_faker_method,
                'fake': self.fake,
                'engine': self,
                'print': lambda *args: self._debug_print(' '.join(str(arg) for arg in args))
            }
            
            exec(script, script_namespace)
            
            if name in script_namespace:
                self.custom_methods[name] = script_namespace[name]
                self._debug_print(f"注册脚本方法: {name}")
            else:
                raise ValueError(f"脚本中未定义函数: {name}")
                
        except Exception as e:
            logger.error(f"注册脚本方法失败: {name} - {str(e)}")
            raise

    def _get_request_header(self, key_path: str = None, default=None):
        """获取请求头数据"""
        self._debug_print(f"获取请求头: {key_path}")
        self._debug_print(f"当前 request: {self.request}")
        headers = self.request.get('headers', {})
        self._debug_print(f"当前 headers: {headers}")
        if key_path is None or key_path == '':
            return headers
        # 先直接查找
        if key_path in headers:
            return headers[key_path]
        # 支持下划线和连字符互转
        alt_key = key_path.replace('-', '_') if '-' in key_path else key_path.replace('_', '-')
        if alt_key in headers:
            return headers[alt_key]
        # 支持嵌套（极少见）
        return self._get_nested_value(headers, key_path, default)

    def _get_request_body(self, key_path: str = None, default=None):
        """获取请求体数据"""
        self._debug_print(f"当前 request: {self.request}")
        body = self.request.get('body', {})
        self._debug_print(f"当前 body: {body}")
        
        if key_path is None or key_path == '':
            self._debug_print(f"返回完整请求体: {body}")
            return body
            
        value = self._get_nested_value(body, key_path, default)
        self._debug_print(f"获取请求体字段 {key_path}: {value}")
        return value

    def _call_faker_method(self, method_name: str, *args, **kwargs):
        """调用Faker方法"""
        self._debug_print(f"调用Faker方法: {method_name}")
        if hasattr(self.fake, method_name):
            return getattr(self.fake, method_name)(*args, **kwargs)
        raise AttributeError(f"Faker方法不存在: {method_name}")

    def _get_nested_value(self, data: dict, key_path: str, default=None):
        """获取嵌套字典中的值"""
        self._debug_print(f"获取嵌套值: {key_path}")
        try:
            keys = key_path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def _resolve_variable(self, var_expression: str) -> Any:
        """解析变量表达式"""
        self._debug_print(f"解析变量表达式: {var_expression}")
        try:
            # 处理断言表达式
            if var_expression.startswith('assert('):
                return self._handle_assertion(var_expression[len('assert('):-1])
            # 1. 先查找请求数据
            if var_expression in self.request:
                value = self.request[var_expression]
                self._debug_print(f"从请求数据中获取: {var_expression} = {value}")
                return value
            # 2. 查找请求头数据
            if var_expression == 'request_header':
                value = self._get_request_header()
                self._debug_print(f"获取完整请求头: {value}")
                return value
            if var_expression.startswith('request_header.'):
                key_path = var_expression[len('request_header.'):]
                value = self._get_request_header(key_path)
                self._debug_print(f"获取请求头字段 {key_path}: {value}")
                return value
            # 3. 查找请求体数据
            if var_expression == 'request_body':
                value = self._get_request_body()
                self._debug_print(f"获取完整请求体: {value}")
                return value
            if var_expression.startswith('request_body.'):
                key_path = var_expression[len('request_body.'):]
                value = self._get_request_body(key_path)
                self._debug_print(f"获取请求体字段 {key_path}: {value}")
                return value
            # 4. 查找自定义方法
            if var_expression in self.custom_methods:
                method = self.custom_methods[var_expression]
                self._debug_print(f"执行自定义方法: {var_expression}")
                return method()
            # 5. 查找 Faker 方法，支持 @faker.xxx 形式
            if var_expression.startswith('faker.'):
                method_part = var_expression[len('faker.'):]
                return self._call_faker_method(method_part)
            # 6. 查找请求数据中的嵌套值
            value = self._get_nested_value(self.request, var_expression)
            if value is not None:
                self._debug_print(f"从请求数据中获取嵌套值: {var_expression} = {value}")
                return value
            return None
        except Exception as e:
            self._debug_print(f"解析变量表达式出错: {str(e)}")
            return None

    def _handle_assertion(self, assertion_expr: str) -> bool:
        """处理断言表达式"""
        self._debug_print(f"处理断言表达式: {assertion_expr}")
        try:
            # 处理复杂断言（包含 && 或 ||）
            if '&&' in assertion_expr:
                parts = assertion_expr.split('&&')
                return all(self._handle_assertion(part.strip()) for part in parts)
            elif '||' in assertion_expr:
                parts = assertion_expr.split('||')
                return any(self._handle_assertion(part.strip()) for part in parts)
            
            # 处理简单断言
            if '==' in assertion_expr:
                left, right = assertion_expr.split('==', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value == right_value
                self._debug_print(f"断言 {left_value} == {right_value}: {result}")
                return result
            elif '!=' in assertion_expr:
                left, right = assertion_expr.split('!=', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value != right_value
                self._debug_print(f"断言 {left_value} != {right_value}: {result}")
                return result
            elif '>=' in assertion_expr:
                left, right = assertion_expr.split('>=', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value >= right_value
                self._debug_print(f"断言 {left_value} >= {right_value}: {result}")
                return result
            elif '<=' in assertion_expr:
                left, right = assertion_expr.split('<=', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value <= right_value
                self._debug_print(f"断言 {left_value} <= {right_value}: {result}")
                return result
            elif '>' in assertion_expr:
                left, right = assertion_expr.split('>', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value > right_value
                self._debug_print(f"断言 {left_value} > {right_value}: {result}")
                return result
            elif '<' in assertion_expr:
                left, right = assertion_expr.split('<', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value < right_value
                self._debug_print(f"断言 {left_value} < {right_value}: {result}")
                return result
            elif 'in' in assertion_expr:
                left, right = assertion_expr.split('in', 1)
                left_value = self._resolve_variable(left.strip())
                right_value = self._parse_literal(right.strip())
                result = left_value in right_value
                self._debug_print(f"断言 {left_value} in {right_value}: {result}")
                return result
            else:
                value = self._resolve_variable(assertion_expr.strip())
                result = bool(value)
                self._debug_print(f"断言 {value} 为真: {result}")
                return result
        except Exception as e:
            self._debug_print(f"处理断言表达式出错: {str(e)}")
            return False

    def _parse_literal(self, value: str):
        # 尝试将字符串解析为字面量（数字、布尔、列表、字符串等）
        import ast
        try:
            return ast.literal_eval(value)
        except Exception:
            return value.strip('"\'')

    def _parse_args(self, args_part: str) -> tuple:
        """解析参数字符串"""
        args = []
        kwargs = {}
        
        if not args_part.strip():
            return args, kwargs

        for arg in args_part.split(','):
            arg = arg.strip()
            if not arg:
                continue
                
            if '=' in arg:
                key, value = arg.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if value.startswith('$'):
                    param_name = value[1:]
                    value = self._get_param_from_request(param_name)
                
                value = self._parse_value(value)
                kwargs[key] = value
            else:
                value = arg.strip()
                
                if value.startswith('$'):
                    param_name = value[1:]
                    value = self._get_param_from_request(param_name)
                
                value = self._parse_value(value)
                args.append(value)
                
        return args, kwargs

    def _parse_value(self, value: str):
        """解析参数值"""
        value = value.strip()
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace('.', '', 1).isdigit() and value.count('.') == 1:
            return float(value)
        else:
            return value.strip("'\"")

    def _get_param_from_request(self, param_name: str):
        """从请求中获取参数值"""
        for source in ['body', 'query', 'headers']:
            if param_name in self.request.get(source, {}):
                return self.request[source][param_name]
        return None

    def generate(self, template: Optional[Union[Dict, str]] = None, request: Optional[Dict] = None) -> Tuple[Dict, Optional[list]]:
        """
        生成响应数据
        Args:
            template: 可选，新的模板
            request: 可选，新的请求数据
        """
        self._debug_print("开始生成数据")
        if template is not None:
            self.template = json.dumps(template) if isinstance(template, dict) else template
        if request is not None:
            self.request = request
        try:
            self._debug_print(f"原始模板: {self.template}")
            template_dict = json.loads(self.template)
            def process_value(value):
                if isinstance(value, str):
                    def replace_var(match):
                        var = match.group(1).strip()
                        resolved = self._resolve_variable(var)
                        # 如果整个 value 就是 @变量，且替换后类型不是字符串，则直接返回原始类型
                        if value.strip() == f"@{var}" and not isinstance(resolved, str):
                            return resolved
                        return str(resolved)
                    # 如果整个 value 是 @变量，直接返回原始类型
                    if re.fullmatch(r'@([a-zA-Z_][\w\-\._()\,\$\'\" ]*)', value.strip()):
                        var = value.strip()[1:]
                        return self._resolve_variable(var)
                    value = re.sub(r'@([a-zA-Z_][\w\-\._()\,\$\'\" ]*)', replace_var, value)
                    return value
                elif isinstance(value, dict):
                    if 'assertions' in value:
                        assertions_dict = value['assertions']
                        return {**{k: process_value(v) for k, v in value.items() if k != 'assertions'},
                                'assertions': {k: self._resolve_variable(v[1:] if isinstance(v, str) and v.startswith('@') else v) for k, v in assertions_dict.items()}}
                    return {k: process_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [process_value(item) for item in value]
                else:
                    return value
            result = process_value(template_dict)
            self._debug_print(f"处理结果: {result}")
            self._debug_print("生成完成")
            if self.debug:
                return result, self.debug_output
            return result, None
        except json.JSONDecodeError as e:
            logger.error(f"模板JSON解析失败: {str(e)}")
            error_result = {"error": "Invalid template format", "details": str(e)}
            if self.debug:
                return error_result, self.debug_output
            return error_result, None
        except Exception as e:
            logger.error(f"模板处理异常: {str(e)}")
            error_result = {"error": str(e)}
            if self.debug:
                return error_result, self.debug_output
            return error_result, None

    def _get_request_data(self, data_type: str, key_path: str = None, default=None):
        """统一的请求数据访问方法"""
        if data_type == 'header':
            data = self.request.get('headers', {})
        elif data_type == 'body':
            data = self.request.get('body', {})
        else:
            return default

        if key_path is None:
            return data

        return self._get_nested_value(data, key_path, default)

    @property
    def request_header(self):
        """请求头访问属性"""
        return self.custom_methods['request_header']

    @property
    def request_body(self):
        """请求体访问属性"""
        return self.custom_methods['request_body']

    def register_custom_method(self, name: str, method: callable):
        """注册自定义方法"""
        self.custom_methods[name] = method
        self._debug_print(f"注册自定义方法: {name}")

    def _parse_assertion_rule(self, rule: str) -> callable:
        """
        解析断言规则字符串，支持jsonpath格式，转换为断言函数
        
        Args:
            rule: 断言规则字符串，如 "age > 18" 或 "$.nested.level1.level2 == 'deep'"
            
        Returns:
            断言函数
        """
        def replace_jsonpath(expr: str, data: dict) -> str:
            # 匹配 $.xxx.xxx 形式
            pattern = re.compile(r'(\$\.[a-zA-Z0-9_\.]+)')
            def repl(match):
                jp = match.group(1)
                try:
                    jsonpath_expr = jsonpath_parse(jp)
                    matches = [m.value for m in jsonpath_expr.find(data)]
                    if matches:
                        v = matches[0]
                        if isinstance(v, str):
                            return f"'{v}'"
                        return str(v)
                    else:
                        return 'None'
                except Exception:
                    return 'None'
            return pattern.sub(repl, expr)

        def assertion_func(data: dict) -> bool:
            try:
                expr = rule.replace('&&', 'and').replace('||', 'or')
                expr = replace_jsonpath(expr, data)
                print(f"断言规则: {rule} 替换后: {expr}")
                # 使用空字典作为globals，避免安全问题
                return bool(eval(expr, {}))
            except Exception as e:
                self._debug_print(f"断言规则执行失败: {rule} - {str(e)}")
                return False
        return assertion_func

    def _flatten_dict(self, d: Dict, prefix: str = '') -> Dict[str, Any]:
        """
        将嵌套字典扁平化
        
        Args:
            d: 嵌套字典
            prefix: 键前缀
            
        Returns:
            扁平化的字典
        """
        items = []
        for k, v in d.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _generate_assertion_key(self, assertion: str) -> str:
        """
        根据断言规则自动生成key
        
        Args:
            assertion: 断言规则字符串，如 "$.age > 18"
            
        Returns:
            生成的key，如 "assert_age_gt_18"
        """
        # 移除 $ 和引号
        expr = assertion.replace("$.", "").replace("'", "").replace('"', '')
        
        # 替换操作符
        expr = expr.replace(" > ", "_gt_")
        expr = expr.replace(" < ", "_lt_")
        expr = expr.replace(" >= ", "_gte_")
        expr = expr.replace(" <= ", "_lte_")
        expr = expr.replace(" == ", "_eq_")
        expr = expr.replace(" != ", "_ne_")
        expr = expr.replace(" && ", "_and_")
        expr = expr.replace(" || ", "_or_")
        
        # 替换点号为下划线
        expr = expr.replace(".", "_")
        
        # 处理len函数
        expr = expr.replace("len(", "len_").replace(")", "")
        
        # 添加前缀
        return f"assert_{expr}"

    def _assertion_dict_to_expr(self, item: dict) -> str:
        """
        将断言字典转为表达式字符串
        Args:
            item: 断言字典，包含 path、op、value
        Returns:
            表达式字符串
        """
        path = item["path"]
        op = item["op"]
        value = item["value"]
        if op.startswith("len"):
            real_op = op[3:]
            return f"len({path}) {real_op} {repr(value)}"
        else:
            return f"{path} {op} {repr(value)}"

    def add_assertion(self, path: str, op: str, value: Any, idx: int = None):
        """
        添加断言规则（结构化path/op/value），自动生成key
        Args:
            path: jsonpath
            op: 操作符
            value: 期望值
            idx: 可选，断言序号，用于生成唯一key
        """
        expr = self._assertion_dict_to_expr({"path": path, "op": op, "value": value})
        if idx is not None:
            key = f"assert_{path.strip('$').replace('.', '_')}_{op}_{idx+1}"
        else:
            key = self._generate_assertion_key(expr)
        def assertion_func(data: dict) -> bool:
            try:
                # 只支持jsonpath表达式替换
                pattern = re.compile(r'(\$\.[a-zA-Z0-9_\.]+)')
                def repl(match):
                    jp = match.group(1)
                    try:
                        jsonpath_expr = jsonpath_parse(jp)
                        matches = [m.value for m in jsonpath_expr.find(data)]
                        if matches:
                            v = matches[0]
                            if isinstance(v, str):
                                return f"'{v}'"
                            return str(v)
                        else:
                            return 'None'
                    except Exception:
                        return 'None'
                expr_eval = pattern.sub(repl, expr)
                return bool(eval(expr_eval, {}))
            except Exception as e:
                self._debug_print(f"断言规则执行失败: {expr} - {str(e)}")
                return False
        self.custom_methods[f'assert_{key}'] = assertion_func
        self._debug_print(f"添加断言规则: {key}")

    def add_assertions(self, assertions: List[Dict]):
        """
        批量添加断言规则，只支持{"path":..., "op":..., "value":...}结构
        Args:
            assertions: 断言字典列表，每项包含 path、op、value
        """
        for idx, item in enumerate(assertions):
            self.add_assertion(item["path"], item["op"], item["value"], idx=idx)

    def verify_assertions(self, data: Dict) -> Dict[str, bool]:
        """
        验证所有断言规则
        Args:
            data: 要验证的数据字典
        Returns:
            断言结果字典，key为断言名称，value为断言结果（布尔值）
        """
        results = {}
        for name, func in self.custom_methods.items():
            if name.startswith('assert_'):
                assertion_name = name[7:]  # 去掉 'assert_' 前缀
                try:
                    result = func(data)
                    results[assertion_name] = bool(result)
                    self._debug_print(f"断言 {assertion_name}: {result}")
                except Exception as e:
                    self._debug_print(f"断言 {assertion_name} 执行失败: {str(e)}")
                    results[assertion_name] = False
        return results

    def generate_with_assertions(self, template: Dict, request_data: Dict, assertions: List[Dict]) -> Tuple[Dict, Dict, Optional[list]]:
        """
        生成数据并验证断言
        Args:
            template: 模板
            request_data: 请求数据
            assertions: 断言字典列表，每项包含 path、op、value
        Returns:
            (生成的数据, 断言结果, debug信息)
        """
        if assertions:
            self.add_assertions(assertions)
        result, debug = self.generate(template, request_data)
        assertion_results = self.verify_assertions(result)
        return result, assertion_results, debug 
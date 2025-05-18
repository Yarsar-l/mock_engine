# Mock Engine API 文档

## 目录
- [TemplateEngine](#templateengine)
- [CodeEngine](#codeengine)

## TemplateEngine

### 类定义

```python
class TemplateEngine:
    def __init__(self, debug=False):
        """
        初始化模板引擎
        
        参数:
            debug (bool): 是否启用调试模式，默认为 False
        """
```

### 方法

#### generate

```python
def generate(self, template, request=None):
    """
    根据模板和请求数据生成结果
    
    参数:
        template (dict): 模板字典
        request (dict, optional): 请求数据字典
        
    返回:
        tuple: (结果字典, 调试输出列表)
    """
```

#### register_method

```python
def register_method(self):
    """
    注册自定义方法的装饰器
    
    用法:
        @engine.register_method()
        def custom_method(value):
            return f"处理后的值: {value}"
    """
```

## CodeEngine

### 类定义

```python
class CodeEngine:
    def __init__(self, debug=False):
        """
        初始化代码引擎
        
        参数:
            debug (bool): 是否启用调试模式，默认为 False
        """
```

### 方法

#### execute

```python
def execute(self, code):
    """
    执行代码字符串
    
    参数:
        code (str): 要执行的代码字符串
        
    返回:
        dict: 包含执行结果的字典，格式如下：
        {
            'data': 执行结果数据,
            'status_code': HTTP 状态码,
            'stdout': 标准输出内容,
            'debug_output': 调试输出列表（仅在调试模式开启时）
        }
    """
```

#### add_context

```python
def add_context(self, key, value):
    """
    添加上下文变量
    
    参数:
        key (str): 变量名
        value (any): 变量值
    """
```

### 内置函数

#### sql

```python
def sql(query, db_config=None):
    """
    执行 SQL 查询
    
    参数:
        query (str): SQL 查询语句
        db_config (dict, optional): 数据库配置字典，包含以下字段：
            - host: 数据库主机
            - user: 用户名
            - password: 密码
            - port: 端口
            - database: 数据库名
            
    返回:
        dict: 查询结果，格式如下：
        {
            'msg': '执行成功！',
            'data': 查询结果列表,
            'affected_rows': 影响的行数（仅适用于 INSERT/UPDATE/DELETE）
        }
    """
```

#### get_context

```python
def get_context(key):
    """
    获取上下文变量
    
    参数:
        key (str): 变量名
        
    返回:
        any: 变量值
    """
```

#### ASSERT

```python
def ASSERT(actual, op, expected, msg=None):
    """
    通用断言方法，可在 code 脚本中直接调用，支持多种断言类型。
    
    参数:
        actual (any): 实际值
        op (str): 操作符，如 ==, !=, >, <, contains, regex, startswith, endswith 等
        expected (any): 期望值
        msg (str, optional): 断言失败时的自定义消息
    
    支持的操作符:
        ==, !=, >, <, >=, <=, contains, not_contains, regex, startswith, endswith
    
    断言失败时抛出 AssertionError
    """
```

##### 用法示例

```python
ASSERT("hello world", op="contains", expected="hello")
ASSERT(5, op=">", expected=3)
ASSERT("abc123", op="regex", expected=r"\d+")
ASSERT("foo", op="==", expected="foo")
ASSERT("bar", op="not_contains", expected="baz")
```

## 返回值说明

### TemplateEngine.generate 返回值

```python
{
    "name": "张三",  # 模板变量替换后的值
    "age": 25,
    "email": "默认邮箱"  # 未提供的变量使用默认值
}
```

### CodeEngine.execute 返回值

```python
{
    "data": {
        "msg": "执行成功！",
        "data": [...]  # 执行结果数据
    },
    "status_code": 200,
    "stdout": "标准输出内容",
    "debug_output": [  # 仅在调试模式开启时
        "开始执行代码",
        "代码内容: ...",
        "执行SQL: ...",
        "代码执行完成"
    ]
}
```

## 错误处理

### 模板引擎错误

- 模板语法错误：抛出 `TemplateError`
- 变量未定义：使用默认值或抛出 `VariableNotDefinedError`
- 方法执行错误：抛出 `MethodExecutionError`

### 代码引擎错误

- 代码语法错误：抛出 `SyntaxError`
- SQL 执行错误：抛出 `SQLExecutionError`
- 上下文变量未定义：抛出 `ContextVariableNotDefinedError`
- 断言失败：抛出 `AssertionError`，并在 execute 返回结果的 error 字段体现

## 示例代码

### 模板引擎示例

```python
from mock_engine.core.template_engine import TemplateEngine

engine = TemplateEngine(debug=True)

@engine.register_method()
def format_name(name):
    return f"尊敬的{name}"

template = {
    "greeting": "{{format_name(name)}}",
    "age": "{{age}}"
}

request = {
    "name": "张三",
    "age": 25
}

result, debug_output = engine.generate(template, request)
```

### 代码引擎示例

```python
from mock_engine.core.code_engine import CodeEngine

engine = CodeEngine(debug=True)

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'database': 'webtest'
}

engine.add_context('user_id', 1)

code = f"""
user_id = get_context('user_id')
result = sql("SELECT * FROM webtest.t_ui_user WHERE id = {user_id}", db_config={db_config})
print("用户信息:", result)
ASSERT("hello world", op="contains", expected="hello")
"""

result = engine.execute(code)
``` 
 # Mock Engine

Mock Engine 是一个强大的 Python 测试数据生成和模拟引擎，专为自动化测试和开发环境设计。它提供了灵活的模板系统和代码执行引擎，支持数据库操作、断言验证等功能。

## 目录
- [快速开始](#快速开始)
- [模板引擎使用指南](#模板引擎使用指南)
- [代码引擎使用指南](#代码引擎使用指南)
- [调试模式](#调试模式)
- [安装说明](#安装说明)

## 快速开始

### 安装
```bash
pip install mock-engine
```

### 基础示例
```python
from mock_engine.core.template_engine import TemplateEngine
from mock_engine.core.code_engine import CodeEngine

# 模板引擎示例
template_engine = TemplateEngine(debug=True)
code_engine = CodeEngine(debug=True)
```

## 模板引擎使用指南

### 1. 基础模板渲染
```python
# 创建模板
template = {
    "greeting": "Hello, @request_body.name!",
    "age": "@request_body.age",
    "headers": {
        "content_type": "@request_header.content-type"
    }
}

# 提供数据
request = {
    "headers": {
        "content-type": "application/json"
    },
    "body": {
        "name": "张三",
        "age": 25
    }
}

# 生成数据
result, debug = template_engine.generate(template, request)
```

### 2. 自定义方法
```python
@template_engine.register_method()
def format_greeting(name):
    return f"你好，{name}！"

template = {
    "greeting": "{{format_greeting(name)}}"
}
```

### 3. 断言功能
```python
# 定义断言规则
assertions = [
    {"path": "$.age", "op": ">", "value": 18},
    {"path": "$.name", "op": "==", "value": "张三"}
]

# 生成数据并验证断言
result, assertion_results, debug = template_engine.generate_with_assertions(
    template, 
    request, 
    assertions
)
```

## 代码引擎使用指南

### 1. 基础代码执行
```python
code = """
# 获取上下文变量
headers = get_context('headers')
body = get_context('body')

# 修改上下文变量
set_context('headers', {'user': '张三'})

# 设置状态码
set_status_code(201)
"""

result = code_engine.execute(code, request)
```

### 2. HTTP 请求
```python
code = """
# GET 请求
response = http_request('GET', 'https://api.example.com/data', 
                       headers={'X-Test': 'test'})

# POST 请求
post_data = {'name': 'test', 'value': 123}
response = http_request('POST', 'https://api.example.com/create', 
                       headers={'Content-Type': 'application/json'},
                       data=post_data)
"""
```

### 3. SQL 操作
```python
code = """
# 执行 SQL 查询
result = sql_execute("SELECT * FROM users WHERE id = %s", params=[1])

# 执行 SQL 更新
sql_execute("UPDATE users SET name = %s WHERE id = %s", 
           params=['新名字', 1])
"""
```

### 4. 断言功能
```python
code = """
# 基础断言
ASSERT(1 + 1, op='==', expected=2)
ASSERT(5, op='>', expected=3)

# 字符串断言
ASSERT('hello world', op='contains', expected='hello')
"""
```

## 调试模式

### 启用调试
```python
# 模板引擎调试
template_engine = TemplateEngine(debug=True)

# 代码引擎调试
code_engine = CodeEngine(debug=True)
```

### 调试输出示例
```python
# 模板引擎调试输出
[
    "开始生成数据",
    "模板内容: {...}",
    "请求数据: {...}",
    "生成完成"
]

# 代码引擎调试输出
[
    "开始执行代码",
    "代码内容: ...",
    "执行SQL: ...",
    "代码执行完成"
]
```

## 安装说明

### 环境要求
- Python 3.7+
- pip

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/yourusername/mock-engine.git

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```


## 注意事项

1. 调试模式会影响性能，建议只在开发环境使用
2. 数据库配置信息建议通过配置文件管理
3. 生产环境请关闭调试模式
4. 注意保护敏感信息（如数据库密码）

## 许可证

MIT License
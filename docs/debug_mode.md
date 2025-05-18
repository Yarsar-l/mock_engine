# Mock Engine 调试模式使用文档

## 目录
- [简介](#简介)
- [模板引擎调试模式](#模板引擎调试模式)
- [代码引擎调试模式](#代码引擎调试模式)
- [调试输出说明](#调试输出说明)
- [使用示例](#使用示例)

## 简介

Mock Engine 提供了强大的调试模式功能，可以帮助开发者更好地理解和调试模板渲染和代码执行过程。调试模式会输出详细的执行日志，包括执行步骤、变量值、SQL 查询等信息。

## 模板引擎调试模式

### 基本用法

```python
from mock_engine.core.template_engine import TemplateEngine

# 创建带调试模式的引擎实例
engine = TemplateEngine(debug=True)

# 创建模板
template = {
    "name": "{{name}}",
    "age": "{{age}}",
    "email": "{{email}}"
}

# 创建请求数据
request = {
    "name": "张三",
    "age": 25
}

# 生成数据并获取调试信息
result, debug_output = engine.generate(template, request)
```

### 调试输出内容

模板引擎的调试输出包含以下信息：
- 开始生成数据的时间戳
- 模板内容
- 请求数据
- 变量替换过程
- 自定义方法执行情况
- 生成完成的时间戳

## 代码引擎调试模式

### 基本用法

```python
from mock_engine.core.code_engine import CodeEngine

# 创建带调试模式的引擎实例
engine = CodeEngine(debug=True)

# 数据库配置
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'database': 'webtest'
}

# 执行代码
code = """
result = sql("SELECT * FROM webtest.t_ui_user LIMIT 1", db_config=db_config)
print("查询结果:", result)
"""

# 执行并获取调试信息
result = engine.execute(code)
```

### 调试输出内容

代码引擎的调试输出包含以下信息：
- 开始执行代码的时间戳
- 代码内容
- SQL 查询语句
- SQL 执行结果
- 上下文变量获取情况
- 代码执行完成的时间戳

## 调试输出说明

### 模板引擎调试输出示例

```python
[
    "开始生成数据",
    "模板内容: {'name': '{{name}}', 'age': '{{age}}', 'email': '{{email}}'}",
    "请求数据: {'name': '张三', 'age': 25}",
    "执行方法: custom_method",
    "生成完成"
]
```

### 代码引擎调试输出示例

```python
[
    "开始执行代码",
    "代码内容: result = sql('SELECT * FROM webtest.t_ui_user LIMIT 1')",
    "执行SQL: SELECT * FROM webtest.t_ui_user LIMIT 1",
    "SQL执行结果: {'msg': '执行成功！', 'data': [...]}",
    "获取上下文变量: test_var",
    "代码执行完成"
]
```

## 使用示例

### 1. 模板引擎自定义方法调试

```python
engine = TemplateEngine(debug=True)

@engine.register_method()
def custom_method(value):
    return f"处理后的值: {value}"

template = {
    "value": "{{custom_method('test')}}"
}

result, debug_output = engine.generate(template)
```

### 2. 代码引擎上下文变量调试

```python
engine = CodeEngine(debug=True)

# 添加上下文变量
engine.add_context("test_var", "test_value")

# 执行代码
code = """
value = get_context("test_var")
print("获取到的值:", value)
"""

result = engine.execute(code)
```

### 3. SQL 查询调试

```python
engine = CodeEngine(debug=True)

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '123456',
    'port': 3306,
    'database': 'webtest'
}

code = f"""
result = sql("SELECT * FROM webtest.t_ui_user LIMIT 1", db_config={db_config})
print("查询结果:", result)
"""

result = engine.execute(code)
```

## 注意事项

1. 调试模式会影响性能，建议只在开发环境中使用
2. 调试输出可能包含敏感信息，请注意日志安全
3. 在生产环境中请关闭调试模式
4. 数据库配置信息建议通过配置文件管理，避免硬编码 
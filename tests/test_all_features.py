import json
from mock_engine.core.code_engine import CodeEngine

def main():
    """测试所有功能的集成测试"""
    code = '''
# 1. 测试请求数据获取和修改
print("=== 测试请求数据获取和修改 ===")
headers = get_context('headers')
body = get_context('body')
query = get_context('query')
print('原始请求头:', headers)
print('原始请求体:', body)
print('原始查询参数:', query)

# 修改请求数据
headers['user'] = 'Edy'
body['name'] = 'Alice'
query['foo'] = 'baz'
set_context('headers', headers)
set_context('body', body)
set_context('query', query)

# 验证修改
headers2 = get_context('headers')
body2 = get_context('body')
query2 = get_context('query')
print('修改后请求头:', headers2)
print('修改后请求体:', body2)
print('修改后查询参数:', query2)

# 2. 测试状态码设置和获取
print("\\n=== 测试状态码设置和获取 ===")
set_status_code(201)
status = get_status_code()
print('设置的状态码:', status)
ASSERT(status, op='==', expected=201)

# 3. 测试 HTTP 请求
print("\\n=== 测试 HTTP 请求 ===")
# GET 请求
response = http_request('GET', 'https://httpbin.org/get', headers={'X-Test': 'test'})
print('GET 响应:', response)
ASSERT(response['status_code'], op='==', expected=200)

# POST 请求
post_data = {'name': 'test', 'value': 123}
response = http_request('POST', 'https://httpbin.org/post', 
                       headers={'Content-Type': 'application/json'},
                       data=post_data)
print('POST 响应:', response)
ASSERT(response['status_code'], op='==', expected=200)

# 4. 测试 SQL 执行
print("\\n=== 测试 SQL 执行 ===")
# 先执行 DROP TABLE IF EXISTS webtest.test_table
sql_execute("DROP TABLE IF EXISTS webtest.test_table")

# 创建表
sql_execute("CREATE TABLE IF NOT EXISTS webtest.test_table (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255), value INT)")

# 插入数据
sql_execute("INSERT INTO webtest.test_table (name, value) VALUES (%s, %s)", params=['test1', 100])

# 查询数据
result = sql_execute("SELECT * FROM webtest.test_table")
print('SQL 查询结果:', result)
ASSERT(len(result), op='>', expected=0)

# 5. 测试断言功能
print("\\n=== 测试断言功能 ===")
ASSERT(1 + 1, op='==', expected=2)
ASSERT(5, op='>', expected=3)
ASSERT('hello world', op='contains', expected='hello')

print("\\n所有测试完成!")
'''

    # 准备测试数据
    request = {
        "headers": {
            "user": "World",
            "content-type": "application/json"
        },
        "body": {
            "name": "John",
            "age": 25
        },
        "query": {
            "foo": "bar"
        }
    }

    # 执行测试
    engine = CodeEngine(debug=True)
    exec_result = engine.execute(code, request)
    
    # 打印执行结果
    print("\n=== 执行结果 ===")
    print("代码执行结果:", json.dumps(exec_result, indent=2, ensure_ascii=False))
    if 'debug_output' in exec_result:
        print("\n调试输出:", json.dumps(exec_result['debug_output'], indent=2, ensure_ascii=False))
    if 'stdout' in exec_result:
        print("\n标准输出:", exec_result['stdout'])

if __name__ == "__main__":
    main() 
def main():
    """直接执行代码测试 request 方法"""
    import json
    from mock_engine.core.code_engine import CodeEngine

    # 初始化 CodeEngine，开启 debug 模式
    engine = CodeEngine(debug=False)
    # 测试代码片段
    code = '''
import json
# 测试 GET 请求
url = "https://httpbin.org/get"
params = {"test": "get"}
response = request(url=url, method="GET", params=params)
print("GET 请求响应:", json.dumps(response, indent=2, ensure_ascii=False))

# 测试 POST 请求
# url = "https://httpbin.org/post"
# data = {"test": "post"}
# headers = {"Content-Type": "application/json"}
# response = request(url=url, method="POST", data=data, headers=headers)
# print("POST 请求响应:", json.dumps(response, indent=2, ensure_ascii=False))
'''
    exec_result = engine.execute(code)
    print("代码执行结果:", json.dumps(exec_result, indent=2, ensure_ascii=False))
    if 'debug_output' in exec_result:
        print("调试输出:", json.dumps(exec_result['debug_output'], indent=2, ensure_ascii=False))
    if 'stdout' in exec_result:
        print("标准输出:", exec_result['stdout'])

if __name__ == "__main__":
    main() 
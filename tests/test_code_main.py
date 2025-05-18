import json
from mock_engine.core.code_engine import CodeEngine

def main():
    """直接执行代码测试 CodeEngine 代码模式"""
    # 测试代码：通过 get_context 访问 HEADERS
    code = '''
headers = get_context('HEADERS')
result = f"Hello, {headers.get('user', 'Guest')}!"
print("代码执行成功，result:", result)
'''
    context = {"HEADERS": {"user": "World"}}
    engine = CodeEngine(debug=True)
    exec_result = engine.execute(code, context)
    print("代码执行结果:", json.dumps(exec_result, indent=2, ensure_ascii=False))
    if 'debug_output' in exec_result:
        print("调试输出:", json.dumps(exec_result['debug_output'], indent=2, ensure_ascii=False))
    if 'stdout' in exec_result:
        print("标准输出:", exec_result['stdout'])

if __name__ == "__main__":
    main() 
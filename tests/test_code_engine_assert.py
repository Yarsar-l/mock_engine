from mock_engine.core.code_engine import CodeEngine

def test_code_engine_assert_success():
    code = '''
ASSERT("hello world", op="contains", expected="hello")
ASSERT(5, op=">", expected=3)
ASSERT("abc123", op="regex", expected=r"\\d+")
ASSERT("foo", op="==", expected="foo")
ASSERT("bar", op="not_contains", expected="baz")
result = "断言全部通过"
'''
    engine = CodeEngine()
    output = engine.execute(code)
    assert output["data"] == "断言全部通过"
    assert output["status_code"] == 200
    print("success output:", output)

def test_code_engine_assert_fail():
    code = '''
ASSERT("hello world", op="contains", expected="bye")
result = "should not reach here"
'''
    engine = CodeEngine()
    output = engine.execute(code)
    assert "error" in output
    assert "断言失败" in output["error"]
    print("fail output:", output)

if __name__ == "__main__":
    test_code_engine_assert_success()
    test_code_engine_assert_fail() 
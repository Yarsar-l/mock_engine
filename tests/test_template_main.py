import json
from mock_engine.core.template_engine import TemplateEngine

def main():
    """直接执行代码测试模板引擎"""
    # 初始化模板引擎，开启 debug 模式
    engine = TemplateEngine(debug=True)

    # 注册自定义方法
    @engine.register_method()
    def format_greeting(name):
        return f"你好，{name}！"

    # 创建模板（使用@变量形式）
    template = {
        "greeting": "Hello, @request_body.name!",
        "name": "@request_body.name",
        "age": "@request_body.age",
        "faker_name": "@faker.name",
        "nested": {
            "level1": {
                "level2": "@request_body.nested.level1.level2"
            }
        },
        "headers": {
            "content_type": "@request_header.content-type",
            "user_agent": "@request_header.user-agent",
            "all_headers": "@request_header"
        },
        "body": {
            "username": "@request_body.username",
            "password": "@request_body.password",
            "profile": {
                "age": "@request_body.profile.age",
                "address": "@request_body.profile.address"
            },
            "all_body": "@request_body"
        }
    }

    # 只包含标准结构的 request 对象
    request = {
        "headers": {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            "authorization": "Bearer token123"
        },
        "body": {
            "name": "John",
            "age": 25,
            "nested": {
                "level1": {
                    "level2": "deep"
                }
            }
        },
        "query": {
            "foo": "bar"
        }
    }

    # 生成数据
    result, debug = engine.generate(template, request)
    
    # 打印结果
    print("\n=== 模板渲染结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    print("\n=== 调试输出 ===")
    for msg in debug:
        print(f"- {msg}")

def test_template_engine_with_assertions():
    """测试模板引擎的断言功能"""
    engine = TemplateEngine(debug=True)
    
    # 测试模板 - 只包含需要返回的数据
    template = {
        "greeting": "Hello, @request_body.username!",
        "name": "@request_body.username",
        "age": "@request_body.profile.age",
        "faker_name": "@faker.name",
        "nested": {
            "level1": {
                "level2": "@request_body.profile.address"
            }
        },
        "headers": {
            "content_type": "@request_header.content-type",
            "user_agent": "@request_header.user-agent",
            "all_headers": "@request_header"
        }
    }
    
    # 测试数据
    request = {
        "headers": {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0",
            "authorization": "Bearer token123"
        },
        "body": {
            "username": "zhangsan",
            "password": "123456",
            "profile": {
                "age": 25,
                "address": "北京市朝阳区"
            }
        },
        "query": {
            "foo": "bar"
        }
    }
    
    # 定义断言规则（每项只包含path、op、value字段）
    assertions = [
        {"path": "$.age", "op": ">", "value": 18},
        {"path": "$.name", "op": "==", "value": "zhangsan"},
        {"path": "$.nested.level1.level2", "op": "==", "value": "北京市朝阳区"},
        {"path": "$.faker_name", "op": "len>", "value": 0},
        {"path": "$.headers.content_type", "op": "==", "value": "application/json"},
        {"path": "$.headers.user_agent", "op": "==", "value": "Mozilla/5.0"},
        {"path": "$.name", "op": "==", "value": "zhangsan"},
        {"path": "$.age", "op": "==", "value": 25}
    ]
    
    # 生成数据并验证断言
    result, assertion_results, debug = engine.generate_with_assertions(template, request, assertions)
    
    # 打印结果
    print("\n=== 模板渲染结果 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n=== 断言验证 ===")
    for name, result in assertion_results.items():
        print(f"{name}: {result}")
    
    if debug:
        print("\n=== 调试信息 ===")
        for d in debug:
            print(d)
    
    # 验证断言结果
    assert assertion_results["assert__age_>_1"], "年龄断言失败"
    assert assertion_results["assert__name_==_2"], "名字断言失败"
    assert assertion_results["assert__nested_level1_level2_==_3"], "嵌套数据断言失败"
    assert assertion_results["assert__faker_name_len>_4"], "Faker断言失败"

if __name__ == "__main__":
    test_template_engine_with_assertions() 
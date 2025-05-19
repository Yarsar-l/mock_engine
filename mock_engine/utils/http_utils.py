import logging
import requests
from typing import Dict, Optional, Any, Callable
# from mock_engine.config import Config
# from mock_engine.plugins import PluginManager
# from mock_engine.cache import Cache
# from mock_engine.validators import SchemaValidator
# from mock_engine.monitoring import PerformanceMonitor

logger = logging.getLogger(__name__)

class RequestEngine:
    """HTTP请求引擎"""

    def __init__(self, base_url: str = 'http://127.0.0.1:8000/mock/', debug_callback: Optional[Callable] = None):
        """
        初始化请求引擎
        
        Args:
            base_url: 基础URL
            debug_callback: 调试回调函数
        """
        self.base_url = base_url.rstrip('/')
        self.debug_callback = debug_callback

    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 30,
        verify: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: 请求方法
            url: 请求路径
            headers: 请求头
            json: JSON数据
            data: 表单数据
            params: 查询参数
            timeout: 超时时间
            verify: 是否验证SSL证书
            
        Returns:
            响应结果字典
        """
        try:
            url = f"{self.base_url}/{url.lstrip('/')}"
            headers = headers or {}
            if self.debug_callback:
                self.debug_callback(f"发送HTTP请求: {method.upper()} {url} headers={headers} params={params} data={data or json}")
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json,
                data=data,
                params=params,
                timeout=timeout,
                verify=verify,
                **kwargs
            )
            if self.debug_callback:
                self.debug_callback(f"HTTP响应: status={response.status_code}")
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"请求发送失败: {str(e)}")
            if self.debug_callback:
                self.debug_callback(f"HTTP请求异常: {str(e)}")
            return {
                'error': str(e),
                'status_code': 500
            }

def send_mock_request(
    method: str,
    path: str = None,
    base_url: str = 'http://127.0.0.1:8000/mock/',
    headers: Optional[Dict] = None,
    data: Optional[Dict] = None,
    debug_callback: Optional[Callable] = None,
    url: Optional[str] = None,
    params: Optional[Dict] = None,
    timeout: int = 30,
    verify: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    发送Mock请求的便捷函数
    
    Args:
        method: 请求方法
        path: 请求路径
        base_url: 基础URL
        headers: 请求头
        data: 请求数据
        debug_callback: 调试回调函数
        url: 完整URL（如果提供，则忽略 path 和 base_url）
        params: 查询参数
        timeout: 超时时间
        verify: 是否验证SSL证书
        
    Returns:
        响应结果字典
    """
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path
    elif path and (path.startswith('http://') or path.startswith('https://')):
        from urllib.parse import urlparse
        parsed = urlparse(path)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path
    try:
        client = RequestEngine(base_url=base_url, debug_callback=debug_callback)
        return client.send_request(
            method=method,
            url=path,
            headers=headers,
            json=data,
            params=params,
            timeout=timeout,
            verify=verify,
            **kwargs
        )
    except Exception as e:
        logger.error(f"请求发送失败: {str(e)}")
        if debug_callback:
            debug_callback(f"HTTP请求异常: {str(e)}")
        return {
            'error': str(e),
            'status_code': 500
        }

def request(*args, **kwargs):
    """对外暴露统一的 request 方法，等价于 send_mock_request"""
    return send_mock_request(*args, **kwargs)

# # 初始化全局组件（测试时注释掉）
# config = Config()
# plugin_manager = PluginManager()
# cache = Cache()
# validator = SchemaValidator()
# monitor = PerformanceMonitor()

def main():
    """直接执行代码测试 request 方法"""
    import sys
    import json
    from mock_engine.core.code_engine import CodeEngine

    # 初始化 CodeEngine，开启 debug 模式
    engine = CodeEngine(debug=True)
    debug_output = []
    debug_callback = lambda msg: debug_output.append(msg)

    # 测试 GET 请求
    url = "https://httpbin.org/get"
    params = {"test": "get"}
    response = request(url=url, method="GET", params=params, debug_callback=debug_callback)
    print("GET 请求响应:", json.dumps(response, indent=2, ensure_ascii=False))
    print("调试输出:", debug_output)

    # 测试 POST 请求
    url = "https://httpbin.org/post"
    data = {"test": "post"}
    headers = {"Content-Type": "application/json"}
    response = request(url=url, method="POST", data=data, headers=headers, debug_callback=debug_callback)
    print("POST 请求响应:", json.dumps(response, indent=2, ensure_ascii=False))
    print("调试输出:", debug_output)

if __name__ == "__main__":
    main() 
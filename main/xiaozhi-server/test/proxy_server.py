#!/usr/bin/env python3
"""
简单的 CORS 代理服务器
用于绕过浏览器的跨域限制，代理请求到 TEN Agent 服务

使用方法:
    python3 proxy_server.py [--port 18007] [--target http://34.212.236.177:3000]
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import argparse
from urllib.parse import urlparse

class CORSProxyHandler(http.server.SimpleHTTPRequestHandler):
    # 目标服务器地址
    target_server = "http://34.212.236.177:3000"
    
    def end_headers(self):
        # 添加 CORS 头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
        super().end_headers()

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """处理 GET 请求"""
        if self.path.startswith('/api/'):
            self._proxy_request('GET')
        else:
            # 静态文件服务
            super().do_GET()

    def do_POST(self):
        """处理 POST 请求"""
        if self.path.startswith('/api/'):
            self._proxy_request('POST')
        else:
            self.send_error(404, "Not Found")

    def _proxy_request(self, method):
        """代理请求到目标服务器"""
        target_url = f"{self.target_server}{self.path}"
        
        print(f"[PROXY] {method} {self.path} -> {target_url}")
        
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # 创建请求
            req = urllib.request.Request(
                target_url,
                data=body,
                method=method
            )
            
            # 复制必要的头
            if self.headers.get('Content-Type'):
                req.add_header('Content-Type', self.headers.get('Content-Type'))
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                
                # 发送响应
                self.send_response(response.status)
                self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', len(response_data))
                self.end_headers()
                self.wfile.write(response_data)
                
                print(f"[PROXY] Response: {response.status}")
                
        except urllib.error.HTTPError as e:
            print(f"[PROXY] HTTP Error: {e.code} - {e.reason}")
            error_body = e.read() if e.fp else b''
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_body)
            
        except urllib.error.URLError as e:
            print(f"[PROXY] URL Error: {e.reason}")
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': str(e.reason)})
            self.wfile.write(error_response.encode())
            
        except Exception as e:
            print(f"[PROXY] Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode())


def run_server(port, target):
    CORSProxyHandler.target_server = target
    
    with socketserver.TCPServer(("", port), CORSProxyHandler) as httpd:
        print(f"=" * 60)
        print(f"CORS 代理服务器已启动")
        print(f"=" * 60)
        print(f"本地地址: http://localhost:{port}")
        print(f"目标服务: {target}")
        print(f"")
        print(f"请在浏览器中访问:")
        print(f"  http://localhost:{port}/test_page_v2.html")
        print(f"")
        print(f"然后在 Agora RTC 模式中填写服务器地址:")
        print(f"  http://localhost:{port}")
        print(f"=" * 60)
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CORS 代理服务器')
    parser.add_argument('--port', type=int, default=18007, help='本地端口 (默认: 18007)')
    parser.add_argument('--target', type=str, default='http://34.212.236.177:3000', 
                        help='目标服务器地址 (默认: http://34.212.236.177:3000)')
    
    args = parser.parse_args()
    run_server(args.port, args.target)

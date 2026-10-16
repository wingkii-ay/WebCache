
# main.py
"""Web 缓存代理服务器入口。"""

import socket
import threading
from urllib.parse import urlunsplit

from cache_manager import CacheManager
from config import CLIENT_TIMEOUT, PROXY_HOST, PROXY_PORT
from http_parser import parse_http_request
from origin_client import fetch_from_origin
from response_handler import build_error_response


cache = CacheManager()


def handle_client(client_socket, client_address):
    """处理单个客户端请求。"""
    try:
        client_socket.settimeout(CLIENT_TIMEOUT)

        request_data = bytearray()

        # 读取完整的 HTTP 请求头
        while b"\r\n\r\n" not in request_data:
            chunk = client_socket.recv(4096)
            if not chunk:
                return

            request_data.extend(chunk)

            if len(request_data) > 65536:
                client_socket.sendall(
                    build_error_response(
                        431, "Request Header Fields Too Large",
                        "Request headers too large"
                    )
                )
                return

        header_end = request_data.find(b"\r\n\r\n") + 4
        # 保留原始字节，由解析器负责解码
        request_bytes = bytes(request_data[:header_end])

        # 解析请求
        request = parse_http_request(request_bytes)

        if request.method != "GET":
            client_socket.sendall(
                build_error_response(
                    501, "Not Implemented",
                    "Only GET requests are supported"
                )
            )
            return

        # 使用规范化后的 URL 作为缓存键
        url = urlunsplit((
            "http",
            request.host if request.port == 80
            else f"{request.host}:{request.port}",
            request.path.split("?", 1)[0],
            request.path.split("?", 1)[1]
            if "?" in request.path else "",
            "",
        ))

        # 查询缓存
        cached_response = cache.get(url)

        if cached_response is not None:
            print(f"[CACHE HIT] {url}")
            client_socket.sendall(cached_response)
            return

        print(f"[CACHE MISS] {url}")

        # 请求目标服务器
        origin_response = fetch_from_origin(
            request.host,
            request.port,
            request.path,
            request.headers,
        )

        # 缓存完整响应并返回客户端
        cache.put(url, origin_response)
        client_socket.sendall(origin_response)

    except ValueError as exc:
        print(f"[BAD REQUEST] {client_address}: {exc}")
        try:
            client_socket.sendall(
                build_error_response(
                    400, "Bad Request", str(exc)
                )
            )
        except OSError:
            pass

    except (OSError, TimeoutError) as exc:
        print(f"[NETWORK ERROR] {client_address}: {exc}")
        try:
            client_socket.sendall(
                build_error_response(
                    502, "Bad Gateway",
                    "Failed to contact the origin server"
                )
            )
        except OSError:
            pass

    except Exception as exc:
        print(f"[ERROR] {client_address}: {exc}")
        try:
            client_socket.sendall(
                build_error_response(
                    500, "Internal Server Error",
                    "Internal proxy server error"
                )
            )
        except OSError:
            pass

    finally:
        client_socket.close()


def start_proxy():
    """启动代理服务器并接收客户端连接。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((PROXY_HOST, PROXY_PORT))
        server.listen(20)

        print(f"Web Cache Proxy listening on {PROXY_HOST}:{PROXY_PORT}")

        try:
            while True:
                client_socket, client_address = server.accept()

                thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )
                thread.start()

        except KeyboardInterrupt:
            print("\nProxy server stopped.")


if __name__ == "__main__":
    start_proxy()

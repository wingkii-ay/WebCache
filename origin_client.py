
# origin_client.py
"""负责与目标 Web 服务器通信。"""

import socket

from config import ORIGIN_TIMEOUT


def fetch_from_origin(host, port, path, headers=None):
    """
    向目标服务器发送 HTTP GET 请求，并返回完整响应字节。

    host: 目标服务器域名
    port: 目标服务器端口
    path: 请求路径，例如 /index.html
    headers: 需要转发的 HTTP 请求头
    """
    request_headers = {
        "Host": host if port == 80 else f"{host}:{port}",
        "Connection": "close",
    }

    if headers:
        for key, value in headers.items():
            if key.lower() not in {
                "host",
                "connection",
                "proxy-connection",
                "content-length",
                "transfer-encoding",
            }:
                request_headers[key] = value

    request_lines = [f"GET {path} HTTP/1.1"]
    request_lines.extend(
        f"{key}: {value}" for key, value in request_headers.items()
    )
    request_text = "\r\n".join(request_lines) + "\r\n\r\n"
    request_bytes = request_text.encode("iso-8859-1")

    with socket.create_connection(
        (host, port), timeout=ORIGIN_TIMEOUT
    ) as sock:
        sock.settimeout(ORIGIN_TIMEOUT)
        sock.sendall(request_bytes)

        response_parts = []
        while True:
            try:
                chunk = sock.recv(8192)
            except socket.timeout:
                raise TimeoutError(
                    f"Timed out while reading response from {host}:{port}"
                )

            if not chunk:
                break

            response_parts.append(chunk)

    return b"".join(response_parts)

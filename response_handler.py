
# response_handler.py
"""生成代理服务器使用的 HTTP 响应。"""

from datetime import datetime, timezone


def build_response(status_code, reason, body, content_type="text/plain; charset=utf-8"):
    """生成完整的 HTTP/1.1 响应字节。"""
    if isinstance(body, str):
        body = body.encode("utf-8")

    headers = [
        f"HTTP/1.1 {status_code} {reason}",
        f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body)}",
        "Connection: close",
    ]

    header_bytes = ("\r\n".join(headers) + "\r\n\r\n").encode("iso-8859-1")
    return header_bytes + body


def build_error_response(status_code, reason, message):
    """生成错误响应。"""
    return build_response(status_code, reason, message)

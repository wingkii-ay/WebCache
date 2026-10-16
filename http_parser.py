# 解析客户端 HTTP 请求

from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass
class HTTPRequest:
    """保存解析后的 HTTP 请求信息。"""

    method: str
    host: str
    port: int
    path: str
    version: str
    headers: dict


def parse_http_request(raw_request: bytes) -> HTTPRequest:
    """
    解析 HTTP 代理请求。

    参数:
        raw_request: 客户端发送的原始 HTTP 请求字节。

    返回:
        HTTPRequest: 解析后的请求对象。

    当前版本支持:
        - HTTP/1.0 和 HTTP/1.1 请求行
        - GET 方法
        - 绝对 URL 和 origin-form 路径
        - Host 请求头
    """

    try:
        request_text = raw_request.decode("iso-8859-1")
    except UnicodeDecodeError as exc:
        raise ValueError("无法解码 HTTP 请求") from exc

    # HTTP 请求头与请求体之间以空行分隔。
    lines = request_text.split("\r\n")

    if not lines or not lines[0].strip():
        raise ValueError("HTTP 请求为空")

    # 解析请求行：METHOD TARGET VERSION
    request_line = lines[0].split()

    if len(request_line) != 3:
        raise ValueError("HTTP 请求行格式错误")

    method, target, version = request_line

    if method.upper() != "GET":
        raise ValueError("当前版本仅支持 GET 请求")

    if version not in ("HTTP/1.0", "HTTP/1.1"):
        raise ValueError("不支持的 HTTP 版本")

    # 解析请求头，统一使用小写键名。
    headers = {}

    for line in lines[1:]:
        if line == "":
            break

        if line[0] in (" ", "\t"):
            raise ValueError("当前版本不支持折叠格式的请求头")

        if ":" not in line:
            raise ValueError(f"请求头格式错误: {line}")

        name, value = line.split(":", 1)
        name = name.strip().lower()
        value = value.strip()

        if not name:
            raise ValueError("请求头名称不能为空")

        if name in headers:
            headers[name] += ", " + value
        else:
            headers[name] = value

    # 浏览器配置 HTTP 代理后，通常发送绝对 URL。
    if target.startswith("http://"):
        url = urlsplit(target)

        if not url.hostname:
            raise ValueError("URL 中缺少主机名")

        if url.username is not None or url.password is not None:
            raise ValueError("不支持 URL 中包含用户凭据")

        try:
            port = url.port or 80
        except ValueError as exc:
            raise ValueError("URL 端口格式错误") from exc

        host = url.hostname

        # URL 中的 fragment 不会发送给源站。
        path = url.path or "/"

        if url.query:
            path += "?" + url.query

    else:
        # 兼容直接使用路径的请求，例如 /index.html。
        # 这种形式必须从 Host 请求头获取目标主机。
        if not target.startswith("/") or target.startswith("//"):
            raise ValueError("不支持的请求目标格式")

        host_header = headers.get("host")

        if not host_header:
            raise ValueError("请求头缺少 Host")

        try:
            host_url = urlsplit("//" + host_header)

            if not host_url.hostname:
                raise ValueError("Host 中缺少主机名")

            host = host_url.hostname
            port = host_url.port or 80

        except ValueError as exc:
            raise ValueError("Host 请求头格式错误") from exc

        path = target

    return HTTPRequest(
        method=method.upper(),
        host=host,
        port=port,
        path=path,
        version=version,
        headers=headers,
    )

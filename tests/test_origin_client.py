
import unittest
from unittest.mock import MagicMock, patch

import origin_client


class TestOriginClient(unittest.TestCase):

    @patch("origin_client.socket.create_connection")
    def test_fetch_returns_complete_response(self, mock_connect):
        """测试能够接收并返回完整的 HTTP 响应"""
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [
            b"HTTP/1.1 200 OK\r\n",
            b"Content-Length: 2\r\n\r\nOK",
            b"",
        ]
        mock_connect.return_value.__enter__.return_value = mock_socket

        response = origin_client.fetch_from_origin(
            "example.com", 80, "/"
        )

        self.assertEqual(
            response,
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK",
        )
        mock_connect.assert_called_once_with(
            ("example.com", 80),
            timeout=origin_client.ORIGIN_TIMEOUT,
        )
        mock_socket.sendall.assert_called_once()

    @patch("origin_client.socket.create_connection")
    def test_request_contains_expected_headers(self, mock_connect):
        """测试请求方法、路径和请求头构造正确"""
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [b"HTTP/1.1 200 OK\r\n\r\nOK", b""]
        mock_connect.return_value.__enter__.return_value = mock_socket

        origin_client.fetch_from_origin(
            "example.com",
            80,
            "/index.html",
            headers={
                "User-Agent": "WebCache-Test",
                "Accept": "text/html",
                "Host": "malicious.example",
                "Connection": "keep-alive",
                "Proxy-Connection": "keep-alive",
                "Content-Length": "100",
                "Transfer-Encoding": "chunked",
            },
        )

        request = mock_socket.sendall.call_args.args[0].decode("iso-8859-1")

        self.assertIn("GET /index.html HTTP/1.1\r\n", request)
        self.assertIn("Host: example.com\r\n", request)
        self.assertIn("Connection: close\r\n", request)
        self.assertIn("User-Agent: WebCache-Test\r\n", request)
        self.assertIn("Accept: text/html\r\n", request)

        # 不应转发这些由代理自行管理或不适合直接转发的请求头
        self.assertNotIn("Host: malicious.example", request)
        self.assertNotIn("Connection: keep-alive", request)
        self.assertNotIn("Proxy-Connection:", request)
        self.assertNotIn("Content-Length:", request)
        self.assertNotIn("Transfer-Encoding:", request)

    @patch("origin_client.socket.create_connection")
    def test_connection_failure(self, mock_connect):
        """测试建立连接失败时异常能够向上传递"""
        mock_connect.side_effect = OSError("Connection failed")

        with self.assertRaises(OSError):
            origin_client.fetch_from_origin(
                "example.com", 80, "/"
            )

    @patch("origin_client.socket.create_connection")
    def test_read_timeout(self, mock_connect):
        """测试接收响应时发生超时"""
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = TimeoutError

        mock_connect.return_value.__enter__.return_value = mock_socket

        with self.assertRaisesRegex(
            TimeoutError,
            "Timed out while reading response",
        ):
            origin_client.fetch_from_origin(
                "example.com", 80, "/"
            )

    @patch("origin_client.socket.create_connection")
    def test_non_default_port_in_host_header(self, mock_connect):
        """测试非默认端口会包含在 Host 请求头中"""
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = [b"HTTP/1.1 200 OK\r\n\r\n", b""]
        mock_connect.return_value.__enter__.return_value = mock_socket

        origin_client.fetch_from_origin(
            "example.com", 8080, "/"
        )

        request = mock_socket.sendall.call_args.args[0].decode("iso-8859-1")
        self.assertIn("Host: example.com:8080\r\n", request)


if __name__ == "__main__":
    unittest.main()

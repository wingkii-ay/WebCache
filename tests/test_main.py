
import unittest
from unittest.mock import MagicMock, patch

import main


class TestHandleClient(unittest.TestCase):

    def setUp(self):
        self.client = MagicMock()
        self.address = ("127.0.0.1", 50000)

    def make_request(self, request):
        """模拟客户端分段读取 HTTP 请求"""
        self.client.recv.return_value = request

    @patch("main.cache")
    def test_cache_hit(self, mock_cache):
        """测试缓存命中时直接返回缓存响应"""
        request = b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n"
        cached_response = b"HTTP/1.1 200 OK\r\n\r\nCached"

        self.make_request(request)
        mock_cache.get.return_value = cached_response

        main.handle_client(self.client, self.address)

        mock_cache.get.assert_called_once()
        self.client.sendall.assert_called_once_with(cached_response)
        self.client.close.assert_called_once()

    @patch("main.fetch_from_origin")
    @patch("main.cache")
    def test_cache_miss_fetches_and_caches_origin_response(
        self, mock_cache, mock_fetch
    ):
        """测试缓存未命中时请求源站、缓存响应并返回"""
        request = b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n"
        origin_response = b"HTTP/1.1 200 OK\r\n\r\nOrigin"

        self.make_request(request)
        mock_cache.get.return_value = None
        mock_fetch.return_value = origin_response

        main.handle_client(self.client, self.address)

        mock_fetch.assert_called_once()
        mock_cache.put.assert_called_once()
        self.client.sendall.assert_called_once_with(origin_response)
        self.client.close.assert_called_once()

    
    @patch("main.cache")
    def test_non_get_request_returns_400(self, mock_cache):
        """测试解析器拒绝非 GET 请求时返回 400"""
        request = b"POST http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n"

        self.make_request(request)

        main.handle_client(self.client, self.address)

        response = self.client.sendall.call_args.args[0]
        self.assertTrue(response.startswith(b"HTTP/1.1 400 Bad Request\r\n"))
        mock_cache.get.assert_not_called()
        self.client.close.assert_called_once()


    @patch("main.cache")
    def test_invalid_request_returns_400(self, mock_cache):
        """测试无法解析的请求返回 400"""
        request = b"INVALID REQUEST\r\n\r\n"

        self.make_request(request)

        main.handle_client(self.client, self.address)

        response = self.client.sendall.call_args.args[0]
        self.assertTrue(response.startswith(b"HTTP/1.1 400 Bad Request\r\n"))
        mock_cache.get.assert_not_called()
        self.client.close.assert_called_once()

    @patch("main.fetch_from_origin")
    @patch("main.cache")
    def test_origin_connection_error_returns_502(
        self, mock_cache, mock_fetch
    ):
        """测试源站连接失败时返回 502"""
        request = b"GET http://example.com/ HTTP/1.1\r\nHost: example.com\r\n\r\n"

        self.make_request(request)
        mock_cache.get.return_value = None
        mock_fetch.side_effect = OSError("Connection failed")

        main.handle_client(self.client, self.address)

        response = self.client.sendall.call_args.args[0]
        self.assertTrue(response.startswith(b"HTTP/1.1 502 Bad Gateway\r\n"))
        self.client.close.assert_called_once()

    @patch("main.cache")
    def test_oversized_request_header_returns_431(self, mock_cache):
        """测试请求头超过限制时返回 431"""
        self.client.recv.return_value = b"A" * 65537

        main.handle_client(self.client, self.address)

        response = self.client.sendall.call_args.args[0]
        self.assertTrue(
            response.startswith(
                b"HTTP/1.1 431 Request Header Fields Too Large\r\n"
            )
        )
        mock_cache.get.assert_not_called()
        self.client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()


import unittest
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from response_handler import build_response, build_error_response


class TestResponseHandler(unittest.TestCase):

    def test_build_response_status_line(self):
        """测试响应状态行"""
        response = build_response(200, "OK", b"Hello")

        self.assertTrue(response.startswith(b"HTTP/1.1 200 OK\r\n"))

    def test_build_response_body(self):
        """测试响应正文"""
        body = b"Hello, WebCache!"
        response = build_response(200, "OK", body)

        self.assertTrue(response.endswith(b"\r\n\r\n" + body))

    def test_content_length_matches_body(self):
        """测试 Content-Length 与正文实际字节数一致"""
        body = "你好，世界"
        response = build_response(200, "OK", body)

        header, response_body = response.split(b"\r\n\r\n", 1)

        self.assertIn(
            f"Content-Length: {len(body.encode('utf-8'))}".encode(),
            header,
        )
        self.assertEqual(response_body, body.encode("utf-8"))

    def test_custom_content_type(self):
        """测试自定义 Content-Type"""
        response = build_response(
            200,
            "OK",
            b"<html></html>",
            content_type="text/html; charset=utf-8",
        )

        header = response.split(b"\r\n\r\n", 1)[0]
        self.assertIn(
            b"Content-Type: text/html; charset=utf-8",
            header,
        )

    def test_connection_close_header(self):
        """测试 Connection 响应头"""
        response = build_response(200, "OK", b"Hello")
        header = response.split(b"\r\n\r\n", 1)[0]

        self.assertIn(b"Connection: close", header)

    def test_date_header_is_valid(self):
        """测试 Date 响应头存在且格式有效"""
        response = build_response(200, "OK", b"Hello")
        header = response.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")

        date_line = next(
            line for line in header.split("\r\n")
            if line.startswith("Date: ")
        )
        date_value = date_line[len("Date: "):]
        parsed_date = parsedate_to_datetime(date_value)

        self.assertIsNotNone(parsed_date.tzinfo)
        self.assertEqual(parsed_date.utcoffset().total_seconds(), 0)

    def test_build_error_response(self):
        """测试错误响应的状态码、正文和内容长度"""
        response = build_error_response(
            502,
            "Bad Gateway",
            "源站连接失败",
        )

        header, body = response.split(b"\r\n\r\n", 1)

        self.assertTrue(header.startswith(b"HTTP/1.1 502 Bad Gateway\r\n"))
        self.assertEqual(body.decode("utf-8"), "源站连接失败")
        self.assertIn(
            f"Content-Length: {len(body)}".encode(),
            header,
        )


if __name__ == "__main__":
    unittest.main()

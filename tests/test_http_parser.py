
import unittest

from http_parser import parse_http_request


class TestHTTPParser(unittest.TestCase):

    def test_absolute_url(self):
        raw = (
            b"GET http://example.com/index.html HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )

        request = parse_http_request(raw)

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.host, "example.com")
        self.assertEqual(request.port, 80)
        self.assertEqual(request.path, "/index.html")
        self.assertEqual(request.version, "HTTP/1.1")

    def test_url_with_port_and_query(self):
        raw = (
            b"GET http://example.com:8080/search?q=network HTTP/1.1\r\n"
            b"Host: example.com:8080\r\n"
            b"\r\n"
        )

        request = parse_http_request(raw)

        self.assertEqual(request.host, "example.com")
        self.assertEqual(request.port, 8080)
        self.assertEqual(request.path, "/search?q=network")

    def test_origin_form(self):
        raw = (
            b"GET /index.html HTTP/1.1\r\n"
            b"Host: example.com:8080\r\n"
            b"\r\n"
        )

        request = parse_http_request(raw)

        self.assertEqual(request.host, "example.com")
        self.assertEqual(request.port, 8080)
        self.assertEqual(request.path, "/index.html")

    def test_missing_host(self):
        raw = (
            b"GET /index.html HTTP/1.1\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )

        with self.assertRaises(ValueError):
            parse_http_request(raw)

    def test_invalid_request_line(self):
        raw = b"GET\r\n\r\n"

        with self.assertRaises(ValueError):
            parse_http_request(raw)

    def test_unsupported_method(self):
        raw = (
            b"POST http://example.com/ HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"\r\n"
        )

        with self.assertRaises(ValueError):
            parse_http_request(raw)


if __name__ == "__main__":
    unittest.main()

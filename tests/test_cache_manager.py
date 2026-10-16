
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cache_manager import CacheManager


class TestCacheManager(unittest.TestCase):

    def setUp(self):
        # 使用临时目录，避免影响项目原有的缓存文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)

        # 将缓存目录临时替换为测试目录
        self.config_patch = patch(
            "cache_manager.CACHE_DIR",
            str(self.cache_dir)
        )
        self.config_patch.start()

        self.manager = CacheManager()

    def tearDown(self):
        # 恢复配置并清理临时目录
        self.config_patch.stop()
        self.temp_dir.cleanup()

    def test_cache_miss(self):
        """测试读取不存在的缓存"""
        self.assertIsNone(self.manager.get("http://example.com/"))

    def test_put_and_get(self):
        """测试写入缓存后能正确读取"""
        url = "http://example.com/"
        response = b"HTTP/1.1 200 OK\r\n\r\nHello"

        result = self.manager.put(url, response)

        self.assertTrue(result)
        self.assertEqual(self.manager.get(url), response)

    def test_update_existing_cache(self):
        """测试更新已有缓存"""
        url = "http://example.com/"
        old_response = b"old response"
        new_response = b"new response"

        self.manager.put(url, old_response)
        result = self.manager.put(url, new_response)

        self.assertTrue(result)
        self.assertEqual(self.manager.get(url), new_response)

    def test_clear_cache(self):
        """测试清空缓存"""
        url = "http://example.com/"
        self.manager.put(url, b"response")

        self.manager.clear()

        self.assertIsNone(self.manager.get(url))

    def test_put_non_bytes_raises_type_error(self):
        """测试写入非 bytes 类型的数据"""
        with self.assertRaises(TypeError):
            self.manager.put("http://example.com/", "response")

    def test_oversized_response_is_not_cached(self):
        """测试超过缓存容量的数据不会被缓存"""
        self.manager.max_size = 5
        url = "http://example.com/"
        response = b"123456"

        result = self.manager.put(url, response)

        self.assertFalse(result)
        self.assertIsNone(self.manager.get(url))

    def test_different_urls_have_independent_cache(self):
        """测试不同 URL 的缓存相互独立"""
        url1 = "http://example.com/1"
        url2 = "http://example.com/2"

        self.manager.put(url1, b"response 1")
        self.manager.put(url2, b"response 2")

        self.assertEqual(self.manager.get(url1), b"response 1")
        self.assertEqual(self.manager.get(url2), b"response 2")


if __name__ == "__main__":
    unittest.main()

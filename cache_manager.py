
# cache_manager.py
"""管理 Web 代理服务器的本地响应缓存。"""

import hashlib
import os
import threading
from pathlib import Path

from config import CACHE_DIR, CACHE_MAX_SIZE


class CacheManager:
    """基于文件系统的简单 HTTP 响应缓存。"""

    def __init__(self):
        self.cache_dir = Path(CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = CACHE_MAX_SIZE
        self.lock = threading.Lock()

    def _get_cache_path(self, url):
        """根据 URL 生成对应的缓存文件路径。"""
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.cache_dir / key

    def get(self, url):
        """读取缓存；缓存不存在时返回 None。"""
        cache_path = self._get_cache_path(url)

        with self.lock:
            if not cache_path.is_file():
                return None
            return cache_path.read_bytes()

    def put(self, url, response):
        """保存完整的 HTTP 响应。超出缓存容量时不保存。"""
        if not isinstance(response, bytes):
            raise TypeError("response must be bytes")

        if len(response) > self.max_size:
            return False

        cache_path = self._get_cache_path(url)

        with self.lock:
            try:
                current_size = sum(
                    path.stat().st_size
                    for path in self.cache_dir.iterdir()
                    if path.is_file()
                )

                old_size = (
                    cache_path.stat().st_size
                    if cache_path.is_file()
                    else 0
                )

                if current_size - old_size + len(response) > self.max_size:
                    return False

                cache_path.write_bytes(response)
                return True
            except OSError:
                return False

    def clear(self):
        """清空所有缓存文件。"""
        with self.lock:
            for path in self.cache_dir.iterdir():
                if path.is_file():
                    path.unlink()

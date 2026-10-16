
# config.py
"""Web 缓存代理服务器的基本配置。"""

# 代理服务器监听地址
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8888

# 客户端连接超时时间（秒）
CLIENT_TIMEOUT = 10

# 缓存配置
CACHE_DIR = "cache"
CACHE_MAX_SIZE = 100 * 1024 * 1024  # 100 MB

# 源服务器连接超时时间（秒）
ORIGIN_TIMEOUT = 10

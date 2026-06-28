"""基于内存的 IP 速率限制器

特性：
- 滑动窗口算法，按时间窗 + 最大请求数控制
- 内存存储，无需 Redis 依赖
- 过期条目自动清理
- 线程安全
"""

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple


class RateLimiter:
    """内存速率限制器 — 滑动窗口"""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._store: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_expired(self, now: float):
        """清理过期条目（每 60 秒触发一次）"""
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        expired_keys = []
        for key, timestamps in self._store.items():
            # 移除过期时间戳
            self._store[key] = [t for t in timestamps if t > cutoff]
            if not self._store[key]:
                expired_keys.append(key)
        for key in expired_keys:
            del self._store[key]

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        """检查是否允许请求

        Returns:
            (allowed: bool, remaining: int)
        """
        now = time.time()
        with self._lock:
            self._cleanup_expired(now)
            cutoff = now - self.window_seconds
            # 清理该 key 下的过期时间戳
            self._store[key] = [t for t in self._store[key] if t > cutoff]
            if len(self._store[key]) >= self.max_requests:
                remaining = 0
                return False, remaining
            self._store[key].append(now)
            remaining = self.max_requests - len(self._store[key])
            return True, remaining


# 全局实例：登录接口限流
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

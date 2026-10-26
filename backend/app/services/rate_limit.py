"""进程内滑动窗口限流。

公网部署时前端完全公开，任何人都能打到后端。代码沙箱和 AI 接口是唯二
「每次调用都要消耗真实资源」的入口，必须限流，否则一次脚本扫描就能把
AI 额度刷爆、或者把 CPU 占满。

设计取舍：
- 进程内内存实现，不引入 Redis 依赖（单机部署足够；多实例部署需换成 Redis）；
- 按「用户 ID 优先，取不到再退化成客户端 IP」分桶 —— 登录态的滥用者换 IP
  也没用，匿名请求（如登录爆破）按 IP 限；
- 只保留滑动窗口内的打卡时间戳，惰性清理，不会被随机 key 撑爆内存。
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class SlidingWindowLimiter:
    """一个 key 在 window 秒内最多允许 limit 次。"""

    def __init__(self, limit: int, window_seconds: int, name: str = "limit"):
        self.limit = limit
        self.window = window_seconds
        self.name = name
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def _sweep(self, now: float) -> None:
        """每 10 个窗口清一次空桶，避免长期运行后字典无限增长。"""
        if now - self._last_sweep < self.window * 10:
            return
        self._last_sweep = now
        dead = [k for k, q in self._hits.items() if not q or now - q[-1] > self.window]
        for k in dead:
            self._hits.pop(k, None)

    def hit(self, key: str) -> tuple[bool, int]:
        """记一次调用。返回 (是否放行, 需等待秒数)。"""
        now = time.monotonic()
        with self._lock:
            self._sweep(now)
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False, max(1, int(self.window - (now - q[0])) + 1)
            q.append(now)
            return True, 0

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._hits.clear()
            else:
                self._hits.pop(key, None)


def client_ip(request: Request) -> str:
    """取真实客户端 IP。

    部署在 Nginx 后面时 `request.client.host` 永远是 127.0.0.1，必须读
    X-Real-IP / X-Forwarded-For（nginx.conf 里已配置转发）。
    """
    for header in ("x-real-ip", "x-forwarded-for"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce(limiter: SlidingWindowLimiter, request: Request, user_id: int | None = None) -> None:
    """超限直接抛 429（带中文提示）。"""
    key = f"u:{user_id}" if user_id else f"ip:{client_ip(request)}"
    allowed, retry_after = limiter.hit(key)
    if not allowed:
        raise HTTPException(
            429,
            f"操作太频繁了（{limiter.name}），请 {retry_after} 秒后再试",
            headers={"Retry-After": str(retry_after)},
        )

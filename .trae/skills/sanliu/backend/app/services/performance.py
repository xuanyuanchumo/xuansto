import time
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json

logger = logging.getLogger("performance")

class PerformanceMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, slow_threshold_ms: float = 200.0):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms
        self.request_stats: dict = {
            "total_requests": 0,
            "slow_requests": 0,
            "total_time_ms": 0.0,
            "endpoint_stats": {}
        }
        global performance_middleware_instance
        performance_middleware_instance = self
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        endpoint = f"{request.method} {request.url.path}"
        
        self.request_stats["total_requests"] += 1
        self.request_stats["total_time_ms"] += duration_ms
        
        if endpoint not in self.request_stats["endpoint_stats"]:
            self.request_stats["endpoint_stats"][endpoint] = {
                "count": 0,
                "total_ms": 0.0,
                "min_ms": float('inf'),
                "max_ms": 0.0,
                "slow_count": 0
            }
        
        stats = self.request_stats["endpoint_stats"][endpoint]
        stats["count"] += 1
        stats["total_ms"] += duration_ms
        stats["min_ms"] = min(stats["min_ms"], duration_ms)
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        
        if duration_ms > self.slow_threshold_ms:
            self.request_stats["slow_requests"] += 1
            stats["slow_count"] += 1
            logger.warning(
                f"Slow request: {endpoint} took {duration_ms:.2f}ms "
                f"(threshold: {self.slow_threshold_ms}ms)"
            )
        
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        
        return response
    
    def get_stats(self) -> dict:
        total = self.request_stats["total_requests"]
        avg_time = (
            self.request_stats["total_time_ms"] / total
            if total > 0 else 0
        )
        
        endpoint_summary = []
        for endpoint, stats in self.request_stats["endpoint_stats"].items():
            avg_ms = stats["total_ms"] / stats["count"] if stats["count"] > 0 else 0
            endpoint_summary.append({
                "endpoint": endpoint,
                "count": stats["count"],
                "avg_ms": round(avg_ms, 2),
                "min_ms": round(stats["min_ms"], 2) if stats["min_ms"] != float('inf') else 0,
                "max_ms": round(stats["max_ms"], 2),
                "slow_count": stats["slow_count"],
                "slow_rate": round(stats["slow_count"] / stats["count"] * 100, 2) if stats["count"] > 0 else 0
            })
        
        endpoint_summary.sort(key=lambda x: x["avg_ms"], reverse=True)
        
        return {
            "total_requests": total,
            "slow_requests": self.request_stats["slow_requests"],
            "slow_rate": round(self.request_stats["slow_requests"] / total * 100, 2) if total > 0 else 0,
            "avg_response_time_ms": round(avg_time, 2),
            "endpoints": endpoint_summary[:20]
        }


performance_middleware_instance: Optional[PerformanceMiddleware] = None


def get_performance_stats() -> dict:
    if performance_middleware_instance:
        return performance_middleware_instance.get_stats()
    return {"error": "Performance middleware not initialized"}

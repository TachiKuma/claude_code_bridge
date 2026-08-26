"""受限并发调度器。

IO 密集阶段（health probe / provider ready / ping）用受限并发池并行，
确保同一时刻在途任务数不超过 ``max_workers``。worker 只做无共享可变状态
的探针，写共享状态的启动临界区由调用方保持在主线程串行执行。"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from threading import BoundedSemaphore, Lock, RLock
import time
from typing import Any


@dataclass(frozen=True)
class BoundedRun:
    """受限并发的运行结果与观测。"""

    results: dict[str, Any]
    peak_in_flight: int
    concurrency_wait_ms: float


class ConcurrencyLimiter:
    """基于信号量的受限并发限流器。

    提供 ``bounded()`` 上下文管理器：进入时 acquire 信号量并计等待时间，
    退出时 release。维护在途峰值计数供观测。
    """

    def __init__(self, max_workers: int) -> None:
        self._max = max(1, int(max_workers))
        self._semaphore = BoundedSemaphore(self._max)
        self._state_lock = RLock()
        self._in_flight = 0
        self._peak = 0

    @property
    def max_workers(self) -> int:
        return self._max

    @property
    def measured_peak(self) -> int:
        return self._peak

    def _enter(self) -> None:
        with self._state_lock:
            self._in_flight += 1
            if self._in_flight > self._peak:
                self._peak = self._in_flight

    def _exit(self) -> None:
        with self._state_lock:
            self._in_flight -= 1

    @contextmanager
    def bounded(self):
        """限流进入临界区。yield 等待时间（ms）。"""
        started_ns = time.monotonic_ns()
        self._semaphore.acquire()
        self._enter()
        wait_ms = (time.monotonic_ns() - started_ns) / 1_000_000
        try:
            yield wait_ms
        finally:
            self._exit()
            self._semaphore.release()


def run_bounded_concurrent(
    *,
    items: Iterable[str],
    worker_fn: Callable[[str], Any],
    limiter: ConcurrencyLimiter,
    thread_name_prefix: str = 'ccb-ready-gate',
) -> BoundedRun:
    """受限并行执行 worker_fn，返回按 items 顺序收集的结果。

    worker_fn 应是无共享可变状态的 IO 密集探针。限流器保证在途任务
    数不超过 max_workers。结果按输入顺序返回；异常由调用方处理。
    """
    item_list = list(items)

    def _run(name: str):
        with limiter.bounded() as wait_ms:
            result = worker_fn(name)
            return (name, result, wait_ms)

    completed: dict[str, Any] = {}
    total_wait_ms = 0.0
    with ThreadPoolExecutor(
        max_workers=limiter.max_workers,
        thread_name_prefix=thread_name_prefix,
    ) as pool:
        futures = {}
        for name in item_list:
            futures[pool.submit(_run, name)] = name
        for future in as_completed(futures):
            name = futures[future]
            _name, result, wait_ms = future.result()
            completed[name] = result
            total_wait_ms += wait_ms

    # 结果按输入顺序收集（不受完成顺序影响）
    results = {name: completed[name] for name in item_list}

    return BoundedRun(
        results=results,
        peak_in_flight=limiter.measured_peak,
        concurrency_wait_ms=total_wait_ms,
    )


__all__ = ['BoundedRun', 'ConcurrencyLimiter', 'run_bounded_concurrent']
"""Ready Gate 受限并发调度器测试。"""

from __future__ import annotations

import threading
import time

from ccbd.ready_gate.concurrency import ConcurrencyLimiter, run_bounded_concurrent


def _slow_worker(name: str, *, delay: float, counter: dict, peak: dict) -> str:
    """记录并发进入峰值，模拟 IO 耗时。"""
    with counter_lock:
        counter['in_flight'] += 1
        peak['value'] = max(peak['value'], counter['in_flight'])
    time.sleep(delay)
    with counter_lock:
        counter['in_flight'] -= 1
    return f'result-{name}'


counter_lock = threading.Lock()


def test_limiter_peak_never_exceeds_max_workers() -> None:
    """并发峰值不超过 max_workers=2。"""
    limiter = ConcurrencyLimiter(2)

    counter = {'in_flight': 0}
    peak = {'value': 0}

    def worker(name: str) -> str:
        return _slow_worker(name, delay=0.05, counter=counter, peak=peak)

    result = run_bounded_concurrent(
        items=[f'a{i}' for i in range(6)],
        worker_fn=worker,
        limiter=limiter,
    )

    assert peak['value'] <= 2
    assert len(result.results) == 6
    assert result.results['a0'] == 'result-a0'


def test_limiter_measured_peak_reflects_max() -> None:
    """limiter.measured_peak 反映实际峰值。"""
    limiter = ConcurrencyLimiter(2)
    counter = {'in_flight': 0}
    peak = {'value': 0}

    def worker(name: str) -> str:
        return _slow_worker(name, delay=0.05, counter=counter, peak=peak)

    run_bounded_concurrent(
        items=[f'b{i}' for i in range(4)],
        worker_fn=worker,
        limiter=limiter,
    )

    assert limiter.measured_peak <= 2
    assert limiter.measured_peak >= 1


def test_concurrency_wait_ms_non_negative() -> None:
    """并发等待时间非负。"""
    limiter = ConcurrencyLimiter(3)
    result = run_bounded_concurrent(
        items=['x1', 'x2', 'x3'],
        worker_fn=lambda name: name.upper(),
        limiter=limiter,
    )
    assert result.concurrency_wait_ms >= 0


def test_results_preserved_all_items() -> None:
    """结果覆盖所有输入项。"""
    limiter = ConcurrencyLimiter(4)
    items = ['agent1', 'agent2', 'agent3']
    result = run_bounded_concurrent(
        items=items,
        worker_fn=lambda name: f'ok-{name}',
        limiter=limiter,
    )
    assert set(result.results.keys()) == set(items)
    assert result.results['agent1'] == 'ok-agent1'


def test_max_workers_clamped_to_at_least_one() -> None:
    """max_workers <= 0 时钳到 1。"""
    limiter = ConcurrencyLimiter(0)
    assert limiter.max_workers == 1
    limiter_neg = ConcurrencyLimiter(-5)
    assert limiter_neg.max_workers == 1


def test_worker_results_collected_in_input_order() -> None:
    """结果按输入顺序收集（dict 保留插入序）。"""
    limiter = ConcurrencyLimiter(5)
    items = ['c', 'a', 'b']
    result = run_bounded_concurrent(
        items=items,
        worker_fn=lambda name: name,
        limiter=limiter,
    )
    assert list(result.results.keys()) == items
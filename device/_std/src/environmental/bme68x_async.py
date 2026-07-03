# @package: bme68x_async
# @version: 1.1.0
# @type: device-std
# @category: environmental
# @sensor_type: A
# @interface: I2C
# @depends: bme68x
# @platforms: *
# @tags: bme680, bme688, temperature, pressure, humidity, gas, async, asyncio
# @author: PlanXLab Development Team

import asyncio
import time
from .bme68x import BME68x

_DONE_SENTINEL = object()


class _StreamIter:
    def __init__(self, dev, gas, interval_ms, poll_ms):
        self._dev = dev
        self._gas = gas
        self._interval_ms = interval_ms
        self._poll_ms = poll_ms

    def __aiter__(self):
        return self

    async def __anext__(self):
        poll = self._poll_ms
        t0 = time.ticks_ms()
        self._dev.start(gas=self._gas)
        while not self._dev.ready():
            await asyncio.sleep_ms(poll)
        result = self._dev.result()
        if self._interval_ms > 0:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            remaining = self._interval_ms - elapsed
            if remaining > 0:
                await asyncio.sleep_ms(remaining)
        return result


class _BurnInIter:
    def __init__(self, dev, poll_ms, mode):
        self._queue = asyncio.Queue()
        asyncio.create_task(self._run(dev, poll_ms, mode))

    def __aiter__(self):
        return self

    async def __anext__(self):
        val = await self._queue.get()
        if val is _DONE_SENTINEL:
            raise StopAsyncIteration
        return val

    async def _run(self, dev, poll, mode):
        period = dev._gas_update_hint_ms
        if period >= 3000:
            win_n = 12
            cov_thr = 1.0
            drift_thr = 0.6
        else:
            win_n = 16
            cov_thr = 1.5
            drift_thr = 0.8

        windows_needed = 3
        max_minutes = 10

        warmup_hits = 0
        for _ in range(8):
            dev.trigger_gas_measurement()
            t_dead = time.ticks_add(time.ticks_ms(), period)
            while time.ticks_diff(t_dead, time.ticks_ms()) > 0:
                if dev.gas_measurement_ready():
                    dev.gas_resistance()
                    warmup_hits += 1
                    break
                await asyncio.sleep_ms(poll)

        await self._queue.put({"phase": "warmup", "samples": warmup_hits, "success": False})

        start_ms = time.ticks_ms()
        xs = []
        last_med = None
        consecutive_ok = 0
        window_idx = 0

        while time.ticks_diff(time.ticks_ms(), start_ms) < max_minutes * 60_000:
            tick0 = time.ticks_ms()

            dev.trigger_gas_measurement()
            deadline = time.ticks_add(time.ticks_ms(), period)
            while time.ticks_diff(deadline, time.ticks_ms()) > 0:
                if dev.gas_measurement_ready():
                    break
                await asyncio.sleep_ms(poll)

            g = dev.gas_resistance()
            if g is not None:
                xs.append(g)
                if len(xs) > win_n:
                    xs.pop(0)

                n = len(xs)
                fill_pct = 100.0 * n / win_n

                if n < win_n:
                    med_partial, cov_partial = dev._median_cov(xs, n)
                    eta_s = (win_n - n) * period / 1000.0
                    await self._queue.put({
                        "phase": "acquire",
                        "samples_in_window": n,
                        "win_n": win_n,
                        "fill_pct": fill_pct,
                        "latest_ohm": g,
                        "median_ohm": med_partial,
                        "cov_pct": cov_partial,
                        "eta_to_window_s": eta_s,
                        "success": False,
                    })
                else:
                    window_idx += 1
                    med, cov = dev._median_cov(xs, win_n)
                    drift = 0.0 if last_med is None else abs((med - last_med) / max(last_med, 1e-9)) * 100.0

                    pass_this = (cov <= cov_thr) and (drift <= drift_thr)
                    consecutive_ok = (consecutive_ok + 1) if pass_this else 0
                    last_med = med

                    await self._queue.put({
                        "phase": "window",
                        "window_idx": window_idx,
                        "median_ohm": med,
                        "cov_pct": cov,
                        "drift_pct": drift,
                        "consecutive_ok": consecutive_ok,
                        "success": False,
                    })

                    if consecutive_ok >= windows_needed:
                        dev.gas_baseline = int(med)
                        elapsed_s = time.ticks_diff(time.ticks_ms(), start_ms) // 1000
                        await self._queue.put({
                            "phase": "done",
                            "success": True,
                            "elapsed_s": elapsed_s,
                            "windows_passed": consecutive_ok,
                            "median_ohm": med,
                            "baseline_ohm": dev._gas_baseline,
                            "mode": mode,
                        })
                        await self._queue.put(_DONE_SENTINEL)
                        return

            remaining = period - time.ticks_diff(time.ticks_ms(), tick0)
            if remaining > 0:
                await asyncio.sleep_ms(remaining)

        elapsed_s = time.ticks_diff(time.ticks_ms(), start_ms) // 1000
        await self._queue.put({
            "phase": "done",
            "success": False,
            "elapsed_s": elapsed_s,
            "windows_passed": consecutive_ok,
            "median_ohm": last_med if last_med is not None else 0.0,
            "baseline_ohm": dev._gas_baseline,
            "mode": mode,
        })
        await self._queue.put(_DONE_SENTINEL)


class BME68xAsync:

    def __init__(self, device: BME68x, poll_ms: int = 10):
        self._dev = device
        self._poll_ms = max(5, int(poll_ms))

    async def read(self, *, gas: bool = False) -> tuple:
        self._dev.start(gas=gas)
        while not self._dev.ready():
            await asyncio.sleep_ms(self._poll_ms)
        return self._dev.result()

    async def read_tph(self) -> tuple:
        return await self.read(gas=False)

    async def read_gas(self) -> tuple:
        return await self.read(gas=True)

    def stream(self, *, gas: bool = False, interval_ms: int = 0) -> "_StreamIter":
        return _StreamIter(self._dev, gas, interval_ms, self._poll_ms)

    def burn_in(self, mode: str = "simple") -> "_BurnInIter":
        return _BurnInIter(self._dev, self._poll_ms, mode)

    def __aiter__(self):
        return _StreamIter(self._dev, False, 0, self._poll_ms)

    async def __anext__(self):
        self._dev.start(gas=False)
        while not self._dev.ready():
            await asyncio.sleep_ms(self._poll_ms)
        return self._dev.result()

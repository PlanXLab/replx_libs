# @package: termio_async
# @version: 1.2.0
# @type: core
# @category: utility
# @interface: std_io
# @depends: termio
# @platforms: *
# @tags: terminal, async, asyncio, keyboard, serial
# @author: PlanXLab Development Team

import asyncio
from termio import KeyReader, ReplSerial


class _KeysIter:
    def __init__(self, reader: KeyReader):
        self._reader = reader

    def __aiter__(self) -> "_KeysIter":
        return self

    async def __anext__(self) -> str:
        while True:
            k = self._reader.key
            if k is not None:
                return k
            await asyncio.sleep_ms(10)


class AsyncKeyReader:
    def __init__(self, reader: KeyReader):
        self._reader = reader

    def __enter__(self) -> "AsyncKeyReader":
        self._reader.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._reader.__exit__(exc_type, exc_val, exc_tb)

    @property
    def reader(self) -> KeyReader:
        return self._reader

    @property
    def key(self) -> str | None:
        return self._reader.key

    async def wait_key(self, timeout_ms: int = 0) -> str | None:
        if timeout_ms == 0:
            # Wait forever
            while True:
                k = self._reader.key
                if k is not None:
                    return k
                await asyncio.sleep_ms(10)
        else:
            # Wait with timeout
            elapsed = 0
            poll_ms = 10
            while elapsed < timeout_ms:
                k = self._reader.key
                if k is not None:
                    return k
                await asyncio.sleep_ms(poll_ms)
                elapsed += poll_ms
            return None

    def keys(self) -> "_KeysIter":
        return _KeysIter(self._reader)

    async def wait_for_key(self, target: str, timeout_ms: int = 0) -> bool:
        if timeout_ms == 0:
            while True:
                k = self._reader.key
                if k == target:
                    return True
                await asyncio.sleep_ms(10)
        else:
            elapsed = 0
            poll_ms = 10
            while elapsed < timeout_ms:
                k = self._reader.key
                if k == target:
                    return True
                await asyncio.sleep_ms(poll_ms)
                elapsed += poll_ms
            return False

    async def wait_for_any(self, keys: list[str], timeout_ms: int = 0) -> str | None:
        if timeout_ms == 0:
            while True:
                k = self._reader.key
                if k in keys:
                    return k
                await asyncio.sleep_ms(10)
        else:
            elapsed = 0
            poll_ms = 10
            while elapsed < timeout_ms:
                k = self._reader.key
                if k in keys:
                    return k
                await asyncio.sleep_ms(poll_ms)
                elapsed += poll_ms
            return None


class AsyncReplSerial:
    def __init__(self, serial: ReplSerial):
        self._serial = serial

    def __enter__(self) -> "AsyncReplSerial":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._serial.close()

    @property
    def serial(self) -> ReplSerial:
        return self._serial

    @property
    def timeout(self) -> float | None:
        return self._serial.timeout

    @timeout.setter
    def timeout(self, value: float | None):
        self._serial.timeout = value

    @property
    def in_waiting(self) -> int:
        return self._serial.in_waiting

    def write(self, data: bytes) -> int:
        return self._serial.write(data)

    async def read(self, size: int = 1, timeout_ms: int = 0) -> bytes:
        result = bytearray()
        elapsed = 0
        poll_ms = 10
        
        while len(result) < size:
            if self._serial.in_waiting > 0:
                old_timeout = self._serial.timeout
                self._serial.timeout = 0
                try:
                    chunk = self._serial._buf.get(min(size - len(result), self._serial.in_waiting))
                    result.extend(chunk)
                finally:
                    self._serial.timeout = old_timeout
            
            if len(result) >= size:
                break
            
            # Check timeout
            if timeout_ms > 0 and elapsed >= timeout_ms:
                break
            
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms
        
        return bytes(result)

    async def read_until(self, expected: bytes = b'\r', timeout_ms: int = 0, max_size: int | None = None) -> bytes:
        elapsed = 0
        poll_ms = 10
        
        while True:
            data = self._serial._buf.get_until(expected, max_size)
            if data is not None:
                return data
            
            if max_size and self._serial.in_waiting >= max_size:
                return self._serial._buf.get(max_size)
            
            if timeout_ms > 0 and elapsed >= timeout_ms:
                return self._serial._buf.get(self._serial.in_waiting)
            
            await asyncio.sleep_ms(poll_ms)
            elapsed += poll_ms

    def close(self):
        self._serial.close()

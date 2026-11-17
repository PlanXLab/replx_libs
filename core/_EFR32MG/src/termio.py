# @package: termio_xbee
# @version: 1.0.0
# @type: core
# @category: utility
# @interface: std_io
# @depends: none
# @platforms: EFR32MG
# @tags: terminal, serial, repl, stdin, xbee
# @author: PlanXLab Development Team

import gc
import usys
import utime

_stdin = usys.stdin.buffer
_stdout = usys.stdout.buffer

class ReplSerial:
    def __init__(self, timeout=None, *, bufsize=128):
        self._timeout = timeout
        self._buf = bytearray(bufsize)
        self._bufsize = bufsize
        self._buf_head = 0
        self._buf_tail = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _pump(self):
        # Drain the firmware stdin buffer into the ring buffer (non-blocking).
        while True:
            data = _stdin.read(-1)
            if not data:
                return
            self._buf_put(data)

    def _buf_put(self, data):
        buf = self._buf
        size = self._bufsize
        head = self._buf_head
        tail = self._buf_tail
        for b in data:
            nxt = (head + 1) % size
            if nxt == tail:
                tail = (tail + 1) % size
            buf[head] = b
            head = nxt
        self._buf_head = head
        self._buf_tail = tail

    def _buf_avail(self):
        return (self._buf_head - self._buf_tail) % self._bufsize

    def _buf_get(self, n=1):
        size = self._bufsize
        avail = (self._buf_head - self._buf_tail) % size
        n = min(n, avail)
        if n == 0:
            return b''
        tail = self._buf_tail
        if tail + n <= size:
            out = self._buf[tail:tail + n]
        else:
            out = self._buf[tail:] + self._buf[:(tail + n) % size]
        self._buf_tail = (tail + n) % size
        return bytes(out)

    def _buf_get_until(self, pattern, max_size=None):
        avail = (self._buf_head - self._buf_tail) % self._bufsize
        max_search = min(avail, max_size) if max_size else avail
        pattern_len = len(pattern)
        if max_search < pattern_len:
            return None
        buf = self._buf
        buf_size = self._bufsize
        pos = self._buf_tail
        matches = 0
        start_pos = -1
        i = 0
        while i < max_search:
            current_byte = buf[pos]
            if current_byte == pattern[matches]:
                if matches == 0:
                    start_pos = i
                matches += 1
                if matches == pattern_len:
                    return self._buf_get(start_pos + pattern_len)
            else:
                if matches > 0:
                    matches = 0
                    if current_byte == pattern[0]:
                        matches = 1
                        start_pos = i
            pos = (pos + 1) % buf_size
            i += 1
        return None

    def _wait(self, t0, budget_ms):
        # Pump until data is buffered or the deadline passes.
        while True:
            self._pump()
            if self._buf_avail():
                return
            if budget_ms is not None and utime.ticks_diff(utime.ticks_ms(), t0) >= budget_ms:
                return
            utime.sleep_ms(1)

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def in_waiting(self):
        self._pump()
        return self._buf_avail()

    def read(self, size=1):
        if size <= 0:
            return b''
        budget = None if self._timeout is None else int(self._timeout * 1000)
        self._wait(utime.ticks_ms(), budget)
        return self._buf_get(size)

    def read_until(self, expected=b'\r', max_size=None):
        if self._timeout == 0:
            self._pump()
            if max_size and self._buf_avail() >= max_size:
                return self._buf_get(max_size)
            data = self._buf_get_until(expected, max_size)
            return data or b''

        t0 = utime.ticks_ms()
        budget = None if self._timeout is None else int(self._timeout * 1000)

        while True:
            self._pump()
            if max_size and self._buf_avail() >= max_size:
                return self._buf_get(max_size)
            data = self._buf_get_until(expected, max_size)
            if data is not None:
                return data
            if budget is not None and utime.ticks_diff(utime.ticks_ms(), t0) >= budget:
                return b''
            utime.sleep_ms(1)

    def write(self, data):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        _stdout.write(data)

    def close(self):
        del self._buf

gc.collect()

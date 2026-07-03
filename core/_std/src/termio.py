# @package: termio
# @version: 1.5.0
# @type: core
# @category: utility
# @interface: std_io
# @depends: none
# @platforms: *
# @tags: terminal, input, keyboard, serial, repl, stdin
# @author: PlanXLab Development Team

import sys
import micropython
import machine
import time
import select

_stdin = sys.stdin.buffer
_stdout = sys.stdout

def _poll_ready(poll_obj, timeout_ms: int = 0) -> bool:
    result = poll_obj.poll(timeout_ms)
    return len(result) > 0

@micropython.native
def _char_width(ch: str) -> int:
    return 1 if ord(ch) < 0x80 else 2

class KeyReader:
    class Key:
        ESC = 'ESC'
        UP = 'UP'
        DOWN = 'DOWN'
        LEFT = 'LEFT'
        RIGHT = 'RIGHT'
        TAB = 'TAB'
        ENTER = 'ENTER'
        SPACE = 'SPACE'
        BACKSPACE = 'BACKSPACE'
        UNKNOWN = 'UNKNOWN'

    # ESC sequence mapping table
    _ESC_SEQUENCES = {
        # Arrow keys
        b'[A': Key.UP,
        b'[B': Key.DOWN,
        b'[C': Key.RIGHT,
        b'[D': Key.LEFT,
    }

    # Special single-byte keys
    _SPECIAL_KEYS = {
        0x09: Key.TAB,
        0x0D: Key.ENTER,
        0x0A: Key.ENTER,
        0x20: Key.SPACE,
        0x08: Key.BACKSPACE,
        0x7F: Key.BACKSPACE,
    }

    def __init__(self, esc_timeout_ms: int = 50):
        self._esc_timeout = esc_timeout_ms
        self._poll = None

    def _decode_escape_sequence(self, seq: bytes) -> str:
        k = self._ESC_SEQUENCES.get(seq)
        if k is not None:
            return k

        if not seq:
            return self.Key.UNKNOWN

        if seq[:1] == b'[':
            last = seq[-1:]
            if last == b'A':
                return self.Key.UP
            if last == b'B':
                return self.Key.DOWN
            if last == b'C':
                return self.Key.RIGHT
            if last == b'D':
                return self.Key.LEFT

        return self.Key.UNKNOWN

    def _read_escape_sequence(self, timeout_ms: int = 50) -> str:
        # Wait briefly for potential sequence
        if not _poll_ready(self._poll, timeout_ms):
            return self.Key.ESC

        seq = bytearray()
        max_seq_len = 16  # Maximum ESC sequence length (incl. modifiers)

        while len(seq) < max_seq_len:
            if not _poll_ready(self._poll, 10):
                break
            b = _stdin.read(1)
            if not b:
                break
            seq.extend(b)

            # Complete sequence match
            k = self._ESC_SEQUENCES.get(bytes(seq))
            if k is not None:
                return k

            # Tilde-terminated sequences
            if b == b'~':
                break

        return self._decode_escape_sequence(bytes(seq))
    
    def __enter__(self) -> "KeyReader":
        self._poll = select.poll()
        self._poll.register(_stdin, select.POLLIN)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._poll is not None:
            try:
                self._poll.unregister(_stdin)
            except:
                pass
            self._poll = None

    def _ensure_initialized(self) -> None:
        if self._poll is None:
            raise RuntimeError("KeyReader must be used within a 'with' statement")

    @property
    def key(self) -> str | None:
        self._ensure_initialized()
        
        if not _poll_ready(self._poll, 0):
            return None
        
        b = _stdin.read(1)
        if not b:
            return None
        
        byte = b[0]
        
        # ESC - could be standalone or start of sequence
        if byte == 0x1B:
            return self._read_escape_sequence(self._esc_timeout)
        
        # Special single-byte keys
        if byte in self._SPECIAL_KEYS:
            return self._SPECIAL_KEYS[byte]
        
        # Regular ASCII character
        if byte < 0x80:
            return chr(byte)
        
        # UTF-8 multi-byte character
        if (byte & 0xE0) == 0xC0:
            seq = b + _stdin.read(1)
        elif (byte & 0xF0) == 0xE0:
            seq = b + _stdin.read(2)
        elif (byte & 0xF8) == 0xF0:
            seq = b + _stdin.read(3)
        else:
            return None
        
        try:
            return seq.decode('utf-8')
        except UnicodeError:
            return None

    def wait_key(self, timeout_ms: int = 0) -> str | None:
        self._ensure_initialized()
        
        if timeout_ms == 0:
            while True:
                if _poll_ready(self._poll, 100):
                    k = self.key
                    if k is not None:
                        return k
        else:
            start = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
                remaining = timeout_ms - time.ticks_diff(time.ticks_ms(), start)
                if remaining <= 0:
                    break
                if _poll_ready(self._poll, min(remaining, 100)):
                    k = self.key
                    if k is not None:
                        return k
            return None


def input(prompt: str = "", mask: str | None = None) -> str:
    repl_in = _stdin
    repl_out = _stdout

    mask_bytes = None
    mask_width = 0
    if mask is not None:
        if not isinstance(mask, str) or len(mask) != 1:
            raise ValueError("mask must be a single character string")
        mask_bytes = mask.encode('utf-8')
        mask_width = _char_width(mask)

    def _w(ch: str) -> int:
        return mask_width if mask_bytes is not None else _char_width(ch)

    def _tail_text(chars) -> str:
        return (mask * len(chars)) if mask_bytes is not None else ''.join(chars)
    
    poll = select.poll()
    poll.register(repl_in, select.POLLIN)
    
    if prompt:
        repl_out.write(prompt.encode('utf-8'))

    buf = []
    pos = 0
    push = None
    
    try:
        while True:
            if push is not None:
                b = push
                push = None
            else:
                poll.poll(-1)
                b = repl_in.read(1)
                if not b:
                    continue
            
            byte = b[0]

            # ENTER - finish input
            if byte in (0x0D, 0x0A):
                repl_out.write(b"\n")
                # Consume any remaining ENTER bytes
                while _poll_ready(poll, 0):
                    nxt = repl_in.read(1)
                    if not nxt:
                        continue
                    if nxt[0] in (0x0D, 0x0A):
                        continue
                    push = nxt
                    break
                break

            # ESC sequence
            if byte == 0x1B:
                if not _poll_ready(poll, 50):
                    continue
                seq = repl_in.read(1)
                if not seq:
                    continue
                
                if seq[0] == 0x5B:  # [
                    cmd = repl_in.read(1)
                    if not cmd:
                        continue
                    
                    cmd_byte = cmd[0]
                    
                    # LEFT
                    if cmd_byte == 0x44:
                        if pos > 0:
                            w = _w(buf[pos - 1])
                            repl_out.write(f"\x1b[{w}D".encode())
                            pos -= 1
                    # RIGHT
                    elif cmd_byte == 0x43:
                        if pos < len(buf):
                            w = _w(buf[pos])
                            repl_out.write(f"\x1b[{w}C".encode())
                            pos += 1
                    # UP (ignored - could add history)
                    elif cmd_byte == 0x41:
                        pass
                    # DOWN (ignored - could add history)
                    elif cmd_byte == 0x42:
                        pass
                    # HOME
                    elif cmd_byte == 0x48:
                        if pos > 0:
                            total_w = (mask_width * pos) if mask_bytes is not None else sum(_char_width(c) for c in buf[:pos])
                            repl_out.write(f"\x1b[{total_w}D".encode())
                            pos = 0
                    # END
                    elif cmd_byte == 0x46:
                        if pos < len(buf):
                            total_w = (mask_width * (len(buf) - pos)) if mask_bytes is not None else sum(_char_width(c) for c in buf[pos:])
                            repl_out.write(f"\x1b[{total_w}C".encode())
                            pos = len(buf)
                    # Insert (0x32) or Delete (0x33)
                    elif cmd_byte in (0x32, 0x33):
                        tilde = repl_in.read(1)
                        if tilde and tilde[0] == 0x7E:
                            # DELETE
                            if cmd_byte == 0x33 and pos < len(buf):
                                buf.pop(pos)
                                repl_out.write(b"\x1b[K")
                                tail_chars = buf[pos:]
                                tail = _tail_text(tail_chars)
                                if tail:
                                    repl_out.write(tail.encode('utf-8'))
                                    ws = (mask_width * len(tail_chars)) if mask_bytes is not None else sum(_char_width(c) for c in tail)
                                    repl_out.write(f"\x1b[{ws}D".encode())
                continue

            # BACKSPACE
            if byte in (0x08, 0x7F) and pos > 0:
                pos -= 1
                removed = buf.pop(pos)
                w = _w(removed)
                repl_out.write(f"\x1b[{w}D".encode())
                repl_out.write(b"\x1b[K")
                tail_chars = buf[pos:]
                tail = _tail_text(tail_chars)
                if tail:
                    repl_out.write(tail.encode('utf-8'))
                    ws = (mask_width * len(tail_chars)) if mask_bytes is not None else sum(_char_width(c) for c in tail)
                    repl_out.write(f"\x1b[{ws}D".encode())
                continue

            # Regular character or UTF-8
            first = byte
            if first < 0x80:
                seq = b
            elif (first & 0xE0) == 0xC0:
                seq = b + repl_in.read(1)
            elif (first & 0xF0) == 0xE0:
                seq = b + repl_in.read(2)
            elif (first & 0xF8) == 0xF0:
                seq = b + repl_in.read(3)
            else:
                continue

            try:
                ch = seq.decode('utf-8')
            except UnicodeError:
                continue

            buf.insert(pos, ch)
            tail_chars = buf[pos + 1:]
            tail = _tail_text(tail_chars)

            if mask_bytes is not None:
                repl_out.write(mask_bytes)
            else:
                repl_out.write(seq)

            if tail:
                repl_out.write(tail.encode('utf-8'))
                ws = (mask_width * len(tail_chars)) if mask_bytes is not None else sum(_char_width(c) for c in tail)
                repl_out.write(f"\x1b[{ws}D".encode())
            pos += 1

    finally:
        poll.unregister(repl_in)

    return ''.join(buf)


class ReplSerial:
    def __init__(self, timeout: float | None = None, *, bufsize: int = 512, poll_ms: int = 10):
        self._timeout = timeout
        self._stdin = _stdin
        self._stdout = sys.stdout.buffer
        self._buf = bytearray(bufsize)
        self._bufsize = bufsize
        self._buf_head = 0
        self._buf_tail = 0
        self._scheduled = False
        self._poll_ms = poll_ms
        self._poll = select.poll()
        self._poll.register(self._stdin, select.POLLIN)
        self._tmr = machine.Timer(-1)
        self._pump_cb = self._pump
        self._tmr.init(period=poll_ms, mode=machine.Timer.PERIODIC, callback=self._tick)

    def __enter__(self) -> "ReplSerial":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @micropython.native
    def _buf_put(self, data: bytes) -> None:
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

    @micropython.native
    def _buf_avail(self) -> int:
        return (self._buf_head - self._buf_tail) % self._bufsize

    @micropython.native
    def _buf_get(self, n: int = 1) -> bytes:
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

    def _buf_get_until(self, pattern: bytes, max_size: int | None = None) -> bytes | None:
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

    def _tick(self, t):
        if not self._scheduled:
            self._scheduled = True
            try:
                micropython.schedule(self._pump_cb, None)
            except RuntimeError:
                self._scheduled = False
            except KeyboardInterrupt:
                self._scheduled = False

    def _pump(self, _):
        try:
            while self._poll.poll(0):
                b = self._stdin.read(1)
                if not b:
                    break
                self._buf_put(b)
        except Exception:
            pass
        finally:
            self._scheduled = False

    def _wait(self, deadline_ms: int | None):
        while not self._buf_avail():
            if deadline_ms is not None and time.ticks_diff(deadline_ms, time.ticks_ms()) <= 0:
                return
            if deadline_ms is None:
                self._poll.poll(self._poll_ms)
            else:
                dur = max(0, time.ticks_diff(deadline_ms, time.ticks_ms()))
                self._poll.poll(min(dur, self._poll_ms))

    @property
    def timeout(self) -> float | None:
        return self._timeout

    @timeout.setter
    def timeout(self, value: float | None):
        self._timeout = value

    @property
    def in_waiting(self) -> int:
        return self._buf_avail()

    def read(self, size: int = 1) -> bytes:
        if size <= 0:
            return b''
        deadline = None if self._timeout is None else time.ticks_add(
            time.ticks_ms(), int(self._timeout * 1000)
        )
        self._wait(deadline)
        return self._buf_get(size)

    def read_until(self, expected: bytes = b'\r', max_size: int | None = None) -> bytes:
        if self._timeout == 0:
            if max_size and self._buf_avail() >= max_size:
                return self._buf_get(max_size)
            data = self._buf_get_until(expected, max_size)
            return data or b''

        deadline = None
        if self._timeout is not None:
            deadline = time.ticks_add(time.ticks_ms(), int(self._timeout * 1000))

        while True:
            if max_size and self._buf_avail() >= max_size:
                return self._buf_get(max_size)
            data = self._buf_get_until(expected, max_size)
            if data is not None:
                return data
            if deadline is not None:
                if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                    return b''
            self._wait(deadline)

    def write(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        self._stdout.write(data)

    def close(self):
        self._tmr.deinit()
        try:
            self._poll.unregister(self._stdin)
        except:
            pass

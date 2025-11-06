import usys
import utime
import uselect
import micropython
import machine
from ringbuffer import RingBuffer

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


def input(prompt:str="") -> str:
    @micropython.native
    def __char_width(ch: str) -> int:
        return 1 if len(ch.encode('utf-8')) == 1 else 2

    repl_in = usys.stdin.buffer
    repl_out = usys.stdout
    
    BACKSPACE = (0x08, 0x7F)
    ENTER = (0x0D, 0x0A)
        
    if prompt:
        repl_out.write(prompt.encode('utf-8'))

    buf = []
    pos = 0
    push = None
    
    while True:
        if push is not None:
            b = push
            push = None
        else:
            while not uselect.select([repl_in], [], [], 0)[0]:
                pass
            b = repl_in.read(1)
            if not b:
                continue
        byte = b[0]

        if byte in ENTER:
            repl_out.write(b"\n")
            while uselect.select([repl_in], [], [], 0)[0]:
                nxt = repl_in.read(1)
                if not nxt:
                    continue
                if nxt[0] in ENTER:
                    continue
                push = nxt
                break
            break

        if byte == 0x1B:
            seq = repl_in.read(1)
            if not seq:
                continue
            
            if seq[0] == 0x5B:
                cmd = repl_in.read(1)
                if not cmd:
                    continue
                
                cmd_byte = cmd[0]
                
                if cmd_byte == 0x44:
                    if pos > 0:
                        w = __char_width(buf[pos-1])
                        repl_out.write(f"\x1b[{w}D".encode())
                        pos -= 1
                elif cmd_byte == 0x43:
                    if pos < len(buf):
                        w = __char_width(buf[pos])
                        repl_out.write(f"\x1b[{w}C".encode())
                        pos += 1
                elif cmd_byte == 0x41:
                    pass
                elif cmd_byte == 0x42:
                    pass
                elif cmd_byte == 0x48:
                    if pos > 0:
                        total_w = sum(__char_width(c) for c in buf[:pos])
                        repl_out.write(f"\x1b[{total_w}D".encode())
                        pos = 0
                elif cmd_byte == 0x46:
                    if pos < len(buf):
                        total_w = sum(__char_width(c) for c in buf[pos:])
                        repl_out.write(f"\x1b[{total_w}C".encode())
                        pos = len(buf)
                elif cmd_byte in (0x32, 0x33):
                    tilde = repl_in.read(1)
                    if tilde and tilde[0] == 0x7E:
                        if cmd_byte == 0x33 and pos < len(buf):
                            removed = buf.pop(pos)
                            repl_out.write(b"\x1b[K")
                            tail = ''.join(buf[pos:])
                            if tail:
                                repl_out.write(tail.encode('utf-8'))
                                ws = sum(__char_width(c) for c in tail)
                                repl_out.write(f"\x1b[{ws}D".encode())
            continue

        if byte in BACKSPACE and pos > 0:
            pos -= 1
            removed = buf.pop(pos)
            w = __char_width(removed)
            repl_out.write(f"\x1b[{w}D".encode())
            repl_out.write(b"\x1b[K")
            tail = ''.join(buf[pos:])
            if tail:
                repl_out.write(tail.encode('utf-8'))
                ws = sum(__char_width(c) for c in tail)
                repl_out.write(f"\x1b[{ws}D".encode())
            continue

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
        w = __char_width(ch)
        tail = ''.join(buf[pos+1:])

        repl_out.write(seq)
        if tail:
            repl_out.write(tail.encode('utf-8'))
            ws = sum(__char_width(c) for c in tail)
            repl_out.write(f"\x1b[{ws}D".encode())
        pos += 1

    return ''.join(buf)


class ReplSerial:
    def __init__(self, timeout:float|None=None, *, bufsize:int=512, poll_ms:int=10):
        self._timeout   = timeout
        self._stdin     = usys.stdin.buffer
        self._stdout    = usys.stdout
        self._buf       = RingBuffer(bufsize)
        self._scheduled = False
        self._tmr = machine.Timer(-1)
        self._tmr.init(period=poll_ms, mode=machine.Timer.PERIODIC, callback=self.__tick)

    def __tick(self, t):
        if not self._scheduled:
            self._scheduled = True
            try:
                micropython.schedule(self.__pump, None)
            except RuntimeError:
                self._scheduled = False

    def __pump(self, _):
        try:
            while uselect.select([self._stdin], [], [], 0)[0]:
                b = self._stdin.read(1)
                if not b:
                    break
                self._buf.put(b)
        except Exception:
            pass
        finally:
            self._scheduled = False

    def __wait(self, deadline_ms:int):
        while not self._buf.avail():
            if deadline_ms is not None and utime.ticks_diff(deadline_ms, utime.ticks_ms()) <= 0:
                return
            dur = None if deadline_ms is None else max(0,
                utime.ticks_diff(deadline_ms, utime.ticks_ms())) / 1000
            uselect.select([self._stdin], [], [], dur)

    @property
    def timeout(self) -> float|None:
        return self._timeout
    
    @timeout.setter
    def timeout(self, value:float|None):
        self._timeout = value

    def read(self, size:int=1) -> bytes:
        if size <= 0:
            return b''
        dl = None if self._timeout is None else utime.ticks_add(utime.ticks_ms(), int(self._timeout*1000))
        self.__wait(dl)
        return self._buf.get(size)

    def read_until(self, expected:bytes=b'\r', max_size:int|None=None) -> bytes:
        if self._timeout == 0:
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)
            
            data = self._buf.get_until(expected, max_size)
            return data or b''

        deadline = None
        if self._timeout is not None:
            deadline = utime.ticks_add(utime.ticks_ms(), int(self._timeout * 1000))

        while True:
            if max_size and self._buf.avail() >= max_size:
                return self._buf.get(max_size)

            data = self._buf.get_until(expected, max_size)
            if data is not None:
                return data

            if deadline is not None:
                if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
                    return b''

            self.__wait(deadline)

    def write(self, data:bytes) -> int:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes or bytearray")
        return self._stdout.write(data)

    def close(self):
        self._tmr.deinit()

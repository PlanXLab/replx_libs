# @package: xnode.diag
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: UART, I2C
# @depends: termviz
# @platforms: xbee
# @tags: diagnostics, repl, i2cdetect, xbee

import gc
import uos
import usys
import utime
import machine
import xbee

def get_sys_info():
    freq = 40000000  # Default frequency of EFR32MG
    temp = xbee.atcmd('TP')
    return freq, temp

def get_mem_info():
    gc.collect()
    free = gc.mem_free()
    used = gc.mem_alloc()
    return free, used, free + used

def get_fs_info(path='/'):
    stats = uos.statvfs(path)
    block_size = stats[0]
    total = block_size * stats[2]
    free = block_size * stats[3]
    used = total - free
    usage_pct = round(used / total * 100, 2) if total else 0.0
    return total, used, free, usage_pct

def i2cdetect(show=False):
    i2c = machine.I2C(1)
    devices = i2c.scan()
    if not show:
        return devices

    from termviz import Term
    print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
    dev_set = set(devices)
    for i in range(8):
        base = i << 4
        print("{:02x}:".format(base), end='')
        for j in range(16):
            addr = base + j
            if addr in dev_set:
                print(Term.FG.BRIGHT_YELLOW + " {:02x}".format(addr) + Term.RESET, end='')
            else:
                print(" --", end='')
        print()

class ReplSerial:
    def __init__(self, timeout=None):
        self._timeout = timeout

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, n):
        self._timeout = n

    def read(self, size=1):
        if self._timeout is None:
            if size <= 0:
                raise ValueError("size must be > 0")
            return usys.stdin.buffer.read(size)
        if self._timeout == 0:
            res = usys.stdin.buffer.read(-1)
            return res if res else b''

        rx_buf = bytearray()
        timeout_ms = int(self._timeout * 1000)
        t0 = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), t0) < timeout_ms:
            b = usys.stdin.buffer.read(-1)
            if b:
                rx_buf.extend(b)
                if len(rx_buf) >= size:
                    return bytes(rx_buf[:size])
            utime.sleep_ms(1)
        return bytes(rx_buf)

    def read_until(self, expected=b'\n', size=None):
        rx_buf = bytearray()
        exp_len = len(expected)
        timeout_ms = int(self._timeout * 1000) if (self._timeout is not None and self._timeout > 0) else None
        t0 = utime.ticks_ms() if timeout_ms is not None else None

        while True:
            if t0 is not None and utime.ticks_diff(utime.ticks_ms(), t0) >= timeout_ms:
                break
            try:
                b = usys.stdin.buffer.read(-1)
                if self._timeout == 0:
                    return b if b else b''
            except Exception:
                return bytes(rx_buf)

            if not b:
                utime.sleep_ms(1)
                continue

            for byte in b:
                rx_buf.append(byte)
                if size is not None and len(rx_buf) >= size:
                    return bytes(rx_buf)
                if len(rx_buf) >= exp_len and rx_buf[-exp_len:] == expected:
                    return bytes(rx_buf)

        return bytes(rx_buf)

    def readline(self, size=None):
        return self.read_until(b'\n', size=size)

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("data must be bytes-like or str")
        return usys.stdout.write(data)

gc.collect()

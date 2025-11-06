import sys
import uselect

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class KeyReader():
    ESC = b'\x1b'
    EXT_CODE_TBL = {b'[A': b'UP', b'[B': b'DOWN', b'[C': b'RIGHT', b'[D': b'LEFT', b'\t': b'TAB', b'\r': b'ENTER', b' ': b'SPACE'}
    
    def __enter__(self):
        self.poller = uselect.poll()
        self.poller.register(sys.stdin.buffer, uselect.POLLIN)
        return self

    def __exit__(self, type, value, traceback):
        self.poller.unregister(sys.stdin.buffer)

    @property
    def ch(self):
        if self.poller.poll(0):
            b = sys.stdin.buffer.read(1)
            
            if b == self.ESC:
                b = b'ESC'
                if self.poller.poll(0):
                    b = sys.stdin.buffer.read(2)
                    b = self.EXT_CODE_TBL.get(b, b'UNKNOWN')
            else:
                b = self.EXT_CODE_TBL.get(b, b)

            return b.decode()

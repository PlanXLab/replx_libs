__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

import micropython


@micropython.native
def _slip_encode_core(payload, payload_len, out_buf) -> int:
    i: int = 0
    j: int = 1  # Skip first END byte
    
    while i < payload_len:
        b: int = payload[i]
        if b == 0xC0:  # END
            out_buf[j] = 0xDB  # ESC
            out_buf[j + 1] = 0xDC  # ESC_END
            j += 2
        elif b == 0xDB:  # ESC
            out_buf[j] = 0xDB  # ESC
            out_buf[j + 1] = 0xDD  # ESC_ESC
            j += 2
        else:
            out_buf[j] = b
            j += 1
        i += 1
    
    return j

class SlipEncoder:
    END      = 0xC0
    ESC      = 0xDB
    ESC_END  = 0xDC
    ESC_ESC  = 0xDD

    @staticmethod
    def encode(payload: bytes) -> bytes:
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("Payload must be bytes or bytearray")
        
        max_size = len(payload) * 2 + 2  # 2x for worst case + 2 END bytes
        out_buf = bytearray(max_size)
        
        out_buf[0] = 0xC0
        
        if isinstance(payload, bytes):
            payload_array = bytearray(payload)
        else:
            payload_array = payload
            
        actual_len = _slip_encode_core(payload_array, len(payload_array), out_buf)
        
        out_buf[actual_len] = 0xC0
        
        return bytes(out_buf[:actual_len + 1])


class SlipDecoder:
    END      = 0xC0
    ESC      = 0xDB
    ESC_END  = 0xDC
    ESC_ESC  = 0xDD

    def __init__(self) -> None:
        self._buf = bytearray()
        self._escaped = False
        self._in_frame = False

    def reset(self) -> None:
        self._buf[:] = b''
        self._escaped = False
        self._in_frame = False

    def feed(self, chunk: bytes) -> list[bytes]:
        if not isinstance(chunk, (bytes, bytearray)):
            raise TypeError("Chunk must be bytes or bytearray")
            
        frames = []
        for b in chunk:
            if self._escaped:
                if b == self.ESC_END:
                    self._buf.append(self.END)
                elif b == self.ESC_ESC:
                    self._buf.append(self.ESC)
                else:          # invalid escape
                    self.reset()
                    continue
                self._escaped = False
                continue

            if b == self.ESC:
                self._escaped = True
            elif b == self.END:
                if self._in_frame:
                    # END frame 
                    frames.append(bytes(self._buf))
                    self._buf[:] = b''
                    self._in_frame = False
                else:
                    # junk end. start frame
                    self._in_frame = True
            else:
                if self._in_frame:
                    self._buf.append(b)
                # else: junk, byte invalid
        return frames

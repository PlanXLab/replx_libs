import micropython

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


#@micropython.native
def _ring_buffer_find_pattern(buf, buf_size, head, tail, pattern, pattern_len, max_search):
    available: int = (head - tail) % buf_size
    search_len: int = min(available, max_search)
    
    if search_len < pattern_len:
        return -1
    
    pos: int = tail
    matches: int = 0
    start_pos: int = -1
    
    i: int = 0
    while i < search_len:
        current_byte: int = buf[pos]
        
        if current_byte == pattern[matches]:
            if matches == 0:
                start_pos = i
            matches += 1
            if matches == pattern_len:
                return start_pos
        else:
            if matches > 0:
                matches = 0
                if current_byte == pattern[0]:
                    matches = 1
                    start_pos = i
        
        pos = (pos + 1) % buf_size
        i += 1
    
    return -1

class RingBuffer:
    def __init__(self, size: int) -> None:
        if not isinstance(size, int):
            raise TypeError("Size must be an integer")
        if size < 2:
            raise ValueError("Buffer size must be at least 2 bytes")
            
        self._buf = bytearray(size)
        self._size = size
        self._head = 0
        self._tail = 0
    
    @micropython.native
    def put(self, data: bytes) -> None:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Data must be bytes or bytearray")
            
        for b in data:
            nxt = (self._head + 1) % self._size
            if nxt == self._tail:
                self._tail = (self._tail + 1) % self._size
            self._buf[self._head] = b
            self._head = nxt

    @micropython.native
    def avail(self) -> int:
        return (self._head - self._tail) % self._size

    @micropython.native
    def get(self, n: int = 1) -> bytes:
        if not isinstance(n, int):
            raise TypeError("n must be an integer")
        if n < 1:
            raise ValueError("n must be at least 1")
            
        n = min(n, self.avail())
        if n == 0:
            return b''
            
        out = self._buf[self._tail:self._tail + n] \
            if self._tail + n <= self._size else \
            self._buf[self._tail:] + self._buf[:(self._tail+n)%self._size]
        self._tail = (self._tail + n) % self._size
        return bytes(out)
    
    @micropython.native
    def peek(self, n: int = 1) -> bytes:
        if not isinstance(n, int):
            raise TypeError("n must be an integer")
        if n < 1:
            raise ValueError("n must be at least 1")
            
        n = min(n, self.avail())
        if n == 0:
            return b''

        if self._tail + n <= self._size:
            return bytes(self._buf[self._tail:self._tail + n])

        part1 = self._buf[self._tail:]
        part2 = self._buf[:(self._tail + n) % self._size]
        return bytes(part1 + part2)
    
    def get_until(self, pattern: bytes, max_size: int | None = None) -> bytes | None:
        if not isinstance(pattern, (bytes, bytearray)):
            raise TypeError("Pattern must be bytes or bytearray")
        if len(pattern) == 0:
            raise ValueError("Pattern cannot be empty")
        
        max_search = min(self.avail(), max_size) if max_size else self.avail()
        
        if max_search < len(pattern):
            return None

        pattern_start = _ring_buffer_find_pattern(self._buf, self._size, self._head, self._tail, pattern, len(pattern), max_search)
        
        if pattern_start == -1:
            return None
        
        length = pattern_start + len(pattern)
        return self.get(length)

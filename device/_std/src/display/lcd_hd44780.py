# @package: lcd_hd44780
# @version: 1.0.0
# @type: device-std
# @category: display
# @interface: I2C
# @depends: i2c
# @platforms: *
# @tags: lcd, display, hd44780, pcf8574, i2c, text, graphics
# @author: PlanXLab Development Team

import time
import micropython
from micropython import const
from i2c import I2CController

_RS = const(0x01)
_EN = const(0x04)
_BL = const(0x08)

_CMD_CLEAR            = const(0x01)
_CMD_HOME             = const(0x02)
_CMD_ENTRY_MODE       = const(0x04)
_ENTRY_INC            = const(0x02)
_ENTRY_SHIFT          = const(0x01)

_CMD_DISPLAY_CTRL     = const(0x08)
_DISP_ON              = const(0x04)
_CURSOR_ON            = const(0x02)
_BLINK_ON             = const(0x01)

_CMD_CURSOR_SHIFT     = const(0x10)
_SHIFT_DISPLAY        = const(0x08)
_SHIFT_RIGHT          = const(0x04)

_CMD_FUNCTION_SET     = const(0x20)
_DATA_8BIT            = const(0x10)
_LINES_2              = const(0x08)
_DOTS_5x10            = const(0x04)

_CMD_SET_CGRAM        = const(0x40)
_CMD_SET_DDRAM        = const(0x80)

_QUEUE_CAP            = const(256)
_INIT_DELAY_US        = const(20000)
_INIT_PULSE_DELAY_US  = const(5000)
_INIT_4BIT_DELAY_US   = const(1000)
_CLEAR_HOME_DELAY_US  = const(1600)

_ROW_ADDR = (0x00, 0x40, 0x14, 0x54)


class HD44780:
    MODE_TEXT = 0
    MODE_GFX  = 1

    def __init__(self, sda: int, scl: int, *, addr: int = 0x27, id: int = 0, freq: int = 400_000,
                 cols: int = 16, rows: int = 2,
                 backlight_on: bool = True, bl_active_high: bool = True, bl_mask: int = _BL):

        self._i2c = I2CController(sda=sda, scl=scl, id=id, freq=freq)
        self._addr = addr  # PCF8574 I2C address

        self._cols = int(cols)
        self._rows = int(rows)
        self._display = True
        self._cursor = False
        self._blink = False
        self._x = self._y = 0

        self._ddram_width = 40
        self._view_off_y = [0] * self._rows
        SPACE = 0x20
        self._shadow_rows = [bytearray([SPACE] * self._ddram_width) for _ in range(self._rows)]

        self._bl_mask = int(bl_mask) & 0xFF
        self._bl_active_high = bool(bl_active_high)
        self._bl_on = bool(backlight_on)

        self._bar_row_mask = 0xFF
        self._bar_cfg = None
        self._gw = self._cols * 5
        self._gh = self._rows * 8
        self._gfb = None  # Lazy init on first graphics mode use
        self._cb_slots = [None] * 8
        self._cb_map = {}

        self._q = bytearray(_QUEUE_CAP)
        self._qv = memoryview(self._q)
        self._qlen = 0
        self._batch_depth = 0
        self._latch_buf = bytearray(1)  # Reusable buffer for _latch

        base = self._ctl_base()
        self._latch(base)
        time.sleep_ms(10)

        time.sleep_us(_INIT_DELAY_US)
        for _ in range(3):
            self._pulse_raw(base | 0x30, immediate=True)
            time.sleep_us(_INIT_PULSE_DELAY_US)
        self._pulse_raw(base | 0x20, immediate=True)
        time.sleep_us(_INIT_4BIT_DELAY_US)

        self._cmd(_CMD_FUNCTION_SET | (_LINES_2 if self._rows > 1 else 0))
        self.set_display(False)
        self.clear()
        self._cmd(_CMD_ENTRY_MODE | _ENTRY_INC)
        self.set_display(True, cursor=False, blink=False)
        self._mode = self.MODE_TEXT

    def begin_batch(self):
        self._batch_depth += 1

    def end_batch(self):
        if self._batch_depth > 0:
            self._batch_depth -= 1
            if self._batch_depth == 0:
                self._flush()

    class _BatchCtx:
        def __init__(self, lcd): 
            self.lcd = lcd
        
        def __enter__(self): 
            self.lcd.begin_batch() 
            return self.lcd
        
        def __exit__(self, exc_type, exc, tb): 
            self.lcd.end_batch()

    def batch(self):
        return self._BatchCtx(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.deinit()
        except:
            pass
        return False

    def flush(self):
        self._flush()

    def _flush(self):
        if self._qlen:
            self._i2c.writeto(self._addr, self._qv[:self._qlen])
            self._qlen = 0

    @micropython.native
    def _q_byte(self, b:int):
        i = self._qlen
        if i >= _QUEUE_CAP:
            self._flush()
            i = 0
            
        self._q[i] = b & 0xFF
        self._qlen = i + 1

    def _ctl_base(self) -> int:
        if self._bl_on:
            return self._bl_mask if self._bl_active_high else 0x00
        else:
            return 0x00 if self._bl_active_high else self._bl_mask

    def _latch(self, v:int):
        self._latch_buf[0] = v & 0xFF
        self._i2c.writeto(self._addr, self._latch_buf)

    def _pulse_raw(self, v:int, *, immediate:bool=False):
        b_on  = (v | _EN) & 0xFF
        b_off = (v & ~_EN) & 0xFF
        if immediate and self._batch_depth == 0:
            self._i2c.writeto(self._addr, bytes([b_on, b_off]))
        else:
            self._q_byte(b_on)
            self._q_byte(b_off)

    @micropython.native
    def _render_row(self, vy:int):
        ddram_width = self._ddram_width
        start = self._view_off_y[vy] % ddram_width
        buf = self._shadow_rows[vy]
        cols = self._cols

        self.begin_batch()
        self._cmd(_CMD_SET_DDRAM | (_ROW_ADDR[vy]))
        for i in range(cols):
            self._data(buf[(start + i) % ddram_width])
        self.end_batch()

    def _render_all(self):
        for vy in range(self._rows):
            self._render_row(vy)

        if self._cursor and self._display:
            self._sync_hw_cursor()

    @micropython.native
    def _write(self, data:int, rs:int):
        base = self._ctl_base() | (_RS if (rs & 1) else 0)
        self._pulse_raw(base | (data & 0xF0))
        self._pulse_raw(base | ((data << 4) & 0xF0))

        if rs == 0 and (data == _CMD_CLEAR or data == _CMD_HOME):
            self._flush()
            time.sleep_us(_CLEAR_HOME_DELAY_US)
        else:
            if self._batch_depth == 0:
                self._flush()

    def _cmd(self, c: int):
        self._write(c & 0xFF, 0)

    def _data(self, d: int):
        self._write(d & 0xFF, 0x01)

    def _sync_hw_cursor(self):
        vx = 0 if self._x < 0 else (self._cols-1 if self._x >= self._cols else self._x)
        vy = 0 if self._y < 0 else (self._rows-1 if self._y >= self._rows else self._y)
        self._cmd(_CMD_SET_DDRAM | (_ROW_ADDR[vy] + vx))

    def backlight(self, on:bool=True):
        self._bl_on = bool(on)
        self._latch(self._ctl_base())

    def deinit(self):
        try:
            self.set_display(on=False, cursor=False, blink=False)
            self.clear()
        except:
            pass

    def __len__(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, n):
        if n == self.MODE_GFX and self._gfb is None:
            self._gfb = bytearray(self._gw * self._gh)
        self._mode = n

    def _ensure_gfb(self):
        """Ensure graphics framebuffer is allocated."""
        if self._gfb is None:
            self._gfb = bytearray(self._gw * self._gh)

    def _move_to(self, x:int, y:int):
        self._x = 0 if x < 0 else (self._cols-1 if x >= self._cols else int(x))
        self._y = 0 if y < 0 else (self._rows-1 if y >= self._rows else int(y))
        self._sync_hw_cursor()

    @micropython.native
    def clear(self):
        self._cmd(_CMD_CLEAR)
        self._x = 0
        self._y = 0

        self._view_off_y = [0] * self._rows
        for b in self._shadow_rows:
            b[:] = b' ' * self._ddram_width
        self._render_all()

    def home(self):
        self._cmd(_CMD_HOME)
        self._x = 0
        self._y = 0

    def set_display(self, on: bool|None = None, cursor: bool|None = None, blink: bool|None = None):
        if on is None: 
            on = self._display
        else: 
            self._display = on

        if cursor is None: 
            cursor = self._cursor
        else: 
            self._cursor = cursor

        if blink is None: 
            blink = self._blink
        else: 
            self._blink = blink

        self._cmd(_CMD_DISPLAY_CTRL | (_DISP_ON if on else 0) | (_CURSOR_ON if cursor else 0) | (_BLINK_ON if blink else 0))

        if self._cursor and self._display:
            self._sync_hw_cursor()

    @micropython.native
    def text(self, text: str|bytes, x: int|None = None, y: int|None = None, *, wrap: bool = False):
        if isinstance(text, (bytes, bytearray)):
            text = text.decode()

        rows = self._rows
        cols = self._cols
        ddram_width = self._ddram_width
        view_off_y = self._view_off_y
        shadow_rows = self._shadow_rows

        if x is not None and y is not None:
            vy = max(0, min(rows - 1, int(y)))
            vx = max(0, min(cols - 1, int(x)))
        else:
            vy, vx = self._y, self._x

        changed_rows = set()
        vcol = (view_off_y[vy] + vx) % ddram_width
        shadow_limit = ddram_width - vcol

        for ch in str(text):
            if ch == '\n':
                changed_rows.add(vy)
                vy = (vy + 1) % rows
                vx = 0
                vcol = (view_off_y[vy] + vx) % ddram_width
                shadow_limit = ddram_width - vcol
                continue

            oc = ord(ch) & 0xFF

            if shadow_limit > 0:
                shadow_rows[vy][vcol] = oc
                vcol += 1
                shadow_limit -= 1
            else:
                if wrap:
                    changed_rows.add(vy)
                    vy = (vy + 1) % rows
                    vx = 0
                    vcol = (view_off_y[vy] + vx) % ddram_width
                    shadow_limit = ddram_width - vcol
                    continue
                else:
                    break

            if vx < cols - 1:
                vx += 1
            else:
                if wrap:
                    changed_rows.add(vy)
                    vy = (vy + 1) % rows
                    vx = 0
                    vcol = (view_off_y[vy] + vx) % ddram_width
                    shadow_limit = ddram_width - vcol

            changed_rows.add(vy)

        self._x, self._y = vx, vy

        for row in changed_rows:
            self._render_row(row)

        if self._cursor and self._display:
            self._sync_hw_cursor()
            
    def scroll_left(self, n:int=1):
        n = max(1, int(n)) % self._ddram_width
        for vy in range(self._rows):
            self._view_off_y[vy] = (self._view_off_y[vy] + n) % self._ddram_width

        self._render_all()
            
    def scroll_right(self, n:int=1):
        n = max(1, int(n)) % self._ddram_width
        for vy in range(self._rows):
            self._view_off_y[vy] = (self._view_off_y[vy] - n) % self._ddram_width

        self._render_all()

    def create_char(self, slot:int, pattern8):
        slot &= 7
        if len(pattern8) != 8:
            raise ValueError("pattern8 must have 8 rows")
        
        self.begin_batch()
        try:
            self._cmd(_CMD_SET_CGRAM | (slot << 3))
            for v in pattern8:
                self._data(int(v) & 0x1F)
        finally:
            self.end_batch()
        
        self._move_to(self._x, self._y) 

    @property
    def bar_patterns(self) -> int:
        return self._bar_row_mask

    @bar_patterns.setter
    def bar_patterns(self, mask:int):
        self._bar_row_mask = int(mask) & 0xFF
        self._bar_cfg = None

    def _ensure_bar_tiles(self, rtl:bool):
        key = (True if rtl else False, self._bar_row_mask)
        if self._bar_cfg == key:
            return
        
        for seg in range(6):
            px = seg
            if px <= 0:
                colmask = 0x00
            elif px >= 5:
                colmask = 0x1F
            else:
                colmask = ((0x1F << (5 - px)) & 0x1F) if not rtl else (0x1F >> (5 - px))
            
            rows = []
            m = self._bar_row_mask
            for rr in range(8):
                use = (m >> (7 - rr)) & 1
                rows.append(colmask if use else 0)
            
            self.create_char(seg, rows)
        
        self._bar_cfg = key

    def bar(self, row:int, value:int, *, max_value:int=100, start_col:int=0, end_col:int=-1):
        if self._mode == self.MODE_GFX:
            raise RuntimeError("Cannot use bar() in Graphics mode")

        rows = self._rows
        cols = self._cols
        r = 0 if row < 0 else (rows - 1 if row >= rows else row)

        # Inline norm_col
        if start_col == -1:
            sc = cols - 1
        elif start_col < 0:
            sc = 0
        elif start_col >= cols:
            sc = cols - 1
        else:
            sc = start_col

        if end_col == -1:
            ec = cols - 1
        elif end_col < 0:
            ec = 0
        elif end_col >= cols:
            ec = cols - 1
        else:
            ec = end_col

        rtl = sc > ec
        step = -1 if rtl else +1
        cells = abs(ec - sc) + 1
        if cells <= 0:
            return

        total_px = cells * 5
        if max_value <= 0: 
            max_value = 1
        
        if value < 0: 
            value = 0
        
        if value > max_value: 
            value = max_value
        
        filled_px = int(value * total_px / max_value)

        self._ensure_bar_tiles(rtl)

        for i in range(cells):
            px = filled_px - i*5
            if px < 0: px = 0
            if px > 5: px = 5
            ch = px
            col = sc + i*step
            self._move_to(col, r)
            self._data(ch)

    # ---- Graphics mode ----

    @micropython.native
    def _cell_pattern(self, cx:int, cy:int):
        x0 = cx * 5
        y0 = cy * 8
        gw = self._gw
        fb = self._gfb
        rows = []
        for rr in range(8):
            base = (y0 + rr) * gw + x0
            b = ((fb[base] & 1) << 4) | ((fb[base+1] & 1) << 3) | ((fb[base+2] & 1) << 2) | ((fb[base+3] & 1) << 1) | (fb[base+4] & 1)
            rows.append(b)
        return tuple(rows)

    def _set_fb(self, x:int, y:int, v:int):
        if 0 <= x < self._gw and 0 <= y < self._gh:
            self._gfb[y * self._gw + x] = 1 if v else 0

    @property
    def g_width(self) -> int:
        return self._gw
    
    @property
    def g_height(self) -> int:
        return self._gh

    def g_clear(self, on=False):
        self._ensure_gfb()
        v = 1 if on else 0
        fb = self._gfb
        n = len(fb)
        fb[:] = bytes([v]) * n

    def g_point(self, x:int, y:int, on=True):
        self._ensure_gfb()
        self._set_fb(x, y, 1 if on else 0)

    @micropython.native
    def g_rect(self, x:int, y:int, w:int, h:int, fill=False, on=True):
        self._ensure_gfb()
        if w <= 0 or h <= 0:
            return
        
        x1, y1 = x + w - 1, y + h - 1
        gw, gh = self._gw, self._gh
        if x1 < 0 or y1 < 0 or x >= gw or y >= gh:
            return
        
        x  = 0 if x  < 0 else x
        y  = 0 if y  < 0 else y
        x1 = gw - 1 if x1 >= gw else x1
        y1 = gh - 1 if y1 >= gh else y1
        v = 1 if on else 0
        fb = self._gfb

        if fill:
            span = x1 - x + 1
            for yy in range(y, y1+1):
                base = yy * gw + x
                for off in range(span):
                    fb[base + off] = v
        else:
            for xx in range(x, x1+1):
                fb[y  * gw + xx] = v
                fb[y1 * gw + xx] = v
            
            for yy in range(y, y1+1):
                fb[yy * gw + x ] = v
                fb[yy * gw + x1] = v

    @micropython.native
    def g_line(self, x0:int, y0:int, x1:int, y1:int, on=True):
        self._ensure_gfb()
        v = 1 if on else 0
        gw, gh = self._gw, self._gh
        dx = abs(x1 - x0); sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0); sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if 0 <= x0 < gw and 0 <= y0 < gh:
                self._gfb[y0 * gw + x0] = v
            
            if x0 == x1 and y0 == y1:
                break
            
            e2 = err << 1
            if e2 >= dy:
                err += dy; x0 += sx
            
            if e2 <= dx:
                err += dx; y0 += sy

    # --- Hamming helpers for 5x8 tiles (popcount LUT for 0..31) ---
    _POP5 = bytes((0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5))

    @micropython.native
    def _pat_dist(self, a, b):
        pop = self._POP5
        s = 0
        for i in range(8):
            s += pop[(a[i] ^ b[i]) & 31]
        
        return s

    def _select_k_prototypes(self, uniq_patterns, counts, k=8):
        n = len(uniq_patterns)
        if n <= k:
            return list(uniq_patterns)
        dist = [[0]*n for _ in range(n)]
        for i in range(n):
            ai = uniq_patterns[i]
            di = dist[i]
            for j in range(i+1, n):
                d = self._pat_dist(ai, uniq_patterns[j])
                di[j] = d
                dist[j][i] = d
        
        w = [counts[uniq_patterns[i]] for i in range(n)]
        first = max(range(n), key=lambda i: w[i])
        centers = [first]
        best_d = dist[first][:]
        
        for _ in range(1, k):
            best_gain, best_j = -1, None
        
            for j in range(n):
                if j in centers:
                    continue
        
                dj = dist[j]
                gain = 0
                for i in range(n):
                    d = dj[i]; bd = best_d[i]
                    if d < bd:
                        gain += (bd - d) * w[i]
        
                if gain > best_gain:
                    best_gain, best_j = gain, j
        
            if best_j is None:
                break
        
            centers.append(best_j)
            dj = dist[best_j]
            for i in range(n):
                if dj[i] < best_d[i]:
                    best_d[i] = dj[i]
        
        return [uniq_patterns[i] for i in centers]

    def _cb_assign(self, need_patterns):
        prev_slots = list(self._cb_slots)
        prev_map   = dict(self._cb_map)

        new_slots = list(prev_slots)
        new_map   = dict(prev_map)

        for p in list(new_map.keys()):
            if p not in need_patterns:
                s = new_map.pop(p)
                new_slots[s] = None

        free_slots = [s for s in range(8) if new_slots[s] is None]

        for p in need_patterns:
            if p in new_map:
                continue
            if not free_slots:
                break
            s = free_slots.pop(0)
            new_slots[s] = p
            new_map[p]   = s

        changed = []
        for s in range(8):
            if new_slots[s] != prev_slots[s] and new_slots[s] is not None:
                changed.append((s, new_slots[s]))

        return new_slots, new_map, changed

    def _cb_slot_of(self, pattern):
        s = self._cb_map.get(pattern, None)
        if s is not None:
            return s

        best_s, best_score = 0, 1_000
        pop5 = self._POP5
        for si, p in enumerate(self._cb_slots):
            if p is None:
                continue
            
            score = 0
            for a, b in zip(pattern, p):
                score += pop5[(a ^ b) & 31]
            
            if score < best_score:
                best_score, best_s = score, si
        
        return best_s

    def g_update(self):
        if self._mode != self.MODE_GFX:
            raise RuntimeError("Cannot use g_update() in Text mode")
        
        cols, rows = self._cols, self._rows
        cell_pattern = self._cell_pattern
        counts = {}
        tiles  = []
        for r in range(rows):
            for c in range(cols):
                pat = cell_pattern(c, r)
                tiles.append(pat)
                counts[pat] = counts.get(pat, 0) + 1
        
        uniq = list(counts.keys())
        if len(uniq) <= 8:
            prototypes = uniq
        else:
            prototypes = self._select_k_prototypes(uniq, counts, 8)
        
        while len(prototypes) < 8:
            prototypes.append((0,0,0,0,0,0,0,0))
        
        new_slots, new_map, changed = self._cb_assign(prototypes)
        prev_disp = self._display
        if changed and prev_disp:
            self.set_display(on=False)
        
        for s, p in changed:
            self.create_char(s, p)
        
        if changed and prev_disp:
            self.set_display(on=True)
        
        self._cb_slots = new_slots
        self._cb_map   = new_map
        
        cb_slot_of = self._cb_slot_of
        idx = 0
        for r in range(rows):
            self._move_to(0, r)
            for c in range(cols):
                t = tiles[idx]; idx += 1
                slot = cb_slot_of(t)
                self._data(slot)

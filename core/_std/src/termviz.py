# @package: termviz
# @version: 1.6.0
# @type: core
# @category: utility
# @interface: none
# @depends: none
# @platforms: *
# @tags: terminal, visualization, color, ansi, chart, graph
# @author: PlanXLab Development Team

import sys
import array
import micropython

class Term:
    @staticmethod
    def rgb(r: int, g: int, b: int, fg: bool = True) -> str:
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError("RGB must be 0..255")
        return "\x1b[{};2;{};{};{}m".format(38 if fg else 48, r, g, b)

    @staticmethod
    def hex_color(code: str, fg: bool = True) -> str:
        s = code.lstrip("#")
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) != 6:
            raise ValueError("HEX must be #rgb or #rrggbb")
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return Term.rgb(r, g, b, fg=fg)

    @staticmethod
    def gray(level: int, fg: bool = True) -> str:
        if not (0 <= level <= 255):
            raise ValueError("gray level 0..255")
        return Term.rgb(level, level, level, fg=fg)

    class FG:
        BLACK = "\x1b[38;2;190;190;190m"
        RED = "\x1b[38;2;224;84;84m"
        GREEN = "\x1b[38;2;84;196;124m"
        YELLOW = "\x1b[38;2;224;188;72m"
        BLUE = "\x1b[38;2;108;164;244m"
        MAGENTA = "\x1b[38;2;208;108;232m"
        CYAN = "\x1b[38;2;84;208;216m"
        WHITE = "\x1b[38;2;238;238;238m"
        
        BRIGHT_BLACK = "\x1b[38;2;220;220;220m"
        BRIGHT_RED = "\x1b[38;2;255;118;118m"
        BRIGHT_GREEN = "\x1b[38;2;118;236;160m"
        BRIGHT_YELLOW = "\x1b[38;2;255;224;136m"
        BRIGHT_BLUE = "\x1b[38;2;144;196;255m"
        BRIGHT_MAGENTA = "\x1b[38;2;236;144;255m"
        BRIGHT_CYAN = "\x1b[38;2;128;240;244m"
        BRIGHT_WHITE = "\x1b[38;2;255;255;255m"
        
        PRIMARY = "\x1b[38;2;144;196;255m"
        SUCCESS = "\x1b[38;2;118;236;160m"
        WARNING = "\x1b[38;2;255;224;136m"
        DANGER = "\x1b[38;2;255;118;118m"
        INFO = "\x1b[38;2;128;240;244m"
        MUTED = "\x1b[38;2;170;170;170m"
        SURFACE = "\x1b[38;2;238;238;238m"

    class BG:
        BLACK = "\x1b[48;2;28;28;28m"
        RED = "\x1b[48;2;86;24;24m"
        GREEN = "\x1b[48;2;24;84;48m"
        YELLOW = "\x1b[48;2;88;72;20m"
        BLUE = "\x1b[48;2;24;44;96m"
        MAGENTA = "\x1b[48;2;64;24;76m"
        CYAN = "\x1b[48;2;20;76;84m"
        WHITE = "\x1b[48;2;234;234;234m"
        
        BRIGHT_BLACK = "\x1b[48;2;44;44;44m"
        BRIGHT_RED = "\x1b[48;2;120;34;34m"
        BRIGHT_GREEN = "\x1b[48;2;36;120;72m"
        BRIGHT_YELLOW = "\x1b[48;2;120;96;32m"
        BRIGHT_BLUE = "\x1b[48;2;36;64;128m"
        BRIGHT_MAGENTA = "\x1b[48;2;96;36;112m"
        BRIGHT_CYAN = "\x1b[48;2;36;108;120m"
        BRIGHT_WHITE = "\x1b[48;2;246;246;246m"
        
        PRIMARY = "\x1b[48;2;36;64;128m"
        SUCCESS = "\x1b[48;2;36;120;72m"
        WARNING = "\x1b[48;2;120;96;32m"
        DANGER = "\x1b[48;2;120;34;34m"
        INFO = "\x1b[48;2;36;108;120m"
        MUTED = "\x1b[48;2;44;44;44m"
        SURFACE = "\x1b[48;2;28;28;28m"

    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"
    DIM = "\x1b[2m"
    ITALIC = "\x1b[3m"
    UNDERLINE = "\x1b[4m"
    REVERSE = "\x1b[7m"
    HIDDEN = "\x1b[8m"
    STRIKE = "\x1b[9m"

    @staticmethod
    def cursor_up(n: int = 1) -> str:
        return "\x1b[{}A".format(n)

    @staticmethod
    def cursor_down(n: int = 1) -> str:
        return "\x1b[{}B".format(n)

    @staticmethod
    def cursor_right(n: int = 1) -> str:
        return "\x1b[{}C".format(n)

    @staticmethod
    def cursor_left(n: int = 1) -> str:
        return "\x1b[{}D".format(n)

    @staticmethod
    def cursor_to(row: int, col: int) -> str:
        return "\x1b[{};{}H".format(row, col)

    @staticmethod
    def cursor_home() -> str:
        return "\x1b[H"

    @staticmethod
    def cursor_col(n: int) -> str:
        return "\x1b[{}G".format(n)

    @staticmethod
    def cursor_save() -> str:
        return "\x1b[s"

    @staticmethod
    def cursor_restore() -> str:
        return "\x1b[u"

    @staticmethod
    def cursor_hide() -> str:
        return "\x1b[?25l"

    @staticmethod
    def cursor_show() -> str:
        return "\x1b[?25h"
    
    @staticmethod
    def cursor_next_line(n: int = 1) -> str:
        return "\x1b[{}E".format(n)

    @staticmethod
    def cursor_prev_line(n: int = 1) -> str:
        return "\x1b[{}F".format(n)

    @staticmethod
    def erase_screen(mode: int = 2) -> str:
        if mode not in (0, 1, 2, 3):
            raise ValueError("mode must be 0|1|2|3")
        return "\x1b[{}J".format(mode)
    
    @staticmethod
    def erase_line(mode: int = 2) -> str:
        if mode not in (0, 1, 2):
            raise ValueError("mode must be 0|1|2")
        return "\x1b[{}K".format(mode)
    
    @staticmethod
    def clear_screen() -> str:
        return "\x1b[H\x1b[2J"
    
    @staticmethod
    def clear_line() -> str:
        return "\x1b[G\x1b[2K"

class Canvas:
    def __init__(self, cols, rows,
                 default_rgb=(220,220,220),
                 color_mode='truecolor',
                 term_rows_cap=None):

        self.cols = int(cols)
        self.rows = int(rows)
        self.default_rgb = default_rgb
        self.color_mode = color_mode

        self._ds_rows = int(term_rows_cap) if term_rows_cap else None
        self._prev_mask_ds = None
        self._prev_color_ds = None
        self._work_mask = None
        self._work_color = None

        self._alloc_buffers()
        self._fg_cur = None

        self._braille = [chr(0x2800+i) for i in range(256)]
        self._sgr_cache = {'tc': {}, 'x256': {}}
        self._bit_map = bytearray([1, 2, 4, 64, 8, 16, 32, 128])
        self._render_buf = []

        w = sys.stdout.buffer.write
        w("\x1b[?1049h")
        w("\x1b[?12l\x1b[?25l")

    @property
    def width(self):
        return self.cols * 2

    @property
    def height(self):
        return self.rows * 4

    def begin(self):
        self._begin_fast()
        self._fg_cur = None

    @micropython.viper
    def _begin_fast(self):
        n = int(len(self._mask_b))
        m = ptr8(self._mask_b)
        c = ptr32(self._color_b)
        i = 0
        while i < n:
            m[i] = 0
            c[i] = int(-1)
            i += 1

    def end(self):
        w = sys.stdout.buffer.write
        w("\x1b[0m")
        w("\x1b[?1049l")
        w("\x1b[?12h\x1b[?25h")
        self._ended = True

    def __enter__(self):
        self._ended = False
        return self

    def __exit__(self, *_):
        if not getattr(self, '_ended', False):
            self.end()
        return False

    def __del__(self):
        if not getattr(self, '_ended', False):
            self.end()

    def clear(self):
        n = self.rows * self.cols
        self._prev_mask_b = bytearray(n)
        self._prev_color_b = array.array('I', (0xFFFFFFFF for _ in range(n)))
        if self._ds_rows and self._ds_rows < self.rows:
            nd = self._ds_rows * self.cols
            self._prev_mask_ds = bytearray(nd)
            self._prev_color_ds = array.array('I', (0xFFFFFFFF for _ in range(nd)))
        self._fg_cur = None
        sys.stdout.buffer.write(b"\x1b[H\x1b[2J")

    @micropython.viper
    def set_px(self, x:int, y:int, rgb:int):
        cols = int(self.cols)
        rows = int(self.rows)
        
        if x < 0 or y < 0: 
            return
        
        cx = x >> 1
        cy = y >> 2
        if cx >= cols or cy >= rows: 
            return
        
        idx = cy * cols + cx

        bm = ptr8(self._bit_map)
        bit = int(bm[int((x & 1) << 2 | (y & 3))])

        m = ptr8(self._mask_b)
        c = ptr32(self._color_b)

        prev_mask = int(m[idx])
        prev_rgb  = int(c[idx])

        m[idx] = (prev_mask | bit) & 0xFF

        if prev_mask == 0 or prev_rgb == int(-1) or prev_rgb == rgb:
            c[idx] = rgb
        else:
            n = int(0)
            v = prev_mask
            while v:
                n += v & 1
                v >>= 1
            pr = (prev_rgb >> 16) & 0xFF
            pg = (prev_rgb >>  8) & 0xFF
            pb =  prev_rgb        & 0xFF
            nr = (rgb >> 16) & 0xFF
            ng = (rgb >>  8) & 0xFF
            nb =  rgb        & 0xFF
            br = (pr * n + nr) // (n + 1)
            bg = (pg * n + ng) // (n + 1)
            bb = (pb * n + nb) // (n + 1)
            c[idx] = (br << 16) | (bg << 8) | bb

    @micropython.viper
    def clr_px(self, x:int, y:int):
        cols = int(self.cols)
        rows = int(self.rows)
        
        if x < 0 or y < 0: 
            return
        
        cx = x >> 1
        cy = y >> 2
        if cx >= cols or cy >= rows: 
            return
        
        idx = cy*cols + cx

        bm = ptr8(self._bit_map)
        bit = int(bm[int((x & 1) << 2 | (y & 3))])
        inv = int((~bit) & 0xFF)

        m = ptr8(self._mask_b)
        c = ptr32(self._color_b)
        v = int(m[idx]) & inv
        m[idx] = v & 0xFF
        if v == 0:
            c[idx] = -1

    @micropython.native
    def render(self, ox=1, oy=1):
        w = sys.stdout.buffer.write
        cur = self._fg_cur

        if self._ds_rows and self._ds_rows < self.rows:
            self._downsample_rows()
            render_rows = int(self._ds_rows)
            m_prev = self._prev_mask_ds
            c_prev = self._prev_color_ds
            m_curr = self._work_mask
            c_curr = self._work_color
        else:
            render_rows = int(self.rows)
            m_prev = self._prev_mask_b
            c_prev = self._prev_color_b
            m_curr = self._mask_b
            c_curr = self._color_b

        cols = int(self.cols)

        for r in range(render_rows):
            row_off = r * cols
            c = 0
            while c < cols:
                idx = row_off + c
                if m_prev[idx] == m_curr[idx] and c_prev[idx] == c_curr[idx]:
                    c += 1
                    continue

                start = c
                rgb_raw = c_curr[idx]
                rgb = self.default_rgb if rgb_raw == 0xFFFFFFFF else rgb_raw

                while c < cols:
                    ii = row_off + c
                    if m_prev[ii] != m_curr[ii] or c_prev[ii] != c_curr[ii]:
                        if c_curr[ii] != rgb_raw:
                            break
                        c += 1
                        continue
                    break
                end = c

                w("\x1b[{};{}H".format(oy + r, ox + start))
                if rgb != cur:
                    w(self.sgr(rgb))
                    cur = rgb

                parts = self._render_buf
                del parts[:]
                for i in range(start, end):
                    m = m_curr[row_off + i]
                    parts.append(' ' if m == 0 else self._braille[m])
                w(''.join(parts))

            j = 0
            while j < cols:
                idx2 = row_off + j
                m_prev[idx2] = m_curr[idx2]
                c_prev[idx2] = c_curr[idx2]
                j += 1

        self._fg_cur = cur

    @micropython.native
    def sgr(self, rgb):
        if rgb is None: rgb = self.default_rgb
        if self.color_mode == '256':
            return self._sgr_256(rgb)
        return self._sgr_truecolor(rgb)

    @staticmethod
    def pack_rgb(rgb):
        if isinstance(rgb, int):
            return rgb & 0xFFFFFF
        r,g,b = rgb
        return ((r & 255) << 16) | ((g & 255) << 8) | (b & 255)

    def _alloc_buffers(self):
        n = self.rows * self.cols
        self._mask_b = bytearray(n)
        self._color_b = array.array('I', (0xFFFFFFFF for _ in range(n)))
        self._prev_mask_b = bytearray(n)
        self._prev_color_b = array.array('I', (0xFFFFFFFF for _ in range(n)))

        if self._ds_rows and self._ds_rows < self.rows:
            nd = self._ds_rows * self.cols
            self._prev_mask_ds = bytearray(nd)
            self._prev_color_ds = array.array('I', (0xFFFFFFFF for _ in range(nd)))
            self._work_mask = bytearray(nd)
            self._work_color = array.array('I', (0xFFFFFFFF for _ in range(nd)))

    def _render_rows_hint(self):
        return self._ds_rows if (self._ds_rows and self._ds_rows < self.rows) else self.rows

    @staticmethod
    def _unpack_rgb(rgb):
        if isinstance(rgb, int):
            return ((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255)
        return rgb

    @micropython.native
    def _sgr_truecolor(self, rgb):
        cache = self._sgr_cache['tc']
        rgb_t = self._unpack_rgb(rgb)
        s = cache.get(rgb_t)
        if s is None:
            r,g,b = rgb_t
            s = "\x1b[38;2;{};{};{}m".format(r,g,b)
            if len(cache) < 64:
                cache[rgb_t] = s
        return s

    @micropython.native
    def _sgr_256(self, rgb):
        cache = self._sgr_cache['x256']
        rgb_t = self._unpack_rgb(rgb)
        s = cache.get(rgb_t)
        if s is None:
            r,g,b = rgb_t
            ri = min(5, int(r*6//256)); gi = min(5, int(g*6//256)); bi = min(5, int(b*6//256))
            n = 16 + 36*ri + 6*gi + bi
            s = "\x1b[38;5;{}m".format(n)
            if len(cache) < 64:
                cache[rgb_t] = s
        return s

    @micropython.native
    def _downsample_rows(self):
        rows_src = int(self.rows)
        rows_dst = int(self._ds_rows)
        cols = int(self.cols)

        m_src = self._mask_b
        c_src = self._color_b
        m_out = self._work_mask
        c_out = self._work_color

        for r_dst in range(rows_dst):
            r0 = (r_dst * rows_src) // rows_dst
            r1 = ((r_dst + 1) * rows_src) // rows_dst
            if r1 <= r0: r1 = r0 + 1
            base_out = r_dst * cols
            for cc in range(cols):
                off = base_out + cc
                mm = 0
                color = -1
                rr = r0
                while rr < r1:
                    off_src = rr*cols + cc
                    ms = m_src[off_src]
                    if ms:
                        mm |= ms
                        if color == -1:
                            color = c_src[off_src]
                    rr += 1
                m_out[off] = mm
                c_out[off] = color if mm else 0xFFFFFFFF

class Plot:
    def __init__(self, canvas, region_px=None, xlim=(0.0,1.0), ylim=(0.0,1.0), color_cycle=None):
        self.cv = canvas

        W = self.cv.width
        H = self.cv.height

        self.xmin, self.xmax = float(xlim[0]), float(xlim[1])
        self.ymin, self.ymax = float(ylim[0]), float(ylim[1])

        self._ylabel = None
        if region_px is None:
            region_px = (2, 2, int(W)-4, int(H)-8)
        self.set_viewport(*region_px)

        self._grid_on = True
        self._xlabel = None; self._title = None
        self._legend_on = True; self._legend_loc = 'upper right'; self._legend_xy = None

        self._xticks = None; self._xticklabels = None
        self._yticks = None; self._yticklabels = None

        self._series = []
        self._legend = []
        self._name_color = (210,210,210)

        self._palette = color_cycle or [
            (80,160,255), (255,120,80), (80,255,120), (255,200,80),
            (200,80,255), (80,255,255), (255,128,170), (128,255,128),
        ]
        self._pi = 0
        self._texts = []
        self._legend_colors = None

    def set_viewport(self, x, y, width, height):
        W, H = self.cv.width, self.cv.height

        x = max(0, int(x))
        y = max(0, int(y))
        width = max(1, int(width))
        height = max(1, int(height))
        if x + width > W:
            width = W - x
        if y + height > H:
            height = H - y

        self._raw_vx, self._raw_vy = x, y
        self._raw_vw, self._raw_vh = width, height
        self._apply_viewport()

    def _apply_viewport(self):
        yl = getattr(self, '_ylabel', None)
        yt = getattr(self, '_yticklabels', None)
        ylabel_len = len(yl[0]) if yl else 0
        ytick_max = max((len(s) for s in yt), default=0) if yt else 0
        if ylabel_len > 0 and ytick_max > 0:
            offset = (ylabel_len + ytick_max + 2) * 2
        elif ylabel_len > 0:
            offset = (ylabel_len + 1) * 2
        elif ytick_max > 0:
            offset = (ytick_max + 1) * 2
        else:
            offset = 0
        W = self.cv.width
        x = min(self._raw_vx + offset, W - 1)
        w = max(1, self._raw_vw - offset)
        if x + w > W:
            w = W - x
        self.vx, self.vy = x, self._raw_vy
        self.vw, self.vh = w, self._raw_vh
        self._update_scale()

    def xlim(self, *args):
        if not args: return (self.xmin, self.xmax)
        a = args[0] if len(args) == 1 else args
        self.xmin = float(min(a[0], a[1]))
        self.xmax = float(max(a[0], a[1]))
        self._update_scale()

    def ylim(self, *args):
        if not args: return (self.ymin, self.ymax)
        a = args[0] if len(args) == 1 else args
        self.ymin = float(min(a[0], a[1]))
        self.ymax = float(max(a[0], a[1]))
        self._update_scale()

    def title(self, s=None, color=(230,230,230)):
        if s is None: return self._title
        self._title = (str(s), color)

    def xlabel(self, s=None, color=(210,210,210)):
        if s is None: return self._xlabel
        self._xlabel = (str(s), color)

    def ylabel(self, s=None, color=(210,210,210)):
        if s is None: return self._ylabel
        self._ylabel = (str(s), color)
        if hasattr(self, '_raw_vx'):
            self._apply_viewport()

    def legend(self, loc=None):
        self._legend_on = True
        if isinstance(loc, tuple):
            self._legend_xy = (float(loc[0]), float(loc[1]))
        elif isinstance(loc, str):
            self._legend_loc = loc.strip().lower()
            self._legend_xy = None

    def set_legend_colors(self, colors):
        self._legend_colors = list(colors) if colors else None

    def clear_legend_items(self):
        self._legend = []
        self._legend_colors = None

    def set_legend_items(self, names):
        items = []
        n = len(names or [])
        for i in range(n):
            nm = str(names[i])
            if self._legend_colors and i < len(self._legend_colors):
                col = self._legend_colors[i]
            else:
                col = self._palette[i % len(self._palette)]
            items.append((nm, col))
        self._legend = items

    def grid(self, flag=None):
        if flag is None: return self._grid_on
        self._grid_on = bool(flag)

    def xticks(self, ticks=None, labels=None):
        if ticks is None: return (self._xticks, self._xticklabels)
        self._xticks = list(ticks)
        self._xticklabels = [str(v) for v in (labels if labels is not None else ticks)]

    def yticks(self, ticks=None, labels=None):
        if ticks is None: return (self._yticks, self._yticklabels)
        self._yticks = list(ticks)
        self._yticklabels = [str(v) for v in (labels if labels is not None else ticks)]
        if hasattr(self, '_raw_vx'):
            self._apply_viewport()

    def plot(self, *args, label=None, color=None):
        c = self._pick(color)
        if len(args) == 1:
            y = args[0]
            n = len(y)
            if n == 0: return
            dx = (self.xmax - self.xmin) / max(1, (n - 1))
            pts = [(self.xmin + i * dx, y[i]) for i in range(n)]
        else:
            x, y = args[0], args[1]
            pts = list(zip(x, y))
        self._series.append(("line", pts, c, label))
        if label: self._legend.append((label, c))

    def scatter(self, x, y=None, size=1, label=None, color=None):
        c = self._pick(color)
        pts = list(zip(x, y)) if y is not None else [(i, v) for i, v in enumerate(x)]
        self._series.append(("scatter", (pts, int(size)), c, label))
        if label: self._legend.append((label, c))

    def bar(self, x, height, width=0.8, label=None, color=None):
        c = self._pick(color)
        if isinstance(x, (list, tuple)):
            xs = x
            hs = height if isinstance(height, (list, tuple)) else [height] * len(xs)
            for xi, hi in zip(xs, hs):
                self._series.append(("vbar", (float(xi), 0.0, float(hi), float(width)), c, label))
        else:
            self._series.append(("vbar", (float(x), 0.0, float(height), float(width)), c, label))
        if label: self._legend.append((label, c))

    def hbar(self, y, width, height=0.8, label=None, color=None):
        c = self._pick(color)
        if isinstance(y, (list, tuple)):
            ys = y
            ws = width if isinstance(width, (list, tuple)) else [width] * len(ys)
            for yi, wi in zip(ys, ws):
                self._series.append(("hbar", (float(yi), 0.0, float(wi), float(height)), c, label))
        else:
            self._series.append(("hbar", (float(y), 0.0, float(width), float(height)), c, label))
        if label: self._legend.append((label, c))

    def hist(self, data, bins=10, range_=None, density=False, label=None, color=None):
        if not data:
            return

        dmin = min(data) if (range_ is None or range_[0] is None) else float(range_[0])
        dmax = max(data) if (range_ is None or range_[1] is None) else float(range_[1])
        if dmax == dmin:
            dmax = dmin + 1.0

        bins = int(bins)
        bw = (dmax - dmin) / bins
        cnt = [0] * bins

        for v in data:
            if v < dmin or v > dmax:
                continue
            k = int((v - dmin) / bw)
            if k >= bins:
                k = bins - 1
            cnt[k] += 1

        if density:
            s = sum(cnt) or 1
            cnt = [c / float(s) for c in cnt]

        if dmin < self.xmin or dmax > self.xmax:
            self.xlim(min(self.xmin, dmin), max(self.xmax, dmax))

        ymax_needed = (max(cnt) if cnt else 1) * 1.05
        if density and ymax_needed < 1.0:
            ymax_needed = 1.0
        if self.ymax < ymax_needed:
            self.ylim(min(self.ymin, 0.0), ymax_needed)

        xs = [dmin + (i + 0.5) * bw for i in range(bins)]
        self.bar(xs, cnt, width=bw, label=label, color=color)

    def text(self, x, y, text, color=(220,220,220)):
        self._texts.append((float(x), float(y), str(text), color))

    def line(self, x0, y0, x1, y1, color=None, label=None, autoscale=False):
        c = self._pick(color)
        x0 = float(x0); y0 = float(y0); x1 = float(x1); y1 = float(y1)

        if autoscale:
            if x0 < self.xmin or x1 < self.xmin or x0 > self.xmax or x1 > self.xmax:
                self.xlim(min(self.xmin, x0, x1), max(self.xmax, x0, x1))
            if y0 < self.ymin or y1 < self.ymin or y0 > self.ymax or y1 > self.ymax:
                self.ylim(min(self.ymin, y0, y1), max(self.ymax, y0, y1))

        self._series.append(("line", [(x0, y0), (x1, y1)], c, label))
        if label:
            self._legend.append((label, c))

    def circle(self, center, r, label=None, color=None, fill=False):
        x, y = float(center[0]), float(center[1])
        c = self._pick(color)
        self._series.append(("circle", (x, y, float(r), bool(fill)), c, label))
        if label: self._legend.append((label, c))

    def polygon(self, vertices, label=None, color=None, fill=False):
        c = self._pick(color)
        verts = [(float(v[0]), float(v[1])) for v in vertices]
        self._series.append(("polygon", (verts, bool(fill)), c, label))
        if label: self._legend.append((label, c))

    def show(self, clear_after=False):
        self.cv.begin()
        self._draw_axes()

        for kind, payload, color, label in self._series:
            if kind == "line":
                pts = payload; rgb = self.cv.pack_rgb(color)
                if not pts: continue
                x0, y0 = pts[0]
                px0, py0 = self._wx(x0), self._wy(y0)
                for x1, y1 in pts[1:]:
                    px1, py1 = self._wx(x1), self._wy(y1)
                    self._line_px(px0, py0, px1, py1, rgb)
                    px0, py0 = px1, py1
            elif kind == "scatter":
                pts, sz = payload; rgb = self.cv.pack_rgb(color)
                for x, y in pts:
                    px, py = self._wx(x), self._wy(y)
                    if sz <= 1:
                        self.cv.set_px(px, py, rgb)
                    else:
                        r = sz - 1
                        for dy in range(-r, r + 1):
                            for dx in range(-r, r + 1):
                                if abs(dx) + abs(dy) <= r:
                                    self.cv.set_px(px + dx, py + dy, rgb)
            elif kind == "vbar":
                x, y0, y1, w_world = payload
                self._fill_vbar(x, y0, y1, w_world, color)
            elif kind == "hbar":
                y, x0, x1, h_world = payload
                self._fill_hbar(y, x0, x1, h_world, color)
            elif kind == "circle":
                cxw, cyw, rw, fill = payload
                cxp = self._wx(cxw)
                cyp = self._wy(cyw)
                rpx = int(max(1.0, rw * (self._sx + self._sy) * 0.5 + 0.5))
                rgb = self.cv.pack_rgb(color)
                if fill:
                    self._fcircle_px(cxp, cyp, rpx, rgb)
                else:
                    self._circle_px(cxp, cyp, rpx, rgb)
            elif kind == "polygon":
                verts, fill = payload
                rgb = self.cv.pack_rgb(color)
                if not verts:
                    continue
                if fill:
                    self._fpoly_px(verts, rgb)
                else:
                    pts_px = [(self._wx(v[0]), self._wy(v[1])) for v in verts]
                    n = len(pts_px)
                    for i in range(n):
                        x0, y0 = pts_px[i]
                        x1, y1 = pts_px[(i + 1) % n]
                        self._line_px(x0, y0, x1, y1, rgb)

        self.cv.render()
        self._queue_tick_labels()
        self._queue_labels()
        self._queue_legend()
        self._queue_texts() 

        if clear_after:
            self._series.clear()
            self._texts.clear()

    def _update_scale(self):
        dx = (self.xmax - self.xmin) or 1.0
        dy = (self.ymax - self.ymin) or 1.0
        self._sx = (self.vw - 1) / dx
        self._sy = (self.vh - 1) / dy

    @micropython.native
    def _wx(self, x: float) -> int:
        return int(self.vx + (x - self.xmin) * self._sx + 0.5)

    @micropython.native
    def _wy(self, y: float) -> int:
        return int(self.vy + self.vh - 1 - (y - self.ymin) * self._sy + 0.5)

    def _pick(self, color):
        if color is not None: return color
        c = self._palette[self._pi % len(self._palette)]
        self._pi += 1
        return c

    def _queue_texts(self):
        if not self._texts:
            return
        
        w = sys.stdout.buffer.write
        vx1 = self.vx + self.vw - 1
        vy1 = self.vy + self.vh - 1
        for x, y, text, color in self._texts:
            px, py = self._wx(x), self._wy(y)

            col = px >> 1
            row = py >> 2
            if row < 0: 
                row = 0
            if col < 0: 
                col = 0
            
            if px < self.vx or px > vx1 or py < self.vy or py > vy1: 
                continue
            
            w("\x1b[{};{}H".format(row + 1, col + 1))
            w(self.cv.sgr(color)); w(text)
        self._texts = []
        
    @micropython.native
    def _line_px(self, x0:int, y0:int, x1:int, y1:int, rgb:int):
        setp = self.cv.set_px
        
        dx = x1 - x0
        sx = 1 if dx >= 0 else -1; dx = dx if dx >= 0 else -dx
        dy = y1 - y0
        sy = 1 if dy >= 0 else -1; dy = -dy if dy < 0 else dy
        err = dx - dy
        while True:
            setp(x0, y0, rgb)
            if x0 == x1 and y0 == y1: break
            e2 = err << 1
            if e2 >= -dy:
                err -= dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    @micropython.native
    def _circle_px(self, cx:int, cy:int, r:int, rgb:int):
        setp = self.cv.set_px
        x = 0
        y = r
        d = 1 - r
        while y >= x:
            setp(cx + x, cy + y, rgb); setp(cx - x, cy + y, rgb)
            setp(cx + x, cy - y, rgb); setp(cx - x, cy - y, rgb)
            setp(cx + y, cy + x, rgb); setp(cx - y, cy + x, rgb)
            setp(cx + y, cy - x, rgb); setp(cx - y, cy - x, rgb)
            if d < 0:
                d += (x << 1) + 3
            else:
                d += ((x - y) << 1) + 5
                y -= 1
            x += 1

    @micropython.native
    def _fcircle_px(self, cx:int, cy:int, r:int, rgb:int):
        setp = self.cv.set_px
        x = 0
        y = r
        d = 1 - r
        while y >= x:
            for xx in range(cx - x, cx + x + 1):
                setp(xx, cy + y, rgb); setp(xx, cy - y, rgb)
            for xx in range(cx - y, cx + y + 1):
                setp(xx, cy + x, rgb); setp(xx, cy - x, rgb)
            if d < 0:
                d += (x << 1) + 3
            else:
                d += ((x - y) << 1) + 5
                y -= 1
            x += 1

    def _fpoly_px(self, verts, rgb):
        pts = [(self._wx(v[0]), self._wy(v[1])) for v in verts]
        n = len(pts)
        if n < 3:
            return
        setp = self.cv.set_px
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        for y in range(min_y, max_y + 1):
            xs = []
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi <= y < yj) or (yj <= y < yi):
                    xs.append(xi + (y - yi) * (xj - xi) / (yj - yi))
                j = i
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(int(xs[k] + 0.5), int(xs[k + 1] + 0.5) + 1):
                    setp(xx, y, rgb)

    @micropython.native
    def _fill_vbar(self, x_world: float, y0_world: float, y1_world: float, w_world: float, color):
        rgb = self.cv.pack_rgb(color)
        px = self._wx(x_world)
        py0 = self._wy(y0_world); py1 = self._wy(y1_world)
        if py0 > py1: py0, py1 = py1, py0
        pw = max(1, int(w_world * self._sx + 0.5))

        vx0 = self.vx; vy0 = self.vy
        vx1 = self.vx + self.vw - 1; vy1 = self.vy + self.vh - 1

        xL = px - (pw >> 1); xR = xL + pw - 1
        if xL < vx0: xL = vx0
        if xR > vx1: xR = vx1
        if py0 < vy0: py0 = vy0
        if py1 > vy1: py1 = vy1
        if xL > xR or py0 > py1:
            return

        setp = self.cv.set_px
        for xx in range(xL, xR + 1):
            for yy in range(py0, py1 + 1):
                setp(xx, yy, rgb)

    @micropython.native
    def _fill_hbar(self, y_world: float, x0_world: float, x1_world: float, h_world: float, color):
        rgb = self.cv.pack_rgb(color)
        py = self._wy(y_world)
        px0 = self._wx(x0_world); px1 = self._wx(x1_world)
        if px0 > px1: px0, px1 = px1, px0
        ph = max(1, int(h_world * self._sy + 0.5))

        vx0 = self.vx; vy0 = self.vy
        vx1 = self.vx + self.vw - 1; vy1 = self.vy + self.vh - 1

        yT = py - (ph >> 1); yB = yT + ph - 1
        if yT < vy0: yT = vy0
        if yB > vy1: yB = vy1
        if px0 < vx0: px0 = vx0
        if px1 > vx1: px1 = vx1
        if px0 > px1 or yT > yB:
            return

        setp = self.cv.set_px
        for yy in range(yT, yB + 1):
            for xx in range(px0, px1 + 1):
                setp(xx, yy, rgb)

    def _draw_axes(self):
        g = (110,110,110)
        rgb = self.cv.pack_rgb(g)

        for xx in range(self.vx, self.vx + self.vw):
            self.cv.set_px(xx, self.vy, rgb)
            self.cv.set_px(xx, self.vy + self.vh - 1, rgb)
        
        for yy in range(self.vy, self.vy + self.vh):
            self.cv.set_px(self.vx, yy, rgb)
            self.cv.set_px(self.vx + self.vw - 1, yy, rgb)

        if not self._grid_on:
            return

        g2 = (70,70,70)
        rgb2 = self.cv.pack_rgb(g2)
        if self._xticks:
            for x in self._xticks:
                px = self._wx(x)
                for yy in range(self.vy, self.vy + self.vh):
                    self.cv.set_px(px, yy, rgb2)
        
        if self._yticks:
            for y in self._yticks:
                py = self._wy(y)
                for xx in range(self.vx, self.vx + self.vw):
                    self.cv.set_px(xx, py, rgb2)

    def _queue_tick_labels(self):
        w = sys.stdout.buffer.write

        if self._yticks:
            left_edge_col = self.vx >> 1
            label_end_col = max(0, left_edge_col - 1)
            clear_width = label_end_col + 1
            blank = " " * clear_width
            vy_row_start = self.vy >> 2
            vy_row_end   = (self.vy + self.vh - 1) >> 2
            for r in range(vy_row_start, vy_row_end + 1):
                w("\x1b[{};1H".format(r + 1)); w(blank)
            used_rows = {}
            for i, v in enumerate(self._yticks):
                py = self._wy(v)
                row = (py >> 2)
                if row < 0 or row in used_rows:
                    continue
                
                used_rows[row] = True
                lab = self._yticklabels[i] if (self._yticklabels and i < len(self._yticklabels)) else str(v)
                start_col = label_end_col - (len(lab) - 1)
                if start_col < 0:
                    start_col = 0
                
                w("\x1b[{};{}H".format(row + 1, start_col + 1))
                w(self.cv.sgr((210,210,210))); w(lab)

        if self._xticks:
            y0_label_str = None
            if self._yticks:
                for j, vy in enumerate(self._yticks):
                    if abs(vy - self.ymin) <= 1e-9:
                        y0_label_str = (self._yticklabels[j] if (self._yticklabels and j < len(self._yticklabels)) else str(vy))
                        break

            base_row = ((self.vy + self.vh - 1) >> 2) + 1
            last_end = -9999
            for i, x in enumerate(self._xticks):
                px = self._wx(x); col0 = (px >> 1)
                lab = self._xticklabels[i] if (self._xticklabels and i < len(self._xticklabels)) else str(x)

                if abs(x - self.xmin) <= 1e-9 and y0_label_str is not None and lab == y0_label_str:
                    continue

                col_lbl = col0 - (len(lab) // 2)
                if col_lbl < 0: col_lbl = 0
                start = col_lbl; end = col_lbl + len(lab) - 1
                if start <= last_end + 1:
                    continue
                
                last_end = end
                w("\x1b[{};{}H".format(base_row + 1, col_lbl + 1))
                w(self.cv.sgr((210,210,210))); w(lab)

    def _queue_labels(self):
        w = sys.stdout.buffer.write

        if self._title:
            s, colr = self._title
            col = self.vx // 2 + max(0, (self.vw // 4) - (len(s) // 2))
            row = max(0, (self.vy // 4) - 1)
            w("\x1b[{};{}H".format(row + 1, col + 1)); w(self.cv.sgr(colr)); w(s)
            
        if self._xlabel:
            s, colr = self._xlabel
            row = ((self.vy + self.vh - 1) >> 2) + 2
            col = self.vx // 2 + max(0, (self.vw // 4) - (len(s) // 2))
            w("\x1b[{};{}H".format(row + 1, col + 1)); w(self.cv.sgr(colr)); w(s)

        if self._ylabel:
            s, colr = self._ylabel
            ytick_max = max((len(lb) for lb in self._yticklabels), default=0) if self._yticklabels else 0
            col = (self.vx // 2) - ytick_max - len(s) - 2
            if col < 0: col = 0
            row = self.vy // 4 + (self.vh // 8)
            w("\x1b[{};{}H".format(row + 1, col + 1)); w(self.cv.sgr(colr)); w(s)

    def _queue_legend(self):
        if not self._legend_on or not self._legend:
            return

        w = sys.stdout.buffer.write

        if self._legend_xy:
            fx, fy = self._legend_xy
            col = (self.vx + int(fx * (self.vw - 1))) >> 1
            row = (self.vy + int((1.0 - fy) * (self.vh - 1))) >> 2
        else:
            pos_map = {
                'upper right': 'ne', 'upper left': 'nw',
                'lower left': 'sw',  'lower right': 'se',
                'upper center': 'n', 'lower center': 's',
                'center left': 'w',  'center right': 'e',
                'center': 'c'
            }
            pos = pos_map.get(self._legend_loc, 'ne')

            if pos in ('ne', 'se'):
                col = (self.vx // 2) + (self.vw // 2 - 14)
            elif pos in ('nw', 'sw'):
                col = (self.vx // 2) + 1
            elif pos == 'e':
                col = (self.vx // 2) + (self.vw // 2 - 12)
            elif pos == 'w':
                col = (self.vx // 2) + 1
            else:
                col = (self.vx // 2) + (self.vw // 4)

            if pos in ('sw', 'se', 's'):
                row = (self.vy // 4) + (self.vh // 4 - min(len(self._legend), 6) - 1)
            elif pos in ('nw', 'ne', 'n'):
                row = (self.vy // 4) + 0
            else:
                row = (self.vy // 4) + (self.vh // 8)

        if row < 0:
            row = 0
        if col < 0:
            col = 0

        name_color = self._name_color
        for i, (nm, colr) in enumerate(self._legend):
            w("\x1b[{};{}H".format(row + 1 + i, col + 1))
            w(self.cv.sgr(colr))
            w("█")
            w("\x1b[{};{}H".format(row + 1 + i, col + 4))
            w(self.cv.sgr(name_color)); w(nm)

    def _text_immediate(self, x, y, s, color=(220,220,220)):
        w = sys.stdout.buffer.write
        
        px, py = self._wx(float(x)), self._wy(float(y))
        col = px >> 1; row = py >> 2
        
        if row < 0: 
            row = 0
            
        if col < 0: 
            col = 0
        
        w("\x1b[{};{}H".format(row+1, col+1))
        w(self.cv.sgr(color)); w(str(s))

class Scope:
    def __init__(self, plot,
                 vmin=-2.0, vmax=2.0,
                 colors=None,
                 show_zero=True,
                 line=True,
                 dot=False,
                 flush_every=2,
                 px_step=2):
        self.ax = plot
        self.cv = plot.cv

        self.show_zero = bool(show_zero)
        self.style_line = bool(line)
        self.style_dot  = bool(dot)

        self.vmin = float(vmin)
        self.vmax = float(vmax) if vmax > vmin else float(vmin) + 1.0
        self.ax.ylim(self.vmin, self.vmax)

        self._colors_user = colors[:] if colors else None
        self._palette = getattr(self.ax, "_palette", [
            (255,  80,  80), ( 80, 255, 120), ( 80, 160, 255), (255, 200,  80),
            (200,  80, 255), ( 80, 255, 255), (255, 128, 170), (128, 255, 128),
        ])

        self.ax_border_rgb = self.cv.pack_rgb((110,110,110))
        self.ax_grid_rgb   = self.cv.pack_rgb((70,70,70))
        self.ax_zero_rgb   = self.cv.pack_rgb((160,160,160))

        self._nch = 0
        self._prev_y = []
        self._colors = []
        self._ch_names = []

        self._t = 0
        self._info_len = 0
        self._info_row = -1
        self._info_col = -1
        self._static_texts = []
                
        self._xstep = 2 if (px_step is None or px_step < 1) else int(px_step)
        self._flush_every = int(flush_every) if flush_every and flush_every > 0 else 1
        self._frame_ctr = 0
        
        self._clear_view_fast()
        self._precalc_static()
        self.ax._draw_axes()
        self._draw_zero_line_if_needed()
        self.cv.render()
        self._draw_static_text_once()

    def reset(self):
        self._t = 0
        self._prev_y = [None] * (self._nch or 1)
        if self._info_len > 0 and self._info_row >= 0:
            w = sys.stdout.buffer.write
            w("\x1b[{};{}H".format(self._info_row + 1, self._info_col + 1))
            w(" " * self._info_len)
        self._info_len = 0
        self._info_row = -1
        self._info_col = -1
        self._static_texts = []

        self._clear_view_fast()
        self._precalc_static()
        self.ax._draw_axes()
        self._draw_zero_line_if_needed()
        self.cv.render()
        self._draw_static_text_once()

    def set_range(self, vmin, vmax):
        self.vmin = float(vmin)
        self.vmax = float(vmax) if vmax > vmin else float(vmin) + 1.0
        self.ax.ylim(self.vmin, self.vmax)
        self.reset()

    def set_channel_names(self, names):
        self._ch_names = [str(n) for n in names] if names else []

        self.ax.set_legend_items(self._ch_names)
        self.ax._queue_legend()

    def set_colors(self, colors):
        self._colors_user = colors[:] if colors else None
        if self._nch > 0:
            self._ensure_channels(self._nch)
    
    def text(self, x, y, text, color=(200,200,200), align='left'):
        self._static_texts.append((float(x), float(y), str(text), color, align))
        self._redraw_text(self._static_texts[-1])

    def _redraw_text(self, entry):
        x, y, text, color, align = entry
        w  = sys.stdout.buffer.write
        cv = self.cv
        ax = self.ax

        px = ax._wx(float(x));  py = ax._wy(float(y))
        vx, vy, vw, vh = ax.vx, ax.vy, ax.vw, ax.vh
        if px < vx or px > vx+vw-1 or py < vy or py > vy+vh-1:
            return
        col = px >> 1
        row = py >> 2

        if align == 'center':
            col -= len(text) // 2
        elif align == 'right':
            col -= len(text)

        if col < 0: col = 0
        if row < 0: row = 0

        w("\x1b[{};{}H".format(row + 1, col + 1))
        w(cv.sgr(color)); w(text)

    @micropython.native
    def tick(self, values, names=None, info_text=None):
        if not isinstance(values, dict) and names is not None:
            self._ch_names = [str(n) for n in names]

        if isinstance(values, dict):
            if values:
                self._ch_names = [str(k) for k in values]
            vals = list(values.values())
        else:
            vals = tuple(values)

        self._ensure_channels(len(vals))

        vx, vy, vw, vh = self.ax.vx, self.ax.vy, self.ax.vw, self.ax.vh
        vx1, vy1 = vx + vw - 1, vy + vh - 1

        xcol0 = vx + self._t
        xcol1 = min(xcol0 + self._xstep - 1, vx1)

        self._clear_vstripe_v(xcol0, xcol1, vy + 1, vy1 - 1)

        for px in range(xcol0, xcol1 + 1):
            self._restore_static_on_column(px)

        set_px = self.cv.set_px
        _wy = self.ax._wy
        if self.style_line:
            line_px = self._line_px

        for i, v in enumerate(vals):
            py_new = _wy(self._clip_y(v))
            py_prev = self._prev_y[i]
            rgb = self._colors[i]

            if (py_prev is None) or (self._t == 0) or (not self.style_line and self.style_dot):
                set_px(xcol1, py_new, rgb)
            else:
                if self.style_line:
                    x_prev = max(vx, xcol0 - self._xstep)
                    line_px(x_prev, py_prev, xcol1, py_new, rgb)
                if self.style_dot:
                    set_px(xcol1, py_new, rgb)

            self._prev_y[i] = py_new

        self._frame_ctr += 1
        if (self._frame_ctr % self._flush_every) == 0:
            self.cv.render()
            self.ax._queue_legend()
            for _e in self._static_texts:
                self._redraw_text(_e)

        if info_text:
            xw = self.ax.xmin + 0.03 * (self.ax.xmax - self.ax.xmin)
            yw = self.ax.ymax - 0.06 * (self.ax.ymax - self.ax.ymin)
            s = str(info_text)
            px, py = self.ax._wx(float(xw)), self.ax._wy(float(yw))
            col = max(0, px >> 1)
            row = max(0, py >> 2)
            pad = max(0, self._info_len - len(s))
            self._info_len = len(s)
            self._info_row = row
            self._info_col = col
            w = sys.stdout.buffer.write
            w("\x1b[{};{}H".format(row + 1, col + 1))
            w(self.cv.sgr((200, 200, 200))); w(s + " " * pad)

        self._t += self._xstep
        if self._t >= vw:
            self._t = 0
            self._prev_y = [None] * self._nch
            
    @micropython.native
    def _clip_y(self, v):
        return 0.0 if v is None else self.vmin if v < self.vmin else self.vmax if v > self.vmax else float(v)

    def _ensure_channels(self, n):
        if n <= 0: 
            n = 1
        if n == self._nch:
            return

        self._nch = n
        self._prev_y = [None] * n

        cols = []
        if self._colors_user:
            for i in range(n):
                cols.append(self.cv.pack_rgb(self._colors_user[i % len(self._colors_user)]))
        else:
            for i in range(n):
                cols.append(self.cv.pack_rgb(self._palette[i % len(self._palette)]))
        
        self._colors = cols

        if not self._ch_names or len(self._ch_names) != n:
            self._ch_names = ["ch{}".format(i+1) for i in range(n)]

        self.ax.set_legend_colors(self._colors) 
        self.ax.set_legend_items(self._ch_names)
        self.ax._queue_legend()

    def _draw_zero_line_if_needed(self):
        if not self.show_zero or not (self.vmin < 0.0 < self.vmax): 
            return
        
        py = self.ax._wy(0.0)
        rgb = self.ax_zero_rgb
        set_px = self.cv.set_px
        vx, vw = self.ax.vx, self.ax.vw
        for xx in range(vx, vx + vw):
            set_px(xx, py, rgb)

    def _clear_view_fast(self):
        cx0 = self.ax.vx >> 1
        cy0 = self.ax.vy >> 2
        cx1 = (self.ax.vx + self.ax.vw - 1) >> 1
        cy1 = (self.ax.vy + self.ax.vh - 1) >> 2
        self._clear_cells_fast_v(cx0, cy0, cx1, cy1)

    @micropython.viper
    def _clear_vstripe_v(self, x0:int, x1:int, y0:int, y1:int):
        cv = self.cv
        cols = int(cv.cols)
        rows = int(cv.rows)
        W = cols << 1
        H = rows << 2

        xx0 = int(x0);  xx1 = int(x1)
        yy0 = int(y0);  yy1 = int(y1)
        if xx0 < 0:
            xx0 = 0
        if yy0 < 0:
            yy0 = 0
        if xx1 >= W:
            xx1 = W - 1
        if yy1 >= H:
            yy1 = H - 1
        if xx0 > xx1 or yy0 > yy1:
            return

        m = ptr8(cv._mask_b)
        c = ptr32(cv._color_b)

        if ((xx0 & 1) == 0) and ((xx1 & 1) == 1):
            cx0 = xx0 >> 1
            cx1 = xx1 >> 1
            cy0 = yy0 >> 2
            cy1 = yy1 >> 2
            y = cy0
            while y <= cy1:
                base = y * cols
                x = cx0
                while x <= cx1:
                    idx = base + x
                    m[idx] = 0
                    c[idx] = -1
                    x += 1
                y += 1
            return

        xx = xx0
        while xx <= xx1:
            cx = xx >> 1
            xm = xx & 1
            yy = yy0
            while yy <= yy1:
                cy = yy >> 2
                ym = yy & 3
                if ym == 3:
                    bi = 6 if xm == 0 else 7
                else:
                    bi = ym + (3 if xm else 0)
                bit = int(1 << bi)
                idx = cy * cols + cx
                v = int(m[idx]) & int((~bit) & 0xFF)
                m[idx] = v
                if v == 0:
                    c[idx] = -1
                yy += 1
            xx += 1

    def _precalc_static(self):
        ax = self.ax
        self._grid_x_px = set(ax._wx(x) for x in (ax._xticks or []))
        self._grid_y_py = set(ax._wy(y) for y in (ax._yticks or []))
        self._zero_py = ax._wy(0.0) if (self.show_zero and self.vmin < 0 < self.vmax) else None

    def _draw_static_text_once(self):
        self.ax._queue_tick_labels()
        self.ax._queue_labels()
        self.ax._queue_legend()

    @micropython.native
    def _restore_static_on_column(self, px):
        ax, cv = self.ax, self.cv
        vx, vy, vw, vh = ax.vx, ax.vy, ax.vw, ax.vh
        vx1, vy1 = vx + vw - 1, vy + vh - 1
        if px < vx or px > vx1: return

        setp = cv.set_px

        if px == vx or px == vx1:
            for yy in range(vy, vy1 + 1):
                setp(px, yy, self.ax_border_rgb)

        setp(px, vy,  self.ax_border_rgb)
        setp(px, vy1, self.ax_border_rgb)

        if px in self._grid_x_px:
            for yy in range(vy, vy1 + 1):
                setp(px, yy, self.ax_grid_rgb)

        if self._grid_y_py:
            for gy in self._grid_y_py:
                if vy <= gy <= vy1:
                    setp(px, gy, self.ax_grid_rgb)

        if self._zero_py is not None and vy <= self._zero_py <= vy1:
            setp(px, self._zero_py, self.ax_zero_rgb)

    @micropython.viper
    def _clear_cells_fast_v(self, cx0:int, cy0:int, cx1:int, cy1:int):
        cols = int(self.cv.cols)
        m = ptr8(self.cv._mask_b)
        c = ptr32(self.cv._color_b)
        y = cy0
        while y <= cy1:
            base = y * cols
            x = cx0
            while x <= cx1:
                idx = base + x
                m[idx] = 0
                c[idx] = -1
                x += 1
            y += 1

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cv.end()
        return False

    @micropython.native
    def _line_px(self, x0:int, y0:int, x1:int, y1:int, rgb:int):
        setp = self.cv.set_px
        dx = x1 - x0
        sx = 1 if dx >= 0 else -1; dx = dx if dx >= 0 else -dx
        dy = y1 - y0
        sy = 1 if dy >= 0 else -1; dy = -dy if dy < 0 else dy
        err = dx + dy if dy < 0 else dx - dy
        while True:
            setp(x0, y0, rgb)
            if x0 == x1 and y0 == y1: 
                break
            e2 = err << 1
            if e2 >= -dy:
                err -= dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

# @package: ws2812
# @version: 1.3
# @type: device-specific
# @category: display
# @interface: GPIO
# @depends: none
# @platforms: rp2
# @tags: led, neopixel, effect, animation, rainbow, fire
# @author: PlanXLab Development Team

import math
import time
import random
import machine 
import micropython
from array import array
from micropython import const

_EMERG_BUF      = const(256)
_LUT_SIZE       = const(256)
_MASK_8         = const(0xFF)
_MASK_15        = const(0x0F)
_HALF           = const(128)
_MAX_VAL        = const(255)
_WHEEL_T1       = const(85)
_WHEEL_T2       = const(170)

micropython.alloc_emergency_exception_buf(_EMERG_BUF)

_SIN8 = bytearray(_LUT_SIZE)
for i in range(_LUT_SIZE):
    _SIN8[i] = int((math.sin(2*math.pi*i/_LUT_SIZE) + 1.0) * 127.5) & _MASK_8

_DIR16 = (
    ( 256,   0), ( 237,  97), ( 181, 181), (  97, 237),
    (   0, 256), (-97,  237), (-181, 181), (-237,  97),
    (-256,   0), (-237, -97), (-181,-181), ( -97,-237),
    (   0,-256), ( 97, -237), ( 181,-181), ( 237, -97),
)

class Effect:
    __slots__ = ("_ws","_W","_H","_N",
                 "__timer","__state","__effect_id",
                 "__busy","__handler","__last_commit_ms",
                 "_min_frame_ms","__path_x","__path_y","__sched_pending","_scheduled_cb",
                 "__timer_period_ms","__desired_period_ms","__last_step_ms")

    def __init__(self, ws):
        self._ws = ws
        self._W = ws.width
        self._H = ws.height
        self._N = self._W * self._H
        
        self.__timer = None
        self.__timer_period_ms = 0
        
        self.__state = {}
        
        self.__effect_id = 0
        self.__busy = False
        self.__handler = None
        self.__sched_pending = False
        self._scheduled_cb = self._scheduled

        frame_us = 30 * self._N + 80
        self._min_frame_ms = max(2, (frame_us + 999)//1000)
        self.__desired_period_ms = self._min_frame_ms
        self.__last_step_ms = time.ticks_add(time.ticks_ms(), -self._min_frame_ms)
        self.__last_commit_ms = time.ticks_add(time.ticks_ms(), -self._min_frame_ms)
        
        self.__path_x, self.__path_y = self._build_snake_path()

    def _build_snake_path(self):
        W, H = self._W, self._H
        N = W * H
        px = bytearray(N)
        py = bytearray(N)
        i = 0
        for y in range(H):
            if y & 1:
                for x in range(W-1, -1, -1):
                    px[i] = x
                    py[i] = y
                    i += 1
            else:
                for x in range(W):
                    px[i] = x
                    py[i] = y
                    i += 1
        return px, py

    def _install(self, period_s: float):
        self.__effect_id += 1
        self.__handler = None
        self.__sched_pending = False
        if self.__state:
            self.__state.clear()

        period_ms = max(int(period_s*1000), self._min_frame_ms)
        self.__desired_period_ms = period_ms
        self.__last_step_ms = time.ticks_add(time.ticks_ms(), -period_ms)
        
        if self.__timer is None:
            try:
                self.__timer = machine.Timer(-1)
            except Exception:
                shared_timer = getattr(self._ws, "_sc_timer", None)
                if shared_timer is None:
                    return
                self.__timer = shared_timer
        
        tick_ms = self._min_frame_ms
        if self.__timer_period_ms == 0:
            self.__timer.init(period=tick_ms, mode=machine.Timer.PERIODIC,
                              callback=self._timer_cb, hard=True)
            self.__timer_period_ms = tick_ms

    def _timer_cb(self, _t):
        # Hard timer callback: keep IRQ-safe; frame work runs in _scheduled().
        if self.__sched_pending:
            return
        if self.__busy:
            return
        if self.__handler is None:
            return
        self.__sched_pending = True
        try:
            micropython.schedule(self._scheduled_cb, 0)
        except Exception:
            self.__sched_pending = False
        
    def _scheduled(self, _):
        if self.__busy:
            self.__sched_pending = False
            return
        if self.__handler is None:
            self.__sched_pending = False
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self.__last_step_ms) < self.__desired_period_ms:
            self.__sched_pending = False
            return
        self.__last_step_ms = now

        self.__busy = True
        try:
            self.__handler()
        except Exception:
            self.__busy = False
            self.__sched_pending = False
            self.stop()
            raise
        finally:
            self.__busy = False
            self.__sched_pending = False

    def stop(self):
        self.__effect_id += 1
        self.__handler = None
        self.__sched_pending = False
        
        if self.__timer:
            try:
                self.__timer.deinit()
            except Exception:
                pass
            self.__timer_period_ms = 0
        
        if self.__state:
            self.__state.clear()
        time.sleep_ms(1)

    def _try_commit(self, changed: bool):
        if not changed:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self.__last_commit_ms) < self._min_frame_ms:
            return
        self._ws.update(wait=False)
        self.__last_commit_ms = now

    @micropython.native
    def _wheel(self, pos:int):
        pos &= _MASK_8
        if pos < _WHEEL_T1:
            return (_MAX_VAL - pos*3, pos*3, 0)
        if pos < _WHEEL_T2:
            pos -= _WHEEL_T1
            return (0, _MAX_VAL - pos*3, pos*3)
        pos -= _WHEEL_T2
        return (pos*3, 0, _MAX_VAL - pos*3)

    def meteor_rain(self, *, colors=((255,80,0),(0,160,255),(255,0,160)),
                    count=4, trail=6, step=2, glitter_prob=32, speed=0.010):
        self._ws.fill((0,0,0))
        N = self._N
        clen = len(colors)
        count = max(1, min(8, int(count)))
        trail = max(2, min(16, int(trail)))
        dots = []
        for _ in range(count):
            pos = random.getrandbits(16) % N
            col = colors[random.getrandbits(8) % clen]
            dots.append({'pos':pos, 'col':col, 'hist':bytearray(trail), 'head':0, 'hlen':0})
        
        grad = [(int(_MAX_VAL*(i+1)/trail)) for i in range(trail)]
        grad.reverse()
        self._install(speed)
        self.__state['met'] = {'dots': dots, 'trail':trail, 'step':max(1, int(step)), 'grad': grad, 'glit': int(glitter_prob)}
        self.__handler = self._meteor_step_grad

    @micropython.native
    def _meteor_step_grad(self):
        ws = self._ws
        N = self._N
        path_x = self.__path_x
        path_y = self.__path_y
        st = self.__state['met']
        dots = st['dots']
        tr = st['trail']
        step = st['step']
        grad = st['grad']
        gp = st['glit']
        changed = False

        for d in dots:
            pos = (d['pos'] + step) % N
            d['pos'] = pos
            x = path_x[pos]; y = path_y[pos]
            hist = d['hist']
            head = d['head'] - 1
            if head < 0:
                head = tr - 1
            hlen = d['hlen']
            if hlen >= tr:
                old = hist[head]
                ox = path_x[old]; oy = path_y[old]
                ws[ox, oy].value = (0,0,0)
            else:
                hlen += 1
                d['hlen'] = hlen
            hist[head] = pos
            d['head'] = head

            cr, cg, cb = d['col']
            for i in range(hlen):
                hp = (head + i) % tr
                px = hist[hp]
                cx = path_x[px]; cy = path_y[px]
                a = grad[i] if i < tr else 0
                vr = (cr*a)>>8; vg = (cg*a)>>8; vb = (cb*a)>>8
                if (random.getrandbits(8) < gp) and (i < 3):
                    vr = min(_MAX_VAL, vr + 80); vg = min(_MAX_VAL, vg + 80); vb = min(_MAX_VAL, vb + 80)
                ws[cx, cy].value = (vr, vg, vb)

            changed = True

        self._try_commit(changed)

    def plasma(self, *, speed=0.008, kx=4, ky=4, hue_step=3):
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['pl'] = {'t': 0, 'kx': int(kx)&_MASK_8, 'ky': int(ky)&_MASK_8, 'hs': int(hue_step)&_MASK_8}
        self.__handler = self._plasma_step_full

    @micropython.native
    def _plasma_step_full(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        wheel = self._wheel
        st = self.__state['pl']
        t = st['t']
        kx = st['kx']
        ky = st['ky']
        hs = st['hs']
        SIN8 = _SIN8

        for y in range(H):
            sy = (y*ky + t) & _MASK_8
            vy = SIN8[sy]
            row = y * w
            for x in range(W):
                sx = (x*kx + t) & _MASK_8
                hval = (vy + SIN8[sx]) >> 1
                r, g, b = wheel((hval + t) & _MASK_8)
                fb[row + x] = pack(r, g, b)

        st['t'] = (t + hs) & _MASK_8
        ws._fb_dirty = True
        self._try_commit(True)

    def fireworks(self, *, rockets=2, tail_glow=40, gravity=10, drag_num=255, drag_den=260,
                sparks=28, burst_speed=220, life_decay=14, speed=0.012, stagger=4):
        ws = self._ws
        ws.fill((0,0,0))
        rockets = max(1, min(5, int(rockets)))
        sparks = max(8, min(60, int(sparks)))
        drag_den = max(1, int(drag_den))

        S_per = max(8, min(24, int(sparks // rockets)))
        burst = max(180, int(burst_speed - (rockets-1)*10))

        rs = []
        for i in range(rockets):
            rs.append(self._fw_spawn(S=S_per, burst=burst, delay=i*int(stagger), colofs=i*51))

        self._install(speed)
        self.__state['fwm'] = {
            'gy': int(gravity), 'dN': int(drag_num), 'dD': drag_den,
            'decay': max(1, int(life_decay)),
            'tail': max(180, min(245, 180 + int(tail_glow))),
            'rockets': rs
        }
        self.__handler = self._fireworks_multi_step

    def _fw_spawn(self, *, S, burst, delay=0, colofs=0):
        W, H = self._W, self._H
        S = int(S)
        x0 = (W//2) << 8
        y0 = (H-1)  << 8
        vy = -(180 + (random.getrandbits(5)))
        vx = (random.getrandbits(4) - 8)
        return {
            'stage': -1 if delay>0 else 0,
            'sleep': int(delay),
            'rx': x0, 'ry': y0, 'rvx': vx, 'rvy': vy,
            'last_px': -1, 'last_py': -1,
            'ticks': 0, 'max_ticks': 200,
            'explode_line': max(1, self._H//2),
            'S': S, 'burst': int(burst),
            'col': int(colofs) & _MASK_8,
            'alive': 0,
            'px': array('h', [0] * S),
            'py': array('h', [0] * S),
            'pvx': array('h', [0] * S),
            'pvy': array('h', [0] * S),
            'pr': bytearray(S), 'pg': bytearray(S), 'pb': bytearray(S),
            'pl': bytearray(S)
        }

    def _fw_reset(self, r, *, delay=0, colofs=0):
        W, H = self._W, self._H
        r['stage'] = -1 if delay > 0 else 0
        r['sleep'] = int(delay)
        r['rx'] = (W//2) << 8
        r['ry'] = (H-1) << 8
        r['rvx'] = random.getrandbits(4) - 8
        r['rvy'] = -(180 + random.getrandbits(5))
        r['last_px'] = -1
        r['last_py'] = -1
        r['ticks'] = 0
        r['col'] = int(colofs) & _MASK_8
        r['alive'] = 0

    @micropython.native
    def _fireworks_multi_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['fwm']
        gy = st['gy']
        dN = st['dN']
        dD = st['dD']
        decay = st['decay']
        tail = st['tail']
        rockets = st['rockets']
        changed = False

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        for y in range(H):
            row = y * fw
            for x in range(W):
                packed = fb[row + x]
                if packed:
                    pr = (packed >> 16) & _MASK_8
                    pg = (packed >> 24) & _MASK_8
                    pb = (packed >> 8) & _MASK_8
                    pr = (pr * tail) >> 8
                    pg = (pg * tail) >> 8
                    pb = (pb * tail) >> 8
                    fb[row + x] = pack(pr, pg, pb) if (pr or pg or pb) else 0
                    changed = True

        for r in rockets:
            stage = r['stage']

            if stage == -1:
                sl = r['sleep'] - 1
                r['sleep'] = sl
                if sl <= 0:
                    r['stage'] = 0
                continue

            if stage == -2:
                sl = r['sleep'] - 1
                r['sleep'] = sl
                if sl <= 0:
                    self._fw_reset(r, delay=0, colofs=(r['col'] + random.getrandbits(6)) & _MASK_8)
                continue

            if stage == 0:
                rx = r['rx']; ry = r['ry']; rvx = r['rvx']; rvy = r['rvy']

                rvy += gy
                rvx = (rvx * dN) // dD
                rvy = (rvy * dN) // dD
                rx  += rvx; ry += rvy

                px = rx >> 8; py = ry >> 8
                if 0 <= px < W and 0 <= py < H:
                    fb[py * fw + px] = pack(_MAX_VAL, 180, 80)
                    r['last_px'] = px; r['last_py'] = py
                r['rx']=rx; r['ry']=ry; r['rvx']=rvx; r['rvy']=rvy
                r['ticks'] += 1
                changed = True

                if (rvy >= 0) or (py <= r['explode_line']) or (r['ticks'] >= r['max_ticks']):
                    S = r['S']; burst = r['burst']
                    cx, cy = rx, ry
                    pxa = r['px']; pya = r['py']; pvxa = r['pvx']; pvya = r['pvy']
                    pra = r['pr']; pga = r['pg']; pba = r['pb']; pla = r['pl']
                    idx = random.getrandbits(4) & _MASK_15
                    step = 1 if S >= 16 else max(1, 16 // S)
                    for n in range(S):
                        dx, dy = _DIR16[idx & _MASK_15]
                        vx = (dx * burst) >> 8
                        vy = (dy * burst) >> 8
                        hue = (r['col'] + (n * (_LUT_SIZE//S)) + (random.getrandbits(5))) & _MASK_8
                        rr, gg, bb = self._wheel(hue)
                        if (random.getrandbits(3) == 0):
                            rr, gg, bb = _MAX_VAL, _MAX_VAL, _MAX_VAL
                        pxa[n] = cx; pya[n] = cy
                        pvxa[n] = vx; pvya[n] = vy
                        pra[n] = rr; pga[n] = gg; pba[n] = bb; pla[n] = _MAX_VAL
                        idx += step
                    r['alive'] = S
                    r['stage'] = 1
                    r['last_px'] = -1; r['last_py'] = -1
                    continue

            else:
                n_parts = r['alive']
                pxa = r['px']; pya = r['py']; pvxa = r['pvx']; pvya = r['pvy']
                pra = r['pr']; pga = r['pg']; pba = r['pb']; pla = r['pl']
                write = 0
                for i in range(n_parts):
                    x = pxa[i]; y = pya[i]
                    vx = pvxa[i]; vy = pvya[i]
                    rr = pra[i]; gg = pga[i]; bb = pba[i]; life = pla[i]

                    vy += gy
                    vx = (vx * dN) // dD
                    vy = (vy * dN) // dD
                    x  += vx; y += vy

                    px = x>>8; py = y>>8
                    if 0 <= px < W and 0 <= py < H:
                        vr = (rr*life)>>8; vg = (gg*life)>>8; vb = (bb*life)>>8
                        if (random.getrandbits(4)==0):
                            vr = _MAX_VAL if vr+64>_MAX_VAL else vr+64
                            vg = _MAX_VAL if vg+64>_MAX_VAL else vg+64
                            vb = _MAX_VAL if vb+64>_MAX_VAL else vb+64
                        pidx = py * fw + px
                        old = fb[pidx]
                        if old:
                            orr = (old >> 16) & _MASK_8
                            ogg = (old >> 24) & _MASK_8
                            obb = (old >> 8) & _MASK_8
                            vr = _MAX_VAL if vr + orr > _MAX_VAL else vr + orr
                            vg = _MAX_VAL if vg + ogg > _MAX_VAL else vg + ogg
                            vb = _MAX_VAL if vb + obb > _MAX_VAL else vb + obb
                        fb[pidx] = pack(vr, vg, vb)

                    life -= decay
                    if life > 8:
                        pxa[write] = x; pya[write] = y
                        pvxa[write] = vx; pvya[write] = vy
                        pra[write] = rr; pga[write] = gg; pba[write] = bb; pla[write] = life
                        write += 1
                r['alive'] = write

                changed = True

                if write == 0:
                    r['stage'] = -2
                    r['sleep'] = (random.getrandbits(3) & 7) + 8

        ws._fb_dirty = changed
        self._try_commit(changed)

    def campfire(self, *, cooling=55, sparking=120, speed=0.010, ember_particles=20, ember_decay=18, base_rows=2):
        ws = self._ws
        ws.fill((0,0,0))
        W, H = self._W, self._H
        N = W*H
        base_rows = max(1, min(base_rows, H))
        ember_particles = max(0, min(N, int(ember_particles)))
        ex = bytearray(ember_particles)
        ey = bytearray(ember_particles)
        ev = bytearray(ember_particles)
        for i in range(ember_particles):
            ex[i] = random.getrandbits(8) % W
            ey[i] = H-1-(random.getrandbits(2)%base_rows)
            ev[i] = 220

        self._install(speed)
        self.__state['cf3'] = {
            'heat': bytearray(N),
            'cool': int(cooling),
            'spark': int(sparking),
            'W': W, 'H': H, 'N': N,
            'ex': ex, 'ey': ey, 'ev': ev,
            'e_dec': int(ember_decay),
            'rows': base_rows
        }
        self.__handler = self._campfire_step2

    @micropython.native
    def _campfire_step2(self):
        ws = self._ws
        st = self.__state['cf3']
        heat = st['heat']
        W = st['W']
        H = st['H']; N = st['N']
        cool = st['cool']
        spark = st['spark']
        rows = st['rows']
        changed = False

        base = (cool * 10) // N + 2
        for i in range(N):
            v = heat[i] - (random.getrandbits(8) % base)
            heat[i] = v if v > 0 else 0

        for i in range(N-1, 1, -1):
            heat[i] = (heat[i-1] + heat[i-2] + heat[i-2]) // 3

        for x in range(W):
            if random.getrandbits(8) < spark:
                idx = random.getrandbits(8) % rows
                i = x + (H-1-idx)*W
                nv = heat[i] + (random.getrandbits(7) + 80)
                heat[i] = _MAX_VAL if nv>_MAX_VAL else nv

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        k = 0
        for y in range(H):
            row = y * fw
            for x in range(W):
                t = heat[k]; k += 1
                if t <= _WHEEL_T1:
                    fb[row + x] = pack(t*3, t>>2, 0)
                elif t <= _WHEEL_T2:
                    tt = t - _WHEEL_T1
                    fb[row + x] = pack(_MAX_VAL, 64 + (tt*3)//4, 0)
                else:
                    tt = t - _WHEEL_T2
                    g2 = _HALF + (tt>>1)
                    b2 = tt << 1
                    fb[row + x] = pack(_MAX_VAL, g2 if g2<_MAX_VAL else _MAX_VAL, b2 if b2<_MAX_VAL else _MAX_VAL)

        ws._fb_dirty = True
        changed = True

        ex = st['ex']
        ey = st['ey']
        ev = st['ev']
        e_d = st['e_dec']
        for i in range(len(ex)):
            x = ex[i]
            y = ey[i]
            v = ev[i]
            if random.getrandbits(2) and y > 0:
                y -= 1
                if random.getrandbits(1):
                    x = (x + (1 if random.getrandbits(1) else -1)) % W

            v -= e_d
            if v <= 0 or y <= 0:
                x = random.getrandbits(8) % W
                y = H-1 - (random.getrandbits(2) % rows)
                v = 200 + (random.getrandbits(6))

            idx = y * fw + x
            packed = fb[idx]
            r = ((packed >> 16) & _MASK_8) + v
            g = ((packed >> 24) & _MASK_8) + (v>>1)
            if r>_MAX_VAL: r=_MAX_VAL
            if g>_MAX_VAL: g=_MAX_VAL
            fb[idx] = pack(r, g, (packed >> 8) & _MASK_8)
            ex[i] = x
            ey[i] = y
            ev[i] = v
            changed = True

        self._try_commit(changed)

    def ripple(self, *, speed=0.010, wavelength=10, phase_step=3, center=None):
        W, H = self._W, self._H
        if center is None:
            cx, cy = W//2, H//2
        else:
            cx, cy = center

        k = max(1, int(wavelength))
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['rip'] = {'t': 0, 'cx': int(cx), 'cy': int(cy), 'k': k, 'step': int(phase_step)&_MASK_8}
        self.__handler = self._ripple_step

    @micropython.native
    def _ripple_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        wheel = self._wheel
        st = self.__state['rip']
        t = st['t'] & _MASK_8
        cx = st['cx']; cy = st['cy']; k = st['k']
        for y in range(H):
            dy = y - cy
            ady = -dy if dy < 0 else dy
            row = y * w
            for x in range(W):
                dx = x - cx
                adx = -dx if dx < 0 else dx
                d = (adx + ady) * k
                h = (t + d) & _MASK_8
                r, g, b = wheel(h)
                fb[row + x] = pack(r, g, b)
        st['t'] = (t + st['step']) & _MASK_8
        ws._fb_dirty = True
        self._try_commit(True)
 
    def matrix_rain(self, *, speed=0.012, spawn_prob=55, decay=28, head_boost=255, trail_boost=120):
        W, H = self._W, self._H
        N = W*H
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['mx'] = {
            'W': W, 'H': H, 'N': N,
            'buf': bytearray(N),
            'y': [- (random.getrandbits(3) & 7) for _ in range(W)],
            'spd': [1 + (random.getrandbits(1)&1) for _ in range(W)],
            'tick': [0]*W,
            'spawn': int(spawn_prob), 'dec': int(decay),
            'hboost': int(head_boost), 'tboost': int(trail_boost)
        }
        self.__handler = self._matrix_rain_step

    @micropython.native
    def _matrix_rain_step(self):
        ws = self._ws
        st = self.__state['mx']
        W = st['W']
        H = st['H']
        N = st['N']
        buf = st['buf']
        yv = st['y']
        spd = st['spd']
        tick = st['tick']
        spawn = st['spawn']
        dec = st['dec']
        hb = st['hboost']
        tb = st['tboost']
  
        for x in range(W):
            t = tick[x] + 1
            if t >= spd[x]:
                tick[x] = 0
                y = yv[x] + 1
                if y >= H + (random.getrandbits(3)&3):
                    y = - (random.getrandbits(3)&7)
                    spd[x] = 1 + (random.getrandbits(1)&1)
                yv[x] = y
                if 0 <= y < H:
                    i = x + y*W
                    v = hb
                    if v > _MAX_VAL: v = _MAX_VAL
                    buf[i] = v
                    if y+1 < H:
                        j = x + (y+1)*W
                        nv = buf[j] + tb
                        buf[j] = _MAX_VAL if nv>_MAX_VAL else nv
                elif (random.getrandbits(8) < spawn):
                    yv[x] = - (random.getrandbits(3)&7)
            else:
                tick[x] = t

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        k = 0
        for yy in range(H):
            row = yy * fw
            for xx in range(W):
                v = buf[k]
                if v > 0:
                    nv = v - dec
                    buf[k] = nv if nv > 0 else 0
                    fb[row + xx] = pack(v >> 3, v, v >> 4)
                else:
                    fb[row + xx] = 0
                k += 1
        ws._fb_dirty = True
        self._try_commit(True)

    def neon_checkerboard(self, *, speed=0.010, tile=4, pulse_step=3, hue_shift=64, edge_boost=80):
        tile = max(1, int(tile))
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['neo'] = {
            't': 0, 'tile': tile, 'step': int(pulse_step)&_MASK_8,
            'hshift': int(hue_shift)&_MASK_8, 'eboost': int(edge_boost)&_MASK_8
        }
        self.__handler = self._neon_checkerboard_step

    @micropython.native
    def _neon_checkerboard_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        wheel = self._wheel
        st = self.__state['neo']
        t = st['t'] & _MASK_8
        tile= st['tile']
        step = st['step']
        hsh = st['hshift']
        eboost = st['eboost']
        SIN8= _SIN8
        tile_m1 = tile - 1
        edge_denom = max(1, tile_m1 * 2)

        for y in range(H):
            ty = y // tile
            by = y - ty*tile
            dy_edge = by if by < tile_m1 - by else tile_m1 - by
            row = y * w
            for x in range(W):
                tx = x // tile
                bx = x - tx*tile
                dx_edge = bx if bx < tile_m1 - bx else tile_m1 - bx

                parity = (tx ^ ty) & 1
                hue = (t + (hsh if parity else 0)) & _MASK_8

                pulse = SIN8[(t + (parity*32)) & _MASK_8]
                edge = dx_edge if dx_edge < dy_edge else dy_edge
                boost = (eboost * (tile_m1 - edge) * 2) // edge_denom
                v = pulse + boost
                if v > _MAX_VAL: v = _MAX_VAL

                r, g, b = wheel(hue)
                fb[row + x] = pack((r*v)>>8, (g*v)>>8, (b*v)>>8)

        st['t'] = (t + step) & _MASK_8
        ws._fb_dirty = True
        self._try_commit(True)

    def petal_vortex(self, *, speed=0.010, petals=6, spin_step=3, radial=3, contrast=200):
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['pet'] = {
            't': 0, 'k': max(3, int(petals)),
            'spin': int(spin_step)&_MASK_8, 'rad': max(1,int(radial)),
            'ctr': int(contrast)&_MASK_8
        }
        self.__handler = self._petal_vortex_step

    @micropython.native
    def _petal_vortex_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        wheel = self._wheel
        st = self.__state['pet']
        t = st['t'] & _MASK_8
        k = st['k']
        rad = st['rad']
        ctr = st['ctr']
        SIN8 = _SIN8

        cx = W//2
        cy = H//2

        s = int(SIN8[t]) - _HALF
        c = int(SIN8[(t + 64) & _MASK_8]) - _HALF

        for y in range(H):
            dy = y - cy
            row = y * w
            for x in range(W):
                dx = x - cx
                xr = (dx*c - dy*s) >> 7
                yr = (dx*s + dy*c) >> 7

                a = SIN8[(xr * k + t) & _MASK_8]
                b = SIN8[(yr * k + t) & _MASK_8]
                m = (a * b) >> 8

                adx = -dx if dx < 0 else dx
                ady = -dy if dy < 0 else dy
                rv  = (adx + ady) * rad
                rv  = _MAX_VAL if rv > _MAX_VAL else rv

                v = m + ((ctr * (_MAX_VAL - rv)) >> 8)
                if v > _MAX_VAL: v = _MAX_VAL

                hue = (t + m) & _MASK_8
                r, g, b = wheel(hue)
                fb[row + x] = pack((r*v)>>8, (g*v)>>8, (b*v)>>8)

        st['t'] = (t + st['spin']) & _MASK_8
        ws._fb_dirty = True
        self._try_commit(True)

    def spark_stream(self, *, speed=0.010, emitters=3, spawn_rate=3, max_sparks=40,
                    base_hue=150, hue_jitter=20, fade=220, gravity=6, swirl=10):
        W = self._W
        emitters = max(1, min(5, int(emitters)))
        max_sparks = max(1, min(96, int(max_sparks)))
        pos = [ (i+1)*W//(emitters+1) for i in range(emitters) ]
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['ssk'] = {
            'pos': pos, 'sr': max(1, int(spawn_rate)), 'max': max_sparks,
            'bh': int(base_hue)&_MASK_8, 'hj': int(hue_jitter)&_MASK_8,
            'fade': int(fade)&_MASK_8, 'g': int(gravity), 'sw': int(swirl),
            'x': array('h', [0] * max_sparks),
            'y': array('h', [0] * max_sparks),
            'vx': array('h', [0] * max_sparks),
            'vy': array('h', [0] * max_sparks),
            'hue': bytearray(max_sparks),
            'life': bytearray(max_sparks),
            'phi': bytearray(max_sparks),
            'cnt': 0
        }
        self.__handler = self._spark_stream_step

    @micropython.native
    def _spark_stream_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['ssk']
        fade = st['fade']
        g = st['g']
        sw = st['sw']
        xs = st['x']; ys = st['y']
        vxs = st['vx']; vys = st['vy']
        hues = st['hue']; lifes = st['life']; phis = st['phi']
        cnt = st['cnt']
        changed = False

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        for y in range(H):
            row = y * fw
            for x in range(W):
                packed = fb[row + x]
                if packed:
                    r = (packed >> 16) & _MASK_8
                    g0 = (packed >> 24) & _MASK_8
                    b = (packed >> 8) & _MASK_8
                    fb[row + x] = pack((r*fade)>>8, (g0*fade)>>8, (b*fade)>>8)

        tries = st['sr']
        emit = st['pos']
        bh = st['bh']
        hj = st['hj']
        while tries > 0 and cnt < st['max']:
            ex = emit[random.getrandbits(8) % len(emit)]
            xs[cnt] = ex << 8
            ys[cnt] = (H - 1) << 8
            vxs[cnt] = (random.getrandbits(4) - 8) * 20
            vys[cnt] = -(140 + random.getrandbits(6))
            hues[cnt] = (bh + (random.getrandbits(7) % (hj+1))) & _MASK_8
            lifes[cnt] = _MAX_VAL
            phis[cnt] = random.getrandbits(8)
            cnt += 1
            tries -= 1

        write = 0
        for i in range(cnt):
            x = xs[i]; y = ys[i]
            vx = vxs[i]; vy = vys[i]
            hue = hues[i]; life = lifes[i]; phi = phis[i]
            phi = (phi + 11) & _MASK_8
            wig = phi if phi < _HALF else (_MAX_VAL - phi)
            vx += ((wig - 64) * sw) >> 6

            vy += g

            x += vx; y += vy

            px = x>>8; py = y>>8
            if 0 <= px < W and 0 <= py < H:
                r, g0, b = self._wheel(hue)
                r = (r*life)>>8; g0 = (g0*life)>>8; b = (b*life)>>8
                pidx = py * fw + px
                existing = fb[pidx]
                nr = ((existing >> 16) & _MASK_8) + r
                ng = ((existing >> 24) & _MASK_8) + g0
                nb = ((existing >> 8) & _MASK_8) + b
                if nr>_MAX_VAL: nr=_MAX_VAL
                if ng>_MAX_VAL: ng=_MAX_VAL
                if nb>_MAX_VAL: nb=_MAX_VAL
                fb[pidx] = pack(nr, ng, nb)
                ws._fb_dirty = True
                changed = True

            life -= 14
            if life > 24 and (py >= -1):
                xs[write] = x; ys[write] = y
                vxs[write] = vx; vys[write] = vy
                hues[write] = hue; lifes[write] = life; phis[write] = phi
                write += 1

        st['cnt'] = write
        self._try_commit(changed)

    def horizontal_wave(self, *, speed=0.008, wavelength=20, phase_step=4, brightness_wave=True):
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['hw'] = {
            't': 0,
            'wl': max(5, int(wavelength)),
            'step': int(phase_step) & _MASK_8,
            'bw': brightness_wave
        }
        self.__handler = self._horizontal_wave_step

    @micropython.native
    def _horizontal_wave_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        st = self.__state['hw']
        t = st['t']
        wl = st['wl']
        bw = st['bw']
        half_h = H >> 1

        for x in range(W):
            hue = (t + (x * _LUT_SIZE // wl)) & _MASK_8
            r, g, b = self._wheel(hue)

            if bw:
                for y in range(H):
                    dy = y - half_h
                    if dy < 0:
                        dy = -dy
                    v = _MAX_VAL - (dy * 24)
                    if v < 60:
                        v = 60
                    fb[y * w + x] = pack((r*v)>>8, (g*v)>>8, (b*v)>>8)
            else:
                px = pack(r, g, b)
                for y in range(H):
                    fb[y * w + x] = px

        st['t'] = (t + st['step']) & _MASK_8
        ws._fb_dirty = True
        self._try_commit(True)

    def comet_horizontal(self, *, count=3, speed=0.008, trail=25, direction="left",
                        colors=None, fade=230):
        W = self._W
        H = self._H
        count = max(1, min(8, int(count)))
        trail = max(5, min(W//2, int(trail)))
        fade = max(200, min(255, int(fade)))
        
        if colors is None:
            colors = []
            for i in range(count):
                colors.append(self._wheel((i * _LUT_SIZE // count) & _MASK_8))
        
        comets = []
        for i in range(count):
            x = (i * W // count) + (random.getrandbits(6) % (W // count))
            col = colors[i % len(colors)]
            comets.append([x << 8, col])
        
        dx = -256 if direction == "left" else 256
        
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['ch'] = {
            'comets': comets,
            'dx': dx,
            'trail': trail,
            'fade': fade,
            'W8': W << 8
        }
        self.__handler = self._comet_horizontal_step

    @micropython.native
    def _comet_horizontal_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['ch']
        comets = st['comets']
        dx = st['dx']
        fade = st['fade']
        W8 = st['W8']

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        for y in range(H):
            row = y * fw
            for x in range(W):
                packed = fb[row + x]
                if packed:
                    r = (packed >> 16) & _MASK_8
                    g = (packed >> 24) & _MASK_8
                    b = (packed >> 8) & _MASK_8
                    fb[row + x] = pack((r*fade)>>8, (g*fade)>>8, (b*fade)>>8)

        for c in comets:
            x8 = c[0]
            r, g, b = c[1]
            
            x8 += dx
            if x8 < 0:
                x8 += W8
            elif x8 >= W8:
                x8 -= W8
            c[0] = x8
            
            px = x8 >> 8
            packed = pack(r, g, b)
            for y in range(H):
                fb[y * fw + px] = packed

        ws._fb_dirty = True
        self._try_commit(True)

    def scrolling_gradient(self, *, speed=0.006, colors=None, segment_width=40):
        W = self._W
        
        if colors is None:
            colors = [
                (255, 0, 0), (255, 128, 0), (255, 255, 0),
                (0, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 255)
            ]
        
        clen = len(colors)
        total_w = segment_width * clen
        
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['sg'] = {
            'colors': colors,
            'clen': clen,
            'segw': segment_width,
            'total': total_w,
            'offset': 0
        }
        self.__handler = self._scrolling_gradient_step

    @micropython.native
    def _scrolling_gradient_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        w = ws._fb_width
        pack = ws._pack_grb
        st = self.__state['sg']
        colors = st['colors']
        clen = st['clen']
        segw = st['segw']
        total = st['total']
        offset = st['offset']

        for x in range(W):
            pos = (x + offset) % total
            seg_idx = pos // segw
            seg_pos = pos % segw
            
            c1 = colors[seg_idx]
            c2 = colors[(seg_idx + 1) % clen]
            
            t = (seg_pos * _LUT_SIZE) // segw
            inv_t = _LUT_SIZE - t
            
            r = (c1[0] * inv_t + c2[0] * t) >> 8
            g = (c1[1] * inv_t + c2[1] * t) >> 8
            b = (c1[2] * inv_t + c2[2] * t) >> 8
            
            packed = pack(r, g, b)
            for y in range(H):
                fb[y * w + x] = packed

        ws._fb_dirty = True
        st['offset'] = (offset + 1) % total
        self._try_commit(True)

    def audio_bars(self, *, speed=0.015, bars=16, decay=25, attack=80,
                  color_mode="gradient", base_color=(0, 255, 128)):
        W = self._W
        H = self._H
        bars = max(4, min(W//2, int(bars)))
        bar_width = W // bars
        
        heights = [0] * bars
        targets = [0] * bars
        
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['ab'] = {
            'bars': bars,
            'bw': bar_width,
            'heights': heights,
            'targets': targets,
            'decay': max(1, min(50, int(decay))),
            'attack': max(1, min(100, int(attack))),
            'mode': color_mode,
            'base': base_color
        }
        self.__handler = self._audio_bars_step

    @micropython.native
    def _audio_bars_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        st = self.__state['ab']
        bars = st['bars']
        bw = st['bw']
        heights = st['heights']
        targets = st['targets']
        decay = st['decay']
        attack = st['attack']
        mode = st['mode']
        base = st['base']

        for i in range(bars):
            if random.getrandbits(7) < attack:
                targets[i] = (random.getrandbits(8) * H) >> 8

        for i in range(bars):
            h = heights[i]
            t = targets[i]
            if h < t:
                h += (t - h + 3) >> 2
                if h > t:
                    h = t
            else:
                h -= decay
                if h < 0:
                    h = 0
            heights[i] = h
            targets[i] = (targets[i] * 240) >> 8

        ws.fill((0, 0, 0))
        
        for i in range(bars):
            h = heights[i]
            x_start = i * bw
            x_end = x_start + bw - 1
            if x_end >= W:
                x_end = W - 1
            
            for y in range(H - 1, H - 1 - h, -1):
                if y < 0:
                    break
                    
                if mode == "gradient":
                    level = H - 1 - y
                    if level < H // 3:
                        r, g, b = 0, 255, 0
                    elif level < (H * 2) // 3:
                        r, g, b = 255, 255, 0
                    else:
                        r, g, b = 255, 0, 0
                else:
                    r, g, b = base
                
                packed = pack(r, g, b)
                for x in range(x_start, x_end + 1):
                    fb[y * fw + x] = packed

        ws._fb_dirty = True
        self._try_commit(True)

    def night_sky(self, *, speed=0.045, stars=40, twinkle_step=3,
                  base=(0, 0, 6), shooting=True):
        N = self._N
        stars = max(4, min(N, int(stars)))
        pos = bytearray(stars)
        phase = bytearray(stars)
        rate = bytearray(stars)
        tone = bytearray(stars)
        used = bytearray(N)
        for i in range(stars):
            p = random.getrandbits(8) % N
            tries = 0
            while used[p] and tries < 8:
                p = (p + 17) % N
                tries += 1
            used[p] = 1
            pos[i] = p
            phase[i] = random.getrandbits(8)
            rate[i] = 1 + (random.getrandbits(2) & 3)
            tone[i] = random.getrandbits(8)

        self._ws.fill(base)
        self._install(speed)
        self.__state['sky'] = {
            'pos': pos, 'phase': phase, 'rate': rate, 'tone': tone,
            'base': base, 'step': int(twinkle_step) & _MASK_8,
            'shoot': 1 if shooting else 0, 'sx': -1, 'sy': 0, 'life': 0
        }
        self.__handler = self._night_sky_step

    @micropython.native
    def _night_sky_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['sky']
        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        br, bg, bb = st['base']

        base_px = pack(br, bg, bb)
        for y in range(H):
            row = y * fw
            for x in range(W):
                fb[row + x] = base_px

        pos = st['pos']
        phase = st['phase']
        rate = st['rate']
        tone = st['tone']
        step = st['step']
        path_x = self.__path_x
        path_y = self.__path_y

        for i in range(len(pos)):
            ph = (phase[i] + step + rate[i]) & _MASK_8
            phase[i] = ph
            amp = _SIN8[ph]
            if amp < 35:
                continue
            amp = 38 + ((amp * 217) >> 8)
            p = pos[i]
            x = path_x[p]
            y = path_y[p]
            t = tone[i]
            if t < 86:
                r = amp
                g = amp
                b = _MAX_VAL if amp + 36 > _MAX_VAL else amp + 36
            elif t < 172:
                r = _MAX_VAL if amp + 24 > _MAX_VAL else amp + 24
                g = amp
                b = amp - (amp >> 4)
            else:
                r = amp
                g = _MAX_VAL if amp + 16 > _MAX_VAL else amp + 16
                b = amp
            fb[y * fw + x] = pack(r, g, b)

        if st['shoot']:
            life = st['life']
            sx = st['sx']
            sy = st['sy']
            if life <= 0:
                if random.getrandbits(8) < 10:
                    sx = random.getrandbits(8) % W
                    sy = random.getrandbits(3) % max(1, H//2)
                    life = 6
            else:
                for k in range(4):
                    x = sx - k
                    y = sy + k
                    if 0 <= x < W and 0 <= y < H:
                        v = _MAX_VAL - k * 48
                        fb[y * fw + x] = pack(v, v, _MAX_VAL)
                sx += 1
                sy += 1
                life -= 1
            st['sx'] = sx
            st['sy'] = sy
            st['life'] = life

        ws._fb_dirty = True
        self._try_commit(True)

    def scanner(self, *, speed=0.006, width=4, color=(255, 0, 0), fade=220, bounce=True):
        W = self._W
        
        self._ws.fill((0,0,0))
        self._install(speed)
        self.__state['scan'] = {
            'pos': 0,
            'dir': 1,
            'width': max(2, min(W//4, int(width))),
            'color': color,
            'fade': max(200, min(255, int(fade))),
            'bounce': bounce
        }
        self.__handler = self._scanner_step

    @micropython.native
    def _scanner_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['scan']
        pos = st['pos']
        d = st['dir']
        width = st['width']
        r, g, b = st['color']
        fade = st['fade']
        bounce = st['bounce']

        fb = ws._fb
        fw = ws._fb_width
        pack = ws._pack_grb
        for y in range(H):
            row = y * fw
            for x in range(W):
                packed = fb[row + x]
                if packed:
                    pr = (packed >> 16) & _MASK_8
                    pg = (packed >> 24) & _MASK_8
                    pb = (packed >> 8) & _MASK_8
                    fb[row + x] = pack((pr*fade)>>8, (pg*fade)>>8, (pb*fade)>>8)

        half_w = width >> 1
        for i in range(width):
            x = pos - half_w + i
            if 0 <= x < W:
                dist = i - half_w
                if dist < 0:
                    dist = -dist
                v = _MAX_VAL - (dist * _MAX_VAL // half_w)
                if v < 0:
                    v = 0
                vr = (r * v) >> 8
                vg = (g * v) >> 8
                vb = (b * v) >> 8
                packed = pack(vr, vg, vb)
                for y in range(H):
                    fb[y * fw + x] = packed

        pos += d
        if bounce:
            if pos >= W - half_w:
                pos = W - half_w - 1
                d = -1
            elif pos < half_w:
                pos = half_w
                d = 1
            st['dir'] = d
        else:
            if pos >= W:
                pos = 0
            elif pos < 0:
                pos = W - 1
        st['pos'] = pos

        ws._fb_dirty = True
        self._try_commit(True)

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

from . import (
    math,
    utime,
    urandom,
    machine, 
    micropython,
    ext
)

micropython.alloc_emergency_exception_buf(256)

_SIN8 = bytearray(256)
for i in range(256):
    # (sin(θ)+1)*127.5 -> 0..255
    _SIN8[i] = int((math.sin(2*math.pi*i/256) + 1.0) * 127.5) & 0xFF

# 16-direction unit vector (normalized × 256). Velocity = (dx*burst)>>8, (dy*burst)>>8
_DIR16 = (
    ( 256,   0), ( 237,  97), ( 181, 181), (  97, 237),
    (   0, 256), (-97,  237), (-181, 181), (-237,  97),
    (-256,   0), (-237, -97), (-181,-181), ( -97,-237),
    (   0,-256), ( 97, -237), ( 181,-181), ( 237, -97),
)

class WS2812Matrix_Effect:
    __slots__ = ("_ws","_W","_H","_N",
                 "__timer","__state","__effect_id",
                 "__busy","__handler","__last_commit_ms",
                 "_min_frame_ms","__path","__sched_pending")

    def __init__(self, ws):
        self._ws = ws
        self._W = ws.width
        self._H = ws.height
        self._N = self._W * self._H
        self.__timer = None
        self.__state = {}
        self.__effect_id = 0
        self.__busy = False
        self.__handler = None
        self.__sched_pending = False

        frame_us = 30 * self._N + 80
        self._min_frame_ms = max(2, (frame_us + 999)//1000)
        self.__last_commit_ms = utime.ticks_ms() - self._min_frame_ms
        self.__path = self.__build_snake_path()

    def __build_snake_path(self):
        W, H = self._W, self._H
        path = []
        app = path.append
        for y in range(H):
            if y & 1:
                for x in range(W-1, -1, -1):
                    app((x, y))
            else:
                for x in range(W):
                    app((x, y))
        return path

    def __install(self, period_s: float, handler):
        self.stop()
        period_ms = max(int(period_s*1000), self._min_frame_ms)
        self.__effect_id += 1
        eid = self.__effect_id
        self.__handler = handler
        self.__sched_pending = False

        def __cb(_t):
            if eid != self.__effect_id or self.__busy or self.__sched_pending:
                return
            self.__sched_pending = True
            try:
                micropython.schedule(self.__scheduled, 0)
            except Exception:
                self.__sched_pending = False

        tm = machine.Timer(-1)
        tm.init(period=period_ms, mode=machine.Timer.PERIODIC, callback=__cb)
        self.__timer = tm

    @micropython.native
    def __scheduled(self, _):
        if self.__busy:
            self.__sched_pending = False
            return
        if self.__handler is None:
            self.__sched_pending = False
            return

        self.__busy = True
        try:
            self.__handler()
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
            finally:
                self.__timer = None

    def __try_commit(self, changed: bool):
        if not changed:
            return
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self.__last_commit_ms) < self._min_frame_ms:
            return
        self._ws.update(wait=False)
        self.__last_commit_ms = now

    @micropython.native
    def __wheel(self, pos:int):
        pos &= 255
        if pos < 85:
            return (255 - pos*3, pos*3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos*3, pos*3)
        pos -= 170
        return (pos*3, 0, 255 - pos*3)

    def sparkle(self, *, base=(0,0,0),
                sparkle_color=(230, 245, 255),
                spawn_per_tick=10, decay_step=28,
                max_active=220, decay_budget_per_tick=72,
                bloom_strength=64, bloom_neighbors=2,
                speed=0.010):
        ws = self._ws
        ws.fill(base)
        nb = ((-1,-1), (0,-1), (1,-1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        self.__state['tw'] = {
            'base': base, 'col': sparkle_color,
            'active': [],
            'spawn': int(spawn_per_tick),
            'dec':   int(decay_step),
            'maxa':  int(max_active),
            'budget':int(decay_budget_per_tick),
            'bloom': int(bloom_strength),
            'bloom_n': int(bloom_neighbors),
            'nb': nb,
            'rr': 0
        }
        self.__install(speed, self.__sparkle_step)

    @micropython.native
    def __sparkle_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['tw']
        base = st['base']
        col = st['col']
        a = st['active']
        dec = st['dec']
        maxa= st['maxa']
        bud = st['budget']
        rr = st['rr']
        bloom = st['bloom']
        bloom_n = st['bloom_n']
        nb = st['nb']

        changed = False
        n = len(a)
        if n:
            end = rr + bud
            i = rr
            while i < end and n > 0:
                idx = i % n
                e = a[idx]
                x, y, r, g, b, v, phi, nbi = e
                phi = (phi + 17) & 0xFF
                tw  = phi if phi < 128 else (255 - phi)
                amp = (v * (tw + 128)) >> 8 
                if amp > 0:
                    ws[x, y].value = ((r*amp)>>8, (g*amp)>>8, (b*amp)>>8)
                    for k in range(bloom_n):
                        dn = nb[(nbi + k) & 7]
                        nx = x + dn[0]; ny = y + dn[1]
                        if 0 <= nx < W and 0 <= ny < H:
                            bamp = (amp * bloom) >> 8
                            if bamp:
                                br, bg, bb = ws[nx, ny].value
                                br = br + ((r*bamp)>>10);  bg = bg + ((g*bamp)>>10);  bb = bb + ((b*bamp)>>10)
                                ws[nx, ny].value = (br if br<255 else 255,
                                                    bg if bg<255 else 255,
                                                    bb if bb<255 else 255)
                    e[7] = (nbi + bloom_n) & 7
                    e[6] = phi
                    nv = v - dec
                    if nv <= 0:
                        ws[x, y].value = base
                        last = a[-1]; a[idx] = last; a.pop(); n -= 1; i -= 1
                    else:
                        e[5] = nv
                else:
                    ws[x, y].value = base
                    last = a[-1]; a[idx] = last; a.pop(); n -= 1; i -= 1
                i += 1
            st['rr'] = i % max(1, n)
            changed = True

        sp = st['spawn']
        cr, cg, cb = col
        while sp > 0 and len(a) < maxa:
            x = urandom.getrandbits(8) % W
            y = urandom.getrandbits(8) % H
            tint = (urandom.getrandbits(3) - 3)
            rr = min(255, max(0, cr + tint))
            gg = min(255, max(0, cg + (tint>>1)))
            bb = min(255, max(0, cb + (tint<<1)))
            ws[x, y].value = (rr, gg, bb)
            a.append([x, y, rr, gg, bb, 255, urandom.getrandbits(8), urandom.getrandbits(8)&7])
            sp -= 1
            changed = True

        self.__try_commit(changed)

    def meteor_rain(self, *, colors=((255,80,0),(0,160,255),(255,0,160)),
                    count=6, trail=9, step=2, glitter_prob=32, speed=0.010):
        self._ws.fill((0,0,0))
        N = self._N
        clen = len(colors)
        dots = []
        for _ in range(count):
            pos = urandom.getrandbits(16) % N
            col = colors[urandom.getrandbits(8) % clen]
            dots.append({'pos':pos, 'col':col, 'hist':[]})
        
        grad = [(int(255*(i+1)/trail)) for i in range(trail)]
        grad.reverse()
        self.__state['met'] = {'dots': dots, 'trail':int(trail), 'step':int(step), 'grad': grad, 'glit': int(glitter_prob)}
        self.__install(speed, self.__meteor_step_grad)

    @micropython.native
    def __meteor_step_grad(self):
        ws = self._ws
        N = self._N
        path = self.__path
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
            x, y = path[pos]
            d['hist'].insert(0, pos)
            if len(d['hist']) > tr:
                old = d['hist'].pop()
                ox, oy = path[old]
                ws[ox, oy].value = (0,0,0)

            cr, cg, cb = d['col']
            L = len(d['hist'])
            for i in range(L):
                px = d['hist'][i]
                cx, cy = path[px]
                a = grad[i] if i < tr else 0
                vr = (cr*a)>>8; vg = (cg*a)>>8; vb = (cb*a)>>8
                if (urandom.getrandbits(8) < gp) and (i < 3):
                    vr = min(255, vr + 80); vg = min(255, vg + 80); vb = min(255, vb + 80)
                ws[cx, cy].value = (vr, vg, vb)

            changed = True

        self.__try_commit(changed)

    def plasma(self, *, speed=0.008, kx=4, ky=4, hue_step=3):
        self._ws.fill((0,0,0))
        self.__state['pl'] = {'t': 0, 'kx': int(kx)&0xFF, 'ky': int(ky)&0xFF, 'hs': int(hue_step)&0xFF}
        self.__install(speed, self.__plasma_step_full)

    @micropython.native
    def __plasma_step_full(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['pl']
        t = st['t']
        kx = st['kx']
        ky = st['ky']
        hs = st['hs']
        SIN8 = _SIN8

        for y in range(H):
            sy = (y*ky + t) & 0xFF
            vy = SIN8[sy]
            for x in range(W):
                sx = (x*kx + t) & 0xFF
                hval = (vy + SIN8[sx]) >> 1
                ws[x, y].value = self.__wheel((hval + t) & 0xFF)

        st['t'] = (t + hs) & 0xFF
        self.__try_commit(True)

    def fireworks(self, *, rockets=3, tail_glow=40, gravity=10, drag_num=255, drag_den=260,
                sparks=36, burst_speed=220, life_decay=12, speed=0.012, stagger=4):
        ws = self._ws
        ws.fill((0,0,0))
        rockets = max(1, min(5, int(rockets)))
        drag_den = max(1, int(drag_den))

        S_per = max(12, int(sparks // rockets))
        burst = max(180, int(burst_speed - (rockets-1)*10))

        rs = []
        for i in range(rockets):
            rs.append(self.__fw_spawn(S=S_per, burst=burst, delay=i*int(stagger), colofs=i*51))

        self.__state['fwm'] = {
            'gy': int(gravity), 'dN': int(drag_num), 'dD': drag_den,
            'decay': max(1, int(life_decay)), 'tail': int(tail_glow),
            'rockets': rs
        }
        self.__install(speed, self.__fireworks_multi_step)

    def __fw_spawn(self, *, S, burst, delay=0, colofs=0):
        W, H = self._W, self._H
        x0 = (W//2) << 8
        y0 = (H-1)  << 8
        vy = -(180 + (urandom.getrandbits(5)))
        vx = (urandom.getrandbits(4) - 8)
        return {
            'stage': -1 if delay>0 else 0,
            'sleep': int(delay),
            'rx': x0, 'ry': y0, 'rvx': vx, 'rvy': vy,
            'last_px': -1, 'last_py': -1,
            'ticks': 0, 'max_ticks': 200,
            'explode_line': max(1, self._H//2),
            'S': int(S), 'burst': int(burst),
            'col': int(colofs) & 0xFF,
            'parts': []  # [x8,y8,vx8,vy8,r,g,b,life]
        }

    @micropython.native
    def __fireworks_multi_step(self):
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

        for r in rockets:
            stage = r['stage']

            if stage == -1:
                sl = r['sleep'] - 1
                r['sleep'] = sl
                if sl <= 0:
                    r['stage'] = 0
                continue

            if stage == 0:
                rx = r['rx']; ry = r['ry']; rvx = r['rvx']; rvy = r['rvy']
                lpx = r['last_px']; lpy = r['last_py']
                if 0 <= lpx < W and 0 <= lpy < H:
                    pr, pg, pb = ws[lpx, lpy].value
                    ws[lpx, lpy].value = (pr*tail//255, pg*tail//255, pb*tail//255)

                rvy += gy
                rvx = (rvx * dN) // dD
                rvy = (rvy * dN) // dD
                rx  += rvx; ry += rvy

                px = rx >> 8; py = ry >> 8
                if 0 <= px < W and 0 <= py < H:
                    ws[px, py].value = (255, 180, 80)
                    r['last_px'] = px; r['last_py'] = py
                r['rx']=rx; r['ry']=ry; r['rvx']=rvx; r['rvy']=rvy
                r['ticks'] += 1
                changed = True

                if (rvy >= 0) or (py <= r['explode_line']) or (r['ticks'] >= r['max_ticks']):
                    parts = []
                    S = r['S']; burst = r['burst']
                    cx, cy = rx, ry
                    idx = urandom.getrandbits(4) & 15
                    step = 1 if S >= 16 else max(1, 16 // S)
                    for n in range(S):
                        dx, dy = _DIR16[idx & 15]
                        vx = (dx * burst) >> 8
                        vy = (dy * burst) >> 8
                        hue = (r['col'] + (n * (256//S)) + (urandom.getrandbits(5))) & 0xFF
                        rr, gg, bb = self.__wheel(hue)
                        if (urandom.getrandbits(3) == 0):
                            rr, gg, bb = 255, 255, 255
                        parts.append([cx, cy, vx, vy, rr, gg, bb, 255])
                        idx += step
                    r['parts'] = parts
                    r['stage'] = 1
                    r['last_px'] = -1; r['last_py'] = -1
                    continue

            else:
                parts = r['parts']
                alive = 0
                for i in range(len(parts)):
                    x, y, vx, vy, rr, gg, bb, life = parts[i]
                    px = x>>8; py = y>>8
                    if 0 <= px < W and 0 <= py < H:
                        pr, pg, pb = ws[px, py].value
                        ws[px, py].value = ((pr*3)>>2, (pg*3)>>2, (pb*3)>>2)

                    vy += gy
                    vx = (vx * dN) // dD
                    vy = (vy * dN) // dD
                    x  += vx; y += vy

                    px = x>>8; py = y>>8
                    if 0 <= px < W and 0 <= py < H:
                        vr = (rr*life)>>8; vg = (gg*life)>>8; vb = (bb*life)>>8
                        if (urandom.getrandbits(4)==0):
                            vr = 255 if vr+64>255 else vr+64
                            vg = 255 if vg+64>255 else vg+64
                            vb = 255 if vb+64>255 else vb+64
                        ws[px, py].value = (vr, vg, vb)

                    life -= decay
                    if life > 8:
                        parts[i] = [x, y, vx, vy, rr, gg, bb, life]
                        alive += 1

                changed = True

                if alive == 0:
                    delay = (urandom.getrandbits(3) & 7) + 2
                    new = self.__fw_spawn(S=r['S'], burst=r['burst'], delay=delay, colofs=(r['col'] + urandom.getrandbits(6)) & 0xFF)
                    r.clear()
                    r.update(new)

        self.__try_commit(changed)


    def campfire(self, *, cooling=55, sparking=120, speed=0.010, ember_particles=28, ember_decay=18, base_rows=2):
        ws = self._ws
        ws.fill((0,0,0))
        W, H = self._W, self._H
        N = W*H
        base_rows = max(1, min(base_rows, H))

        self.__state['cf3'] = {
            'heat': [0]*N,
            'cool': int(cooling),
            'spark': int(sparking),
            'W': W, 'H': H, 'N': N,
            'ember': [[urandom.getrandbits(8)%W, H-1-(urandom.getrandbits(2)%base_rows), 220] for _ in range(ember_particles)],
            'e_dec': int(ember_decay),
            'rows': base_rows
        }
        self.__install(speed, self.__campfire_step2)

    @micropython.native
    def __campfire_step2(self):
        ws = self._ws
        st = self.__state['cf3']
        heat = st['heat']
        W = st['W']
        H = st['H']; N = st['N']
        N = st['N']
        cool = st['cool']
        spark = st['spark']
        rows = st['rows']
        changed = False

        base = (cool * 10) // N + 2
        for i in range(N):
            v = heat[i] - (urandom.getrandbits(8) % base)
            heat[i] = v if v > 0 else 0

        for i in range(N-1, 1, -1):
            heat[i] = (heat[i-1] + heat[i-2] + heat[i-2]) // 3

        for x in range(W):
            if urandom.getrandbits(8) < spark:
                idx = urandom.getrandbits(8) % rows
                i = x + (H-1-idx)*W
                nv = heat[i] + (urandom.getrandbits(7) + 80)
                heat[i] = 255 if nv>255 else nv

        k = 0
        for y in range(H):
            for x in range(W):
                t = heat[k]; k += 1
                if t <= 85:
                    ws[x, y].value = (t*3, t//4, 0)
                elif t <= 170:
                    tt = t - 85
                    ws[x, y].value = (255, 64 + (tt*3)//4, 0)
                else:
                    tt = t - 170
                    g  = 128 + (tt//2)
                    ws[x, y].value = (255, g if g<255 else 255, (tt*2) if (tt*2) < 255 else 255)

        changed = True

        em  = st['ember']
        e_d = st['e_dec']
        for i in range(len(em)):
            x, y, v = em[i]
            if urandom.getrandbits(2) and y > 0:
                y -= 1
                if urandom.getrandbits(1):
                    x = (x + (1 if urandom.getrandbits(1) else -1)) % W

            v -= e_d
            if v <= 0 or y <= 0:
                x = urandom.getrandbits(8) % W
                y = H-1 - (urandom.getrandbits(2) % rows)
                v = 200 + (urandom.getrandbits(6))

            r, g, b = ws[x, y].value
            r = r + v; g = g + (v>>1)
            if r>255: r=255
            if g>255: g=255
            ws[x, y].value = (r, g, b)
            em[i] = [x, y, v]
            changed = True

        self.__try_commit(changed)

    def ripple(self, *, speed=0.010, wavelength=10, phase_step=3, center=None):
        W, H = self._W, self._H
        if center is None:
            cx, cy = W//2, H//2
        else:
            cx, cy = center

        k = max(1, int(wavelength))
        self.__state['rip'] = {'t': 0, 'cx': int(cx), 'cy': int(cy), 'k': k, 'step': int(phase_step)&0xFF}
        self._ws.fill((0,0,0))
        self.__install(speed, self.__ripple_step)

    @micropython.native
    def __ripple_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['rip']
        t = st['t'] & 0xFF
        cx = st['cx']; cy = st['cy']; k = st['k']
        for y in range(H):
            dy = y - cy
            ady = -dy if dy < 0 else dy
            for x in range(W):
                dx = x - cx
                adx = -dx if dx < 0 else dx
                d = (adx + ady) * k
                h = (t + d) & 0xFF
                ws[x, y].value = self.__wheel(h)
        st['t'] = (t + st['step']) & 0xFF
        self.__try_commit(True)
 
    def matrix_rain(self, *, speed=0.012, spawn_prob=70, decay=28, head_boost=255, trail_boost=120):
        W, H = self._W, self._H
        N = W*H
        self.__state['mx'] = {
            'W': W, 'H': H, 'N': N,
            'buf': bytearray(N),
            'y': [- (urandom.getrandbits(3) & 7) for _ in range(W)],
            'spd': [1 + (urandom.getrandbits(1)&1) for _ in range(W)],
            'tick': [0]*W,
            'spawn': int(spawn_prob), 'dec': int(decay),
            'hboost': int(head_boost), 'tboost': int(trail_boost)
        }
        self._ws.fill((0,0,0))
        self.__install(speed, self.__matrix_rain_step)

    @micropython.native
    def __matrix_rain_step(self):
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
                if y >= H + (urandom.getrandbits(3)&3):
                    y = - (urandom.getrandbits(3)&7)
                    spd[x] = 1 + (urandom.getrandbits(1)&1)
                yv[x] = y
                if 0 <= y < H:
                    i = x + y*W
                    v = hb
                    if v > 255: v = 255
                    buf[i] = v
                    if y+1 < H:
                        j = x + (y+1)*W
                        nv = buf[j] + tb
                        buf[j] = 255 if nv>255 else nv
                elif (urandom.getrandbits(8) < spawn):
                    yv[x] = - (urandom.getrandbits(3)&7)
            else:
                tick[x] = t

        k = 0
        for yy in range(H):
            for xx in range(W):
                v = buf[k]
                if v > 0:
                    nv = v - dec
                    buf[k] = nv if nv > 0 else 0
                    g = v
                    r = v >> 3
                    b = v >> 4
                    ws[xx, yy].value = (r, g, b)
                else:
                    ws[xx, yy].value = (0,0,0)
                k += 1
        self.__try_commit(True)

    def neon_checkerboard(self, *, speed=0.010, tile=4, pulse_step=3, hue_shift=64, edge_boost=80):
        tile = max(1, int(tile))
        self.__state['neo'] = {
            't': 0, 'tile': tile, 'step': int(pulse_step)&0xFF,
            'hshift': int(hue_shift)&0xFF, 'eboost': int(edge_boost)&0xFF
        }
        self._ws.fill((0,0,0))
        self.__install(speed, self.__neon_step)

    @micropython.native
    def __neon_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['neo']
        t = st['t'] & 0xFF
        tile= st['tile']
        step = st['step']
        hsh = st['hshift']
        eboost = st['eboost']
        SIN8= _SIN8

        for y in range(H):
            ty = y // tile
            by = y - ty*tile
            dy_edge = by if by < tile - 1 - by else tile - 1 - by
            for x in range(W):
                tx = x // tile
                bx = x - tx*tile
                dx_edge = bx if bx < tile - 1 - bx else tile - 1 - bx

                parity = (tx ^ ty) & 1
                hue = (t + (hsh if parity else 0)) & 0xFF

                pulse = SIN8[(t + (parity*32)) & 0xFF]
                edge = dx_edge if dx_edge < dy_edge else dy_edge
                boost = (eboost * (tile-1 - edge) * 2) // max(1, (tile-1)*2)
                v = pulse + boost
                if v > 255: v = 255

                r, g, b = self.__wheel(hue)
                ws[x, y].value = ((r*v)>>8, (g*v)>>8, (b*v)>>8)

        st['t'] = (t + step) & 0xFF
        self.__try_commit(True)

    def petal_vortex(self, *, speed=0.010, petals=6, spin_step=3, radial=3, contrast=200):
        self.__state['pet'] = {
            't': 0, 'k': max(3, int(petals)),
            'spin': int(spin_step)&0xFF, 'rad': max(1,int(radial)),
            'ctr': int(contrast)&0xFF
        }
        self._ws.fill((0,0,0))
        self.__install(speed, self.__petal_step)

    @micropython.native
    def __petal_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['pet']
        t = st['t'] & 0xFF
        k = st['k']
        rad = st['rad']
        ctr = st['ctr']
        SIN8 = _SIN8

        cx = W//2
        cy = H//2

        s = int(SIN8[t]) - 128
        c = int(SIN8[(t + 64) & 0xFF]) - 128

        for y in range(H):
            dy = y - cy
            for x in range(W):
                dx = x - cx
                xr = (dx*c - dy*s) >> 7
                yr = (dx*s + dy*c) >> 7

                a = SIN8[(xr * k + t) & 0xFF]
                b = SIN8[(yr * k + t) & 0xFF]
                m = (a * b) >> 8

                adx = -dx if dx < 0 else dx
                ady = -dy if dy < 0 else dy
                rv  = (adx + ady) * rad
                rv  = 255 if rv > 255 else rv

                v = m + ((ctr * (255 - rv)) >> 8)
                if v > 255: v = 255

                hue = (t + m) & 0xFF
                r, g, b = self.__wheel(hue)
                ws[x, y].value = ((r*v)>>8, (g*v)>>8, (b*v)>>8)

        st['t'] = (t + st['spin']) & 0xFF
        self.__try_commit(True)

    def spark_stream(self, *, speed=0.010, emitters=3, spawn_rate=4, max_sparks=48,
                    base_hue=150, hue_jitter=20, fade=220, gravity=6, swirl=10):
        W = self._W
        emitters = max(1, min(5, int(emitters)))
        pos = [ (i+1)*W//(emitters+1) for i in range(emitters) ]
        self.__state['ssk'] = {
            'pos': pos, 'sr': int(spawn_rate), 'max': int(max_sparks),
            'bh': int(base_hue)&0xFF, 'hj': int(hue_jitter)&0xFF,
            'fade': int(fade)&0xFF, 'g': int(gravity), 'sw': int(swirl),
            'p': []
        }
        self._ws.fill((0,0,0))
        self.__install(speed, self.__spark_stream_step)

    @micropython.native
    def __spark_stream_step(self):
        ws = self._ws
        W = self._W
        H = self._H
        st = self.__state['ssk']
        p = st['p']
        fade = st['fade']
        g = st['g']
        sw = st['sw']
        changed = False

        for y in range(H):
            for x in range(W):
                r, g0, b = ws[x, y].value
                ws[x, y].value = ((r*fade)>>8, (g0*fade)>>8, (b*fade)>>8)

        tries = st['sr']
        emit = st['pos']
        bh = st['bh']
        hj = st['hj']
        while tries > 0 and len(p) < st['max']:
            ex = emit[urandom.getrandbits(8) % len(emit)]
            vx = ( (urandom.getrandbits(4) - 8) * 20 )
            vy = - (140 + (urandom.getrandbits(6)))
            hue= (bh + (urandom.getrandbits(7) % (hj+1))) & 0xFF
            p.append([ex<<8, (H-1)<<8, vx, vy, hue, 255, urandom.getrandbits(8)])
            tries -= 1

        alive = []
        for i in range(len(p)):
            x, y, vx, vy, hue, life, phi = p[i]
            phi = (phi + 11) & 0xFF
            wig = phi if phi < 128 else (255 - phi)
            vx += ((wig - 64) * sw) >> 6

            vy += g

            x += vx; y += vy

            px = x>>8; py = y>>8
            if 0 <= px < W and 0 <= py < H:
                r, g0, b = self.__wheel(hue)
                r = (r*life)>>8; g0 = (g0*life)>>8; b = (b*life)>>8
                cr, cg, cb = ws[px, py].value
                nr = cr + r; ng = cg + g0; nb = cb + b
                if nr>255: nr=255
                if ng>255: ng=255
                if nb>255: nb=255
                ws[px, py].value = (nr, ng, nb)
                changed = True

            life -= 14
            if life > 24 and (py >= -1):
                alive.append([x,y,vx,vy,hue,life,phi])

        st['p'] = alive
        self.__try_commit(changed)
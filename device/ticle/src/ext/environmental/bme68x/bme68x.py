import math
import utime
import ustruct
from ticle import I2CMaster

__version__ = "1.0.0"
__author__  = "PlanX Lab Development Team"


class BME68x:
    _FORCED_MODE         = 0x01
    _SLEEP_MODE          = 0x00
    _REG_STATUS          = 0x1D
    _BIT_MEASURING       = 0x20 
    _REG_CTRL_GAS1       = 0x71
    _REG_RES_HEAT_0      = 0x5A    # res_heat_0..9 (0x5A..0x63)
    _REG_GAS_WAIT_0      = 0x64    # gas_wait_0..9 (0x64..0x6D)

    _BIT_NEW_DATA        = 0x80
    _BIT_HEAT_STAB       = 0x10    # bit4
    _BIT_GAS_VALID       = 0x20    # bit5 (data block flags)

    _OS_CODE             = {'off':0, 'x1':1, 'x2':2, 'x4':3, 'x8':4, 'x16':5}
    _IIR_COEFFS          = [0, 1, 3, 7, 15, 31, 63, 127]  # ex: eco=strong filter (127), precision=weak filter (3)
    _IIR_TO_CODE         = {c:i for i, c in enumerate(_IIR_COEFFS)}
    _OSRS_MULT           = (0, 1, 2, 4, 8, 16)
    _DATA_BLOCK_LEN      = 17

    _ISA_G               = 9.80665  # m/s^2
    _ISA_R               = 287.05   # J/(kg·K)
    _ISA_L               = 0.0065   # K/m (temperature lapse rate)

    _NORM_BASE_PERIOD_MS = 3000 

    # from Bosch BME68x GAS LUTs
    _GAS_LUT1 = (
        2147483647, 2147483647, 2147483647, 2147483647,
        2147483647, 2126008810, 2147483647, 2130303777,
        2147483647, 2147483647, 2143188679, 2136746228,
        2147483647, 2126008810, 2147483647, 2147483647
    )
    _GAS_LUT2 = (
        4096000000, 2048000000, 1024000000, 512000000,
        255744255,  127110228,  64000000,   32258064,
        16016016,   8000000,    4000000,    2000000,
        1000000,    500000,     250000,     125000
    )

    def __init__(self, scl:int, sda:int, *, addr: int = 0x77,
                 profile_preset: str = "standard",      # "eco", "standard", "precision"
                 ):
        self._i2c  = I2CMaster(sda=sda, scl=scl)
        self._addr = int(addr)

        chip_id = self._i2c.readfrom_mem(self._addr, 0xD0, 1)[0]
        if chip_id != 0x61:
            raise OSError("BME68x (BME680/BME688) not detected")

        self._i2c.writeto_mem(self._addr, 0xE0, bytes([0xB6]))
        utime.sleep_ms(5)

        self._set_power_mode(self._SLEEP_MODE)

        # Calibration (datasheet)
        cal1 = self._i2c.readfrom_mem(self._addr, 0x8A, 23)
        cal2 = self._i2c.readfrom_mem(self._addr, 0xE1, 14)
        cal3 = self._i2c.readfrom_mem(self._addr, 0x00, 5)

        # Temperature calibration
        par_t2 = ustruct.unpack('<h', cal1[0:2])[0]
        par_t3 = ustruct.unpack('b',  cal1[2:3])[0]
        par_t1 = ustruct.unpack('<H', cal2[8:10])[0]
        self.__par_t1, self.__par_t2, self.__par_t3 = par_t1, par_t2, par_t3

        # Pressure calibration
        par_p1 = ustruct.unpack('<H', cal1[4:6])[0]
        par_p2 = ustruct.unpack('<h', cal1[6:8])[0]
        par_p3 = ustruct.unpack('b',  cal1[8:9])[0]
        par_p4 = ustruct.unpack('<h', cal1[10:12])[0]
        par_p5 = ustruct.unpack('<h', cal1[12:14])[0]
        par_p7 = ustruct.unpack('b',  cal1[14:15])[0]
        par_p6 = ustruct.unpack('b',  cal1[15:16])[0]
        par_p8 = ustruct.unpack('<h', cal1[18:20])[0]
        par_p9 = ustruct.unpack('<h', cal1[20:22])[0]
        par_p10 = cal1[22]
        self._pressure_calibration = [par_p1, par_p2, par_p3, par_p4, par_p5, par_p6, par_p7, par_p8, par_p9, par_p10]

        # Humidity calibration (H1/H2 bit-mixed)
        e1 = cal2[0]  # 0xE1
        e2 = cal2[1]  # 0xE2
        e3 = cal2[2]  # 0xE3
        
        par_h1 = (e3 << 4) | (e2 & 0x0F)        # par_h1: 0xE2[3:0] / 0xE3
        par_h2 = (e1 << 4) | ((e2 >> 4) & 0x0F) # par_h2: 0xE2[7:4] / 0xE1
        if par_h2 & 0x800:  # 12-bit sign
            par_h2 -= 1 << 12
            
        par_h3 = ustruct.unpack('b', bytes([cal2[3]]))[0]
        par_h4 = ustruct.unpack('b', bytes([cal2[4]]))[0]
        par_h5 = ustruct.unpack('b', bytes([cal2[5]]))[0]
        par_h6 = cal2[6]
        par_h7 = ustruct.unpack('b', bytes([cal2[7]]))[0]
        self._humidity_calibration = [par_h1, par_h2, par_h3, par_h4, par_h5, par_h6, par_h7]

        # Gas/Heater calibration
        par_gh2 = ustruct.unpack('<h', cal2[10:12])[0]
        par_gh1 = ustruct.unpack('b',  cal2[12:13])[0]
        par_gh3 = ustruct.unpack('b',  cal2[13:14])[0]
        self.__par_gh1, self.__par_gh2, self.__par_gh3 = par_gh1, par_gh2, par_gh3

        res_heat_val = ustruct.unpack('b', bytes([cal3[0]]))[0]
        res_heat_range = (cal3[2] >> 4) & 0x03
        range_sw_err = (cal3[4] >> 4) & 0x0F
        self._res_heat_val = res_heat_val
        self._res_heat_range = res_heat_range
        self._sw_err = range_sw_err

        # OSRS/TPH settings cache
        self._osrs_t = None
        self._osrs_p = None
        self._osrs_h = None
        self._tph_est_ms_cache = None

        # Lazy cache & filter states
        self._temperature_correction = 0.0

        self._t_fine = None
        self._adc_pres = None
        self._adc_temp = None
        self._adc_hum = None
        self._adc_gas = None
        self._gas_range = None

        self._ready_gas = False

        self._cache_ts_ms = None
        self._temp_c = None
        self._pres_hpa = None
        self._humi_rh = None
        self._gas_ohm = None

        # Gas cycle state
        self._heater_sig = (-1, -1)    # (rh0, gw0)
        self._profile_steps = 1
        self._gas_update_hint_ms = self._NORM_BASE_PERIOD_MS  # 3s
        self._require_heat_stab = False 
        
        # Gas baseline/IAQ
        self._gas_baseline = 90_000  # 90 kOhm
        self._gas_baseline_auto_update_ms = 300_000  # 5 min
        self._iaq_last_baseline_update_ms = utime.ticks_ms()
        self._period_gas_warn = False
        self._gas_hist = []

        self._buf17 = bytearray(self._DATA_BLOCK_LEN)
         
        self.set_profile_preset(profile_preset)
    
    @property
    def gas_update_hint_ms(self):
        return self._gas_update_hint_ms

    @gas_update_hint_ms.setter
    def gas_update_hint_ms(self, value: int):
        v = int(value)
        if v < 200:
            raise ValueError("Minimum period is 200ms.")
        
        min_tph, min_gas = self._estimate_min_periods_ms(v)
        if v < min_tph:
            raise ValueError(f"gas_update_hint_ms too small for current T/P/H oversampling (>= {min_tph} ms needed).")
        self._period_gas_warn = (v < min_gas)

        self._gas_update_hint_ms = v
        new_dur_ms = self._predict_gas_wait_for_period(self._gas_update_hint_ms)

        self._perform_reading(need_gas=False)
        Tamb = self._temperature()
        Ttarget = 320.0  # Standard profile target temperature (recommended range 200-400°C)
        rh = self._calc_res_heat(int(Ttarget), float(Tamb))
        gw = self._encode_gas_wait(int(new_dur_ms))

        if self._heater_sig != (rh, gw):
            self._i2c.writeto_mem(self._addr, self._REG_RES_HEAT_0, bytes([rh]))
            self._i2c.writeto_mem(self._addr, self._REG_GAS_WAIT_0, bytes([gw]))
            self.set_gas_nb_conv(0)
            self._profile_steps = 1
            self._heater_sig = (rh, gw)

    @property
    def gas_update_hint_maybe_too_short(self) -> bool:
        return getattr(self, "_period_gas_warn", False)

    @property
    def require_heat_stab(self) -> bool:
        return self._require_heat_stab

    @require_heat_stab.setter
    def require_heat_stab(self, v: bool):
        self._require_heat_stab = bool(v)

    @property
    def gas_baseline(self):
        return self._gas_baseline

    @gas_baseline.setter
    def gas_baseline(self, value: int):
        self._gas_baseline = max(80_000, min(320_000, int(value)))

    @property
    def gas_baseline_auto_update_ms(self):
        return self._gas_baseline_auto_update_ms

    @gas_baseline_auto_update_ms.setter
    def gas_baseline_auto_update_ms(self, update_ms: int):
        self._gas_baseline_auto_update_ms = max(60_000, int(update_ms))

    def adjust_temperature_correction(self, delta):
        """
        When using a gas heater, the internal temperature may be slightly higher. 
        Calibrate using something like adjust_temperature_correction(-1.0).
        """
        self._temperature_correction += float(delta)

    def set_tph_oversampling(self, *, osrs_t='x2', osrs_p='x4', osrs_h='x1'):
        def _code(v):
            if isinstance(v, str):
                if v not in self._OS_CODE:
                    raise ValueError("osrs must be one of 'off','x1','x2','x4','x8','x16'")
                return self._OS_CODE[v]
            v = int(v)
            if not (0 <= v <= 5):
                raise ValueError("osrs code must be 0..5")
            return v

        ht = _code(osrs_h)
        tt = _code(osrs_t)
        pt = _code(osrs_p)

        hum = self._i2c.readfrom_mem(self._addr, 0x72, 1)[0]
        hum = (hum & ~0x07) | (ht & 0x07)
        self._i2c.writeto_mem(self._addr, 0x72, bytes([hum]))

        meas = self._i2c.readfrom_mem(self._addr, 0x74, 1)[0]
        meas = (meas & ~((0x7 << 5) | (0x7 << 2))) | ((tt & 0x7) << 5) | ((pt & 0x7) << 2)
        self._i2c.writeto_mem(self._addr, 0x74, bytes([meas]))

        self._osrs_t, self._osrs_p, self._osrs_h = tt, pt, ht
        self._tph_est_ms_cache = self._calc_tph_time_ms_from_codes(tt, pt, ht)

    def set_tph_iir_filter(self, coeff: int):
        coeff = int(coeff)
        if coeff not in self._IIR_TO_CODE:
            raise ValueError("coeff must be one of 0,1,3,7,15,31,63,127")
        
        code = self._IIR_TO_CODE[coeff]
        cfg = self._i2c.readfrom_mem(self._addr, 0x75, 1)[0]
        cfg = (cfg & ~(0x7 << 2)) | ((code & 0x7) << 2)
        self._i2c.writeto_mem(self._addr, 0x75, bytes([cfg]))

    def set_profile_preset(self, preset: str):
        p = preset.lower()
        if not p in ("eco", "standard", "precision"):
            raise ValueError("preset must be one of 'eco', 'standard', 'precision'")
        
        if p == "eco":
            self.set_tph_oversampling(osrs_t='x1', osrs_p='x2', osrs_h='off')
            self.set_tph_iir_filter(127)
            self.gas_update_hint_ms = 6000
        elif p == "precision":
            self.set_tph_oversampling(osrs_t='x4', osrs_p='x16', osrs_h='x2')
            self.set_tph_iir_filter(3)
            self.gas_update_hint_ms = 1500
        else:  # standard
            self.set_tph_oversampling(osrs_t='x2', osrs_p='x4', osrs_h='x1')
            self.set_tph_iir_filter(15)
            self.gas_update_hint_ms = self._NORM_BASE_PERIOD_MS  # 3s

    def set_gas_heater_profiles(self, temps_c: list, durations_ms: list, amb_temp_c: float = None):
        tlist = list(temps_c)
        dlist = list(durations_ms)
        if not (1 <= len(tlist) <= 10) or len(tlist) != len(dlist):
            raise ValueError("temps_c/durations_ms must have length 1..10 and equal length")

        if amb_temp_c is None:
            if not self._tph_cache_is_fresh():
                self._perform_reading(need_gas=False)
            amb_temp_c = self._temperature()

        for i, (tc, dm) in enumerate(zip(tlist, dlist)):
            rh = self._calc_res_heat(int(tc), float(amb_temp_c))
            gw = self._encode_gas_wait(int(dm))
            self._i2c.writeto_mem(self._addr, self._REG_RES_HEAT_0 + i, bytes([rh]))
            self._i2c.writeto_mem(self._addr, self._REG_GAS_WAIT_0 + i, bytes([gw]))

        self.set_gas_nb_conv(len(tlist) - 1)
        self._profile_steps = len(tlist)  # 1..10

    def set_gas_nb_conv(self, n: int = 0):
        n = max(0, min(9, int(n)))
        val = self._i2c.readfrom_mem(self._addr, self._REG_CTRL_GAS1, 1)[0]
        # keep run_gas(bit4), replace nb_conv(low 4 bits)
        val = (val & ~0x0F) | n
        self._i2c.writeto_mem(self._addr, self._REG_CTRL_GAS1, bytes([val]))

    def reset_cache(self):
        self._cache_ts_ms = None
        self._temp_c = self._pres_hpa = self._humi_rh = self._gas_ohm = None

    def temperature(self) -> float:
        self._ensure_sample(need_gas=False)
        return self._temp_c

    def pressure(self) -> float:
        self._ensure_sample(need_gas=False)
        return self._pres_hpa

    def sea_level(self, altitude, temp_c: float = None) -> float:
        self._ensure_sample(need_gas=False)
        p = float(self._pres_hpa)
        h = float(altitude)
        if temp_c is None:
            temp_c = self._temperature()
        
        TmK = float(temp_c) + 273.15
        L = self._ISA_L
        k = self._ISA_G / (self._ISA_R * L)
        Tavg = TmK + 0.5 * L * h
        Tavg = 200.0 if Tavg < 200.0 else Tavg
        return p * pow(1.0 - (L * h) / Tavg, -k)

    def altitude(self, sealevel, temp_c: float = None) -> float:
        self._ensure_sample(need_gas=False)
        p  = float(self._pres_hpa)   # hPa
        p0 = float(sealevel)
        if p <= 0.0 or p0 <= 0.0:
            return 0.0

        if temp_c is None:
            temp_c = self._temperature()

        h0 = 44330.0 * (1.0 - pow(p / p0, 1.0 / 5.255))
        TmK = float(temp_c) + 273.15
        L = self._ISA_L
        k = self._ISA_G / (self._ISA_R * L)  # ≈ 5.255
        Tavg = TmK + 0.5 * L * h0
        Tavg = 200.0 if Tavg < 200.0 else Tavg
        return (Tavg / L) * (pow(p0 / p, 1.0 / k) - 1.0)  # hypsometric rearranged

    def humidity(self) -> float:
        self._ensure_sample(need_gas=False)
        return self._humi_rh

    def trigger_gas_measurement(self, *, steps: int = None) -> int:
        if steps is not None:
            steps = max(1, min(10, int(steps)))
            self.set_gas_nb_conv(steps - 1)
            self._profile_steps = steps

        self._ready_gas = False
        self._gas_ohm = None

        self._set_run_gas(True)
        self._set_power_mode(self._FORCED_MODE)
        return self._estimate_eta_ms(need_gas=True)

    def gas_measurement_ready(self) -> bool:
        st = self._i2c.readfrom_mem(self._addr, self._REG_STATUS, 1)[0]
        if not (st & self._BIT_NEW_DATA):
            return False

        self._i2c.readfrom_mem_into(self._addr, self._REG_STATUS, self._buf17)
        self._parse_and_cache_sample(self._buf17, assume_need_gas=True)
        return bool(self._ready_gas)

    def gas_resistance(self):
        return self._gas_ohm if self._ready_gas else None

    def burn_in(self, mode: str = "simple"):
        period = self._gas_update_hint_ms

        # Heuristics by period
        if period >= 3000:
            win_n = 12
            cov_thr = 1.0   # %
            drift_thr = 0.6 # %
        else:
            win_n = 16
            cov_thr = 1.5
            drift_thr = 0.8

        windows_needed = 3
        max_minutes = 10

        warmup_hits = 0
        for _ in range(8):
            _ = self.trigger_gas_measurement()
            t_dead = utime.ticks_add(utime.ticks_ms(), period)
            ready = False
            while utime.ticks_diff(t_dead, utime.ticks_ms()) > 0:
                if self.gas_measurement_ready():
                    ready = True
                    break
                utime.sleep_ms(2)
            if ready:
                _ = self.gas_resistance()
                warmup_hits += 1
            yield {"phase": "warmup", "samples": warmup_hits, "success": False}

        start_ms = utime.ticks_ms()
        xs = []
        last_med = None
        consecutive_ok = 0
        window_idx = 0

        while utime.ticks_diff(utime.ticks_ms(), start_ms) < max_minutes * 60_000:
            tick0 = utime.ticks_ms()

            _ = self.trigger_gas_measurement()
            deadline = utime.ticks_add(utime.ticks_ms(), period)
            ready = False
            while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
                if self.gas_measurement_ready():
                    ready = True
                    break
                utime.sleep_ms(2)

            if ready:
                g = self.gas_resistance()
                if g is not None:
                    xs.append(g)

                    samples_in_window = min(len(xs), win_n)
                    fill_pct = 100.0 * samples_in_window / win_n

                    if samples_in_window < win_n:
                        med_partial, cov_partial = self._median_cov(xs, samples_in_window)
                        eta_s = (win_n - samples_in_window) * period / 1000.0
                        yield {
                            "phase": "acquire",
                            "samples_in_window": int(samples_in_window),
                            "win_n": int(win_n),
                            "fill_pct": float(fill_pct),
                            "latest_ohm": float(g),
                            "median_ohm": float(med_partial),
                            "cov_pct": float(cov_partial),
                            "eta_to_window_s": float(eta_s),
                            "success": False,
                        }

                    if samples_in_window >= win_n:
                        window_idx += 1
                        med, cov = self._median_cov(xs, win_n)
                        drift = 0.0 if (last_med is None or last_med == 0.0) else abs((med - last_med) / max(last_med, 1e-9)) * 100.0

                        pass_this = (cov <= cov_thr) and (drift <= drift_thr)
                        consecutive_ok = (consecutive_ok + 1) if pass_this else 0
                        last_med = med

                        yield {
                            "phase": "window",
                            "window_idx": window_idx,
                            "median_ohm": float(med),
                            "cov_pct": float(cov),
                            "drift_pct": float(drift),
                            "success": False,
                        }

                        if consecutive_ok >= windows_needed:
                            self.gas_baseline = int(med)
                            elapsed_s = utime.ticks_diff(utime.ticks_ms(), start_ms) // 1000
                            yield {
                                "phase": "done",
                                "success": True,
                                "elapsed_s": int(elapsed_s),
                                "windows_passed": int(consecutive_ok),
                                "median_ohm": float(med),
                                "baseline_ohm": float(self._gas_baseline),
                                "mode": mode,
                            }
                            return

            next_tick = utime.ticks_add(tick0, period)
            while utime.ticks_diff(next_tick, utime.ticks_ms()) > 0:
                utime.sleep_ms(1)

        elapsed_s = utime.ticks_diff(utime.ticks_ms(), start_ms) // 1000
        yield {
            "phase": "done",
            "success": False,
            "elapsed_s": int(elapsed_s),
            "windows_passed": int(consecutive_ok),
            "median_ohm": float(last_med if last_med is not None else 0.0),
            "baseline_ohm": float(self._gas_baseline),
            "mode": mode,
        }

    def iaq_heuristics(self, *,
            temp_weighting=0.08, pressure_weighting=0.02,
            humi_weighting=0.15, gas_weighting=0.75,
            gas_ema_alpha=0.02,
            temp_baseline=25.0, pressure_baseline=1013.25, humi_baseline=50.0
            ):
        eta_ms = self.trigger_gas_measurement()
        deadline = utime.ticks_add(utime.ticks_ms(), eta_ms + 20)
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            if self.gas_measurement_ready():
                break
            utime.sleep_ms(3)

        gas = self.gas_resistance()
        if gas is None:
            return None

        temp = self._temp_c
        pres = self._pres_hpa
        humi = self._humi_rh

        hist = self._gas_hist
        hist.append(gas)
        if len(hist) > 4:
            hist.pop(0)

        rising = False
        if len(hist) >= 3:
            inc1 = (hist[-2] - hist[-3]) / max(hist[-3], 1e-9)
            inc2 = (hist[-1] - hist[-2]) / max(hist[-2], 1e-9)
            rising = (inc1 > 0.003) and (inc2 > 0.003)

        now = utime.ticks_ms()
        near_env = (abs(temp - temp_baseline) <= 1.0) and (abs(humi - humi_baseline) <= 5.0)
        cleaner  = (gas >= self._gas_baseline * 0.98)
        if near_env and cleaner and rising and utime.ticks_diff(now, self._iaq_last_baseline_update_ms) >= self._gas_baseline_auto_update_ms:
            self._gas_baseline = (1.0 - gas_ema_alpha) * self._gas_baseline + gas_ema_alpha * gas
            self._iaq_last_baseline_update_ms = now

        hum_bad  = min(abs(humi - humi_baseline) / max(humi_baseline * 2.0, 1e-9), 1.0) * (humi_weighting * 100.0)
        temp_bad = min(abs(temp - temp_baseline) / 10.0, 1.0) * (temp_weighting * 100.0)
        pres_bad = min(abs(pres - pressure_baseline) / 50.0, 1.0) * (pressure_weighting * 100.0)

        drop = max((self._gas_baseline - gas) / max(self._gas_baseline, 1e-9), 0.0)
        gamma = 0.8
        gas_bad = min(pow(drop, gamma), 1.0) * (gas_weighting * 100.0)

        iaq_val = int(min(max(5.0 * (hum_bad + temp_bad + pres_bad + gas_bad), 0.0), 500.0))
        return iaq_val, temp, pres, humi, gas

    def _set_power_mode(self, value):
        tmp = self._i2c.readfrom_mem(self._addr, 0x74, 1)[0]
        tmp &= ~0x03
        tmp |= (value & 0x03)
        self._i2c.writeto_mem(self._addr, 0x74, bytes([tmp]))

    def _decode_gas_wait_ms(self, reg_val: int) -> int:
        factor = (reg_val >> 6) & 0x03
        mant = reg_val & 0x3F
        return mant * (1 << (2 * factor))

    def _read_nb_conv_and_total_gas_wait_ms(self) -> tuple:
        ctrl = self._i2c.readfrom_mem(self._addr, self._REG_CTRL_GAS1, 1)[0]
        run_gas = (ctrl & 0x10) != 0
        nb = ctrl & 0x0F
        if not run_gas:
            return False, nb, 0

        total = 0
        steps = nb + 1
        for i in range(steps):
            gw = self._i2c.readfrom_mem(self._addr, self._REG_GAS_WAIT_0 + i, 1)[0]
            total += self._decode_gas_wait_ms(gw)
        return True, nb, total

    def _predict_gas_wait_for_period(self, period_ms: int) -> int:
        base = int(period_ms)
        dur = int(120 * base / self._NORM_BASE_PERIOD_MS)
        if dur < 20:  
            dur = 20
        if dur > 120: 
            dur = 120
        return dur

    def _estimate_min_periods_ms(self, candidate_ms: int) -> tuple:
        tph = self._estimate_tph_time_ms()
        min_tph = tph + 30
        run_gas, nb_conv, gas_total = self._read_nb_conv_and_total_gas_wait_ms()
        if run_gas and gas_total > 0:
            min_gas = tph + gas_total + 60
        else:
            gw = self._predict_gas_wait_for_period(candidate_ms)
            min_gas = tph + gw + 60
        return (int(min_tph), int(min_gas))

    def _estimate_tph_time_ms(self) -> int:
        if self._tph_est_ms_cache is not None and self._osrs_t is not None and self._osrs_p is not None and self._osrs_h is not None:
            return self._tph_est_ms_cache

        ctrl_meas = self._i2c.readfrom_mem(self._addr, 0x74, 1)[0]
        ctrl_hum  = self._i2c.readfrom_mem(self._addr, 0x72, 1)[0]
        tt = (ctrl_meas >> 5) & 0x07
        pt = (ctrl_meas >> 2) & 0x07
        ht = (ctrl_hum  >> 0) & 0x07
        self._osrs_t, self._osrs_p, self._osrs_h = tt, pt, ht
        self._tph_est_ms_cache = self._calc_tph_time_ms_from_codes(tt, pt, ht)
        return self._tph_est_ms_cache

    def _calc_tph_time_ms_from_codes(self, osrs_t: int, osrs_p: int, osrs_h: int) -> int:
        ot = self._OSRS_MULT[osrs_t] if 0 <= osrs_t <= 5 else 0
        op = self._OSRS_MULT[osrs_p] if 0 <= osrs_p <= 5 else 0
        oh = self._OSRS_MULT[osrs_h] if 0 <= osrs_h <= 5 else 0

        t_ms = 1.25 + (2.3 * ot) + (2.3 * op + 0.575) + (2.3 * oh + 0.575)
        return int(t_ms + 0.5)

    def _try_collect_ready_sample(self, *, assume_need_gas: bool) -> bool:
        st = self._i2c.readfrom_mem(self._addr, self._REG_STATUS, 1)[0]
        if not (st & self._BIT_NEW_DATA):
            return False
        
        self._i2c.readfrom_mem_into(self._addr, self._REG_STATUS, self._buf17)
        self._parse_and_cache_sample(self._buf17, assume_need_gas=assume_need_gas)
        return True

    def _perform_reading(self, need_gas: bool):
        st = self._i2c.readfrom_mem(self._addr, self._REG_STATUS, 1)[0]
        if st & self._BIT_NEW_DATA:
            self._i2c.readfrom_mem_into(self._addr, self._REG_STATUS, self._buf17)
            self._parse_and_cache_sample(self._buf17, assume_need_gas=need_gas)
            if (need_gas and self._ready_gas) or (not need_gas):
                return

        cg = self._i2c.readfrom_mem(self._addr, self._REG_CTRL_GAS1, 1)[0]
        was_on = (cg & 0x10) != 0
        nb_conv = (cg & 0x0F)  # 0..9

        if was_on != need_gas:
            self._set_run_gas(need_gas)

        if need_gas:
            steps = nb_conv + 1
            gas_wait_ms = 0
            for i in range(steps):
                gw = self._i2c.readfrom_mem(self._addr, self._REG_GAS_WAIT_0 + i, 1)[0]
                gas_wait_ms += self._decode_gas_wait_ms(gw)
        else:
            gas_wait_ms = 0

        tph_ms = self._estimate_tph_time_ms()
        t_est_ms = tph_ms + gas_wait_ms
        margin_ms = max(80, t_est_ms // 3 + 40)

        def _wait_once(extra_margin=0):
            self._set_power_mode(self._FORCED_MODE)

            t0 = utime.ticks_add(utime.ticks_ms(), 5)
            while utime.ticks_diff(t0, utime.ticks_ms()) > 0:
                st = self._i2c.readfrom_mem(self._addr, self._REG_STATUS, 1)[0]
                if st & self._BIT_MEASURING:
                    break

            deadline = utime.ticks_add(utime.ticks_ms(), t_est_ms + margin_ms + extra_margin)
            while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
                st = self._i2c.readfrom_mem(self._addr, self._REG_STATUS, 1)[0]
                if st & self._BIT_NEW_DATA:
                    return True
                utime.sleep_ms(3)
            return False

        if not _wait_once():
            if not _wait_once(extra_margin=margin_ms):
                raise OSError(f"BME68x data timeout: tph={tph_ms}ms gas={gas_wait_ms}ms steps={nb_conv+1}")

        self._i2c.readfrom_mem_into(self._addr, self._REG_STATUS, self._buf17)
        self._parse_and_cache_sample(self._buf17, assume_need_gas=need_gas)

        if was_on != need_gas:
            self._set_run_gas(was_on)

    def _parse_and_cache_sample(self, data: bytes, *, assume_need_gas: bool):
        mv = memoryview(data)
        self._adc_pres = (mv[2] << 12) | (mv[3] << 4) | (mv[4] >> 4)
        self._adc_temp = (mv[5] << 12) | (mv[6] << 4) | (mv[7] >> 4)
        self._adc_hum  = ustruct.unpack(">H", bytes(mv[8:10]))[0]
        self._adc_gas  = (ustruct.unpack(">H", bytes(mv[13:15]))[0] >> 6)
        self._gas_range = mv[14] & 0x0F

        var1 = (self._adc_temp / 8.0) - (self.__par_t1 * 2.0)
        var2 = (var1 * self.__par_t2) / 2048.0
        var3 = ((var1 / 2.0) * (var1 / 2.0)) / 4096.0
        var3 = (var3 * self.__par_t3 * 16.0) / 16384.0
        self._t_fine = int(var2 + var3)

        flags = data[14]

        if assume_need_gas:
            gas_valid = (flags & self._BIT_GAS_VALID) != 0
            heat_ok = ((flags & self._BIT_HEAT_STAB) != 0) or (not self._require_heat_stab)
            self._ready_gas = bool(gas_valid and heat_ok)
        else:
            self._ready_gas = False

        t = self._temperature()
        p = self._pressure()
        h = self._humidity()

        g = None
        if assume_need_gas and self._ready_gas:
            g = self._gas()

        self._cache_ts_ms = utime.ticks_ms()
        self._temp_c, self._pres_hpa, self._humi_rh = t, p, h
        if assume_need_gas:
            self._gas_ohm = g

    def _estimate_eta_ms(self, *, need_gas: bool) -> int:
        tph = self._estimate_tph_time_ms()
        if not need_gas:
            return tph + 60

        run_gas, nb_conv, gas_total = self._read_nb_conv_and_total_gas_wait_ms()
        if not run_gas or gas_total <= 0:
            gas_total = 0
            steps = self._profile_steps
            for i in range(steps):
                gw = self._i2c.readfrom_mem(self._addr, self._REG_GAS_WAIT_0 + i, 1)[0]
                gas_total += self._decode_gas_wait_ms(gw)

        return tph + gas_total + 60

    def _set_run_gas(self, enable: bool):
        val = self._i2c.readfrom_mem(self._addr, self._REG_CTRL_GAS1, 1)[0]
        new = (val | 0x10) if enable else (val & ~0x10)
        if new != val:
            self._i2c.writeto_mem(self._addr, self._REG_CTRL_GAS1, bytes([new]))
        return new

    def _sat_vapor_pressure_hpa(self, T_c):
        return 6.112 * math.exp((17.62 * T_c) / (243.12 + T_c))

    def _compensate_rh_for_temp(self, rh_meas, temp):
        T_meas = temp - self._temperature_correction
        T_corr = temp
        e = (max(0.0, min(100.0, rh_meas)) / 100.0) * self._sat_vapor_pressure_hpa(T_meas)
        rh_corr = 100.0 * e / self._sat_vapor_pressure_hpa(T_corr)
        rh_corr = 0.0 if rh_corr < 0.0 else 100.0 if rh_corr > 100.0 else rh_corr
        return rh_corr

    def _temperature(self):
        return ((((self._t_fine * 5) + 128) / 256.0) / 100.0) + self._temperature_correction

    def _pressure(self):
        p = self._pressure_calibration
        var1 = (self._t_fine / 2.0) - 64000.0
        var2 = ((var1 / 4.0) * (var1 / 4.0)) / 2048.0
        var2 = (var2 * p[5]) / 4.0
        var2 = var2 + (var1 * p[4] * 2.0)
        var2 = (var2 / 4.0) + (p[3] * 65536.0)
        var1 = ((((var1 / 4.0) * (var1 / 4.0)) / 8192.0) * (p[2] * 32.0) / 8.0) + ((p[1] * var1) / 2.0)
        var1 = var1 / 262144.0
        var1 = ((32768.0 + var1) * p[0]) / 32768.0
        calc_pres = 1048576.0 - self._adc_pres
        calc_pres = (calc_pres - (var2 / 4096.0)) * 3125.0
        calc_pres = (calc_pres / var1) * 2.0
        var1 = (p[8] * (((calc_pres / 8.0) * (calc_pres / 8.0)) / 8192.0)) / 4096.0
        var2 = ((calc_pres / 4.0) * p[7]) / 8192.0
        var3 = (((calc_pres / 256.0) ** 3) * p[9]) / 131072.0
        calc_pres += (var1 + var2 + var3 + (p[6] * 128.0)) / 16.0
        return calc_pres / 100.0  # hPa

    def _humidity(self):
        h = self._humidity_calibration
        temp_scaled = ((self._t_fine * 5.0) + 128.0) / 256.0
        var1 = (self._adc_hum - (h[0] * 16.0)) - ((temp_scaled * h[2]) / 200.0)
        var2 = (h[1] * (((temp_scaled * h[3]) / 100.0) + (((temp_scaled * ((temp_scaled * h[4]) / 100.0)) / 64.0) / 100.0) + 16384.0)) / 1024.0
        var3 = var1 * var2
        var4 = (h[5] * 128.0 + ((temp_scaled * h[6]) / 100.0)) / 16.0
        var5 = ((var3 / 16384.0) * (var3 / 16384.0)) / 1024.0
        var6 = (var4 * var5) / 2.0
        calc_hum = ((((var3 + var6) / 1024.0) * 1000.0) / 4096.0) / 1000.0
        if abs(self._temperature_correction) > 1e-6:
            calc_hum = self._compensate_rh_for_temp(calc_hum, self._temperature())
        return 100.0 if calc_hum > 100.0 else 0.0 if calc_hum < 0.0 else calc_hum

    def _gas(self):
        adc = int(self._adc_gas)
        gr = int(self._gas_range) & 0x0F
        rs_err = int(self._sw_err)

        var1 = ((1340 + (5 * rs_err)) * self._GAS_LUT1[gr]) >> 16
        var2 = (((adc << 15) - 16777216) + var1)
        var3 = ((self._GAS_LUT2[gr] * var1) >> 9)
        var3 += (var2 >> 1)
        gas_res_ohm = (var3 // var2) if var2 != 0 else 0
        return float(gas_res_ohm)

    def _calc_res_heat(self, target_temp_c: int, amb_temp_c: float) -> int:
        t = min(int(target_temp_c), 400)
        gh1 = float(self.__par_gh1)
        gh2 = float(self.__par_gh2)
        gh3 = float(self.__par_gh3)
        htr = float(self._res_heat_range)
        htv = float(self._res_heat_val)
        var1 = (gh1 / 16.0) + 49.0
        var2 = (gh2 / 32768.0) * 0.0005 + 0.00235
        var3 = gh3 / 1024.0
        var4 = var1 * (1.0 + var2 * float(t))
        var5 = var4 + (var3 * float(amb_temp_c))
        res_heat = int(3.4 * ((var5 * (4.0 / (4.0 + htr)) * (1.0 / (1.0 + (htv * 0.002)))) - 25.0))
        return max(0, min(res_heat, 255))

    def _tph_cache_is_fresh(self) -> bool:
        ts = self._cache_ts_ms
        if ts is None or self._temp_c is None or self._pres_hpa is None or self._humi_rh is None:
            return False
        age = utime.ticks_diff(utime.ticks_ms(), ts)
        if age < 0:
            return False  # wrap-around case
        t_est_ms = self._estimate_tph_time_ms()
        return age <= (t_est_ms + 5)

    def _encode_gas_wait(self, ms: int) -> int:
        dur = int(ms)
        if dur >= 0xFC0:  # >=4032ms
            return 0xFF
        factor = 0
        while dur > 0x3F and factor < 3:
            dur //= 4
            factor += 1
        return int((dur & 0x3F) | (factor << 6))

    def _ensure_sample(self, *, need_gas: bool):
        if not need_gas and self._tph_cache_is_fresh():
            return

        self._perform_reading(need_gas=need_gas)
        t = self._temperature()
        p = self._pressure()
        h = self._humidity()
        g = None
        if need_gas and self._ready_gas:
            g = self._gas()
    
        self._cache_ts_ms = utime.ticks_ms()
        self._temp_c, self._pres_hpa, self._humi_rh = t, p, h
        if need_gas:
            self._gas_ohm = g

    def _median_cov(self, samples, window_size):
        if not samples:
            return (0.0, 1e9)  # median, cov%
        
        n = len(samples)
        w = max(1, min(window_size, n))
        xs = list(samples[-w:])
        xs.sort()
        mid = w // 2
        if w % 2 == 1:
            med = float(xs[mid])
        else:
            med = (xs[mid - 1] + xs[mid]) / 2.0

        s1 = 0.0
        s2 = 0.0
        for v in xs:
            s1 += v
            s2 += v * v
        mean = s1 / w
        mean_sq = s2 / w
        var = max(0.0, mean_sq - mean * mean)
        std = var ** 0.5
        cov = 1e9 if abs(mean) < 1e-12 else abs(std / mean) * 100.0
        return (float(med), float(cov))

    def _update_baseline_ema(self, new_baseline, alpha=0.02):
        self._gas_baseline = (1.0 - alpha) * float(self._gas_baseline) + alpha * float(new_baseline)
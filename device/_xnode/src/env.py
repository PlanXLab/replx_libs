# @package: xnode.env
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: none
# @platforms: xbee
# @tags: bh1750, bme680, illuminance, tphg, iaq, sensor

import gc
import utime
import ustruct
import machine
from micropython import const

class Illuminance:
    BH1750_ADDR = const(0x23)
    POWER_OFF = const(0x00)
    POWER_ON = const(0x01)
    POWER_RESET = const(0x07)
    CONT_HIGH_RES = const(0x10)
    CONT_HIGH_RES_2 = const(0x11)
    CONT_LOW_RES = const(0x13)
    ONE_TIME_HIGH_RES = const(0x20)
    ONE_TIME_HIGH_RES_2 = const(0x21)
    ONE_TIME_LOW_RES = const(0x23)

    def __init__(self, *, mode=CONT_HIGH_RES):
        self._addr = Illuminance.BH1750_ADDR
        self._i2c = machine.I2C(1)
        self._buf1 = bytearray(1)
        self._buf2 = bytearray(2)
        self._mode = mode
        self.init(mode)

    def _write_cmd(self, cmd):
        self._buf1[0] = cmd
        self._i2c.writeto(self._addr, self._buf1)

    def init(self, mode=CONT_HIGH_RES):
        self._mode = mode
        self._write_cmd(self.POWER_ON)
        self._write_cmd(self.POWER_RESET)
        self._write_cmd(mode)

    def deinit(self):
        self._write_cmd(self.POWER_OFF)

    def read_raw(self):
        self._i2c.readfrom_into(self._addr, self._buf2)
        return (self._buf2[0] << 8) | self._buf2[1]

    def read_lux(self, continuous=True):
        raw = self.read(continuous=continuous)
        scale = 2.4 if self._mode in (self.CONT_HIGH_RES_2, self.ONE_TIME_HIGH_RES_2) else 1.2
        return round(raw / scale, 1)

    def read(self, continuous=True):
        if not continuous:
            one_mode = self.ONE_TIME_LOW_RES if self._mode in (self.CONT_LOW_RES, self.ONE_TIME_LOW_RES) else (
                self.ONE_TIME_HIGH_RES_2 if self._mode in (self.CONT_HIGH_RES_2, self.ONE_TIME_HIGH_RES_2) else self.ONE_TIME_HIGH_RES
            )
            self._write_cmd(self.POWER_ON)
            self._write_cmd(one_mode)
            utime.sleep_ms(24 if one_mode == self.ONE_TIME_LOW_RES else 180)
        return self.read_raw()

class Tphg:
    BME680_ADDR = const(0x77)
    FORCED_MODE = const(0x01)
    SLEEP_MODE = const(0x00)

    # Compact integer lookup tables to minimize float tuple overhead in RAM
    _LOOKUP_1 = (
        2147483647, 2147483647, 2147483647, 2147483647,
        2147483647, 2126008810, 2147483647, 2130303777,
        2147483647, 2147483647, 2143188679, 2136746228,
        2147483647, 2126008810, 2147483647, 2147483647
    )

    _LOOKUP_2 = (
        4096000000, 2048000000, 1024000000, 512000000,
        255744255, 127110228, 64000000, 32258064,
        16016016, 8000000, 4000000, 2000000,
        1000000, 500000, 250000, 125000
    )

    def __init__(self, temp_weighting=0.10, pressure_weighting=0.05, humi_weighting=0.20, gas_weighting=0.65,
                 gas_ema_alpha=0.1, temp_baseline=23.0, pressure_baseline=1013.25, humi_baseline=45.0, gas_baseline=450000):
        total_weighting = temp_weighting + pressure_weighting + humi_weighting + gas_weighting
        if abs(total_weighting - 1.0) > 0.001:
            raise ValueError("The sum of weightings is not equal to 1.")

        self._addr = Tphg.BME680_ADDR
        self._i2c = machine.I2C(1)
        self._buf1 = bytearray(1)
        self._buf17 = bytearray(17)

        self._write_reg(0xE0, 0xB6)  # Soft reset
        utime.sleep_ms(5)

        self._set_power_mode(Tphg.SLEEP_MODE)

        t_cal = bytearray(41)
        self._i2c.readfrom_mem_into(self._addr, 0x89, memoryview(t_cal)[:25])
        self._i2c.readfrom_mem_into(self._addr, 0xE1, memoryview(t_cal)[25:])
        self._sw_err = (self._read_reg(0x04) & 0xF0) / 16.0

        cal = ustruct.unpack("<hbBHhbBhhbbHhhBBBHbbbBbHhbb", memoryview(t_cal)[1:39])
        del t_cal
        self._temp_cal = (float(cal[23]), float(cal[0]), float(cal[1]))
        self._pres_cal = (
            float(cal[3]), float(cal[4]), float(cal[5]), float(cal[7]), float(cal[8]),
            float(cal[10]), float(cal[9]), float(cal[12]), float(cal[13]), float(cal[14])
        )

        h0 = cal[17] / 16.0
        h1 = (cal[16] * 16.0) + (cal[17] % 16.0)
        self._hum_cal = (h0, h1, float(cal[18]), float(cal[19]), float(cal[20]), float(cal[21]), float(cal[22]))
        del cal
        gc.collect()

        self._write_reg(0x72, 0b001)                        # Humidity oversampling x1
        self._write_reg(0x74, (0b010 << 5) | (0b011 << 2))  # Temp oversampling x2, Pres oversampling x4
        self._write_reg(0x75, 0b001 << 2)                   # Filter coeff 3
        self._write_reg(0x50, 0x1F)                         # idac_heat_0
        self._write_reg(0x5A, 0x73)                         # res_heat_0
        self._write_reg(0x64, 0x64)                         # gas_wait_0 (100ms)
        self._write_reg(0x71, 0b1 << 4)                     # run_gas=1, nb_conv=0
        utime.sleep_ms(50)

        self._temperature_offset = -10.0
        self._t_fine = 0
        self._adc_pres = 0.0
        self._adc_temp = 0.0
        self._adc_hum = 0
        self._adc_gas = 0
        self._gas_range = 0

        self.temp_weighting = temp_weighting
        self.pressure_weighting = pressure_weighting
        self.humi_weighting = humi_weighting
        self.gas_weighting = gas_weighting
        self.gas_ema_alpha = gas_ema_alpha
        self.temp_baseline = temp_baseline
        self.pressure_baseline = pressure_baseline
        self.humi_baseline = humi_baseline
        self.gas_baseline = gas_baseline

    def _read_reg(self, reg):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf1)
        return self._buf1[0]

    def _write_reg(self, reg, val):
        self._buf1[0] = val & 0xFF
        self._i2c.writeto_mem(self._addr, reg, self._buf1)

    def _set_power_mode(self, value):
        tmp = (self._read_reg(0x74) & ~0x03) | value
        self._write_reg(0x74, tmp)

    def _perform_reading(self):
        self._set_power_mode(Tphg.FORCED_MODE)

        t_end = utime.ticks_add(utime.ticks_ms(), 150)
        while utime.ticks_diff(t_end, utime.ticks_ms()) > 0:
            if (self._read_reg(0x1D) & 0x20) == 0:
                break
            utime.sleep_ms(5)

        ready = False
        t_end = utime.ticks_add(utime.ticks_ms(), 150)
        while utime.ticks_diff(t_end, utime.ticks_ms()) > 0:
            if (self._read_reg(0x1D) & 0x80) != 0:
                ready = True
                break
            utime.sleep_ms(5)

        if not ready:
            raise OSError("BME680 sensor data not ready")

        buf = self._buf17
        self._i2c.readfrom_mem_into(self._addr, 0x1D, buf)
        self._adc_pres = (buf[2] * 4096.0) + (buf[3] * 16.0) + (buf[4] / 16.0)
        self._adc_temp = (buf[5] * 4096.0) + (buf[6] * 16.0) + (buf[7] / 16.0)
        self._adc_hum = (buf[8] << 8) | buf[9]
        self._adc_gas = ((buf[13] << 8) | buf[14]) >> 6
        self._gas_range = buf[14] & 0x0F

        tc = self._temp_cal
        var1 = (self._adc_temp / 8.0) - (tc[0] * 2.0)
        var2 = (var1 * tc[1]) / 2048.0
        var3 = (((var1 / 2.0) * (var1 / 2.0)) / 4096.0) * (tc[2] * 16.0) / 16384.0
        self._t_fine = int(var2 + var3)

    def _temperature(self):
        return ((((self._t_fine * 5) + 128) / 256.0) / 100.0) + self._temperature_offset

    def _pressure(self):
        pc = self._pres_cal
        var1 = (self._t_fine / 2.0) - 64000.0
        var2 = (((var1 / 4.0) * (var1 / 4.0)) / 2048.0) * pc[5] / 4.0
        var2 = var2 + (var1 * pc[4] * 2.0)
        var2 = (var2 / 4.0) + (pc[3] * 65536.0)
        var1 = (((((var1 / 4.0) * (var1 / 4.0)) / 8192.0) * (pc[2] * 32.0) / 8.0) + ((pc[1] * var1) / 2.0)) / 262144.0
        var1 = ((32768.0 + var1) * pc[0]) / 32768.0
        calc_pres = ((1048576.0 - self._adc_pres) - (var2 / 4096.0)) * 3125.0
        calc_pres = (calc_pres / var1) * 2.0
        var1 = (pc[8] * (((calc_pres / 8.0) * (calc_pres / 8.0)) / 8192.0)) / 4096.0
        var2 = ((calc_pres / 4.0) * pc[7]) / 8192.0
        var3 = (((calc_pres / 256.0) ** 3) * pc[9]) / 131072.0
        calc_pres += (var1 + var2 + var3 + (pc[6] * 128.0)) / 16.0
        return calc_pres / 100.0

    def _humidity(self):
        hc = self._hum_cal
        temp_scaled = ((self._t_fine * 5) + 128) / 256.0
        var1 = (self._adc_hum - (hc[0] * 16.0)) - ((temp_scaled * hc[2]) / 200.0)
        var2 = (hc[1] * (((temp_scaled * hc[3]) / 100.0) + (((temp_scaled * ((temp_scaled * hc[4]) / 100.0)) / 64.0) / 100.0) + 16384.0)) / 1024.0
        var3 = var1 * var2
        var4 = ((hc[5] * 128.0) + ((temp_scaled * hc[6]) / 100.0)) / 16.0
        var5 = ((var3 / 16384.0) * (var3 / 16384.0)) / 1024.0
        var6 = (var4 * var5) / 2.0
        calc_hum = ((((var3 + var6) / 1024.0) * 1000.0) / 4096.0) / 1000.0
        return 100.0 if calc_hum > 100.0 else 0.0 if calc_hum < 0.0 else calc_hum

    def _gas(self):
        gr = self._gas_range & 0x0F
        var1 = ((1340.0 + (5.0 * self._sw_err)) * self._LOOKUP_1[gr]) / 65536.0
        var2 = ((self._adc_gas * 32768.0) - 16777216.0) + var1
        var3 = (self._LOOKUP_2[gr] * var1) / 512.0
        return (var3 + (var2 / 2.0)) / var2

    @property
    def temperature_offset(self):
        return self._temperature_offset

    @temperature_offset.setter
    def temperature_offset(self, value):
        self._temperature_offset = float(value)

    def set_temperature_correction(self, value, relative=True):
        if relative:
            self._temperature_offset += value
        else:
            self._temperature_offset = float(value)

    @property
    def temperature(self):
        self._perform_reading()
        return self._temperature()

    @property
    def pressure(self):
        self._perform_reading()
        return self._pressure()

    @property
    def humidity(self):
        self._perform_reading()
        return self._humidity()

    @property
    def gas(self):
        self._perform_reading()
        return self._gas()

    def read(self, gas=False):
        self._perform_reading()
        if not gas:
            return self._temperature(), self._pressure(), self._humidity(), None
        return self._temperature(), self._pressure(), self._humidity(), self._gas()

    def sealevel(self, altitude):
        self._perform_reading()
        press = self._pressure()
        return press / pow((1.0 - altitude / 44330.0), 5.255), press

    def altitude(self, sealevel=1013.25):
        self._perform_reading()
        press = self._pressure()
        return 44330.0 * (1.0 - pow(press / sealevel, 1.0 / 5.255)), press

    def iaq(self):
        self._perform_reading()
        temp = self._temperature()
        pres = self._pressure()
        humi = self._humidity()
        gas = self._gas()

        hum_offset = humi - self.humi_baseline
        hum_score = (1.0 - min(max(abs(hum_offset) / (self.humi_baseline * 2.0), 0.0), 1.0)) * (self.humi_weighting * 100.0)

        temp_offset = temp - self.temp_baseline
        temp_score = (1.0 - min(max(abs(temp_offset) / 10.0, 0.0), 1.0)) * (self.temp_weighting * 100.0)

        self.gas_baseline = (self.gas_ema_alpha * gas) + ((1.0 - self.gas_ema_alpha) * self.gas_baseline)
        gas_offset = self.gas_baseline - gas
        gas_score = (gas_offset / self.gas_baseline) * (self.gas_weighting * 100.0)
        gas_score = max(0.0, min(gas_score, self.gas_weighting * 100.0))

        pressure_offset = pres - self.pressure_baseline
        pressure_score = (1.0 - min(max(abs(pressure_offset) / 50.0, 0.0), 1.0)) * (self.pressure_weighting * 100.0)

        iaq_score = round((hum_score + temp_score + gas_score + pressure_score) * 5.0)
        return iaq_score, temp, pres, humi, gas

    def burn_in(self, threshold=0.01, count=10, timeout_sec=180):
        self._perform_reading()
        prev_gas = self._gas()

        counter = 0
        timeout_ms = timeout_sec * 1000
        t_start = utime.ticks_ms()
        t_interval = t_start

        while True:
            now = utime.ticks_ms()
            if utime.ticks_diff(now, t_interval) >= 1000:
                self._perform_reading()
                curr_gas = self._gas()
                gas_change = abs((curr_gas - prev_gas) / prev_gas) if prev_gas else 0.0

                counter = counter + 1 if gas_change <= threshold else 0
                if counter > count:
                    yield True, curr_gas, 0.0
                    break
                else:
                    yield False, curr_gas, gas_change

                prev_gas = curr_gas
                t_interval = utime.ticks_ms()

            if utime.ticks_diff(utime.ticks_ms(), t_start) > timeout_ms:
                yield False, 0.0, 0.0
                break
            utime.sleep_ms(10)

    burnIn = burn_in

gc.collect()

# @package: xnode.diag
# @version: 1.4.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: termviz
# @platforms: xbee
# @tags: diagnostics, i2cdetect, xbee

import gc
import uos
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

gc.collect()

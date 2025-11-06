import machine
import gc
import uos
import micropython

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


@micropython.native
def get_sys_info() -> tuple:
    freq = machine.freq()
    
    try:
        adc = machine.ADC(4)
    except ValueError:
        adc = machine.ADC(machine.Pin(29))
    
    raw = adc.read_u16()
    voltage = raw * (3.3 / 65535)
    temp = 27.0 - (voltage - 0.706) / 0.001721
    
    return (freq, temp)


def get_mem_info() -> tuple:
    free = gc.mem_free()
    allocated = gc.mem_alloc()
    total = free + allocated
    
    return (free, allocated, total)


def get_fs_info(path: str = '/') -> tuple:
    stat = uos.statvfs(path)
    
    block_size = stat[0]
    total_blocks = stat[2]
    free_blocks = stat[3]
    
    total = block_size * total_blocks
    free = block_size * free_blocks
    used = total - free
    
    return (total, used, free)

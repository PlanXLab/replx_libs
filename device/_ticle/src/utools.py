# @package: utools
# @version: 1.3
# @type: device-specific
# @category: utility
# @interface: none
# @depends: none
# @platforms: rp2
# @tags: pio, state-machine, rp2, utility
# @author: PlanXLab Development Team

import rp2

_SM_PREFERRED_ORDER = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1)


def find_free_sm(count: int | None = None, pio: int | list[int] | tuple[int, ...] | None = None) -> list[int]:
    @rp2.asm_pio()
    def _nop():
        nop()

    if count is not None:
        count = int(count)
        if count < 0:
            raise ValueError("count must be >= 0")
        if count == 0:
            return []
    
    if pio is None:
        order = _SM_PREFERRED_ORDER
    elif isinstance(pio, (list, tuple)):
        blocks = [int(b) for b in pio]
        for b in blocks:
            if b not in (0, 1, 2):
                raise ValueError("PIO block ID must be 0, 1, or 2")
        if set(blocks) == {0, 1, 2}:
            order = _SM_PREFERRED_ORDER
        else:
            pools = {
                0: (2, 3, 0, 1),
                1: (4, 5, 6, 7),
                2: (8, 9, 10, 11)
            }
            order = []
            for b in blocks:
                for sm_id in pools[b]:
                    if sm_id not in order:
                        order.append(sm_id)
    else:
        b = int(pio)
        if b == 0:
            order = (2, 3, 0, 1)
        elif b == 1:
            order = (4, 5, 6, 7)
        elif b == 2:
            order = (8, 9, 10, 11)
        else:
            raise ValueError("pio must be 0, 1, or 2")

    available = []
    for i in order:
        try:
            sm = rp2.StateMachine(i, _nop)
            sm.active(0)
            available.append(i)
            if count is not None and len(available) >= count:
                return available
        except:
            pass
    
    if count is None:
        return available
    
    if len(available) < count:
        pio_str = f" on PIO {pio}" if pio is not None else ""
        raise RuntimeError(f"Need {count} SM{pio_str}, only {len(available)} available")
    
    return available


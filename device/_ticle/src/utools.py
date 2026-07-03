# @package: utools
# @version: 1.2
# @type: device-specific
# @category: utility
# @interface: none
# @depends: none
# @platforms: rp2
# @tags: pio, state-machine, rp2, utility
# @author: PlanXLab Development Team

import rp2

_SM_PREFERRED_ORDER = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1)


def find_free_sm(count: int | None = None) -> list[int]:
    @rp2.asm_pio()
    def _nop():
        nop()

    if count is not None:
        count = int(count)
        if count < 0:
            raise ValueError("count must be >= 0")
        if count == 0:
            return []
    
    available = []
    for i in _SM_PREFERRED_ORDER:
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
        raise RuntimeError(f"Need {count} SM, only {len(available)} available")
    
    return available


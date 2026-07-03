# @package: termviz
# @version: 1.0.0
# @type: core
# @category: utility
# @interface: none
# @depends: none
# @platforms: EFR32MG
# @tags: terminal,color, ansi
# @author: PlanXLab Development Team

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

"""Full-size ANSI keyboard layout for the visual key picker."""

from dataclasses import dataclass


@dataclass(frozen=True)
class KeyDef:
    label: str
    key_id: str
    width: float = 1.0
    height: float = 1.0


@dataclass(frozen=True)
class KeyRow:
    keys: tuple[KeyDef, ...]
    gap_before: float = 0.0


def _fn(label: str, n: int) -> KeyDef:
    return KeyDef(label, f"key:f{n}")


def _vk(label: str, code: int, width: float = 1.0, height: float = 1.0) -> KeyDef:
    return KeyDef(label, f"vk:{code}", width, height)


def _char(label: str, ch: str, width: float = 1.0) -> KeyDef:
    return KeyDef(label, f"char:{ch}", width)


def _key(label: str, name: str, width: float = 1.0) -> KeyDef:
    return KeyDef(label, f"key:{name}", width)


KEYBOARD_ROWS: tuple[KeyRow, ...] = (
    KeyRow(
        (
            _key("Esc", "esc"),
            _fn("F1", 1),
            _fn("F2", 2),
            _fn("F3", 3),
            _fn("F4", 4),
            _fn("F5", 5),
            _fn("F6", 6),
            _fn("F7", 7),
            _fn("F8", 8),
            _fn("F9", 9),
            _fn("F10", 10),
            _fn("F11", 11),
            _fn("F12", 12),
            _key("PrtSc", "print_screen"),
            _key("ScrLk", "scroll_lock"),
            _key("Pause", "pause"),
        ),
        gap_before=0,
    ),
    KeyRow(
        (
            _char("`", "`"),
            _char("1", "1"),
            _char("2", "2"),
            _char("3", "3"),
            _char("4", "4"),
            _char("5", "5"),
            _char("6", "6"),
            _char("7", "7"),
            _char("8", "8"),
            _char("9", "9"),
            _char("0", "0"),
            _char("-", "-"),
            _char("=", "="),
            _key("Backspace", "backspace", 2.0),
        ),
        gap_before=0,
    ),
    KeyRow(
        (
            _key("Tab", "tab", 1.5),
            _char("Q", "q"),
            _char("W", "w"),
            _char("E", "e"),
            _char("R", "r"),
            _char("T", "t"),
            _char("Y", "y"),
            _char("U", "u"),
            _char("I", "i"),
            _char("O", "o"),
            _char("P", "p"),
            _char("[", "["),
            _char("]", "]"),
            _char("\\", "\\", 1.5),
        ),
        gap_before=0,
    ),
    KeyRow(
        (
            _key("Caps", "caps_lock", 1.75),
            _char("A", "a"),
            _char("S", "s"),
            _char("D", "d"),
            _char("F", "f"),
            _char("G", "g"),
            _char("H", "h"),
            _char("J", "j"),
            _char("K", "k"),
            _char("L", "l"),
            _char(";", ";"),
            _char("'", "'"),
            _key("Enter", "enter", 2.25),
        ),
        gap_before=0,
    ),
    KeyRow(
        (
            _key("Shift", "shift", 2.25),
            _char("Z", "z"),
            _char("X", "x"),
            _char("C", "c"),
            _char("V", "v"),
            _char("B", "b"),
            _char("N", "n"),
            _char("M", "m"),
            _char(",", ","),
            _char(".", "."),
            _char("/", "/"),
            _key("Shift", "shift_r", 2.75),
        ),
        gap_before=0,
    ),
    KeyRow(
        (
            _key("Ctrl", "ctrl_l", 1.25),
            _key("Win", "cmd", 1.25),
            _key("Alt", "alt_l", 1.25),
            _key("Space", "space", 6.25),
            _key("Alt", "alt_gr", 1.25),
            _key("Win", "cmd_r", 1.25),
            _key("Menu", "menu", 1.25),
            _key("Ctrl", "ctrl_r", 1.25),
        ),
        gap_before=0,
    ),
)

NAV_CLUSTER_ROWS: tuple[KeyRow, ...] = (
    KeyRow((_key("Ins", "insert"), _key("Home", "home"), _key("PgUp", "page_up")), gap_before=0),
    KeyRow((_key("Del", "delete"), _key("End", "end"), _key("PgDn", "page_down")), gap_before=0),
    KeyRow((), gap_before=0),
    KeyRow((_key("↑", "up"),), gap_before=1.0),
    KeyRow((_key("←", "left"), _key("↓", "down"), _key("→", "right")), gap_before=0),
)

NUMPAD_ROWS: tuple[KeyRow, ...] = (
    KeyRow((_key("Num", "num_lock"), _vk("/", 111), _vk("*", 106), _vk("-", 109)), gap_before=0),
    KeyRow((_vk("7", 103), _vk("8", 104), _vk("9", 105), _vk("+", 107, height=2.0)), gap_before=0),
    KeyRow((_vk("4", 100), _vk("5", 101), _vk("6", 102)), gap_before=0),
    KeyRow((_vk("1", 97), _vk("2", 98), _vk("3", 99), _key("Enter", "enter")), gap_before=0),
    KeyRow((_vk("0", 96, width=2.0), _vk(".", 110)), gap_before=0),
)

ALL_LAYOUT_KEY_IDS: frozenset[str] = frozenset(
    key.key_id
    for section in (KEYBOARD_ROWS, NAV_CLUSTER_ROWS, NUMPAD_ROWS)
    for row in section
    for key in row.keys
)

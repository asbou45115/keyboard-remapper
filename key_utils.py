"""Serialize pynput keys to stable string IDs for storage and remapping."""

from pynput import keyboard

# Common Windows virtual key codes -> readable names
VK_NAMES = {
    8: "Backspace",
    9: "Tab",
    13: "Enter",
    16: "Shift",
    17: "Ctrl",
    18: "Alt",
    20: "Caps Lock",
    27: "Escape",
    32: "Space",
    33: "Page Up",
    34: "Page Down",
    35: "End",
    36: "Home",
    37: "Left",
    38: "Up",
    39: "Right",
    40: "Down",
    45: "Insert",
    46: "Delete",
    96: "Numpad 0",
    97: "Numpad 1",
    98: "Numpad 2",
    99: "Numpad 3",
    100: "Numpad 4",
    101: "Numpad 5",
    102: "Numpad 6",
    103: "Numpad 7",
    104: "Numpad 8",
    105: "Numpad 9",
    106: "Numpad *",
    107: "Numpad +",
    109: "Numpad -",
    110: "Numpad .",
    111: "Numpad /",
    112: "F1",
    113: "F2",
    114: "F3",
    115: "F4",
    116: "F5",
    117: "F6",
    118: "F7",
    119: "F8",
    120: "F9",
    121: "F10",
    122: "F11",
    123: "F12",
}

DEFAULT_MAPPINGS = {
    "vk:104": "char:w",
    "vk:100": "char:a",
    "vk:102": "char:d",
    "vk:98": "char:s",
}


def key_to_id(key) -> str | None:
    """Convert a pynput key event into a stable string identifier."""
    if isinstance(key, keyboard.Key):
        return f"key:{key.name}"

    char = getattr(key, "char", None)
    if char is not None and char.isprintable():
        return f"char:{char.lower()}"

    vk = getattr(key, "vk", None)
    if vk is not None:
        return f"vk:{vk}"

    return None


def parse_key_id(key_id: str):
    """Convert a stored string identifier back into a pynput key object."""
    prefix, value = key_id.split(":", 1)
    if prefix == "char":
        return keyboard.KeyCode.from_char(value)
    if prefix == "key":
        return keyboard.Key[value]
    if prefix == "vk":
        return keyboard.KeyCode.from_vk(int(value))
    raise ValueError(f"Unknown key id format: {key_id}")


def key_id_to_display(key_id: str) -> str:
    """Human-readable label for a stored key identifier."""
    prefix, value = key_id.split(":", 1)
    if prefix == "char":
        return value.upper()
    if prefix == "key":
        return value.replace("_", " ").title()
    if prefix == "vk":
        return VK_NAMES.get(int(value), f"VK {value}")
    return key_id

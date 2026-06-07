"""Visual full-size keyboard for picking keys to remap."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from keyboard_layout import KEYBOARD_ROWS, NAV_CLUSTER_ROWS, NUMPAD_ROWS, KeyDef, KeyRow


KEY_UNIT_W = 42
KEY_UNIT_H = 42
KEY_GAP = 3
SECTION_GAP = 18

FILL_DEFAULT = "#3c3c3c"
FILL_HOVER = "#505050"
FILL_SELECTED = "#2563eb"
FILL_MAPPED = "#166534"
OUTLINE = "#555555"
TEXT = "#f0f0f0"


@dataclass(frozen=True)
class PlacedKey:
    key: KeyDef
    x: int
    y: int
    width: int
    height: int



def _place_rows(rows: tuple[KeyRow, ...], x_offset: float, y_offset: float = 0.0) -> list[PlacedKey]:
    placed: list[PlacedKey] = []
    y = y_offset

    for row in rows:
        x = x_offset + row.gap_before * (KEY_UNIT_W + KEY_GAP)
        row_height = 1.0

        for key in row.keys:
            w = int(key.width * KEY_UNIT_W + (key.width - 1) * KEY_GAP)
            h = int(key.height * KEY_UNIT_H + (key.height - 1) * KEY_GAP)
            row_height = max(row_height, key.height)
            placed.append(PlacedKey(key, int(x), int(y), w, h))
            x += w + KEY_GAP

        y += row_height * KEY_UNIT_H + KEY_GAP

    return placed


def _layout_keys() -> list[PlacedKey]:
    main = _place_rows(KEYBOARD_ROWS, 0, 0)
    main_width = max(pk.x + pk.width for pk in main)

    nav_y = KEY_UNIT_H + KEY_GAP
    nav = _place_rows(NAV_CLUSTER_ROWS, main_width + SECTION_GAP, nav_y)

    numpad_y = KEY_UNIT_H + KEY_GAP
    numpad_x = main_width + SECTION_GAP
    if nav:
        numpad_x = max(pk.x + pk.width for pk in nav) + SECTION_GAP

    numpad = _place_numpad(numpad_x, numpad_y)
    return main + nav + numpad


def _place_numpad(x_start: float, y_start: float) -> list[PlacedKey]:
    """Place numpad with tall + and Enter keys."""
    placed: list[PlacedKey] = []
    x = x_start
    y = y_start

    def add(key: KeyDef, px: float, py: float) -> None:
        w = int(key.width * KEY_UNIT_W + (key.width - 1) * KEY_GAP)
        h = int(key.height * KEY_UNIT_H + (key.height - 1) * KEY_GAP)
        placed.append(PlacedKey(key, int(px), int(py), w, h))

    row0 = NUMPAD_ROWS[0].keys
    cx = x
    for key in row0:
        add(key, cx, y)
        cx += int(key.width * KEY_UNIT_W + KEY_GAP)

    y += KEY_UNIT_H + KEY_GAP
    row1 = NUMPAD_ROWS[1].keys
    cx = x
    plus_key = row1[3]
    for key in row1[:3]:
        add(key, cx, y)
        cx += KEY_UNIT_W + KEY_GAP
    add(plus_key, cx, y)

    y2 = y + KEY_UNIT_H + KEY_GAP
    row2 = NUMPAD_ROWS[2].keys
    cx = x
    for key in row2:
        add(key, cx, y2)
        cx += KEY_UNIT_W + KEY_GAP

    y3 = y2 + KEY_UNIT_H + KEY_GAP
    row3 = NUMPAD_ROWS[3].keys
    cx = x
    enter_key = row3[3]
    for key in row3[:3]:
        add(key, cx, y3)
        cx += KEY_UNIT_W + KEY_GAP
    add(enter_key, cx, y3)

    y4 = y3 + KEY_UNIT_H + KEY_GAP
    row4 = NUMPAD_ROWS[4].keys
    zero, dot = row4
    add(zero, x, y4)
    add(dot, x + int(2 * KEY_UNIT_W + KEY_GAP), y4)

    return placed


class VisualKeyboard(tk.Canvas):
    def __init__(
        self,
        master,
        on_key_selected: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, highlightthickness=0, **kwargs)
        self._on_key_selected = on_key_selected
        self._placed = _layout_keys()
        self._selected_id: str | None = None
        self._mapped_targets: set[str] = set()
        self._item_to_key_id: dict[int, str] = {}
        self._key_id_to_items: dict[str, list[int]] = {}

        width = max(pk.x + pk.width for pk in self._placed) + 8
        height = max(pk.y + pk.height for pk in self._placed) + 8
        self.configure(width=width, height=height, bg="#2b2b2b")

        self._draw_keys()
        self.bind("<Button-1>", self._on_click)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)

    def _draw_keys(self) -> None:
        for placed in self._placed:
            fill = self._fill_for(placed.key.key_id)
            rect = self.create_rectangle(
                placed.x,
                placed.y,
                placed.x + placed.width,
                placed.y + placed.height,
                fill=fill,
                outline=OUTLINE,
                width=1,
                tags=("key", placed.key.key_id),
            )
            text = self.create_text(
                placed.x + placed.width // 2,
                placed.y + placed.height // 2,
                text=placed.key.label,
                fill=TEXT,
                font=("Segoe UI", 8),
                tags=("key", placed.key.key_id),
            )
            self._item_to_key_id[rect] = placed.key.key_id
            self._item_to_key_id[text] = placed.key.key_id
            self._key_id_to_items.setdefault(placed.key.key_id, []).extend([rect, text])

    def _fill_for(self, key_id: str) -> str:
        if key_id == self._selected_id:
            return FILL_SELECTED
        if key_id in self._mapped_targets:
            return FILL_MAPPED
        return FILL_DEFAULT

    def _refresh_colors(self) -> None:
        for key_id, items in self._key_id_to_items.items():
            fill = self._fill_for(key_id)
            for item in items:
                if self.type(item) == "rectangle":
                    self.itemconfigure(item, fill=fill)

    def set_selected(self, key_id: str | None) -> None:
        self._selected_id = key_id
        self._refresh_colors()

    def set_mapped_targets(self, targets: set[str]) -> None:
        self._mapped_targets = set(targets)
        self._refresh_colors()

    def _key_at(self, x: int, y: int) -> str | None:
        item = self.find_overlapping(x, y, x, y)
        for iid in item:
            key_id = self._item_to_key_id.get(iid)
            if key_id is not None:
                return key_id
        return None

    def _on_click(self, event) -> None:
        key_id = self._key_at(event.x, event.y)
        if key_id is not None:
            self._on_key_selected(key_id)

    def _on_motion(self, event) -> None:
        key_id = self._key_at(event.x, event.y)
        for placed in self._placed:
            fill = self._fill_for(placed.key.key_id)
            if (
                key_id == placed.key.key_id
                and placed.key.key_id != self._selected_id
                and placed.key.key_id not in self._mapped_targets
            ):
                fill = FILL_HOVER
            for item in self._key_id_to_items.get(placed.key.key_id, []):
                if self.type(item) == "rectangle":
                    self.itemconfigure(item, fill=fill)

    def _on_leave(self, _event) -> None:
        self._refresh_colors()

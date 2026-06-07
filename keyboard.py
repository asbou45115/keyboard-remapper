"""GUI key remapper — map any key to any key."""

import json
import sys
import tkinter as tk
from pathlib import Path
from threading import Event, Thread
from tkinter import messagebox, ttk

from key_utils import key_id_to_display
from keyboard_widget import VisualKeyboard
from remapper_engine import RemapperEngine, capture_key


def resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative


def config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "mappings.json"
    return Path(__file__).parent / "mappings.json"


def load_mappings() -> dict[str, str]:
    path = config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_mappings(mappings: dict[str, str]) -> None:
    path = config_path()
    path.write_text(json.dumps(mappings, indent=2), encoding="utf-8")


class KeyRemapperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Key Remapper")
        self.geometry("1120x720")
        self.minsize(1120, 600)
        self._set_window_icon()

        self.mappings = load_mappings()
        self.engine = RemapperEngine(self.mappings)
        self._pending_source: str | None = None
        self._pending_target: str | None = None
        self._listening_for_source = False
        self._capture_cancel = Event()

        self._build_ui()
        self._refresh_mapping_list()
        self._start_source_listen()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        icon = resource_path("assets/keyboard_linux_6170.ico")
        if icon.exists():
            try:
                self.iconbitmap(str(icon))
            except tk.TclError:
                pass

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(outer)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        self.toggle_btn = ttk.Button(status_frame, text="Start Remapping", command=self._toggle_remapping)
        self.toggle_btn.pack(side=tk.RIGHT)

        list_frame = ttk.LabelFrame(outer, text="Mappings", padding=8)
        list_frame.pack(fill=tk.X, pady=(0, 10))

        columns = ("source", "target")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5)
        self.tree.heading("source", text="From (your keyboard)")
        self.tree.heading("target", text="To (visual keyboard)")
        self.tree.column("source", width=200)
        self.tree.column("target", width=200)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(outer, text="Remove Selected", command=self._remove_selected).pack(anchor=tk.W, pady=(0, 10))

        add_frame = ttk.LabelFrame(outer, text="Add Mapping", padding=8)
        add_frame.pack(fill=tk.BOTH, expand=True)

        self.hint_var = tk.StringVar(
            value="Press a key on your physical keyboard, then click the key on the visual keyboard it should become."
        )
        ttk.Label(add_frame, textvariable=self.hint_var, wraplength=900).pack(anchor=tk.W, pady=(0, 6))

        mapping_row = ttk.Frame(add_frame)
        mapping_row.pack(fill=tk.X, pady=(0, 8))

        self.source_var = tk.StringVar(value="Press a key on your keyboard...")
        self.target_var = tk.StringVar(value="(not set)")

        ttk.Label(mapping_row, text="From:", width=6).pack(side=tk.LEFT)
        ttk.Label(mapping_row, textvariable=self.source_var, font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 24)
        )
        ttk.Label(mapping_row, text="To:", width=4).pack(side=tk.LEFT)
        ttk.Label(mapping_row, textvariable=self.target_var, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        kb_container = ttk.Frame(add_frame)
        kb_container.pack(fill=tk.BOTH, expand=True)

        self.visual_keyboard = VisualKeyboard(kb_container, on_key_selected=self._on_visual_key_selected)
        self.visual_keyboard.pack(anchor=tk.W)
        self._sync_keyboard_highlights()

        btn_row = ttk.Frame(add_frame)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Clear", command=self._clear_capture_fields).pack(side=tk.LEFT)

        ttk.Label(
            outer,
            text="Tip: Green keys on the visual keyboard are already mapped targets. Stop remapping before adding new mappings.",
            foreground="gray",
        ).pack(anchor=tk.W, pady=(8, 0))

    def _sync_keyboard_highlights(self) -> None:
        self.visual_keyboard.set_mapped_targets(set(self.mappings.values()))
        self.visual_keyboard.set_selected(self._pending_target)

    def _refresh_mapping_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for source_id, target_id in sorted(self.mappings.items(), key=lambda item: key_id_to_display(item[0])):
            self.tree.insert(
                "",
                tk.END,
                iid=source_id,
                values=(key_id_to_display(source_id), key_id_to_display(target_id)),
            )
        self._sync_keyboard_highlights()

    def _persist(self) -> None:
        save_mappings(self.mappings)
        self.engine.set_mappings(self.mappings)

    def _toggle_remapping(self) -> None:
        if self.engine.running:
            self.engine.stop()
            self.status_var.set("Stopped")
            self.toggle_btn.configure(text="Start Remapping")
            self._start_source_listen()
        else:
            if not self.mappings:
                messagebox.showwarning("No mappings", "Add at least one key mapping first.")
                return
            self._stop_source_listen()
            self.engine.start()
            self.status_var.set("Running")
            self.toggle_btn.configure(text="Stop Remapping")

    def _on_visual_key_selected(self, key_id: str) -> None:
        if self.engine.running:
            messagebox.showinfo("Stop remapping", "Stop remapping before adding new mappings.")
            return
        if self._pending_source is None:
            messagebox.showinfo("Select source first", "Press a key on your physical keyboard first.")
            return

        self._pending_target = key_id
        self.target_var.set(key_id_to_display(key_id))
        self._sync_keyboard_highlights()
        self._apply_pending_mapping()

    def _start_source_listen(self) -> None:
        if self.engine.running:
            return
        self._capture_cancel.set()
        self._capture_cancel = Event()
        cancel = self._capture_cancel
        self._listening_for_source = True
        Thread(target=self._run_source_capture, args=(cancel,), daemon=True).start()

    def _stop_source_listen(self) -> None:
        self._listening_for_source = False
        self._capture_cancel.set()

    def _run_source_capture(self, cancel: Event) -> None:
        key_id = capture_key(timeout=None, cancel=cancel)

        def finish() -> None:
            if cancel is not self._capture_cancel:
                return
            self._listening_for_source = False

            if key_id is None:
                if not cancel.is_set():
                    self.source_var.set("(timed out)")
                    self.hint_var.set("Timed out. Press a key on your physical keyboard to try again.")
                    self._start_source_listen()
                return

            self._pending_source = key_id
            self._pending_target = None
            self.source_var.set(key_id_to_display(key_id))
            self.target_var.set("Click a key on the visual keyboard...")
            self.hint_var.set(
                f"From: {key_id_to_display(key_id)}. Click the key on the visual keyboard it should become."
            )
            self._sync_keyboard_highlights()

        self.after(0, finish)

    def _clear_capture_fields(self) -> None:
        self._stop_source_listen()
        self.source_var.set("Press a key on your keyboard...")
        self.target_var.set("(not set)")
        self._pending_source = None
        self._pending_target = None
        self.hint_var.set(
            "Press a key on your physical keyboard, then click the key on the visual keyboard it should become."
        )
        self._sync_keyboard_highlights()
        self._start_source_listen()

    def _apply_pending_mapping(self) -> None:
        source_id = self._pending_source
        target_id = self._pending_target

        if not source_id or not target_id:
            return
        if source_id == target_id:
            messagebox.showwarning("Invalid mapping", "Source and target cannot be the same key.")
            self._clear_capture_fields()
            return

        self.mappings[source_id] = target_id
        self._persist()
        self._refresh_mapping_list()
        added = f"{key_id_to_display(source_id)} → {key_id_to_display(target_id)}"
        self._clear_capture_fields()
        self.hint_var.set(f"Added {added}. Press another key on your physical keyboard to add more.")

    def _remove_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        for source_id in selected:
            self.mappings.pop(source_id, None)
        self._persist()
        self._refresh_mapping_list()

    def _on_close(self) -> None:
        self._stop_source_listen()
        self.engine.stop()
        self._persist()
        self.destroy()


def main() -> None:
    app = KeyRemapperApp()
    app.mainloop()


if __name__ == "__main__":
    main()

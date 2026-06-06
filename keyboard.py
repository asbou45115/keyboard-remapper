"""GUI key remapper — map any key to any key."""

import json
import sys
import tkinter as tk
from pathlib import Path
from threading import Thread
from tkinter import messagebox, ttk

from key_utils import DEFAULT_MAPPINGS, key_id_to_display
from remapper_engine import RemapperEngine, capture_key


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
    return dict(DEFAULT_MAPPINGS)


def save_mappings(mappings: dict[str, str]) -> None:
    path = config_path()
    path.write_text(json.dumps(mappings, indent=2), encoding="utf-8")


class KeyRemapperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Key Remapper")
        self.geometry("560x480")
        self.minsize(480, 400)

        self.mappings = load_mappings()
        self.engine = RemapperEngine(self.mappings)
        self._capture_target: str | None = None
        self._capturing = False
        self._pending_source: str | None = None
        self._pending_target: str | None = None

        self._build_ui()
        self._refresh_mapping_list()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.Frame(main)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=(6, 0)
        )

        self.toggle_btn = ttk.Button(status_frame, text="Start Remapping", command=self._toggle_remapping)
        self.toggle_btn.pack(side=tk.RIGHT)

        list_frame = ttk.LabelFrame(main, text="Mappings", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("source", "target")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.tree.heading("source", text="From")
        self.tree.heading("target", text="To")
        self.tree.column("source", width=200)
        self.tree.column("target", width=200)

        scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(main, text="Remove Selected", command=self._remove_selected).pack(anchor=tk.W, pady=(0, 10))

        add_frame = ttk.LabelFrame(main, text="Add Mapping", padding=8)
        add_frame.pack(fill=tk.X)

        self.source_var = tk.StringVar(value="(not set)")
        self.target_var = tk.StringVar(value="(not set)")

        row1 = ttk.Frame(add_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="From:", width=8).pack(side=tk.LEFT)
        ttk.Label(row1, textvariable=self.source_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row1, text="Capture", width=10, command=lambda: self._start_capture("source")).pack(
            side=tk.RIGHT
        )

        row2 = ttk.Frame(add_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="To:", width=8).pack(side=tk.LEFT)
        ttk.Label(row2, textvariable=self.target_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(row2, text="Capture", width=10, command=lambda: self._start_capture("target")).pack(
            side=tk.RIGHT
        )

        btn_row = ttk.Frame(add_frame)
        btn_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_row, text="Add Mapping", command=self._add_mapping).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Clear", command=self._clear_capture_fields).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(
            main,
            text="Tip: Keep Num Lock on for numpad keys. Run as admin if a game ignores remapped keys.",
            foreground="gray",
        ).pack(anchor=tk.W, pady=(8, 0))

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

    def _persist(self) -> None:
        save_mappings(self.mappings)
        self.engine.set_mappings(self.mappings)

    def _toggle_remapping(self) -> None:
        if self.engine.running:
            self.engine.stop()
            self.status_var.set("Stopped")
            self.toggle_btn.configure(text="Start Remapping")
        else:
            if not self.mappings:
                messagebox.showwarning("No mappings", "Add at least one key mapping first.")
                return
            self.engine.start()
            self.status_var.set("Running")
            self.toggle_btn.configure(text="Stop Remapping")

    def _start_capture(self, target: str) -> None:
        if self._capturing:
            return
        if self.engine.running:
            messagebox.showinfo("Stop remapping", "Stop remapping before capturing new keys.")
            return
        self._capturing = True
        self._capture_target = target
        var = self.source_var if target == "source" else self.target_var
        var.set("Press a key...")
        Thread(target=self._run_capture, daemon=True).start()

    def _run_capture(self) -> None:
        target = self._capture_target
        key_id = capture_key(timeout=10)

        def finish() -> None:
            if target == "source":
                var = self.source_var
                self._pending_source = key_id
            else:
                var = self.target_var
                self._pending_target = key_id

            if key_id is None:
                var.set("(timed out)")
            else:
                var.set(key_id_to_display(key_id))

            self._capturing = False
            self._capture_target = None

        self.after(0, finish)

    def _clear_capture_fields(self) -> None:
        self.source_var.set("(not set)")
        self.target_var.set("(not set)")
        self._pending_source = None
        self._pending_target = None

    def _add_mapping(self) -> None:
        source_id = self._pending_source
        target_id = self._pending_target

        if not source_id or not target_id:
            messagebox.showinfo("Missing keys", "Capture both a source key and a target key.")
            return
        if source_id == target_id:
            messagebox.showwarning("Invalid mapping", "Source and target cannot be the same key.")
            return

        self.mappings[source_id] = target_id
        self._persist()
        self._refresh_mapping_list()
        self._clear_capture_fields()

    def _remove_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        for source_id in selected:
            self.mappings.pop(source_id, None)
        self._persist()
        self._refresh_mapping_list()

    def _on_close(self) -> None:
        self.engine.stop()
        self._persist()
        self.destroy()


def main() -> None:
    app = KeyRemapperApp()
    app.mainloop()


if __name__ == "__main__":
    main()

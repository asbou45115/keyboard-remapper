# Key Remapper

A Windows GUI app that remaps any key to any other key. Useful for games with limited rebinding (for example, mapping numpad movement to WASD in Shin Megami Tensei).

## Features

- Remap any key to any other key via a simple GUI
- Capture source and target keys with one click
- Start/stop remapping without closing the app
- Mappings saved automatically to `mappings.json`
- Buildable as a standalone `.exe` (no Python install required on the target machine)

## Default mappings

These are loaded on first run:

| From     | To |
|----------|----|
| Numpad 8 | W  |
| Numpad 4 | A  |
| Numpad 6 | D  |
| Numpad 2 | S  |

## Project files

| File                 | Purpose                              |
|----------------------|--------------------------------------|
| `keyboard.py`        | Main GUI entry point                 |
| `key_utils.py`       | Key serialization and display names  |
| `remapper_engine.py` | Background keyboard listener         |
| `pyproject.toml`     | Project metadata and dependencies    |
| `uv.lock`            | Locked dependency versions (uv)      |
| `build.bat`          | One-click executable build script    |
| `mappings.json`      | Saved key mappings (created at run)  |

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install uv if you do not have it yet:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Create the virtual environment and install dependencies:

```powershell
uv sync
```

## Run from source

```powershell
uv run python keyboard.py
```

## Build the executable

```powershell
.\build.bat
```

Or manually (after `uv sync`):

```powershell
uv run pyinstaller --onefile --windowed --name KeyRemapper ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    keyboard.py
```

The executable is written to `dist\KeyRemapper.exe`. Place or keep `mappings.json` in the same folder as the exe to persist your bindings.

## Usage

1. Open the app (`uv run python keyboard.py` or `dist\KeyRemapper.exe`).
2. Click **Capture** next to **From** and press the key you want to remap.
3. Click **Capture** next to **To** and press the key it should become.
4. Click **Add Mapping**.
5. Click **Start Remapping** and leave the app running in the background while you play.

To remove a mapping, select it in the list and click **Remove Selected**.

## Notes

- Keep **Num Lock on** when using numpad keys.
- **Stop remapping** before capturing new keys.
- Some games require running the app **as Administrator** for key suppression to work.
- Supports single-key to single-key remapping only (not typing whole strings).

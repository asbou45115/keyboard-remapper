@echo off
setlocal

echo Syncing dependencies...
uv sync

echo.
echo Building keyboard.exe...
uv run pyinstaller keyboard.spec

echo.
echo Done. Executable is at: dist\keyboard.exe
echo Place mappings.json next to the exe to persist your key bindings.
pause

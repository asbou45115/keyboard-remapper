@echo off
setlocal

echo Syncing dependencies...
uv sync

echo.
echo Building KeyRemapper.exe...
uv run pyinstaller KeyRemapper.spec

echo.
echo Done. Executable is at: dist\KeyRemapper.exe
echo Place mappings.json next to the exe to persist your key bindings.
pause

@echo off
setlocal

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building KeyRemapper.exe...
pyinstaller --onefile --windowed --name KeyRemapper ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    keyboard.py

echo.
echo Done. Executable is at: dist\KeyRemapper.exe
echo Place mappings.json next to the exe to persist your key bindings.
pause

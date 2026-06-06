@echo off
setlocal enabledelayedexpansion
title WhisperX Build

echo.
echo   +----------------------------------------------------+
echo   ^|    WhisperX Transcriber - Thin Launcher Build    ^|
echo   +----------------------------------------------------+
echo.

set "ROOT=%~dp0.."
set "VENV=%ROOT%\.venv"
set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "PYINST=%VENV%\Scripts\pyinstaller.exe"
set "DIST=%ROOT%\dist\WhisperX Transcriber"

rem -- Check venv ---------------------------------------------------------------
if not exist "%PY%" (
    echo   ERROR: .venv not found at %VENV%
    echo   Run run.bat once to create the environment, then re-run this script.
    echo.
    pause
    exit /b 1
)

rem -- Install build tools ------------------------------------------------------
echo   [1/5] Checking build tools...
"%PY%" -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo         Installing PyInstaller...
    "%PIP%" install pyinstaller --quiet
)
"%PY%" -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo         Installing Pillow...
    "%PIP%" install Pillow --quiet
)
echo         Done.

rem -- Build thin launcher ------------------------------------------------------
echo   [2/4] Building thin launcher (no torch / no whisperx)...
echo         This should be fast - only GUI deps are bundled.
echo.
"%PYINST%" "%ROOT%\packaging\launcher.spec" --noconfirm --distpath "%ROOT%\dist"
if errorlevel 1 (
    echo.
    echo   ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo.
echo         Done.

rem -- Stage source files into dist ---------------------------------------------
echo   [3/4] Copying source files into dist...
copy /Y "%ROOT%\app.py"          "%DIST%\app.py"          >nul
copy /Y "%ROOT%\transcribe.py"   "%DIST%\transcribe.py"   >nul 2>&1

rem Create empty runtime/ and Models/ placeholder folders
if not exist "%DIST%\runtime"  mkdir "%DIST%\runtime"
if not exist "%DIST%\Models"   mkdir "%DIST%\Models"

rem Copy icon into assets/ subdir (used by app.py at runtime)
if exist "%ROOT%\assets\icon.ico" (
    if not exist "%DIST%\assets" mkdir "%DIST%\assets"
    copy /Y "%ROOT%\assets\icon.ico" "%DIST%\assets\icon.ico" >nul
)
echo         Done.

rem -- Report size --------------------------------------------------------------
echo   [4/4] Build summary:
echo.
for /f "tokens=*" %%s in ('powershell -NoProfile -Command "(Get-ChildItem -Path '%DIST%' -Recurse -Exclude 'runtime','Models' | Measure-Object -Property Length -Sum).Sum / 1MB" 2^>nul') do (
    echo         Launcher size (excl. runtime + Models): %%s MB
)
echo         Output: %DIST%\
echo.
echo   ============================================================
echo   Next step: build the Inno Setup installer
echo     - Open packaging\installer.iss in Inno Setup Compiler
echo     - Or run:  ISCC packaging\installer.iss
echo   ============================================================
echo.
pause

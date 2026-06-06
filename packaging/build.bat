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
set "DIST=%ROOT%\dist\WhisperXTranscriber"

rem -- Check venv ---------------------------------------------------------------
if not exist "%PY%" (
    echo   ERROR: .venv not found at %VENV%
    echo   Run run.bat once to create the environment, then re-run this script.
    echo.
    pause
    exit /b 1
)

rem -- Install build tools ------------------------------------------------------
echo   [1/4] Checking build tools...
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
copy /Y "%ROOT%\app.py"           "%DIST%\app.py"           >nul
copy /Y "%ROOT%\setup_wizard.py"  "%DIST%\setup_wizard.py"  >nul
copy /Y "%ROOT%\transcribe.py"    "%DIST%\transcribe.py"    >nul
copy /Y "%ROOT%\version.txt"      "%DIST%\version.txt"      >nul

rem Requirements files (used by setup wizard to know what to install)
copy /Y "%ROOT%\requirements-core.txt" "%DIST%\requirements-core.txt" >nul
copy /Y "%ROOT%\requirements-cpu.txt"  "%DIST%\requirements-cpu.txt"  >nul
copy /Y "%ROOT%\requirements-gpu.txt"  "%DIST%\requirements-gpu.txt"  >nul

rem Create empty runtime/ and Models/ placeholder folders
if not exist "%DIST%\runtime"  mkdir "%DIST%\runtime"
if not exist "%DIST%\Models"   mkdir "%DIST%\Models"

rem Copy icon into assets/ subdir
if exist "%ROOT%\assets\icon.ico" (
    if not exist "%DIST%\assets" mkdir "%DIST%\assets"
    copy /Y "%ROOT%\assets\icon.ico" "%DIST%\assets\icon.ico" >nul
)
echo         Done.

rem -- Build Inno Setup installer -----------------------------------------------
echo   [4/4] Building installer...
set "ISCC="
for %%p in (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    "C:\Program Files\Inno Setup 6\ISCC.exe"
) do (
    if exist %%p set "ISCC=%%~p"
)

if defined ISCC (
    echo         Running Inno Setup...
    "%ISCC%" "%ROOT%\packaging\installer.iss"
    if errorlevel 1 (
        echo   ERROR: Inno Setup build failed.
        pause
        exit /b 1
    )
    echo.
    echo   ============================================================
    echo   Installer ready: dist\installer\WhisperXTranscriber-Setup.exe
    echo   ============================================================
) else (
    echo   WARNING: Inno Setup not found. Skipping installer build.
    echo   Install from: https://jrsoftware.org/isdl.php
    echo   Then run: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\installer.iss
)
echo.
pause

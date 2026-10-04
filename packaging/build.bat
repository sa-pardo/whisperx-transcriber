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
set "UV=%ROOT%\.tools\uv\uv.exe"
set "DIST=%ROOT%\dist\WhisperXTranscriber"

rem -- Check venv ---------------------------------------------------------------
if not exist "%PY%" (
    echo   ERROR: .venv not found at %VENV%
    echo   Run run.bat once to create the environment, then re-run this script.
    echo.
    exit /b 1
)

rem -- Install build tools ------------------------------------------------------
echo   [1/4] Checking build tools...
if not exist "%UV%" (
    where uv.exe >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: uv not found. Run run.bat once, then retry the build.
        exit /b 1
    )
    set "UV=uv.exe"
)

"%PY%" -c "import PyInstaller, PIL" >nul 2>&1
if errorlevel 1 (
    echo         Installing PyInstaller and Pillow into .venv...
    "%UV%" pip install --python "%PY%" pyinstaller Pillow --quiet
    if errorlevel 1 (
        echo   ERROR: Could not install build tools into .venv.
        exit /b 1
    )
)
echo         Done.

rem -- Build thin launcher ------------------------------------------------------
echo   [2/4] Building thin launcher (no torch / no whisperx)...
echo         This should be fast - only GUI deps are bundled.
echo.
"%PY%" -m PyInstaller "%ROOT%\packaging\launcher.spec" --noconfirm --distpath "%ROOT%\dist"
if errorlevel 1 (
    echo.
    echo   ERROR: PyInstaller build failed.
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
copy /Y "%ROOT%\requirements-core.txt" "%DIST%\requirements-core.txt" >nul
copy /Y "%ROOT%\requirements-cpu.txt" "%DIST%\requirements-cpu.txt" >nul
copy /Y "%ROOT%\requirements-gpu.txt" "%DIST%\requirements-gpu.txt" >nul

rem Copy the pipeline + runner modules
if not exist "%DIST%\core" mkdir "%DIST%\core"
copy /Y "%ROOT%\core\__init__.py"  "%DIST%\core\__init__.py"  >nul
copy /Y "%ROOT%\core\pipeline.py"  "%DIST%\core\pipeline.py"  >nul
copy /Y "%ROOT%\core\runner.py"    "%DIST%\core\runner.py"    >nul
copy /Y "%ROOT%\core\settings.py"  "%DIST%\core\settings.py"  >nul
copy /Y "%ROOT%\core\runtime.py"   "%DIST%\core\runtime.py"   >nul

rem Create empty runtime/ and Models/ placeholder folders
if not exist "%DIST%\runtime"  mkdir "%DIST%\runtime"
if not exist "%DIST%\Models"   mkdir "%DIST%\Models"

rem Copy icon into assets/ subdir
if exist "%ROOT%\assets\icon.ico" (
    if not exist "%DIST%\assets" mkdir "%DIST%\assets"
    copy /Y "%ROOT%\assets\icon.ico" "%DIST%\assets\icon.ico" >nul
)
echo         Done.

rem -- Create portable zip ------------------------------------------------------
echo   [4/4] Creating portable zip...
if not exist "%ROOT%\dist\release" mkdir "%ROOT%\dist\release"
set "ZIP=%ROOT%\dist\release\WhisperXTranscriber.zip"
if exist "%ZIP%" del /f "%ZIP%"
"%PY%" "%ROOT%\packaging\release.py" "%DIST%" "%ZIP%"
if errorlevel 1 (
    echo   ERROR: Zip creation failed.
    exit /b 1
)

echo.
echo   ============================================================
echo   Release zip ready: dist\release\WhisperXTranscriber.zip
echo   ============================================================
echo.

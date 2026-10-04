@echo off
setlocal DisableDelayedExpansion
title WhisperX Transcriber

rem  WhisperX Transcriber - Windows launcher
rem  First run : creates .venv and installs all dependencies (5-20 min)
rem  Later runs: opens the app instantly

set "WX_ROOT=%~dp0"
set "PY=%WX_ROOT%.venv\Scripts\python.exe"
set "APP=%WX_ROOT%app.py"
set "UV=%WX_ROOT%.tools\uv\uv.exe"
set "PYTHON_VERSION=3.11.16"
set "UV_DOWNLOAD_URL=https://github.com/astral-sh/uv/releases/download/0.12.21/uv-x86_64-pc-windows-msvc.zip"
set "UV_SHA256=5d223efa0bf00208c3853246af09420419dfbd352536aa6bb8163d6170e23890"
set "UV_PYTHON_INSTALL_DIR=%WX_ROOT%.tools\python"
set "UV_PYTHON_BIN_DIR=%WX_ROOT%.tools\python-bin"
set "UV_CACHE_DIR=%WX_ROOT%.cache\uv"
set "UV_NO_MODIFY_PATH=1"

echo.
echo   +------------------------------------------+
echo   ^|       WhisperX  Transcriber             ^|
echo   ^|       AI Transcription by Muqaddimah    ^|
echo   +------------------------------------------+
echo.

rem -- Check app.py is present -------------------------------------------------
if not exist "%APP%" (
    echo   ERROR: app.py not found.
    echo   Make sure run.bat is in the same folder as app.py.
    echo.
    pause
    exit /b 1
)

rem -- Prefer Python from this folder's virtual environment --------------------
echo   Checking local Python...
if exist "%PY%" (
    "%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo   ERROR: Python in .venv cannot run or is older than 3.10.
        echo   Rename .venv and run this script again to create a new environment.
        goto :error
    )
    "%PY%" --version
) else (
    echo   No local Python found. Setup will download Python %PYTHON_VERSION%.
)
echo.

rem -- Find uv locally, on PATH, or download it --------------------------------
echo   Checking local uv...
"%UV%" --version >nul 2>&1
if not errorlevel 1 goto :uv_ready

echo   Checking uv on PATH...
uv.exe --version >nul 2>&1
if not errorlevel 1 (
    set "UV=uv.exe"
    goto :uv_ready
)

rem UV still points to the local install path if neither check succeeded.
echo   Downloading uv locally...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $tools = Join-Path $env:WX_ROOT '.tools'; New-Item -ItemType Directory -Path $tools -Force | Out-Null; $archive = Join-Path $tools 'uv.zip'; Invoke-WebRequest -UseBasicParsing -Uri $env:UV_DOWNLOAD_URL -OutFile $archive; if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $env:UV_SHA256) { throw 'uv SHA256 verification failed.' }; Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $tools 'uv') -Force; Remove-Item -LiteralPath $archive"
if errorlevel 1 (
    echo   ERROR: Could not download or verify uv. See the error above.
    goto :error
)
"%UV%" --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Downloaded uv could not run.
    goto :error
)

:uv_ready
"%UV%" --version
echo.

rem -- Reuse existing Python, installing packages if setup was incomplete --------
if not exist "%PY%" goto :create_venv
"%PY%" -c "import importlib.util; names = ('torch', 'torchaudio', 'whisperx', 'customtkinter', 'PIL'); raise SystemExit(0 if all(importlib.util.find_spec(name) is not None for name in names) else 1)" >nul 2>&1
if not errorlevel 1 (
    echo   Environment ready.
    echo.
    goto :launch
)
echo   Installing missing dependencies in the existing environment...
goto :install_packages

rem -- First-time setup --------------------------------------------------------
:create_venv
echo   First-time setup - this takes a few minutes.
echo   Internet connection required to download packages.
echo.

echo   [1/3] Installing local Python and creating virtual environment...
"%UV%" python install "%PYTHON_VERSION%" --no-registry
if errorlevel 1 (
    echo   ERROR: Could not install Python locally. Check your internet connection.
    goto :error
)
"%UV%" venv --python "%PYTHON_VERSION%" --managed-python "%WX_ROOT%.venv"
if errorlevel 1 (
    echo   ERROR: Could not create virtual environment.
    goto :error
)
echo         Done.

:install_packages
echo   [2/3] Installing PyTorch...
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo         NVIDIA GPU detected - installing CUDA 12.1 build
    echo         Downloading ~2.5 GB, please be patient...
    "%UV%" pip install --python "%PY%" torch torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet
) else (
    echo         No NVIDIA GPU - installing CPU build...
    "%UV%" pip install --python "%PY%" torch torchaudio --index-url https://download.pytorch.org/whl/cpu --quiet
)
if errorlevel 1 (
    echo   ERROR: PyTorch install failed. Check your internet connection.
    goto :error
)
echo         Done.

echo   [3/3] Installing WhisperX and UI dependencies...
echo         Downloading ~500 MB, almost there...
"%UV%" pip install --python "%PY%" whisperx customtkinter Pillow --quiet
if errorlevel 1 (
    echo   ERROR: Package install failed.
    goto :error
)
echo         Done.

echo.
echo   Setup complete! The app will open now.
echo   Next time just double-click run.bat - it will open instantly.
echo.

rem -- Launch ------------------------------------------------------------------
:launch
echo   Launching...
echo.
"%PY%" "%APP%"

if errorlevel 1 (
    echo.
    echo   The app exited with an error.
    echo   Open an issue at: https://github.com/muqaddimah/whisperx-transcriber/issues
    echo.
    pause
    exit /b 1
)
exit /b 0

:error
echo.
pause
exit /b 1

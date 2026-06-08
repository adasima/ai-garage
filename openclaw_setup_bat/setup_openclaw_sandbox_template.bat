@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  OpenClaw Sandbox Setup Script
::  - LM Studio: http://YOUR_HOST_IP:1234
::  - Model: YOUR_MODEL_NAME
::  - Discord bot token support
::  - Log: %USERPROFILE%\Desktop\openclaw_setup.log
:: ============================================================

:: ---- Settings ------------------------------------------------
:: ★ Sandbox環境から見たホストOSのIPアドレスに変更してください
:: （ipconfigコマンドのWi-FiまたはイーサネットアダプターのIPv4アドレス等）
set "HOST_IP=192.168.x.x"
set "LMS_PORT=1234"
set "LMS_MODEL=qwen3.5-9b@q4_k_m"
set "OPENCLAW_PORT=18789"
set "LOGFILE=%USERPROFILE%\Desktop\openclaw_setup.log"
set "WORKDIR=%TEMP%\openclaw_setup"
:: ★ Discord Bot Token（空欄ならDiscord設定をスキップします）
set "DISCORD_BOT_TOKEN="
:: ★ Gateway Token（Control UIの認証パスワードのようなもの）
set "GATEWAY_TOKEN=my-secure-token-1234"
:: --------------------------------------------------------------

:: ---- Log init -----------------------------------------------
if exist "%LOGFILE%" del "%LOGFILE%" > nul 2>&1
echo [LOG START] %DATE% %TIME% > "%LOGFILE%"

call :L "============================================================"
call :L "  OpenClaw Sandbox Setup"
call :L "  %DATE% %TIME%"
call :L "============================================================"
call :L "."
call :L "Settings:"
call :L "  Host IP:       %HOST_IP%"
call :L "  LM Studio:     http://%HOST_IP%:%LMS_PORT%/v1"
call :L "  Model:         %LMS_MODEL%"
call :L "  OpenClaw Port: %OPENCLAW_PORT%"
call :L "  Log File:      %LOGFILE%"
call :L "  Work Dir:      %WORKDIR%"
call :L "."

:: ---- Work directory -----------------------------------------
if not exist "%WORKDIR%" mkdir "%WORKDIR%"

:: ==== STEP 1: PowerShell ExecutionPolicy =====================
call :L "[1/9] Fixing PowerShell Execution Policy..."
powershell -Command "Set-ExecutionPolicy Unrestricted -Scope CurrentUser -Force" >> "%LOGFILE%" 2>&1
call :L "  Done."
call :L "."

:: ==== STEP 2: LM Studio connectivity ========================
call :L "[2/9] LM Studio connectivity check..."
call :L "  URL: http://%HOST_IP%:%LMS_PORT%/v1/models"
curl.exe -s --connect-timeout 5 "http://%HOST_IP%:%LMS_PORT%/v1/models" > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    call :L "  OK: LM Studio is responding"
) else (
    call :L "[WARN] Cannot connect to LM Studio."
    call :L "  - Is LM Studio running on the host?"
    call :L "  - Is port %LMS_PORT% allowed through firewall?"
    call :L "  - Is 'Serve on Local Network' enabled in LM Studio?"
    call :L "  Continuing setup anyway..."
)
call :L "."

:: ==== STEP 3: Git ============================================
call :L "[3/9] Checking Git..."
git --version > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    for /f "tokens=*" %%V in ('git --version 2^>nul') do call :L "  Already installed: %%V"
) else (
    call :L "  Downloading Git for Windows..."
    curl.exe -fsSL "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe" -o "%WORKDIR%\git_setup.exe"
    if not exist "%WORKDIR%\git_setup.exe" (
        call :L "[ERROR] Git download failed."
        goto :fail
    )
    call :L "  Installing Git (silent)..."
    start /wait "" "%WORKDIR%\git_setup.exe" /VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES
    set "PATH=!PATH!;C:\Program Files\Git\cmd;C:\Program Files\Git\bin"
    git --version > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=*" %%V in ('git --version 2^>nul') do call :L "  Installed: %%V"
    ) else (
        call :L "[WARN] git not found after install."
    )
)
call :L "."

:: ==== STEP 4: Node.js ========================================
call :L "[4/9] Checking Node.js..."
node --version > nul 2>&1
if !ERRORLEVEL! EQU 0 (
    for /f "tokens=*" %%V in ('node --version 2^>nul') do call :L "  Already installed: %%V"
) else (
    call :L "  Downloading Node.js v22.14.0 LTS..."
    curl.exe -fsSL "https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi" -o "%WORKDIR%\node_setup.msi"
    if not exist "%WORKDIR%\node_setup.msi" (
        call :L "[ERROR] Node.js download failed."
        goto :fail
    )
    call :L "  Installing Node.js (silent)..."
    msiexec.exe /i "%WORKDIR%\node_setup.msi" /qn /norestart
    set "PATH=!PATH!;C:\Program Files\nodejs;%APPDATA%\npm"
    :: msiexec is async-ish, wait a moment
    timeout /t 5 /nobreak > nul
    node --version > nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=*" %%V in ('node --version 2^>nul') do call :L "  Installed: %%V"
    ) else (
        call :L "[ERROR] node not found after install."
        goto :fail
    )
)
call :L "."

:: ==== STEP 5: OpenClaw =======================================
call :L "[5/9] Checking OpenClaw..."

:: Check if openclaw shim AND module files exist
set "OC_SHIM=%APPDATA%\npm\openclaw.cmd"
set "OC_MODULE=%APPDATA%\npm\node_modules\openclaw"

if exist "!OC_SHIM!" (
    if exist "!OC_MODULE!\package.json" (
        call :L "  OpenClaw is already installed."
        call :L "  Shim: !OC_SHIM!"
        goto :oc_ok
    )
)

:: Remove broken install if exists
call :L "  openclaw not found or broken. Cleaning up..."
if exist "!OC_SHIM!" del "!OC_SHIM!" > nul 2>&1
if exist "%APPDATA%\npm\openclaw" del "%APPDATA%\npm\openclaw" > nul 2>&1
:: Force remove leftover node_modules if present
if exist "!OC_MODULE!" (
    call :L "  Force removing leftover openclaw folder..."
    rmdir /s /q "!OC_MODULE!" >> "%LOGFILE%" 2>&1
)

:: npm install with --ignore-scripts
:: node-llama-cpp postinstall tries to build llama.cpp (needs cmake/compilers)
:: which fails in Sandbox. LM Studio handles inference, so we skip it.
call :L "  Installing OpenClaw via npm (--ignore-scripts)..."
call npm install -g openclaw@latest --ignore-scripts >> "%LOGFILE%" 2>&1
set "NPMERR=!ERRORLEVEL!"
set "PATH=!PATH!;%APPDATA%\npm"

:: If npm failed, try install.cmd
if !NPMERR! NEQ 0 (
    call :L "  [WARN] npm install failed (code !NPMERR!). Trying install.cmd..."
    curl.exe -fsSL https://openclaw.ai/install.cmd -o "%WORKDIR%\install_openclaw.cmd"
    if exist "%WORKDIR%\install_openclaw.cmd" (
        call :L "  Running install.cmd..."
        call "%WORKDIR%\install_openclaw.cmd" >> "%LOGFILE%" 2>&1
    ) else (
        call :L "  [WARN] install.cmd download also failed."
    )
    set "PATH=!PATH!;%APPDATA%\npm"
)

:: Verify by checking files exist (avoid running openclaw --version which may hang)
if not exist "!OC_MODULE!\package.json" (
    call :L "[ERROR] openclaw module not found after install."
    call :L "  Expected: !OC_MODULE!"
    call :L "  npm global prefix:"
    for /f "tokens=*" %%P in ('npm config get prefix 2^>nul') do call :L "    %%P"
    dir "%APPDATA%\npm\node_modules\" >> "%LOGFILE%" 2>&1
    call :L "  PATH=!PATH!"
    goto :fail
)

:: Check if shim exists, create if missing
if not exist "!OC_SHIM!" (
    call :L "  Shim not found, checking for entry point..."
    :: Find the correct entry point
    if exist "!OC_MODULE!\openclaw.mjs" (
        call :L "  Creating openclaw shim for openclaw.mjs..."
        echo @echo off > "!OC_SHIM!"
        echo node "%%APPDATA%%\npm\node_modules\openclaw\openclaw.mjs" %%* >> "!OC_SHIM!"
    ) else if exist "!OC_MODULE!\dist\cli\index.js" (
        call :L "  Creating openclaw shim for dist/cli/index.js..."
        echo @echo off > "!OC_SHIM!"
        echo node "%%APPDATA%%\npm\node_modules\openclaw\dist\cli\index.js" %%* >> "!OC_SHIM!"
    ) else (
        call :L "  Entry point unknown. Listing module root:"
        dir "!OC_MODULE!\*.mjs" "!OC_MODULE!\*.js" >> "%LOGFILE%" 2>&1
        call :L "  Trying package.json bin field..."
        type "!OC_MODULE!\package.json" | findstr /i "bin" >> "%LOGFILE%" 2>&1
    )
)

call :L "  OpenClaw installed successfully."


:oc_ok
call :L "."

:: ==== STEP 6: Onboarding Wizard ==============================
call :L "[6/9] Running Onboarding Wizard (non-interactive)..."
call :L "  Provider: Custom (LM Studio / OpenAI-compatible)"
call :L "  Model:    %LMS_MODEL%"
call :L "  Base URL: http://%HOST_IP%:%LMS_PORT%/v1"
call :L "."

call :L "  Running: openclaw onboard ..."
call openclaw onboard ^
    --non-interactive ^
    --accept-risk ^
    --mode local ^
    --auth-choice custom-api-key ^
    --custom-base-url "http://%HOST_IP%:%LMS_PORT%/v1" ^
    --custom-model-id "%LMS_MODEL%" ^
    --custom-api-key "lm-studio" ^
    --custom-provider-id "lmstudio" ^
    --custom-compatibility openai ^
    --secret-input-mode plaintext ^
    --gateway-port %OPENCLAW_PORT% ^
    --gateway-bind loopback ^
    --gateway-auth token ^
    --gateway-token "%GATEWAY_TOKEN%" ^
    --skip-channels ^
    --skip-skills >> "%LOGFILE%" 2>&1

set "OB_ERR=!ERRORLEVEL!"
call :L "  onboard exit code: !OB_ERR!"

if !OB_ERR! NEQ 0 (
    call :L "  [WARN] Onboarding returned non-zero. This may be normal"
    call :L "  (gateway health check can fail during initial setup)."
    call :L "  Config/workspace/sessions should still be created."
    call :L "  Checking if config was written..."
    if exist "%USERPROFILE%\.openclaw\openclaw.json" (
        call :L "  OK: openclaw.json exists. Continuing..."
    ) else (
        call :L "[ERROR] openclaw.json NOT created. Onboard truly failed."
        goto :fail
    )
)
call :L "."

:: ==== STEP 7: Discord Bot Token ==============================
if defined DISCORD_BOT_TOKEN (
    call :L "[7/9] Configuring Discord bot..."
    call :L "  Setting Discord bot token..."
    call openclaw config set channels.discord.token "\"%DISCORD_BOT_TOKEN%\"" --json >> "%LOGFILE%" 2>&1
    call openclaw config set channels.discord.enabled true --json >> "%LOGFILE%" 2>&1
    call :L "  Discord bot configured."
) else (
    call :L "[7/9] Discord bot token not set. Skipping Discord setup."
    call :L "  To add Discord later: openclaw config set channels.discord.token '\"TOKEN\"' --json"
)
call :L "."

:: ==== STEP 8: Gateway ========================================
call :L "[8/9] Starting Gateway..."
:: Start gateway in a separate window so it keeps running
start "OpenClaw Gateway" cmd /k "openclaw gateway --port %OPENCLAW_PORT%"
call :L "  Gateway started in separate window. Waiting 5s..."
timeout /t 5 /nobreak > nul

:: Check gateway status
call openclaw gateway status >> "%LOGFILE%" 2>&1
if !ERRORLEVEL! EQU 0 (
    call :L "  Gateway is running."
) else (
    call :L "  [WARN] Gateway status check returned non-zero."
    call :L "  The gateway window should still be running."
)
call :L "."

:: ==== STEP 9: Browser ========================================
call :L "[9/9] Opening OpenClaw Control UI..."
set "UI_URL=http://127.0.0.1:%OPENCLAW_PORT%/?token=%GATEWAY_TOKEN%"
call :L "  URL: !UI_URL!"
timeout /t 2 /nobreak > nul
start "" "!UI_URL!"

call :L "."
call :L "============================================================"
call :L "  Setup Complete!"
call :L "  Control UI: !UI_URL!"
call :L "  LM Studio:  http://%HOST_IP%:%LMS_PORT%/v1"
call :L "  Model:      %LMS_MODEL%"
call :L "  Log:        %LOGFILE%"
call :L "============================================================"
call :L "."

:: Cleanup temp files
call :L "Cleaning up temp files..."
if exist "%WORKDIR%\git_setup.exe" del "%WORKDIR%\git_setup.exe"
if exist "%WORKDIR%\node_setup.msi" del "%WORKDIR%\node_setup.msi"
if exist "%WORKDIR%\install_openclaw.cmd" del "%WORKDIR%\install_openclaw.cmd"

echo.
echo Setup complete. Log: %LOGFILE%
echo.
pause
endlocal
exit /b 0

:: ============================================================
:fail
:: ============================================================
call :L "."
call :L "============================================================"
call :L "  SETUP FAILED - Check log for details"
call :L "  Log: %LOGFILE%"
call :L "============================================================"
echo.
echo SETUP FAILED. Log: %LOGFILE%
echo.
echo --- Last 30 lines of log ---
set "N=0"
for /f "usebackq delims=" %%A in ("%LOGFILE%") do (
    set /a N+=1
    set "LINE_!N!=%%A"
)
set /a START=!N!-30
if !START! LSS 1 set START=1
for /l %%I in (!START!,1,!N!) do (
    if defined LINE_%%I echo !LINE_%%I!
)
echo.
pause
endlocal
exit /b 1

:: ============================================================
:: :L - Log a line to both console and file
:: ============================================================
:L
set "M=%~1"
if "!M!"=="." (
    echo.
    echo.>> "%LOGFILE%"
) else (
    echo !M!
    echo !M!>> "%LOGFILE%"
)
exit /b 0

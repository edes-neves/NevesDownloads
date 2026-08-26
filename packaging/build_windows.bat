@echo off
REM ============================================================================
REM Neves Downloads - Script de build para Windows (.exe empacotado).
REM
REM Gera um executável único (onefile) em dist\NevesDownloads.exe
REM
REM Uso:
REM   build_windows.bat
REM
REM Pré-requisitos:
REM   - Python 3.11+ instalado e no PATH (ou venv ativado)
REM   - Dependências do projeto instaladas (pip install -r requirements.txt)
REM   - PyInstaller instalado (pip install pyinstaller)
REM ============================================================================
setlocal

set ROOT_DIR=%~dp0..
cd /d "%ROOT_DIR%"

REM -- Verifica Python ---------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Ative seu venv ou adicione o Python ao PATH.
    exit /b 1
)

REM -- Verifica / instala PyInstaller ----------------------------------------
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ERRO: Falha ao instalar PyInstaller.
        exit /b 1
    )
)

REM -- Limpa builds anteriores -----------------------------------------------
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM -- Build ------------------------------------------------------------------
echo === Construindo NevesDownloads com PyInstaller (onefile) ===
python -m PyInstaller --noconfirm --clean packaging\NevesDownloads.spec
if errorlevel 1 (
    echo ERRO: Build do PyInstaller falhou.
    exit /b 1
)

REM -- Verifica resultado ------------------------------------------------------
if exist "dist\NevesDownloads.exe" (
    echo.
    echo === Build concluido com sucesso ===
    echo Executavel gerado em: dist\NevesDownloads.exe
    dir /b "dist\NevesDownloads.exe"
) else (
    echo.
    echo ATENCAO: Nao foi possivel localizar dist\NevesDownloads.exe
    echo Verifique a pasta dist\ para ver os artefatos gerados.
)

REM -- Gera um .zip para distribuiracao (opcional) ---------------------------
if exist "dist\NevesDownloads.exe" (
    where powershell >nul 2>nul
    if not errorlevel 1 (
        echo.
        echo Gerando pacote .zip para distribuicao...
        powershell -NoProfile -Command "Compress-Archive -Path 'dist\NevesDownloads.exe' -DestinationPath 'dist\NevesDownloads.zip' -Force"
        if exist "dist\NevesDownloads.zip" (
            echo Pacote gerado: dist\NevesDownloads.zip
        )
    )
)

echo.
echo Build concluido. Artefatos em: %ROOT_DIR%\dist\
endlocal

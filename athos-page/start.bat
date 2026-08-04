@echo off
chcp 65001 >nul
title Athos Tecnologia — Dev Server

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   ATHOS TECNOLOGIA — Ambiente Local       ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ——— Verifica se as portas já estão em uso ———
set SITE_PORT=3030
set FLASK_PORT=5000

netstat -an | find ":%SITE_PORT% " | find "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo  [AVISO] Porta %SITE_PORT% ja esta em uso ^(site^). Pulando.
    set SITE_SKIP=1
) else (
    set SITE_SKIP=0
)

netstat -an | find ":%FLASK_PORT% " | find "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    echo  [AVISO] Porta %FLASK_PORT% ja esta em uso ^(console^). Pulando.
    set FLASK_SKIP=1
) else (
    set FLASK_SKIP=0
)

:: ——— Inicia site estático (porta 3030) ———
if %SITE_SKIP%==0 (
    echo  [1/2] Iniciando site estatico na porta %SITE_PORT%...
    start "Athos Site :3030" cmd /k "cd /d %~dp0 && python -m http.server %SITE_PORT%"
)

:: ——— Inicia Flask — Console de Chamados (porta 5000) ———
if %FLASK_SKIP%==0 (
    echo  [2/2] Iniciando Hub Servisdesk na porta %FLASK_PORT%...
    start "Hub Servisdesk :5000" cmd /k "cd /d C:\athos\projetos\console-chamados && python app.py"
)

:: ——— Aguarda os servidores subirem ———
echo.
echo  Aguardando servidores...
timeout /t 3 /nobreak >nul

:: ——— Abre o navegador ———
echo  Abrindo navegador...
start "" "http://localhost:%SITE_PORT%/index.html"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  Site:    http://localhost:3030           ║
echo  ║  Console: http://localhost:5000           ║
echo  ║                                           ║
echo  ║  Feche as janelas de terminal para parar  ║
echo  ╚══════════════════════════════════════════╝
echo.
pause

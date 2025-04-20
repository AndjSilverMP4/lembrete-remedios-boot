@echo off
setlocal enabledelayedexpansion

REM === Caminho do projeto (onde estão webhook.py, main.py e ngrok.exe)
set "PASTA_PROJETO=D:\AREA DO PROGRAMADOR\MEUS PROGRAMAS\lembrete-remedios-boot"
set "NGROK_EXE=%PASTA_PROJETO%\ngrok.exe"

REM === Verifica se o ngrok existe
if not exist "%NGROK_EXE%" (
    echo ❌ NGROK não encontrado! Caminho inválido:
    echo %NGROK_EXE%
    pause
    exit /b
)

REM === Acessa a pasta do projeto
cd /d "%PASTA_PROJETO%"

REM === Inicia main.py em nova janela
start "Agendador - main.py" cmd /k "python main.py"

REM === Inicia webhook.py (Flask) em nova janela
start "Webhook - webhook.py" cmd /k "python webhook.py"

REM === Aguarda o Flask iniciar
timeout /t 3 > nul

REM === Testa se Flask está no ar
echo Verificando se Flask está online em http://127.0.0.1:8080/webhook...
powershell -Command "try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8080/webhook' -Method POST -Body '{}' -ErrorAction Stop; if ($r.StatusCode -eq 200) { Write-Host '✅ Flask (webhook.py) está online!' } else { Write-Host '⚠️ Flask respondeu com erro!' } } catch { Write-Host '❌ Flask não está respondendo!' }"

REM === Inicia ngrok em nova janela
start "Ngrok Tunnel" cmd /k ""%NGROK_EXE%" http 8080"

REM === Aguarda o ngrok gerar o túnel
timeout /t 5 > nul

REM === Captura o link público via API local do ngrok
echo Buscando URL pública do ngrok...
for /f "tokens=*" %%i in ('powershell -Command "(Invoke-RestMethod -Uri http://127.0.0.1:4040/api/tunnels).tunnels[0].public_url"') do (
    set "NGROK_URL=%%i"
)

echo.
if defined NGROK_URL (
    echo ✅ URL pública do ngrok:
    echo !NGROK_URL!
    echo.
    echo 🛠️  Cole essa URL no seu Twilio Sandbox:
    echo !NGROK_URL!/webhook
) else (
    echo ❌ Não foi possível obter a URL do ngrok.
)

pause

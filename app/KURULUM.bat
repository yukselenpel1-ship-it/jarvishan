@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo JARVIS v0.4 kurulumu - Python 3.11 veya 3.12 gerektirir.
py -3.12 -V >nul 2>&1
if not errorlevel 1 (
    py -3.12 -m venv .venv
) else (
    py -3.11 -V >nul 2>&1
    if errorlevel 1 (
        echo Python 3.12 bulunamadı. https://www.python.org/downloads/ adresinden kurun.
        echo Kurulumda Python Launcher seçeneğini etkinleştirin.
        pause
        exit /b 1
    )
    py -3.11 -m venv .venv
)
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Masaustu kisayolu olusturuluyor...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0KISAYOL.ps1"
echo Kurulum tamamlandı. Masaustundeki JARVIS kisayolunu acabilirsiniz.
pause
exit /b 0
:failed
echo Kurulum tamamlanamadı. Yukarıdaki hata mesajını kontrol edin.
echo Arayüz için Python ile main.py dosyasını çalıştırabilirsiniz; ses özellikleri eksik olabilir.
pause
exit /b 1

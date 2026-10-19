@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Revize edilmis yeni IFC dosyasini bu dosyanin UZERINE birakin.
  pause
  exit /b
)
echo Bir onceki onayin kayit dosyasini (..._record.json) bu pencerenin icine surukleyip Enter a basin:
set /p PREV=
set PREV=%PREV:"=%
set /p NOTE="Revizyon notu (ornek: L3 kapi revizyonu) ve Enter: "
python dkitabe.py stamp "%~1" --previous "%PREV%" --note "%NOTE%"
pause

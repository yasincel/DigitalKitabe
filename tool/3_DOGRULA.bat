@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Kontrol edilecek IFC dosyasini bu dosyanin UZERINE birakin.
  pause
  exit /b
)
echo Simdi onayli modelin kayit dosyasini (..._record.json) bu pencerenin icine surukleyip Enter a basin:
set /p REC=
set REC=%REC:"=%
python dkitabe.py verify "%~1" "%REC%"
pause

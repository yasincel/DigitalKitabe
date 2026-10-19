@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Amblem ya da desen gorselini (PNG/JPG) bu dosyanin UZERINE birakin.
  pause
  exit /b
)
echo Kayitlarin bulundugu klasoru bu pencerenin icine surukleyip Enter a basin:
set /p REG=
set REG=%REG:"=%
python dkitabe.py identify "%~1" "%REG%"
pause

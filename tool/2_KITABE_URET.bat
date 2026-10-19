@echo off
cd /d "%~dp0"
if "%~1"=="" (
  echo Bir IFC dosyasini fareyle tutup bu dosyanin UZERINE birakin.
  pause
  exit /b
)
set /p NOTE="Kisa bir not yazin (ornek: Tasarim onayi) ve Enter: "
python dkitabe.py stamp "%~1" --note "%NOTE%"
echo.
echo Ciktilar IFC dosyasinin yanindaki ..._kitabe klasorunde.
pause

@echo off
cd /d "%~dp0"
echo Dijital Kitabe - kutuphaneler kuruluyor. Birkac dakika surebilir...
python -m pip install -r requirements.txt
echo.
echo Kurulum bitti. Yukarida kirmizi ERROR yazisi yoksa her sey yolunda.
pause

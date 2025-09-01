@echo off
chcp 65001 > nul
echo.
echo.
python3 EdgeDomain.py -f domain.txt
echo.
pause
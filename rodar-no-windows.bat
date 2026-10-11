@echo off
chcp 65001 >nul
REM OSINTIA - lançador para Windows: roda os testes e a auditoria do caso de demonstração.
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% --version >nul 2>nul || (echo Python 3 nao encontrado. Instale em https://www.python.org/downloads/ & pause & exit /b 1)
echo == Testes do nucleo ==
%PY% -m unittest discover -s testes
echo.
echo == Auditoria do caso de demonstracao ==
%PY% -m osintia auditar dados/demo/triagem_perfis.jsonl
echo.
echo == Coordenacao no caso de demonstracao ==
%PY% -m osintia coordenacao dados/demo/campanha_coordenada.csv
echo.
pause

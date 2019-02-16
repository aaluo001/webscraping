@echo off
set PYTHONPATH=%PY_WORKSPACE%\webscraping
python %PYTHONPATH%\test\util\TestMysqlDBApi.py %*
rem pause

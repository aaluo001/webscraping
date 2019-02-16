@echo off
set PYTHONPATH=%PY_WORKSPACE%\webscraping
python %PYTHONPATH%\test\util\TestSqliteDBApi.py %*
rem pause

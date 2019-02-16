@echo off
set PYTHONPATH=%PY_WORKSPACE%\webscraping
python %PYTHONPATH%\test\util\TestLog.py %*
rem pause

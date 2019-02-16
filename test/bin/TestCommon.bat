@echo off
set PYTHONPATH=%PY_WORKSPACE%\webscraping
python %PYTHONPATH%\test\util\TestCommon.py %*
rem pause

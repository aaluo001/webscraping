@echo off
set PYTHONPATH=%PY_WORKSPACE%\webscraping
python %PYTHONPATH%\test\util\TestMongoCache.py %*
rem pause

@echo off
chcp 65001 > nul
set "PYTHONPATH=E:\GitHub开源项目\TachiKuma\claude_code_bridge\lib;%PYTHONPATH%"
"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.py" %*
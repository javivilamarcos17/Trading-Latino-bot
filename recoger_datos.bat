@echo off
REM Recolector de datos en vivo de la ARENA (paper-trading). Lo ejecuta la tarea programada.
REM Para parar: borrar la tarea con  schtasks /Delete /TN "TradingArenaPaper" /F
cd /d "C:\Users\javiv\Desktop\Trading Jaime Merino"
echo ---- %DATE% %TIME% ---- >> "data_store\paper_arena\log.txt"
".venv\Scripts\python.exe" -m trading_latino.live.arena >> "data_store\paper_arena\log.txt" 2>&1

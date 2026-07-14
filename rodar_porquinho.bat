@echo off
title Porquinho WhatsApp - Cerebro Python Local
echo ========================================================
echo 🐷 INICIANDO CEREBRO DO PORQUINHO (PYTHON FASTAPI)...
echo ========================================================
echo Webhook local rodando em: http://localhost:8000/webhook-evolution
echo ========================================================
py -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause

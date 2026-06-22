@echo off
REM ParaFOMO X botu - gunluk paylasim (Windows Task Scheduler bunu cagirir)
REM Bu .bat dosyasinin bulundugu klasore gecer ve botu calistirir.
cd /d "%~dp0"
node post-x.mjs >> x-bot.log 2>&1

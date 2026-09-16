@echo off
title NEET QuizBot - Local Server
echo ===================================================
echo             NEET QuizBot - Local Runner
echo ===================================================
echo.

if not exist .env (
    echo [!] .env file not found! Creating from .env.example...
    copy .env.example .env
    echo [!] Please paste your Telegram BOT_TOKEN in the .env file.
    notepad .env
    echo.
    echo Once you have saved your BOT_TOKEN in .env, press any key to start the bot.
    pause
)

echo Starting bot in Long-Polling mode...
echo (Press Ctrl+C to stop)
echo.

"C:\Users\akash\AppData\Local\Programs\Python\Python311\python.exe" -m app.main

pause

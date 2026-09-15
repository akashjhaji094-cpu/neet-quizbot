# NEET QuizBot — Telegram QuizBot-like Framework

[![CI - Test Suite](https://img.shields.io/badge/tests-26%20passed-brightgreen.svg)](tests/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v20+-0088cc.svg)](https://core.telegram.org/bots/api)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A clean, modular, production-ready Telegram QuizBot engine built with **Python 3.11**, **python-telegram-bot**, **PostgreSQL**, and **SQLAlchemy 2.0**.

This framework independently reproduces the publicly observable workflow and user experience of Telegram'\''s `@QuizBot` using official Telegram Bot API mechanisms, tailored specifically for competitive exams like **NEET** (+4 for correct, -1 for wrong, 0 for unattempted).

---

## 🌟 Key Features

- **Native Telegram Quiz Poll Creation**: Uses `KeyboardButton.request_poll(type="quiz")` so quiz creators use Telegram'\''s native client UI to type questions, options, and designate the correct answer.
- **Pre-Question Media Support**: Attach photos, diagrams, videos, animations, or notes that are displayed to participants right before the question.
- **Server-Side Countdown Timer**: Per-question timer (5s to 300s or No Timer) with server-side timeout enforcement. Expired questions are automatically scored as unattempted (0 marks).
- **Anti-Cheat Shuffling Engine**: 
  - Randomize question sequence per attempt.
  - Randomize answer options per attempt.
  - Automatic bi-directional remapping ensures correct answer grading remains 100% accurate regardless of permutation.
- **Independent NEET Scoring Engine**: Scoring is calculated independently from Telegram'\''s client counters:
  $$\text{Score} = (\text{Correct} \times 4) + (\text{Wrong} \times -1) + (\text{Unattempted} \times 0)$$
  Extensible for custom marking schemes (e.g. JEE, UPSC).
- **Telegram Deep Linking**: Generates unique share links (`https://t.me/<BOT_USERNAME>?start=quiz_<QUIZ_ID>`) and group sharing buttons (`startgroup`).
- **Crash & Restart Recovery**: Draft sessions and question states are persisted in PostgreSQL, preventing loss of unfinished quizzes on bot restarts or worker cycling.
- **Historical Retries**: Participants can retry quizzes without overwriting historical attempts.
- **Creator Analytics**: `/stats` command provides aggregate statistics (total attempts, average score, highest/lowest scores, percentage).
- **Production & Cloud Ready**: Fully containerized with Docker, Docker Compose, Heroku `Procfile`, Webhook support, and Alembic database migrations.

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message, NEET scoring breakdown, and quick action buttons. Also handles deep links (`/start quiz_<ID>`). |
| `/newquiz` | Start creating a new quiz. Checks for unfinished sessions. |
| `/quizzes` or `/myquizzes` | List all quizzes created by you with Start, Share, and Stats actions. |
| `/undo` | Remove the latest question from the active draft quiz. |
| `/done` | Finish question input and proceed to timer & shuffle settings. |
| `/cancel` | Discard active draft quiz session safely. |
| `/stop` | Stop any active quiz session or attempt. |
| `/stats` | View comprehensive creator statistics and attempt metrics. |
| `/help` | Detailed guide on quiz creation and NEET scoring rules. |
| `/lang` | Language selection (English default, Hindi ready). |

---

## 🏗 System Architecture

```
neet-quizbot/
├── app/
│   ├── main.py                      # Application entrypoint (Webhook / Polling)
│   ├── config.py                    # Environment settings & DB URL normalization
│   ├── bot/
│   │   ├── setup.py                 # Bot builder, handler routing, setMyCommands
│   │   ├── commands/                # Command handlers (/start, /newquiz, etc.)
│   │   ├── handlers/                # Creation, participant, poll answers, callbacks
│   │   ├── keyboards/               # Native poll request reply keyboard & inline menus
│   │   └── states/                  # Quiz creation lifecycle states
│   ├── database/
│   │   ├── connection.py            # SQLAlchemy engine, sessionmaker, init_db
│   │   ├── models/                  # User, Quiz, Question, Option, Attempt, Draft models
│   │   ├── repositories/            # Repository pattern abstraction layer
│   │   └── migrations/              # Alembic migrations & version scripts
│   ├── services/
│   │   ├── scoring_service.py       # Independent NEET scoring engine
│   │   ├── quiz_service.py          # Quiz lifecycle, publishing, deep links
│   │   ├── question_service.py      # Question addition, undo, pre-question media
│   │   ├── attempt_service.py       # Participant attempt execution & option remapping
│   │   └── timer_service.py         # Server-side timeout scheduler via JobQueue
│   └── utils/
│       ├── localization.py          # Multi-language string catalogs
│       └── logger.py                # Structured console logging
├── tests/                           # 26 automated unit & integration tests
├── Dockerfile                       # Production Python 3.11 slim container
├── docker-compose.yml               # Local PostgreSQL + QuizBot service stack
├── Procfile                         # Heroku process definition (web & worker)
├── requirements.txt                 # Pinned dependencies
├── alembic.ini                      # Alembic configuration
└── .env.example                     # Environment variables template
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL (or local SQLite for development)
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 2. Obtain Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to choose a name and username.
3. Copy the HTTP API token provided.

### 3. Clone and Configure
```bash
git clone https://github.com/akashjhaji094-cpu/neet-quizbot.git
cd neet-quizbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

Edit `.env` and set your credentials:
```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_EXAMPLE
DATABASE_URL=sqlite:///./quizbot.db  # Or postgresql://user:pass@localhost:5432/quizbot_db
```

### 4. Run Migrations & Start Bot
```bash
# Run database migrations
alembic upgrade head

# Start bot in long-polling mode
python -m app.main
```

---

## 🐳 Running with Docker Compose

Run the entire stack (PostgreSQL + QuizBot) with a single command:
```bash
# Set your BOT_TOKEN in .env
docker compose up --build -d
```

---

## ☁️ Heroku Deployment Guide

### Step 1: Install Heroku CLI & Login
```bash
heroku login
```

### Step 2: Create Heroku Application
```bash
heroku create my-neet-quizbot
```

### Step 3: Add Heroku Postgres Add-on
```bash
heroku addons:create heroku-postgresql:essential-0
```

### Step 4: Set Environment Variables
```bash
heroku config:set BOT_TOKEN="your_telegram_bot_token_here"
heroku config:set ENVIRONMENT="production"
heroku config:set WEBHOOK_URL="https://my-neet-quizbot.herokuapp.com"
```

> **Note**: Heroku automatically supplies `DATABASE_URL` and assigns `$PORT`. The application'\''s configuration adapter automatically converts legacy `postgres://` URLs to `postgresql://` required by SQLAlchemy 2.0.

### Step 5: Deploy Code to Heroku
```bash
git push heroku main
```

### Step 6: Run Database Migrations on Heroku
```bash
heroku run alembic upgrade head
```

### Step 7: Scale the Process
For Webhook mode:
```bash
heroku ps:scale web=1
```
Or for Long-Polling mode:
```bash
heroku ps:scale worker=1
```

### Step 8: Verify Logs
```bash
heroku logs --tail
```

---

## 🧪 Running the Test Suite

The repository includes a comprehensive test suite with 26 automated tests covering scoring calculations, question shuffling, option remapping, server timeouts, duplicate poll answers, undo, and permissions:

```bash
pytest -v
```

---

## 📄 License

MIT License. Free for open-source and commercial use.

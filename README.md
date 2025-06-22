# JBbot

A Telegram bot that notifies users about traffic conditions at the Tuas and Woodlands checkpoints between Singapore and Johor Bahru. Users can subscribe to receive notifications when traffic changes, check the current traffic time to JB, and manage their subscription.

---

## Features

- **/start** – Welcome message and instructions
- **/help** – List all available commands
- **/check** – Get the current "time to JB" for both checkpoints
- **/subscribe** – Subscribe to traffic change notifications
- **/unsubscribe** – Unsubscribe from notifications

Traffic data is extracted from checkpoint camera images using OCR, and subscriber management is handled via Supabase.

---

## Setup

### 1. Clone the repository

```sh
git clone https://github.com/YOUR-USERNAME/JBbot.git
cd JBbot
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root with the following content:

```
TELEBOT_TOKEN=your_telegram_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TUAS_CHECKPOINT_URL=your_tuas_checkpoint_image_url
WOODLANDS_CHECKPOINT_URL=your_woodlands_checkpoint_image_url
```

### 4. Set up Supabase

- Create a table called `subscribers` with at least a `user_id` column (type: bigint or text).
- Enable Row Level Security (RLS) and add a policy to allow inserts (see project code or Supabase docs).

### 5. Run the bot

```sh
python main.py
```

---

## Deployment

- You can deploy this bot to a cloud platform (e.g., Railway, Render, Fly.io, Heroku).
- Store your secrets as environment variables on your deployment platform.
- GitHub Actions can be used for CI/CD, but not for 24/7 bot hosting.

---

## License

MIT

---

## Credits

- [python-telegram-bot](https://python-telegram-bot.org/)
- [Supabase](https://supabase.com/)
- [pytesseract](https://github.com/madmaze/pytesseract)

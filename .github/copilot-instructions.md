# Copilot Instructions for JBbot

## Project Overview
- JBbot is a Telegram bot for monitoring traffic at Singapore-Malaysia checkpoints (Tuas, Woodlands).
- Users interact via Telegram commands: `/start`, `/help`, `/check`, `/subscribe`, `/unsubscribe`.
- Traffic times are extracted from checkpoint camera images using OCR (pytesseract + Pillow).
- Subscriber management is handled via Supabase (table: `subscribers`).

## Key Files & Structure
- `main.py`: Core bot logic, OCR extraction, Supabase integration, command handlers, scheduler.
- `.env`: Required for secrets (see README for keys).
- `requirements.txt`: All dependencies must be compatible; see notes below.
- `README.md`: Setup, environment, and deployment instructions.

## Critical Patterns & Conventions
- **Async Handlers:** All Telegram command handlers are async functions.
- **Supabase Usage:**
  - Table: `subscribers` with a `user_id` column.
  - Use `supabase.table(...).insert(...)` and `.delete().eq(...)` for CRUD.
  - Always check for RLS policies if you see DB errors.
- **OCR Extraction:**
  - `get_traffic_time(url, checkpoint)` crops images based on checkpoint, then runs OCR.
  - Crop box coordinates are hardcoded and may need tuning for new image formats.
- **Scheduler:**
  - Uses `schedule` and a background thread to check traffic every 5 minutes.
  - Notifies subscribers if traffic time changes.
- **Error Handling:**
  - Broad `Exception` catches are used to avoid missing notifications/updates; log all errors.

## Dependency Management
- **Compatibility:**
  - `python-telegram-bot==20.3` (requires `httpx<0.25.0`)
  - `supabase==1.0.4` (requires `httpx<0.25.0`)
  - Pin `httpx==0.24.1` for compatibility.
- **Install:** Always use `pip install -r requirements.txt`.

## Environment & Secrets
- All secrets (bot token, Supabase keys, checkpoint URLs) must be set in `.env` or as environment variables.
- Never hardcode secrets in code.

## Example Patterns
- **Add Subscriber:**
  ```python
  supabase.table("subscribers").insert({"user_id": user_id}).execute()
  ```
- **OCR Crop Logic:**
  ```python
  if checkpoint == "Woodlands":
      crop_box = (1200, 200, 1700, 300)
      img = img.crop(crop_box)
  ```
- **Async Command Handler:**
  ```python
  async def subscribe(update: Update) -> None:
      user_id = update.effective_user.id
      add_subscriber(user_id)
      await update.message.reply_text("You have subscribed...")
  ```

## Build & Run
- Local: `python main.py`
- Deployment: See README for cloud options; secrets must be set in environment.

## Troubleshooting
- If you see Supabase errors, check RLS and table schema.
- If you see import errors, check `requirements.txt` and Python version.
- If OCR is inaccurate, adjust crop box coordinates in `get_traffic_time()`.

---

_If any section is unclear or missing, please provide feedback so this guide can be improved._

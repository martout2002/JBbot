"""SG-JB Traffic Telegram Bot: subscribe/unsubscribe, traffic check, help command."""
import os
import re
import time
import threading
from io import BytesIO
import logging
import asyncio

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler
import pytesseract
from PIL import Image
import requests
import schedule
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Telegram Bot Token
TOKEN = os.environ.get("TELEBOT_TOKEN")  # Bot token

# Checkpoint URLs
CHECKPOINTS = {
    "Tuas": os.environ.get("TUAS_CHECKPOINT_URL"),
    "Woodlands": os.environ.get("WOODLANDS_CHECKPOINT_URL")
}

# Global state to track previous times
previous_times = {
    "Tuas": None,
    "Woodlands": None
}
#test
#idk smth to test
#gestsetes
async def start(update: Update) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Welcome to SG-JB Traffic Bot!\n"
        "I'll notify you when traffic conditions change at Tuas or Woodlands checkpoints.\n"
        "Type /help to see all available commands."
    )

async def help_command(update: Update) -> None:
    """Send a help message with all commands."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/check - Get current traffic status\n"
        "/subscribe - Receive notifications when traffic changes\n"
        "/unsubscribe - Stop receiving notifications"
    )

def add_subscriber(user_id):
    """Add a user to the subscribers table."""
    supabase.table("subscribers").insert({"user_id": user_id}).execute()

def remove_subscriber(user_id):
    """Remove a user from the subscribers table."""
    supabase.table("subscribers").delete().eq("user_id", user_id).execute()

def get_subscribers():
    """Get all subscriber user IDs."""
    data = supabase.table("subscribers").select("user_id").execute()
    return [row["user_id"] for row in data.data]

async def subscribe(update: Update) -> None:
    """Subscribe the user to notifications."""
    user_id = update.effective_user.id
    add_subscriber(user_id)
    await update.message.reply_text("You have subscribed to traffic change notifications.")

async def unsubscribe(update: Update) -> None:
    """Unsubscribe the user from notifications."""
    user_id = update.effective_user.id
    remove_subscriber(user_id)
    await update.message.reply_text("You have unsubscribed from notifications.")

async def check_traffic(update: Update) -> None:
    """Check current traffic conditions."""
    messages = []
    for checkpoint, url in CHECKPOINTS.items():
        try:
            time_to_jb = get_traffic_time(url, checkpoint)
            messages.append(f"{checkpoint} checkpoint: {time_to_jb}")
        except Exception as e:
            logger.error("Error checking %s: %s", checkpoint, e)
            messages.append(f"Could not retrieve {checkpoint} data")
    await update.message.reply_text("\n".join(messages))

def get_traffic_time(image_url, checkpoint=None):
    """Download image and extract only the 'time to JB' using OCR."""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    if checkpoint == "Woodlands":
        crop_box = (1200, 200, 1700, 300)
        img = img.crop(crop_box)
    if checkpoint == "Tuas":
        crop_box = (50, 330, 500, 450)
        img = img.crop(crop_box)
    img = img.convert('L')
    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    text = pytesseract.image_to_string(img, config='--psm 6')
    logger.info("OCR output for %s:\n%s", image_url, text)
    match = re.search(r'(\d+\s*min[s]? to JB)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    for line in text.split('\n'):
        if 'mins to JB' in line or 'min to JB' in line:
            return line.strip()
    return "Time not available"

async def notify_subscribers(checkpoint, time_to_jb):
    """Notify all subscribed users about traffic change."""
    message = f"🚨 Traffic change at {checkpoint}: {time_to_jb}"
    subs = get_subscribers()
    if not subs:
        logger.info("No subscribers to notify.")
        return
    for uid in subs:
        try:
            await bot_send_message(int(uid), message)
        except Exception as e:  # Broad exception to avoid missing notifications
            logger.error("Failed to notify %s: %s", uid, e)

async def bot_send_message(user_id, message):
    """Send a message to a user."""
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=user_id, text=message)

def check_traffic_changes():
    """Check for traffic changes and notify subscribers."""
    for checkpoint, url in CHECKPOINTS.items():
        try:
            current_time = get_traffic_time(url)
            if previous_times[checkpoint] and previous_times[checkpoint] != current_time:
                import asyncio
                asyncio.run(notify_subscribers(checkpoint, current_time))
            previous_times[checkpoint] = current_time
        except Exception as e:  # Broad exception to avoid missing traffic updates
            logger.error("Error monitoring %s: %s", checkpoint, e)

def run_scheduler():
    """Run the scheduler in a separate thread."""
    schedule.every(5).minutes.do(check_traffic_changes)
    while True:
        schedule.run_pending()
        time.sleep(1)

def main() -> None:
    """Start the bot."""
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("check", check_traffic))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.run_polling()

if __name__ == "__main__":
    main()

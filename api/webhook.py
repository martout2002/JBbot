from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import re
from supabase import create_client, Client

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEBOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Your Vercel deployment URL + /api/webhook
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Checkpoint URLs
CHECKPOINTS = {
    "Tuas": os.environ.get("TUAS_CHECKPOINT_URL"),
    "Woodlands": os.environ.get("WOODLANDS_CHECKPOINT_URL")
}

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bot command functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Welcome to SG-JB Traffic Bot!\n"
        "I'll notify you when traffic conditions change at Tuas or Woodlands checkpoints.\n"
        "Type /help to see all available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message with all commands."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/check - Get current traffic status\n"
        "/subscribe - Receive notifications when traffic changes\n"
        "/unsubscribe - Stop receiving notifications\n"
    )

def add_subscriber(user_id):
    supabase.table("subscribers").insert({"user_id": user_id}).execute()

def remove_subscriber(user_id):
    supabase.table("subscribers").delete().eq("user_id", user_id).execute()

def get_subscribers():
    data = supabase.table("subscribers").select("user_id").execute()
    return [row["user_id"] for row in data.data]

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    add_subscriber(user_id)
    await update.message.reply_text("You have subscribed to traffic change notifications.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    remove_subscriber(user_id)
    await update.message.reply_text("You have unsubscribed from notifications.")

async def check_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check current traffic conditions."""
    messages = []
    for checkpoint, url in CHECKPOINTS.items():
        try:
            time_to_jb = get_traffic_time(url, checkpoint)
            messages.append(f"{checkpoint} checkpoint: {time_to_jb}")
        except Exception as e:
            logger.error(f"Error checking {checkpoint}: {e}")
            messages.append(f"Could not retrieve {checkpoint} data")
    await update.message.reply_text("\n".join(messages))

def get_traffic_time(image_url, checkpoint=None):
    """Download image and extract only the 'time to JB' using OCR."""
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    
    if checkpoint == "Woodlands":
        # Example crop box: (left, upper, right, lower)
        # Adjust these numbers based on your image!
        crop_box = (1200, 200, 1700, 300)  # <-- Tweak as needed
        img = img.crop(crop_box)
        
    if checkpoint == "Tuas":
        # Example crop box for Tuas
        crop_box = (50, 330, 500, 450)
        img = img.crop(crop_box)
    
    # Preprocess image if needed (improve OCR accuracy)
    img = img.convert('L')  # Convert to grayscale
    img = img.point(lambda x: 0 if x < 128 else 255, '1')  # Thresholding
    
    # Use Tesseract to extract text
    text = pytesseract.image_to_string(img, config='--psm 6')
    logger.info(f"OCR output for {image_url}:\n{text}")
    
    # Use regex to extract only the 'time to JB' (e.g., '22 mins to JB')
    match = re.search(r'(\d+\s*min[s]? to JB)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    # Fallback: try to find the line manually
    for line in text.split('\n'):
        if 'mins to JB' in line or 'min to JB' in line:
            return line.strip()
    return "Time not available"

# Initialize the application
application = Application.builder().token(TOKEN).build()

# Add command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("check", check_traffic))
application.add_handler(CommandHandler("subscribe", subscribe))
application.add_handler(CommandHandler("unsubscribe", unsubscribe))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('OK'.encode())
        
        # Process the update
        update = Update.de_json(json.loads(post_data), application.bot)
        application.process_update(update)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Webhook is active!'.encode())

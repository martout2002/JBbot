from http.server import BaseHTTPRequestHandler
import os
import logging
import requests
from PIL import Image
from io import BytesIO
import re
import json
from supabase import create_client, Client
import asyncio
from telegram import Bot

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEBOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Checkpoint URLs
CHECKPOINTS = {
    "Tuas": os.environ.get("TUAS_CHECKPOINT_URL"),
    "Woodlands": os.environ.get("WOODLANDS_CHECKPOINT_URL")
}

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Global state to track previous times (will reset on each function execution, but that's okay)
previous_times = {}

def get_subscribers():
    data = supabase.table("subscribers").select("user_id").execute()
    return [row["user_id"] for row in data.data]

async def bot_send_message(user_id, message):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=user_id, text=message)

def get_traffic_time(image_url, checkpoint=None):
    """Download image and extract only the 'time to JB' using OCR."""
    import pytesseract
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    
    if checkpoint == "Woodlands":
        crop_box = (1200, 200, 1700, 300)
        img = img.crop(crop_box)
        
    if checkpoint == "Tuas":
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
        except Exception as e:
            logger.error(f"Failed to notify {uid}: {e}")

async def check_traffic_changes():
    """Check for traffic changes and notify subscribers."""
    # First, load previous times from database
    try:
        data = supabase.table("checkpoint_times").select("*").execute()
        for row in data.data:
            previous_times[row["checkpoint"]] = row["time"]
    except Exception as e:
        logger.error(f"Error loading previous times: {e}")
        # Initialize if we couldn't load
        for checkpoint in CHECKPOINTS:
            previous_times[checkpoint] = None

    # Now check current times and update
    for checkpoint, url in CHECKPOINTS.items():
        try:
            current_time = get_traffic_time(url, checkpoint)
            if previous_times.get(checkpoint) and previous_times[checkpoint] != current_time:
                # Traffic condition changed - notify subscribers
                await notify_subscribers(checkpoint, current_time)
            
            # Update previous time in database
            try:
                if previous_times.get(checkpoint) is None:
                    # Insert new record
                    supabase.table("checkpoint_times").insert(
                        {"checkpoint": checkpoint, "time": current_time}
                    ).execute()
                else:
                    # Update existing record
                    supabase.table("checkpoint_times").update(
                        {"time": current_time}
                    ).eq("checkpoint", checkpoint).execute()
            except Exception as e:
                logger.error(f"Error updating database: {e}")
                
            # Update local cache
            previous_times[checkpoint] = current_time
        except Exception as e:
            logger.error(f"Error monitoring {checkpoint}: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Run the traffic check
        asyncio.run(check_traffic_changes())
        
        self.wfile.write(json.dumps({"status": "Traffic check completed"}).encode())

from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ.get("TELEBOT_TOKEN")

# Bot command functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Welcome to SG-JB Traffic Bot!\n"
        "This is a test version without OCR or database functionality.\n"
        "Type /help to see all available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message with all commands."""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/test - Test that the bot is working\n"
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Test command to verify bot functionality."""
    await update.message.reply_text("Bot is working! 🎉")

# Initialize the application
application = Application.builder().token(TOKEN).build()

# Add command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("test", test_command))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('OK'.encode())
            
            # Process the update
            update_data = json.loads(post_data)
            update = Update.de_json(update_data, application.bot)
            
            # Use asyncio to run the async function
            import asyncio
            asyncio.run(application.process_update(update))
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error: {str(e)}'.encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Simple webhook is active!'.encode())

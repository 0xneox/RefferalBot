import os
import json
import random
from datetime import time
from urllib.parse import urlencode, urljoin
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# Load Telegram bot token from environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))  # Ensure you set this in the .env file for security
BASE_URL = os.getenv("BASE_URL", "http://yourdomain.com/")  # Base URL for referral links

# File to store referral data
DATA_FILE = "referral_data.json"

# Load referral data from file
def load_referral_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save referral data to file
def save_referral_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

# Initialize referral data
referral_data = load_referral_data()

def generate_referral_link(user_id: str) -> str:
    """Generate a unique referral link for a user."""
    return urljoin(BASE_URL, f"referral?user_id={user_id}")

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    referral_link = generate_referral_link(user.id)
    await update.message.reply_text(f"Welcome {user.first_name}! Use your referral link: {referral_link} to invite others. Use /referral to see your referral count or /leaderboard to see the top referrers.")

async def referral(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    referrals = referral_data.get(user_id, {}).get('referrals', 0)
    await update.message.reply_text(f"You have referred {referrals} people.")

async def leaderboard(update: Update, context: CallbackContext) -> None:
    # Sort the referral data by the number of referrals
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1].get('referrals', 0), reverse=True)
    
    leaderboard_text = "<b>Top Referrers:</b>\n\n"
    for position, (user_id, data) in enumerate(sorted_referrals[:10], start=1):
        try:
            user = await context.bot.get_chat(user_id)
            leaderboard_text += f"{position}. {user.first_name} - {data.get('referrals', 0)} referrals\n"
        except Exception as e:
            logging.error(f"Error fetching user {user_id}: {e}")
            leaderboard_text += f"{position}. User ID {user_id} - {data.get('referrals', 0)} referrals\n"
    
    if not sorted_referrals:
        leaderboard_text = "No referrals have been made yet."
    
    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)

async def track_invites(update: Update, context: CallbackContext) -> None:
    new_members = update.message.new_chat_members
    inviter_id = str(update.message.from_user.id)

    for member in new_members:
        if inviter_id not in referral_data:
            referral_data[inviter_id] = {'referrals': 0}
        referral_data[inviter_id]['referrals'] += 1

    save_referral_data(referral_data)
    await update.message.reply_text(f"Referral tracked! You have referred {referral_data[inviter_id]['referrals']} people.")

async def handle_referral_link(update: Update, context: CallbackContext) -> None:
    user_id = context.args[0]
    if user_id:
        if user_id not in referral_data:
            referral_data[user_id] = {'referrals': 0}
        referrer_id = str(update.effective_user.id)
        if referrer_id not in referral_data:
            referral_data[referrer_id] = {'referrals': 0}
        referral_data[referrer_id]['referrals'] += 1
        referral_data[user_id]['referrals'] += 1
        save_referral_data(referral_data)
        await update.message.reply_text(f"Referral link tracked! {update.effective_user.first_name} has been referred.")

async def random_winner(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    # Sort the referral data by the number of referrals and pick a random winner from the top 10
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1].get('referrals', 0), reverse=True)
    if sorted_referrals:
        top_referrers = sorted_referrals[:10]
        winner_id, data = random.choice(top_referrers)
        try:
            winner = await context.bot.get_chat(winner_id)
            await update.message.reply_text(f"🎉 The random winner from the top referrers is {winner.first_name} with {data.get('referrals', 0)} referrals!")
        except Exception as e:
            logging.error(f"Error fetching winner {winner_id}: {e}")
            await update.message.reply_text(f"🎉 The random winner from the top referrers is User ID {winner_id} with {data.get('referrals', 0)} referrals!")
    else:
        await update.message.reply_text("No referrals have been made yet.")

async def send_daily_leaderboard(context: CallbackContext) -> None:
    chat_id = context.job.chat_id
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1].get('referrals', 0), reverse=True)
    
    leaderboard_text = "<b>Daily Leaderboard - Top Referrers:</b>\n\n"
    for position, (user_id, data) in enumerate(sorted_referrals[:10], start=1):
        try:
            user = await context.bot.get_chat(user_id)
            leaderboard_text += f"{position}. {user.first_name} - {data.get('referrals', 0)} referrals\n"
        except Exception as e:
            logging.error(f"Error fetching user {user_id}: {e}")
            leaderboard_text += f"{position}. User ID {user_id} - {data.get('referrals', 0)} referrals\n"
    
    if not sorted_referrals:
        leaderboard_text = "No referrals have been made yet."
    
    await context.bot.send_message(chat_id=chat_id, text=leaderboard_text, parse_mode=ParseMode.HTML)

def set_daily_leaderboard(job_queue: JobQueue, chat_id: int):
    job_queue.run_daily(send_daily_leaderboard, time=time(hour=9, minute=0), chat_id=chat_id)

def main():
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("pickwinner", random_winner))  # Admin-only command to pick a random winner

    # Track invites using a message handler for new chat members
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))

    # Handle referral links (assuming your app will use a command or webhook to process this)
    application.add_handler(CommandHandler("referral_link", handle_referral_link))

    # Schedule daily leaderboard
    set_daily_leaderboard(application.job_queue, chat_id=-1001234567890)  # Replace with your group/chat ID

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()

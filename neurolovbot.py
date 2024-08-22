import os
import json
import random
from datetime import time
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue
from dotenv import load_dotenv

load_dotenv()

# Load Telegram bot token from environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))  # Ensure you set this in the .env file for security

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

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(f"Welcome {user.first_name}! Use /referral to see your referral count or /leaderboard to see the top referrers.")

def referral(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    referrals = referral_data.get(user_id, 0)
    update.message.reply_text(f"You have referred {referrals} people.")

def leaderboard(update: Update, context: CallbackContext) -> None:
    # Sort the referral data by the number of referrals
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1], reverse=True)
    
    leaderboard_text = "<b>Top Referrers:</b>\n\n"
    for position, (user_id, count) in enumerate(sorted_referrals[:10], start=1):
        user = context.bot.get_chat(user_id)
        leaderboard_text += f"{position}. {user.first_name} - {count} referrals\n"
    
    if not sorted_referrals:
        leaderboard_text = "No referrals have been made yet."
    
    update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)

def track_invites(update: Update, context: CallbackContext) -> None:
    new_members = update.message.new_chat_members
    inviter_id = str(update.message.from_user.id)

    for member in new_members:
        if inviter_id not in referral_data:
            referral_data[inviter_id] = 0
        referral_data[inviter_id] += 1

    save_referral_data(referral_data)
    update.message.reply_text(f"Referral tracked! You have referred {referral_data[inviter_id]} people.")

def random_winner(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id != ADMIN_USER_ID:
        update.message.reply_text("You do not have permission to use this command.")
        return

    # Sort the referral data by the number of referrals and pick a random winner from the top 10
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1], reverse=True)
    if sorted_referrals:
        top_referrers = sorted_referrals[:10]
        winner_id, count = random.choice(top_referrers)
        winner = context.bot.get_chat(winner_id)
        update.message.reply_text(f"🎉 The random winner from the top referrers is {winner.first_name} with {count} referrals!")
    else:
        update.message.reply_text("No referrals have been made yet.")

def send_daily_leaderboard(context: CallbackContext) -> None:
    chat_id = context.job.context
    sorted_referrals = sorted(referral_data.items(), key=lambda item: item[1], reverse=True)
    
    leaderboard_text = "<b>Daily Leaderboard - Top Referrers:</b>\n\n"
    for position, (user_id, count) in enumerate(sorted_referrals[:10], start=1):
        user = context.bot.get_chat(user_id)
        leaderboard_text += f"{position}. {user.first_name} - {count} referrals\n"
    
    if not sorted_referrals:
        leaderboard_text = "No referrals have been made yet."
    
    context.bot.send_message(chat_id=chat_id, text=leaderboard_text, parse_mode=ParseMode.HTML)

def set_daily_leaderboard(job_queue: JobQueue, chat_id: int):
    job_queue.run_daily(send_daily_leaderboard, time=time(hour=9, minute=0), context=chat_id)

def main():
    updater = Updater(BOT_TOKEN)

    dp = updater.dispatcher
    job_queue = updater.job_queue

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("referral", referral))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(CommandHandler("pickwinner", random_winner))  # Admin-only command to pick a random winner

    # Track invites using a message handler for new chat members
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, track_invites))

    # Schedule daily leaderboard
    set_daily_leaderboard(job_queue, chat_id=-1001234567890)  # Replace with your group/chat ID

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

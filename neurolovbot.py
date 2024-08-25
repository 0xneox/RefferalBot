import os
import json
import random
from datetime import time, datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv

# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# TG token and other configs from env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
GROUP_INVITE_LINK = os.getenv("GROUP_INVITE_LINK")

# Store user data
USER_DATA_FILE = "user_data.json"
OLD_REFERRAL_FILE = "referral_data.json"  # Old referral data

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            data = json.load(file)
            logger.debug(f"Loaded data from {filename}: {data}")
            return data
    logger.warning(f"File {filename} does not exist. Returning empty dict.")
    return {}

def save_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=2)
    logger.debug(f"Saved data to {filename}: {data}")

# Initialize user data
user_data = load_data(USER_DATA_FILE)
old_referral_data = load_data(OLD_REFERRAL_FILE)

def ensure_user_data_structure(user_id, name="Unknown", username=None):
    user_id = str(user_id)  # Ensure user_id is a string
    logger.debug(f"Ensuring user data structure for user_id: {user_id}, name: {name}, username: {username}")
    if user_id not in user_data:
        logger.info(f"Creating new user data entry for user_id: {user_id}")
        user_data[user_id] = {
            "id": user_id,
            "name": name,
            "username": username,
            "join_date": datetime.now().isoformat(),
            "referrer": None,
            "referrals": [],
            "total_referrals": 0,
            "link_referrals": 0,
            "group_referrals": 0
        }
    else:
        logger.info(f"Updating existing user data for user_id: {user_id}")
        # Update name and username
        user_data[user_id]["name"] = name
        user_data[user_id]["username"] = username
    
    save_data(user_data, USER_DATA_FILE)
    logger.debug(f"User data after update: {user_data[user_id]}")
    return user_data[user_id]

# Migrate old referral data to new format and ensure consistent keys
for user_id, referral_count in old_referral_data.items():
    user_data_entry = ensure_user_data_structure(user_id)
    user_data_entry["total_referrals"] = referral_count
    user_data_entry["link_referrals"] = referral_count

save_data(user_data, USER_DATA_FILE)

def get_user_display_name(user_data):
    logger.debug(f"Getting display name for user data: {user_data}")
    if user_data.get('username'):
        return f"@{user_data['username']}"
    elif user_data.get('name'):
        return user_data['name']
    elif user_data.get('id'):
        return f"User {user_data['id']}"
    else:
        logger.warning(f"Unable to get display name for user data: {user_data}")
        return "Unknown User"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    referrer_id = context.args[0] if context.args else None

    logger.info(f"Start command received from user: {user_id}, name: {user.first_name}, username: {user.username}")
    user_data_entry = ensure_user_data_structure(user_id, user.first_name, user.username)
    logger.info(f"User data updated: {user_data_entry}")
    
    if referrer_id and referrer_id != user_id:
        referrer_data = ensure_user_data_structure(referrer_id)
        referrer_data["referrals"].append(user_id)
        referrer_data["total_referrals"] += 1
        referrer_data["link_referrals"] += 1
        save_data(user_data, USER_DATA_FILE)
        referrer_name = get_user_display_name(referrer_data)
        await update.message.reply_text(f"Welcome {user.first_name}! You were referred by {referrer_name}.")
    else:
        await update.message.reply_text(f"Welcome {user.first_name}! Use /referral to get your referral link.")

    keyboard = [
        [InlineKeyboardButton("Join Our Group", url=GROUP_INVITE_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click the button below to join our group:", reply_markup=reply_markup)

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    referral_link = f"{GROUP_INVITE_LINK}?start={user_id}"
    user_info = ensure_user_data_structure(user_id, user.first_name, user.username)

    logger.info(f"Referral command received from user: {user_id}")
    logger.debug(f"User info: {user_info}")

    keyboard = [
        [InlineKeyboardButton("Share Referral Link", switch_inline_query=f"Join our group! {referral_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Your referral link is: {referral_link}\n"
        f"Total referrals: {user_info['total_referrals']}\n"
        f"Link referrals: {user_info['link_referrals']}\n"
        f"Group add referrals: {user_info['group_referrals']}\n"
        "Click the button below to share your referral link:",
        reply_markup=reply_markup
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Generating leaderboard")
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['total_referrals'], reverse=True)
    
    leaderboard_text = "<b>Top Referrers:</b>\n\n"
    for position, (user_id, data) in enumerate(sorted_users[:10], start=1):
        user_display = get_user_display_name(data)
        leaderboard_text += f"{position}. {user_display} - {data['total_referrals']} total referrals "
        leaderboard_text += f"({data['link_referrals']} by link, {data['group_referrals']} by group add)\n"
    
    if not sorted_users:
        leaderboard_text = "No referrals have been made yet."
    
    logger.info(f"Leaderboard generated: {leaderboard_text}")
    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)

async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    
    logger.info(f"User info requested for user: {user_id}")
    data = ensure_user_data_structure(user_id, user.first_name, user.username)
    join_date = datetime.fromisoformat(data['join_date'])
    account_age = (datetime.now() - join_date).days
    
    info_text = f"User: {get_user_display_name(data)}\n"
    info_text += f"Account Age: {account_age} days\n"
    info_text += f"Premium Status: {'Yes' if user.is_premium else 'No'}\n"
    info_text += f"Total Referrals: {data['total_referrals']}\n"
    info_text += f"Link Referrals: {data['link_referrals']}\n"
    info_text += f"Group Add Referrals: {data['group_referrals']}\n"
    
    if data['referrer']:
        referrer = ensure_user_data_structure(data['referrer'])
        referrer_display = get_user_display_name(referrer)
        info_text += f"Referred by: {referrer_display}\n"
    
    info_text += "\nPeople you referred:\n"
    for referred_id in data['referrals'][:5]:  # Show only the first 5 referrals
        referred_data = ensure_user_data_structure(referred_id)
        referred_display = get_user_display_name(referred_data)
        info_text += f"- {referred_display}\n"
    
    if len(data['referrals']) > 5:
        info_text += f"...and {len(data['referrals']) - 5} more"

    logger.info(f"User info generated for {user_id}: {info_text}")
    await update.message.reply_text(info_text)

async def random_winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if str(user.id) != ADMIN_USER_ID:
        await update.message.reply_text("You do not have permission to use this command.")
        return

    logger.info("Selecting random winner")
    active_users = [uid for uid, data in user_data.items() if data['total_referrals'] > 0]
    if active_users:
        winner_id = random.choice(active_users)
        winner_data = ensure_user_data_structure(winner_id)
        winner_display = get_user_display_name(winner_data)
        message = (
            f"🎉 The random winner is {winner_display} with {winner_data['total_referrals']} total referrals "
            f"({winner_data['link_referrals']} by link, {winner_data['group_referrals']} by group add)!"
        )
        logger.info(f"Random winner selected: {message}")
        await update.message.reply_text(message)
    else:
        logger.info("No eligible users for random draw")
        await update.message.reply_text("No eligible users for the random draw.")

async def send_daily_leaderboard(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Generating daily leaderboard")
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['total_referrals'], reverse=True)
    
    leaderboard_text = "<b>Daily Leaderboard - Top Referrers:</b>\n\n"
    for position, (user_id, data) in enumerate(sorted_users[:25], start=1):
        user_display = get_user_display_name(data)
        leaderboard_text += f"{position}. {user_display} - {data['total_referrals']} total referrals "
        leaderboard_text += f"({data['link_referrals']} by link, {data['group_referrals']} by group add)\n"
    
    if not sorted_users:
        leaderboard_text = "No referrals have been made yet."
    
    logger.info(f"Daily leaderboard generated: {leaderboard_text}")
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=leaderboard_text, parse_mode=ParseMode.HTML)

async def referral_tree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    
    logger.info(f"Generating referral tree for user: {user_id}")
    user_data_entry = ensure_user_data_structure(user_id, user.first_name, user.username)
    
    tree_text = f"Referral Tree for {get_user_display_name(user_data_entry)}:\n"
    
    def build_tree(uid, level=0):
        nonlocal tree_text
        data = ensure_user_data_structure(uid)
        user_display = get_user_display_name(data)
        tree_text += f"{'  ' * level}└─ {user_display} ({data['total_referrals']} total, {data['link_referrals']} by link, {data['group_referrals']} by group)\n"
        for referred_id in data['referrals']:
            build_tree(referred_id, level + 1)
    
    build_tree(user_id)
    
    logger.info(f"Referral tree generated for {user_id}: {tree_text}")
    await update.message.reply_text(tree_text)

async def track_group_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_members = update.message.new_chat_members
    inviter = update.message.from_user
    inviter_id = str(inviter.id)

    logger.info(f"Tracking group add: inviter {inviter_id}, new members: {[m.id for m in new_members]}")
    inviter_data = ensure_user_data_structure(inviter_id, inviter.first_name, inviter.username)

    for member in new_members:
        if not member.is_bot:
            member_id = str(member.id)
            member_data = ensure_user_data_structure(member_id, member.first_name, member.username)
            member_data["referrer"] = inviter_id
            
            inviter_data["referrals"].append(member_id)
            inviter_data["total_referrals"] += 1
            inviter_data["group_referrals"] += 1

    save_data(user_data, USER_DATA_FILE)
    inviter_display = get_user_display_name(inviter_data)
    logger.info(f"Group add referral tracked: {inviter_display} referred {len(new_members)} new members")
    await update.message.reply_text(f"Group add referral tracked! {inviter_display} has referred {inviter_data['total_referrals']} people in total.")

def main() -> None:
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("referral", referral))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("user", user_info))
        application.add_handler(CommandHandler("pickwinner", random_winner))
        application.add_handler(CommandHandler("tree", referral_tree))

        # Add message handler for new chat members
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_group_add))

        # Schedule daily leaderboard
        application.job_queue.run_daily(send_daily_leaderboard, time=time(hour=0, minute=0, second=0))

        logger.info("Starting bot")
        application.run_polling()

    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == '__main__':
    main()

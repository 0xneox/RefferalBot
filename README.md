# Telegram Referral Bot

This Telegram bot is designed to manage and track referrals within a group. It provides features such as referral links, leaderboards, and user statistics to encourage and monitor user engagement.

## Features

- **Referral System**: Users can generate unique referral links to invite others.
- **Leaderboard**: View top referrers and their statistics.
- **User Info**: Check personal referral stats and account information.
- **Referral Tree**: Visualize the hierarchy of referrals.
- **Random Winner Selection**: Admin can pick a random winner from active referrers.
- **Daily Leaderboard**: Automatically posts a daily leaderboard to the group.
- **Group Add Tracking**: Monitors and credits users for adding new members to the group.

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/telegram-referral-bot.git
   cd telegram-referral-bot
   ```

2. Install the required dependencies:
   ```
   pip install python-telegram-bot python-dotenv
   ```

3. Create a `.env` file in the project root with the following content:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ADMIN_USER_ID=your_admin_user_id
   GROUP_CHAT_ID=your_group_chat_id
   GROUP_INVITE_LINK=https://t.me/your_group_invite_link
   ```

   Replace the placeholders with your actual bot token, admin user ID, group chat ID, and group invite link.

4. Run the bot:
   ```
   python bot.py
   ```

## Usage

- `/start`: Initiates the bot and registers the user. If used with a referral parameter, it credits the referrer.
- `/referral`: Generates a unique referral link for the user.
- `/leaderboard`: Displays the top referrers and their stats.
- `/user`: Shows the user's personal referral statistics and account info.
- `/tree`: Visualizes the user's referral tree.
- `/pickwinner`: (Admin only) Selects a random winner from active referrers.

## Data Storage

The bot stores user data in a JSON file (`user_data.json`). This file is automatically created and updated as users interact with the bot.

## Customization

You can customize the bot by modifying the following:

- Adjust the number of users shown in the leaderboard by changing the slice in the `leaderboard` function.
- Modify the daily leaderboard posting time in the `main` function.
- Customize messages and responses throughout the code to fit your group's style and needs.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.


## Disclaimer

This bot is provided as-is, without any guarantees or warranty. The authors are not responsible for any damage or data loss that may occur from using this bot.

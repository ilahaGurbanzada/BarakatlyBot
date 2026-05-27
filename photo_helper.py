"""
Photo File ID Helper
=====================

Run this AFTER your main bot is working, to capture photo file_ids.

How it works:
1. Stop your main bot (Ctrl+C)
2. Run: python photo_helper.py
3. In Telegram, send any photo to your bot
4. The script prints the file_id — copy it
5. Paste it into menu.py for the right farmer:
     "main_photo_id": "AgACAgIAAxkBAAI...",
6. Repeat for all farmer photos
7. Stop this script (Ctrl+C) and run bot.py again

Why this approach? Telegram caches photos for free forever once uploaded.
You upload each photo ONE TIME, then the bot reuses the file_id —
no Google Drive, no hosting, no bandwidth costs.
"""

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Print file_id of any photo sent to the bot."""
    photo = update.message.photo[-1]  # highest resolution version
    file_id = photo.file_id

    print("\n" + "=" * 60)
    print(f"📸 PHOTO RECEIVED from {update.effective_user.first_name}")
    print(f"file_id: {file_id}")
    print("=" * 60 + "\n")

    await update.message.reply_text(
        f"✅ File ID:\n\n`{file_id}`\n\n"
        f"Bunu menu.py-də müvafiq fermerin yanına əlavə edin.",
        parse_mode="Markdown",
    )


def main():
    if not BOT_TOKEN:
        print("❌ Set BOT_TOKEN in .env first")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("📸 Photo helper running. Send photos to your bot.")
    print("   File IDs will appear here. Press Ctrl+C to stop.\n")
    app.run_polling()


if __name__ == "__main__":
    main()

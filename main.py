import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Logging configuration
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Configuration - Token from environment variable or direct fallback
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8616428378:AAHYrUDzQKbbjAEjd0Dvs5fZvawv6S2e7Nw")
ADMIN_USERNAME = "Trusted_zone_1122"
ADMIN_ID = 7624991230
CARD_PRICE = 30

# In-memory storage
user_balances = {}
card_stock = {} # {"BIN": ["card1", "card2"]}

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("🔍 Search BIN", callback_data="search_bin")],
        [InlineKeyboardButton("💰 My Balance", callback_data="my_balance"), InlineKeyboardButton("➕ Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("👤 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 হ্যালো {user.first_name}!\n\n"
        f"আমাদের অটোমেটেড ফেসবুক এডস কার্ড বটে স্বাগতম।\n"
        f"এখানে আপনি বিভিন্ন BIN-এর কার্ড অটোমেটিক কিনতে পারবেন।\n\n"
        f"📌 প্রতি কার্ডের মূল্য: {CARD_PRICE} BDT"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        query = update.callback_query
        await query.answer()
        await query.message.reply_text(welcome_text, reply_markup=reply_markup)

# Admin Command: Single Card Add (/addcard <BIN> <CARD>)
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করার অনুমোদন পাননি।")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ ভুল ফরমেট!\n\n"
            "একটি কার্ড অ্যাড করার নিয়ম:\n"
            "`/addcard <BIN> <CARD_DETAILS>`\n\n"
            "উদাহরণ:\n"
            "`/addcard 426684 4266841850892165|12|29|492`",
            parse_mode="Markdown"
        )
        return

    bin_num = context.args[0]
    card_details = " ".join(context.args[1:])

    if bin_num not in card_stock:
        card_stock[bin_num] = []

    card_stock[bin_num].append(card_details)
    total_count = len(card_stock[bin_num])

    await update.message.reply_text(
        f"✅ ১টি কার্ড সফলভাবে যোগ করা হয়েছে!\n\n"
        f"📌 **BIN:** `{bin_num}`\n"
        f"💳 **Card:** `{card_details}`\n"
        f"📦 **এই BIN-এ মোট কার্ড আছে:** {total_count} টি",
        parse_mode="Markdown"
    )

# Admin Command: Bulk Cards Add (/addcards <BIN> \n card1 \n card2...)
async def add_cards_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করার অনুমোদন পাননি।")
        return

    text = update.message.text
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]

    # First line check
    first_line_parts = lines[0].split()
    if len(first_line_parts) < 2:
        await update.message.reply_text(
            "⚠️ ভুল ফরমেট!\n\n"
            "একসাথে একাধিক কার্ড যোগ করার সঠিক নিয়ম:\n\n"
            "`/addcards <BIN>`\n"
            "`card1|MM|YY|CVC`\n"
            "`card2|MM|YY|CVC`\n\n"
            "উদাহরণ:\n"
            "`/addcards 426684`\n"
            "`4266841850892165|12|29|492`\n"
            "`4266841803198751|01|29|747`",
            parse_mode="Markdown"
        )
        return

    bin_num = first_line_parts[1]
    card_lines = lines[1:] # All remaining lines

    if not card_lines:
        await update.message.reply_text("⚠️ অনুগ্রহ করে কমান্ডের নিচের লাইনে কার্ডের তালিকা দিন।")
        return

    if bin_num not in card_stock:
        card_stock[bin_num] = []

    added_count = 0
    for card in card_lines:
        card_stock[bin_num].append(card)
        added_count += 1

    total_count = len(card_stock[bin_num])

    await update.message.reply_text(
        f"✅ **সফলভাবে {added_count} টি কার্ড যোগ করা হয়েছে!**\n\n"
        f"📌 **BIN:** `{bin_num}`\n"
        f"📦 **এই BIN-এ বর্তমান মোট স্টক:** {total_count} টি",
        parse_mode="Markdown"
    )

# Admin Command: Check Stock
async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করার অনুমোদন পাননি।")
        return

    if not card_stock:
        await update.message.reply_text("📦 বর্তমানে কোনো কার্ড স্টকে নেই।")
        return

    text = "📦 **বর্তমান কার্ড স্টক তালিকা:**\n\n"
    for bin_num, cards in card_stock.items():
        text += f"🔹 **BIN:** `{bin_num}` ➔ {len(cards)} টি কার্ড আছে\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# Main Function
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CommandHandler("addcards", add_cards_bulk))
    app.add_handler(CommandHandler("stock", check_stock))

    app.run_polling()

if __name__ == "__main__":
    main()

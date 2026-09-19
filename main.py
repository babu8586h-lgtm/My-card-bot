import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Configuration
BOT_TOKEN = "8616428378:AAHYrUDzQKbbjAEjd0Dvs5fZvavw6S2e7Nw"
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

# Admin Command: Add Card
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহার করার অনুমোদন পাননি।")
        return

    # Usage: /addcard <BIN> <CARD_DETAILS>
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ ভুল ফরমেট!\n\n"
            "সঠিক নিয়ম:\n"
            "`/addcard <BIN> <CARD_DETAILS>`\n\n"
            "উদাহরণ:\n"
            "`/addcard 411122 4111221234567890|05|28|123`",
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
        f"✅ কার্ড সফলভাবে যোগ করা হয়েছে!\n\n"
        f"📌 **BIN:** `{bin_num}`\n"
        f"💳 **Card:** `{card_details}`\n"
        f"📦 **এই BIN-এ মোট কার্ড আছে:** {total_count} টি",
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
    app.add_handler(CommandHandler("stock", check_stock))

    app.run_polling()

if __name__ == "__main__":
    main()

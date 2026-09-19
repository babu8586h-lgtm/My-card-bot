import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationRule
)

# ==========================================
# আপনার তথ্য দিয়ে সেটআপ করুন
# ==========================================
BOT_TOKEN = "8616428378:AAHYrUDzQKbbjAEjdODvs5fZvavw6S2e7Nw"      # BotFather এর টোকেন
ADMIN_USERNAME = "Trusted_zone_1122" # আপনার টেলিগ্রাম ইউজারনেম (উইদাউট @)
ADMIN_ID = 7624991230                # আপনার টেলিগ্রাম Numeric User ID (জেনে নিতে @userinfobot এ মেসেজ দিন)
CARD_PRICE = 30                        # প্রতি কার্ডের দাম (৩০ টাকা)

# ডাটাবেস (মেমোরি)
user_balances = {}  # {user_id: balance}
card_stock = {}     # {"411122": ["Card1_Details", "Card2_Details"]}

# স্টেট ডেফিনিশন
WAITING_FOR_BIN = 1

# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("🔍 Search BIN", callback_data="search_bin")],
        [InlineKeyboardButton("💰 My Balance", callback_data="my_balance"),
         InlineKeyboardButton("➕ Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("👨‍💻 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 হ্যালো {user.first_name}!\n\n"
        f"আমাদের অটোমেটেড ফেইসবুক এডস কার্ড বটে স্বাগতম।\n"
        f"এখানে আপনি বিভিন্ন BIN-এর কার্ড অটোমেটিক কিনতে পারবেন।\n\n"
        f"📌 **প্রতি কার্ডের মূল্য:** {CARD_PRICE} BDT"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

# বাটন হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "my_balance":
        balance = user_balances.get(user_id, 0.0)
        await query.message.reply_text(f"💳 **আপনার বর্তমান ব্যালেন্স:** {balance} BDT", parse_mode='Markdown')

    elif query.data == "add_balance":
        msg = (
            f"➕ **ব্যালেন্স এড করার নিয়ম:**\n\n"
            f"১. এডমিনকে টাকা পাঠান।\n"
            f"২. আপনার Telegram User ID: `{user_id}` এডমিনকে পাঠান।\n\n"
            f"📩 এডমিনের সাথে যোগাযোগ করুন: @{ADMIN_USERNAME}"
        )
        await query.message.reply_text(msg, parse_mode='Markdown')

    elif query.data == "search_bin":
        context.user_data['state'] = WAITING_FOR_BIN
        await query.message.reply_text("🔍 কার্ডের **প্রথম ৬ ডিজিট (BIN)** লিখে মেসেজ দিন (যেমন: `411122`):", parse_mode='Markdown')

    elif query.data.startswith("buy_"):
        bin_number = query.data.split("_")[1]
        balance = user_balances.get(user_id, 0.0)

        if balance < CARD_PRICE:
            await query.message.reply_text(
                f"❌ **অপর্যাপ্ত ব্যালেন্স!**\n\n"
                f"আপনার ব্যালেন্স: {balance} BDT\n"
                f"কার্ডের দাম: {CARD_PRICE} BDT\n\n"
                f"ব্যালেন্স এড করতে এডমিনের সাথে কথা বলুন: @{ADMIN_USERNAME}"
            )
            return

        if bin_number in card_stock and len(card_stock[bin_number]) > 0:
            # ব্যালেন্স কাটা
            user_balances[user_id] -= CARD_PRICE
            # কার্ড দেওয়া
            card = card_stock[bin_number].pop(0)
            
            await query.message.reply_text(
                f"✅ **পারচেজ সফল হয়েছে!**\n\n"
                f"💳 **আপনার কার্ডের তথ্য:**\n`{card}`\n\n"
                f"💰 **অবশিষ্ট ব্যালেন্স:** {user_balances[user_id]} BDT",
                parse_mode='Markdown'
            )
        else:
            await query.message.reply_text("❌ দুঃখিত! এই BIN-এর কোনো কার্ড বর্তমানে স্টোকে নেই।")

# টেক্সট মেসেজ (BIN সার্চিং)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == WAITING_FOR_BIN:
        bin_number = update.message.text.strip()
        context.user_data['state'] = None  # রিসেট স্টেট

        if len(bin_number) >= 6 and bin_number.isdigit():
            bin_prefix = bin_number[:6]
            
            if bin_prefix in card_stock and len(card_stock[bin_prefix]) > 0:
                count = len(card_stock[bin_prefix])
                keyboard = [[InlineKeyboardButton(f"🛒 Purchase ({CARD_PRICE} BDT)", callback_data=f"buy_{bin_prefix}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    f"✅ **কার্ড পাওয়া গেছে!**\n\n"
                    f"🔹 **BIN:** `{bin_prefix}`\n"
                    f"🔹 **স্টোক এভেলেবেল:** {count} টি\n"
                    f"🔹 **মূল্য:** {CARD_PRICE} BDT\n\n"
                    f"কিনতে নিচের পারচেজ বাটনে ক্লিক করুন:",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ **BIN: {bin_prefix}** - এই BIN-এর কোনো কার্ড বর্তমানে এভেলেবেল নেই।")
        else:
            await update.message.reply_text("⚠️ অনুগ্রহ করে সঠিক ৬ ডিজিটের BIN নম্বর দিন।")

# ==========================================
# এডমিন কমান্ডস (Admin Only)
# ==========================================

# ইউজারের ব্যালেন্স এড করার কমান্ড: /addbalance USER_ID AMOUNT
async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_user_id = int(context.args[0])
        amount = float(context.args[1])
        
        user_balances[target_user_id] = user_balances.get(target_user_id, 0.0) + amount
        await update.message.reply_text(f"✅ User `{target_user_id}` এর একাউন্টে {amount} BDT সফলভাবে এড করা হয়েছে।")
        
        # ইউজারকে নোটিফিকেশন পাঠানো
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 আপনার একাউন্টে **{amount} BDT** ব্যালেন্স এড করা হয়েছে!\nবর্তমান ব্যালেন্স: {user_balances[target_user_id]} BDT"
        )
    except Exception as e:
        await update.message.reply_text("⚠️ সঠিক ফরম্যাট: `/addbalance USER_ID AMOUNT`", parse_mode='Markdown')

# বটে কার্ড আপলোড করার কমান্ড: /addcard BIN CARD_DETAILS
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        bin_number = context.args[0].strip()[:6]
        card_details = " ".join(context.args[1:])

        if bin_number not in card_stock:
            card_stock[bin_number] = []
        
        card_stock[bin_number].append(card_details)
        await update.message.reply_text(f"✅ BIN `{bin_number}` এ নতুন কার্ড এড করা হয়েছে। বর্তমান মোট স্টোক: {len(card_stock[bin_number])} টি।")
    except Exception as e:
        await update.message.reply_text("⚠️ সঠিক ফরম্যাট: `/addcard BIN_NUMBER CARD_DETAILS`", parse_mode='Markdown')

# মেইন রানার
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbalance", add_balance))
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started with Balance & BIN Search System...")
    app.run_polling()

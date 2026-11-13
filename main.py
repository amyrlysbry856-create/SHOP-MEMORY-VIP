
import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

db = sqlite3.connect("vip.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS customers (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    purchases INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0
)
""")
db.commit()

def get_level(purchases):
    if purchases >= 5:
        return "🥇 GOLD", 6, 3
    elif purchases >= 3:
        return "🥈 SILVER", 4, 2
    return "🥉 BRONZE", 2, 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.execute(
        "INSERT OR IGNORE INTO customers (user_id, name) VALUES (?, ?)",
        (user.id, user.first_name)
    )
    db.commit()

    await update.message.reply_text(
        "💎 به باشگاه مشتریان SHOP MEMORY خوش آمدی!\n\n"
        "برای مشاهده وضعیت عضویتت دستور /vip را بفرست."
    )

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = db.execute(
        "SELECT purchases, balance FROM customers WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if not row:
        await update.message.reply_text("ابتدا دستور /start را بفرست.")
        return

    purchases, balance = row
    level, discount, credit = get_level(purchases)

    await update.message.reply_text(
        f"👑 SHOP MEMORY VIP\n\n"
        f"سطح عضویت: {level}\n"
        f"تعداد خرید موفق: {purchases}\n"
        f"تخفیف خرید بعدی: {discount}%\n"
        f"اعتبار هدیه: {balance:,} تومان\n\n"
        "💎 ممنون از اعتمادت!"
    )

async def addpurchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or ADMIN_ID == 0:
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "فرمت:\n/addpurchase USER_ID AMOUNT"
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("اطلاعات واردشده معتبر نیست.")
        return

    row = db.execute(
        "SELECT purchases FROM customers WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if not row:
        await update.message.reply_text(
            "مشتری هنوز ربات را فعال نکرده است."
        )
        return

    purchases = row[0] + 1
    level, discount, credit_rate = get_level(purchases)
    credit = amount * credit_rate // 100

    db.execute(
        "UPDATE customers SET purchases = ?, balance = balance + ? WHERE user_id = ?",
        (purchases, credit, user_id)
    )
    db.commit()

    await update.message.reply_text(
        f"✅ خرید ثبت شد!\n"
        f"سطح مشتری: {level}\n"
        f"اعتبار اضافه‌شده: {credit:,} تومان"
    )

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("addpurchase", addpurchase))
    app.run_polling()

if __name__ == "__main__":
    main()
  

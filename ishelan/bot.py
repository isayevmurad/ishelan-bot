"""
İş Bildiriş Telegram Botu
Qurulum: pip install python-telegram-bot requests beautifulsoup4 schedule
İşə salmaq: python bot.py
"""
 
import json
import os
import schedule
import time
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import asyncio
from scraper import scrape_all, load_existing_jobs
 
# ─── AYARLAR ────────────────────────────────────────────────────────────────
BOT_TOKEN = "8834745814:AAHx_aAHa4bj0pduqIHjVvPdhDTUHY7me4w"   # @BotFather-dan alırsan
USERS_FILE = "users.json"
ADMIN_ID = 0  # Öz Telegram ID-ni yaz (isteğe bağlı)
 
# ─── KATEQORİYALAR ──────────────────────────────────────────────────────────
CATEGORIES = {
    "it": "💻 İT / Proqramlaşdırma",
    "maliyye": "💰 Maliyyə / Mühasibat",
    "marketinq": "📣 Marketinq / Satış",
    "muhendis": "⚙️ Mühəndislik",
    "tibb": "🏥 Tibb",
    "tehsil": "🎓 Təhsil",
    "insan": "👥 İnsan Resursları",
    "diger": "🔹 Digər",
}
 
# ─── İSTİFADƏÇİ VERİLƏNLƏRİ ────────────────────────────────────────────────
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
 
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
 
def get_user(user_id):
    users = load_users()
    return users.get(str(user_id))
 
def update_user(user_id, data):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"plan": "free", "categories": [], "keywords": []}
    users[uid].update(data)
    save_users(users)
 
# ─── MATCHING ───────────────────────────────────────────────────────────────
def job_matches_user(job, user):
    """İş elanı istifadəçiyə uyğundurmu?"""
    keywords = [k.lower() for k in user.get("keywords", [])]
    categories = user.get("categories", [])
    title = job["title"].lower()
 
    # Keyword uyğunluğu
    if keywords:
        if any(kw in title for kw in keywords):
            return True
 
    # Kateqoriya uyğunluğu (sadə keyword mapping)
    cat_keywords = {
        "it": ["proqram", "developer", "software", "it ", "web", "python", "java", "data"],
        "maliyye": ["mühasib", "maliyy", "finans", "accountant", "economist"],
        "marketinq": ["market", "satış", "sales", "smm", "reklam"],
        "muhendis": ["mühəndis", "engineer", "texnik", "texnolo"],
        "tibb": ["həkim", "tibb", "nurse", "doctor", "aptek"],
        "tehsil": ["müəllim", "teacher", "təhsil", "tədris"],
        "insan": ["hr ", "insan resursu", "recruitment", "işə qəbul"],
    }
 
    for cat in categories:
        if cat in cat_keywords:
            if any(kw in title for kw in cat_keywords[cat]):
                return True
 
    # Kateqoriya seçilməyibsə, hamısını göndər
    if not categories and not keywords:
        return True
 
    return False
 
 
# ─── KOMANDALAR ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    update_user(user_id, {"name": name})
 
    text = (
        f"Salam, {name}! 👋\n\n"
        "Bu bot sənə uyğun iş elanlarını *dərhal* xəbər verir.\n\n"
        "📋 *Komandalar:*\n"
        "/kateqoriya — İzləmək istədiyin sahəni seç\n"
        "/keyword — Açar söz əlavə et (məs: mühasib, manager)\n"
        "/status — Ayarlarına bax\n"
        "/test — İndi elanları yoxla\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
 
 
async def kateqoriya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id) or {}
    selected = user.get("categories", [])
 
    keyboard = []
    for key, label in CATEGORIES.items():
        check = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(check + label, callback_data=f"cat_{key}")])
    keyboard.append([InlineKeyboardButton("💾 Saxla", callback_data="cat_save")])
 
    await update.message.reply_text(
        "Hansı sahələri izləmək istəyirsən?\n(Bir neçəsini seçə bilərsən)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
 
 
async def cat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
 
    if data == "cat_save":
        user = get_user(user_id) or {}
        cats = user.get("categories", [])
        labels = [CATEGORIES[c] for c in cats if c in CATEGORIES]
        await query.edit_message_text(
            f"✅ Saxlandı!\nSeçilən sahələr: {', '.join(labels) if labels else 'Hamısı'}"
        )
        return
 
    cat_key = data.replace("cat_", "")
    user = get_user(user_id) or {}
    cats = user.get("categories", [])
 
    if cat_key in cats:
        cats.remove(cat_key)
    else:
        cats.append(cat_key)
 
    update_user(user_id, {"categories": cats})
 
    # Düymələri yenilə
    keyboard = []
    for key, label in CATEGORIES.items():
        check = "✅ " if key in cats else ""
        keyboard.append([InlineKeyboardButton(check + label, callback_data=f"cat_{key}")])
    keyboard.append([InlineKeyboardButton("💾 Saxla", callback_data="cat_save")])
 
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
 
 
async def keyword_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.effective_user.id
 
    if not args:
        user = get_user(user_id) or {}
        kws = user.get("keywords", [])
        await update.message.reply_text(
            f"Hazırkı açar sözlər: {', '.join(kws) if kws else 'Yoxdur'}\n\n"
            "Əlavə etmək üçün: /keyword mühasib\n"
            "Silmək üçün: /keyword_sil mühasib"
        )
        return
 
    word = " ".join(args).lower().strip()
    user = get_user(user_id) or {}
    kws = user.get("keywords", [])
    if word not in kws:
        kws.append(word)
        update_user(user_id, {"keywords": kws})
        await update.message.reply_text(f"✅ '{word}' əlavə edildi!")
    else:
        await update.message.reply_text(f"ℹ️ '{word}' artıq var.")
 
 
async def keyword_sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = update.effective_user.id
    if not args:
        await update.message.reply_text("Silmək üçün: /keyword_sil mühasib")
        return
    word = " ".join(args).lower().strip()
    user = get_user(user_id) or {}
    kws = user.get("keywords", [])
    if word in kws:
        kws.remove(word)
        update_user(user_id, {"keywords": kws})
        await update.message.reply_text(f"🗑️ '{word}' silindi.")
    else:
        await update.message.reply_text(f"'{word}' tapılmadı.")
 
 
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id) or {}
    cats = [CATEGORIES.get(c, c) for c in user.get("categories", [])]
    kws = user.get("keywords", [])
    plan = user.get("plan", "free")
 
    text = (
        f"📊 *Ayarların:*\n\n"
        f"Plan: {'⭐ Premium' if plan == 'premium' else '🆓 Pulsuz'}\n"
        f"Sahələr: {', '.join(cats) if cats else 'Hamısı'}\n"
        f"Açar sözlər: {', '.join(kws) if kws else 'Yoxdur'}\n\n"
        f"_Pulsuz: Gündə 1 bildiriş_\n"
        f"_Premium (4 AZN/ay): Anlıq bildiriş_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
 
 
async def test_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Elanlar yoxlanılır... (20 san gözlə)")
 
    # Mövcud elanları göstər
    all_jobs = load_existing_jobs()
 
    if not all_jobs:
        # Yoxdursa yeni scrape et
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, scrape_all)
        all_jobs = load_existing_jobs()
 
    if not all_jobs:
        await update.message.reply_text("Elan tapılmadı.")
        return
 
    await update.message.reply_text(f"✅ {len(all_jobs)} elan tapıldı. Son 5-i:")
 
    for job in all_jobs[:5]:
        msg = (
            f"💼 *{job['title']}*\n"
            f"🏢 {job['company']}\n"
            f"💰 {job['salary']}\n"
            f"🔗 [Bax]({job['url']})"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
 
 
# ─── OTOMATİK BİLDİRİŞ SİSTEMİ ─────────────────────────────────────────────
async def send_notifications(app):
    """Yeni elanları tapıb uyğun istifadəçilərə göndərir"""
    new_jobs = scrape_all()
    if not new_jobs:
        return
 
    users = load_users()
    for user_id, user in users.items():
        matched = [j for j in new_jobs if job_matches_user(j, user)]
        if not matched:
            continue
 
        plan = user.get("plan", "free")
 
        # Premium: dərhal göndər
        if plan == "premium":
            for job in matched[:3]:
                msg = (
                    f"🔔 *Yeni iş elanı!*\n\n"
                    f"💼 *{job['title']}*\n"
                    f"🏢 {job['company']}\n"
                    f"💰 {job['salary']}\n"
                    f"🔗 [Bax]({job['url']})"
                )
                try:
                    await app.bot.send_message(
                        chat_id=int(user_id),
                        text=msg,
                        parse_mode="Markdown",
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    print(f"Göndərmə xətası ({user_id}): {e}")
 
 
def run_scheduler(app):
    """30 dəqiqədə bir scrape edir"""
    def job():
        import asyncio
        asyncio.run(send_notifications(app))
 
    schedule.every(30).minutes.do(job)
 
    while True:
        schedule.run_pending()
        time.sleep(60)
 
 
# ─── ANA FUNKSIYA ────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()
 
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kateqoriya", kateqoriya))
    app.add_handler(CommandHandler("keyword", keyword_cmd))
    app.add_handler(CommandHandler("keyword_sil", keyword_sil))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("test", test_cmd))
    app.add_handler(CallbackQueryHandler(cat_callback, pattern="^cat_"))
 
    # Scheduler ayrı thread-də işləsin
    scheduler_thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    scheduler_thread.start()
 
    print("🤖 Bot işləyir...")
 
    # Render-də WEBHOOK_URL varsa webhook, yoxdursa polling
    webhook_url = os.environ.get("WEBHOOK_URL")
    port = int(os.environ.get("PORT", 8443))
 
    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
        )
    else:
        app.run_polling(drop_pending_updates=True)
 
 
if __name__ == "__main__":
    main()

import logging
import requests
import datetime
import pytz
import schedule
import time
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Remplace ces deux clés par les tiennes
BOT_TOKEN = '8221475744:AAGTUEjkLl6QVMAzbA8cppIGAJilUP5_4X4'
API_KEY = 'd11cb4cd983342b58f3cc08efc7e31f5'

# Ton ID pour recevoir les notifications chaque jour à 10h
ADMIN_CHAT_ID = 5774934825

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Fonctions d’analyse ===
def analyse_match(match):
    home = match['homeTeam']['name']
    away = match['awayTeam']['name']
    status = match['status']
    date = match['utcDate'][:10]

    stats = []

    if status != "FINISHED":
        return f"🕒 Match prévu : {home} vs {away} le {date}\n"

    score = match['score']
    full_home = score['fullTime']['home']
    full_away = score['fullTime']['away']

    stats.append(f"🏟️ {home} {full_home} - {full_away} {away}")
    stats.append("📊 Statistiques :")

    total_buts = full_home + full_away
    stats.append(f"➕ Total buts : {total_buts}")

    if full_home > 0 and full_away > 0:
        stats.append("✅ Les deux équipes ont marqué")
    else:
        stats.append("❌ Une seule équipe a marqué")

    # Supposons qu’on récupère les cartons (fake ici)
    stats.append(f"🟨 Cartons jaunes : {match.get('yellowCards', 'non disponible')}")
    stats.append(f"🟥 Cartons rouges : {match.get('redCards', 'non disponible')}")

    return "\n".join(stats)

# === Récupération des matchs du jour ===
def get_today_matches():
    today = datetime.datetime.utcnow().date().isoformat()
    url = f"https://api.football-data.org/v4/matches?dateFrom={today}&dateTo={today}"
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return ["⚠️ Erreur lors de la récupération des matchs."]

    data = response.json()
    matches = data.get('matches', [])
    if not matches:
        return ["Aucun match aujourd'hui."]

    return [analyse_match(match) for match in matches]

# === Commande /analyse ===
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Analyse en cours...")
    messages = get_today_matches()
    for msg in messages:
        await update.message.reply_text(msg)

# === Notification quotidienne à 10h (GMT+1) ===
async def daily_notification(app):
    messages = get_today_matches()
    text = "\n\n".join(messages)
    await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📅 Analyse automatique des matchs du jour :\n\n{text}")

# === Planification ===
def schedule_daily(app):
    def job():
        asyncio.run(daily_notification(app))

    schedule.every().day.at("09:00").do(job)  # 10h GMT+1 = 09h UTC

    while True:
        schedule.run_pending()
        time.sleep(60)

# === Lancement du bot ===
async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("analyse", analyse))

    # Tâche parallèle pour les notifications journalières
    loop = asyncio.get_event_loop()
    loop.create_task(asyncio.to_thread(schedule_daily, app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(start_bot())

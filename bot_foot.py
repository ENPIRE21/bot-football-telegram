import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from datetime import datetime
import asyncio
import pytz

TOKEN = "8221475744:AAGTUEjkLl6QVMAzbA8cppIGAJilUP5_4X4"
API_KEY = "d11cb4cd983342b58f3cc08efc7e31f5"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fonction pour obtenir les matchs du jour
def get_today_matches():
    url = f"https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "Erreur lors de la récupération des matchs."
    
    data = response.json()
    matches = data.get("matches", [])
    if not matches:
        return "Aucun match prévu aujourd'hui."
    
    result = "📅 *Matchs du jour avec statistiques :*\n"
    for match in matches:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score = match["score"]
        status = match["status"]
        full_score = f'{score["fullTime"]["home"]} - {score["fullTime"]["away"]}' if score["fullTime"]["home"] is not None else "à venir"
        both_teams_score = "✅ Oui" if all(score["fullTime"].values()) else "❌ Non"
        
        yellow_cards = red_cards = "N/A"
        stats = match.get("bookings") or []
        yellow_cards = sum(1 for x in stats if x.get("card") == "YELLOW")
        red_cards = sum(1 for x in stats if x.get("card") == "RED")

        result += f"\n🏟️ {home} vs {away}\n"
        result += f"⏱️ Statut : {status}\n"
        result += f"🔢 Score : {full_score}\n"
        result += f"⚽ Les deux équipes ont marqué ? {both_teams_score}\n"
        result += f"🟨 Cartons jaunes : {yellow_cards} | 🟥 Cartons rouges : {red_cards}\n"
        result += "────────────────────────\n"
    
    return result

# Commande manuelle
async def match_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    result = get_today_matches()
    await context.bot.send_message(chat_id=chat_id, text=result, parse_mode="Markdown")

# Notification automatique à 10h
async def daily_job(app):
    while True:
        now = datetime.now(pytz.timezone('Africa/Abidjan'))
        if now.hour == 10 and now.minute == 0:
            result = get_today_matches()
            for user_id in USERS:
                try:
                    await app.bot.send_message(chat_id=user_id, text="🕙 *Analyse automatique des matchs du jour :*\n\n" + result, parse_mode="Markdown")
                except Exception as e:
                    logger.warning(f"Erreur en envoyant à {user_id}: {e}")
            await asyncio.sleep(60)  # pour ne pas envoyer 60 fois
        await asyncio.sleep(30)

# Stockage utilisateurs (temporaire ici, à améliorer avec BDD si besoin)
USERS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS.add(user_id)
    await update.message.reply_text("👋 Bienvenue ! Tu recevras les analyses automatiques chaque jour à 10h. Tape /matchs pour voir les matchs d'aujourd'hui.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("matchs", match_handler))
    asyncio.create_task(daily_job(app))
    app.run_polling()

if __name__ == '__main__':
    main()

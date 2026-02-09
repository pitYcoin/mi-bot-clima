import os
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- 1. CONFIGURACIÓN DEL SERVIDOR WEB (Para que Render no se apague) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "El Bot de Potrerillos está funcionando 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. LÓGICA DEL CLIMA ---
def obtener_clima():
    # Reemplaza 'TU_API_KEY_AQUI' por tu llave de WeatherAPI
    API_KEY = "TU_API_KEY_DE_WEATHER"
    URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q=-32.95,-69.18&lang=es"
    try:
        r = requests.get(URL).json()
        temp = r['current']['temp_c']
        viento = r['current']['wind_kph']
        condicion = r['current']['condition']['text']
        return f"🏔️ Potrerillos: {temp}°C, {condicion}. Viento: {viento} km/h."
    except:
        return "❌ No pude obtener el clima ahora mismo."

# --- 3. COMANDOS DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu monitor de Potrerillos. Usa /clima para ver el estado actual.")

async def clima_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_clima = obtener_clima()
    await update.message.reply_text(texto_clima)

# --- 4. ARRANQUE ---
if __name__ == '__main__':
    # Arrancar servidor web
    threading.Thread(target=run_flask).start()
    
    # Arrancar Telegram (Reemplaza 'TU_TOKEN_TELEGRAM' por el tuyo)
    TOKEN = "TOKEN_TELEGRAM"
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clima", clima_comando))
    
    print("Bot activo...")

    application.run_polling()


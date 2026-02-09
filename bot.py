import logging
import os
import requests
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM") 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT, LON = -32.95, -69.18  # Potrerillos, Mendoza

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE FLASK ---
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot de Emergencias Potrerillos: ACTIVO 24/7", 200

def run_flask():
    # Render asigna un puerto dinámico, lo tomamos de la variable de entorno
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- FUNCIONES DE DATOS ---
def obtener_clima():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    try:
        response = requests.get(url).json()
        if response.get("cod") != 200:
            return None
        temp = response['main']['temp']
        viento_vel = response['wind']['speed'] * 3.6
        desc = response['weather'][0]['description']
        rafagas = response['wind'].get('gust', response['wind']['speed']) * 3.6
        return {"temp": temp, "viento": viento_vel, "rafagas": rafagas, "desc": desc}
    except Exception as e:
        logger.error(f"Error clima: {e}")
        return None

# --- MANEJADOR DE ERRORES (Soluciona tu error de 'No error handlers') ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Excepción al procesar update:", exc_info=context.error)

# --- COMANDOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🏔️ Estado Actual'], ['🚨 Emergencias', '📝 Consejos Zonda']]
    reply_markup = ReplyKeyboardMarkup(botones, resize_keyboard=True)
    mensaje = (f"Hola {update.effective_user.first_name}. Monitor Potrerillos activo.")
    await update.message.reply_text(mensaje, reply_markup=reply_markup)

async def reporte_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_clima()
    if not datos:
        await update.message.reply_text("❌ Error al conectar con sensores.")
        return
    alerta = "SÍ - VIENTO FUERTE" if datos['rafagas'] > 50 else "NO"
    reporte = (f"🌡️ **Temp:** {datos['temp']}°C\n🌬️ **Viento:** {datos['viento']:.1f} km/h\n💨 **Ráfagas:** {datos['rafagas']:.1f} km/h\n⚠️ **Alerta:** {alerta}")
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def emergencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 **EMERGENCIAS: 911**\nDefensa Civil: 103", parse_mode='Markdown')

async def consejos_zonda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **ZONDA:** Cerrar aberturas, evitar fuego.", parse_mode='Markdown')

# --- FUNCIÓN PRINCIPAL ASÍNCRONA ---
async def main():
    if not TOKEN_TELEGRAM:
        logger.error("FALTA TOKEN_TELEGRAM")
        return

    # Construir la aplicación
    application = Application.builder().token(TOKEN_TELEGRAM).build()

    # Agregar manejadores
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text('🏔️ Estado Actual'), reporte_clima))
    application.add_handler(MessageHandler(filters.Text('🚨 Emergencias'), emergencias))
    application.add_handler(MessageHandler(filters.Text('📝 Consejos Zonda'), consejos_zonda))

    # --- EL TRUCO PARA RENDER ---
    await application.initialize()
    # Limpiamos cualquier webhook viejo antes de arrancar
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.start()
    
    logger.info("Bot en marcha...")
    
    # Iniciamos polling
    await application.updater.start_polling()
    
    # Mantener vivo el loop
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        await application.stop()

if __name__ == '__main__':
    # 1. Iniciar Flask en segundo plano
    Thread(target=run_flask, daemon=True).start()
    
    # 2. Iniciar el Bot de Telegram
    try:
        asyncio.run(main())
    except Exception as e:
        logger.fatal(f"El bot se detuvo: {e}")



import logging
import os
import requests
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 1. CONFIGURACIÓN (Variables de entorno)
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM") 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
LAT, LON = -32.95, -69.18  # Potrerillos, Mendoza

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. SERVIDOR WEB (Para que Render no dé error)
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot de Emergencias Potrerillos: ACTIVO 24/7", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# 3. FUNCIONES DE LÓGICA (Tu trabajo anterior)
def obtener_clima():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    try:
        response = requests.get(url).json()
        if response.get("cod") != 200: return None
        return {
            "temp": response['main']['temp'],
            "viento": response['wind']['speed'] * 3.6,
            "rafagas": response['wind'].get('gust', response['wind']['speed']) * 3.6,
            "desc": response['weather'][0]['description']
        }
    except Exception as e:
        logger.error(f"Error clima: {e}")
        return None

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Excepción al procesar update:", exc_info=context.error)

# 4. COMANDOS (Lo que el bot responde)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [['🏔️ Estado Actual'], ['🚨 Emergencias', '📝 Consejos Zonda']]
    await update.message.reply_text("Monitor Potrerillos activo.", reply_markup=ReplyKeyboardMarkup(botones, resize_keyboard=True))

async def reporte_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = obtener_clima()
    if not datos:
        await update.message.reply_text("❌ Error en sensores.")
        return
    alerta = "SÍ - VIENTO FUERTE" if datos['rafagas'] > 50 else "NO"
    reporte = f"🌡️ **Temp:** {datos['temp']}°C\n🌬️ **Viento:** {datos['viento']:.1f} km/h\n⚠️ **Alerta:** {alerta}"
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def emergencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚨 **EMERGENCIAS: 911**", parse_mode='Markdown')

async def consejos_zonda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **ZONDA:** Cerrar aberturas.", parse_mode='Markdown')

# 5. EL NUEVO MAIN (LO QUE CAMBIAMOS PARA ARREGLAR EL ERROR)
async def main():
    if not TOKEN_TELEGRAM:
        logger.error("FALTA TOKEN_TELEGRAM")
        return

    application = Application.builder().token(TOKEN_TELEGRAM).build()

    # Añadimos los manejadores
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text('🏔️ Estado Actual'), reporte_clima))
    application.add_handler(MessageHandler(filters.Text('🚨 Emergencias'), emergencias))
    application.add_handler(MessageHandler(filters.Text('📝 Consejos Zonda'), consejos_zonda))

    # LIMPIEZA INICIAL
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True) # <-- ESTO ARREGLA EL CONFLICTO
    await application.start()
    
    logger.info("¡Iniciando Polling con éxito!")
    
    # Iniciamos el updater
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Mantener el loop vivo
    while True:
        await asyncio.sleep(10)

# ... (aquí arriba están tus funciones de clima, consejos y el main anterior) ...

if __name__ == '__main__':
    # 1. Iniciamos el servidor web para que Render no nos corte
    port = int(os.environ.get("PORT", 10000))
    # Usamos un hilo (Thread) para que Flask corra sin detener al bot
    Thread(target=lambda: flask_app.run(host='0.0.0.0', port=port), daemon=True).start()
    
    # 2. PRÁCTICA TITÁNICA: El bucle infinito de vida
    while True:
        try:
            logger.info("Intentando conectar con Telegram...")
            asyncio.run(main())  # Esto lanza tu función principal del bot
        except Exception as e:
            # Si el bot cae por red o por GitHub, espera y revive solo
            logger.error(f"⚠️ El sistema cayó por: {e}. Reintentando en 15 segundos...")
            import time
            time.sleep(15)


import logging
import os
import requests
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURACIÓN ---
# ⚠️ IMPORTANTE: Las claves ahora se cargan desde variables de entorno para mayor seguridad
# Asegúrate de que estas variables de entorno estén configuradas en Render
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM") 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") # Clave para OpenWeatherMap
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # URL pública de tu servidor (ej: https://tu-app.onrender.com)

LAT, LON = -32.95, -69.18  # Coordenadas exactas Potrerillos, Mendoza

# Configuración de logs para monitoreo (te avisará en la consola si algo falla)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURACIÓN DE FLASK (SERVIDOR WEB) ---
flask_app = Flask(__name__)

@flask_app.route('/') # Esta ruta es para que Render sepa que el servicio está vivo
def index():
    return "Bot de Emergencias Potrerillos: ACTIVO 24/7"
 
@flask_app.route(f'/{TOKEN_TELEGRAM}', methods=['POST'])
async def telegram_webhook():
    """Esta ruta recibe las actualizaciones de Telegram y las procesa."""
    update_data = request.get_json(force=True)
    await app.process_update(Update.de_json(update_data, app.bot))
    return "ok", 200

# --- FUNCIONES DE DATOS ---

def obtener_clima():
    """Consulta la API de OpenWeather para datos de montaña."""
    # Construimos la URL de consulta
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    
    try:
        response = requests.get(url).json()
        
        # Verificamos si la API respondió correctamente (código 200)
        if response.get("cod") != 200:
            logging.error(f"Error API: {response.get('message')}")
            return None

        temp = response['main']['temp']
        viento_vel = response['wind']['speed'] * 3.6  # Convertir m/s a km/h
        desc = response['weather'][0]['description']
        
        # La API gratuita a veces no trae ráfagas (gusts), usamos speed como base si no hay ráfagas
        rafagas = response['wind'].get('gust', response['wind']['speed']) * 3.6
        
        return {"temp": temp, "viento": viento_vel, "rafagas": rafagas, "desc": desc}
    except Exception as e:
        logging.error(f"Error crítico obteniendo clima: {e}")
        return None

# --- MANEJADOR DE ERRORES ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra el error para que no se caiga el bot y sepamos qué pasó."""
    logging.error("Ocurrió una excepción al procesar una actualización:", exc_info=context.error)

# --- COMANDOS DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bienvenida con botones de acceso rápido."""
    user = update.effective_user
    # Teclado simplificado con 3 funciones principales
    botones = [['🏔️ Estado Actual'], ['🚨 Emergencias', '📝 Consejos Zonda']]
    reply_markup = ReplyKeyboardMarkup(botones, resize_keyboard=True)
    
    mensaje_bienvenida = (
        f"Hola {user.first_name}. Soy el **Monitor de Emergencias Potrerillos**.\n\n"
        "Mi misión es brindarte información crítica sobre el clima en El Salto, "
        "Las Carditas, Valle del Sol y el Dique.\n"
        "Utiliza los botones inferiores para obtener reportes en tiempo real."
    )
    await update.message.reply_text(mensaje_bienvenida, reply_markup=reply_markup, parse_mode='Markdown')

async def reporte_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enviá el reporte estructurado según tu protocolo."""
    datos = obtener_clima()
    if not datos:
        await update.message.reply_text("❌ Error al conectar con los sensores meteorológicos (Verifica tu API Key).")
        return

    # Lógica de Alerta basada en el viento (Protocolo Zonda)
    alerta = "NO"
    if datos['rafagas'] > 50: # Corregido el símbolo >
        alerta = "SÍ - VIENTO FUERTE / POSIBLE ZONDA"
    
    reporte = (
        "📊 **REPORTE DE ESTADO - POTRERILLOS**\n"
        "------------------------------------\n"
        f"🌡️ **Temperatura:** {datos['temp']}°C\n"
        f"🌬️ **Viento:** {datos['viento']:.1f} km/h\n"
        f"💨 **Ráfagas:** {datos['rafagas']:.1f} km/h\n"
        f"☁️ **Condición:** {datos['desc'].capitalize()}\n\n"
        f"⚠️ **Alerta Activa:** {alerta}\n"
        "------------------------------------\n"
        "📍 **Zonas Monitoreadas:** El Salto, Valle del Sol, Las Carditas.\n\n"
        "✅ **Acción:** Asegurar objetos sueltos y evitar fuego."
    )
    await update.message.reply_text(reporte, parse_mode='Markdown')

async def emergencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contactos de emergencia."""
    msg = (
        "🚨 **CONTACTOS DE EMERGENCIA**\n\n"
        "📞 **Emergencias:** 911\n"
        "📞 **Defensa Civil Mendoza:** 103\n"
        "📞 **Centro de Salud Potrerillos:** 02624 48-2003\n\n"
        "⚠️ *Si hay crecida de arroyos, no intentes cruzar badenes.*"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def consejos_zonda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📝 **CONSEJOS ANTE VIENTO ZONDA**\n"
        "1. Hidratarse permanentemente.\n"
        "2. Cerrar y asegurar puertas y ventanas.\n"
        "3. **PROHIBIDO** encender fuego al aire libre.\n"
        "4. Evitar transitar bajo árboles o cables eléctricos."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- MANEJADOR DE MENSAJES DE TEXTO (BOTONES) ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == '🏔️ Estado Actual':
        await reporte_clima(update, context)
    elif text == '🚨 Emergencias':
        await emergencias(update, context)
    elif text == '📝 Consejos Zonda':
        await consejos_zonda(update, context)

# --- INICIO DEL PROGRAMA ---

if __name__ == '__main__':
    # 1. Verificación de seguridad antes de arrancar
    if not all([TOKEN_TELEGRAM, OPENWEATHER_API_KEY, WEBHOOK_URL]):
        logging.critical("❌ ERROR CRÍTICO: Asegúrate de que las variables de entorno TOKEN_TELEGRAM, OPENWEATHER_API_KEY y WEBHOOK_URL están configuradas.")
        exit(1)

    # 2. Crear la aplicación del bot
    app = Application.builder().token(TOKEN_TELEGRAM).build()

    # 3. Registrar el manejador de errores (¡MUY IMPORTANTE!)
    app.add_error_handler(error_handler)

    # 4. Añadir comandos y manejadores de mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clima", reporte_clima))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 5. Configurar el webhook de forma asíncrona
    async def setup():
        print(f"Configurando webhook en la URL: {WEBHOOK_URL}/{TOKEN_TELEGRAM}")
        await app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN_TELEGRAM}")

    # Ejecutamos la configuración del webhook
    asyncio.run(setup())

    # 6. Iniciar el servidor Flask
    # Render asigna un puerto automáticamente en la variable de entorno 'PORT'
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"🏔️ Servidor Flask iniciado en el puerto {port}. El bot está escuchando vía webhook.")
    flask_app.run(host='0.0.0.0', port=port)
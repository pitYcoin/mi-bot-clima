import os
import requests
import threading
import logging
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. CONFIGURACIÓN INICIAL ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
app = Flask(__name__)

# Configuración del servidor para Render
@app.route('/')
def home():
    return "Sentinel Potrerillos: SISTEMA ACTIVO"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. LÓGICA DE INTELIGENCIA METEOROLÓGICA ---
def obtener_analisis_montaña():
    API_KEY = os.environ.get("API_KEY_WEATHER")
    # Coordenadas exactas: Potrerillos, Mendoza
    URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q=-32.95,-69.18&lang=es"
    
    try:
        r = requests.get(URL).json()
        temp = r['current']['temp_c']
        viento = r['current']['wind_kph']
        rafagas = r['current']['gust_kph']
        humedad = r['current']['humidity']
        presion = r['current']['pressure_mb']
        condicion = r['current']['condition']['text']

        # Protocolo de Seguridad (Nivel Especialista)
        estado = "🟢 NORMAL"
        consejo = "Condiciones estables. Mantenga siempre agua y abrigo en el vehículo."
        color_emoji = "🏔️"

        # Detección de Viento Zonda (Baja humedad + ráfagas altas)
        if rafagas > 55 and humedad < 25:
            estado = "🔴 ALERTA SEVERA: VIENTO ZONDA"
            consejo = "PROHIBIDO ENCENDER FUEGO. Asegure techos. Peligro de caída de árboles y cables."
            color_emoji = "🔥"
        # Detección de Tormentas de Verano (Crecida de arroyos)
        elif "lluvia" in condicion.lower() or "tormenta" in condicion.lower():
            estado = "🟠 ALERTA: CRECIDA DE ARROYOS"
            consejo = "No cruce badenes en El Salto o Valle del Sol. Rayos detectados en la zona."
            color_emoji = "⛈️"
        # Viento fuerte de montaña
        elif rafagas > 40:
            estado = "🟡 PRECAUCIÓN: RÁFAGAS"
            consejo = "Viento fuerte en la zona del Dique. Reduzca la velocidad al conducir."
            color_emoji = "💨"

        reporte = (
            f"{color_emoji} **MONITOR SENTINEL POTRERILLOS**\n"
            f"----------------------------------------\n"
            f"🌡️ **Temperatura:** {temp}°C\n"
            f"☁️ **Cielo:** {condicion.capitalize()}\n"
            f"🌬️ **Viento:** {viento} km/h (Ráfagas: {rafagas} km/h)\n"
            f"💧 **Humedad:** {humedad}% | 📉 **Presión:** {presion} hPa\n\n"
            f"🚨 **ESTADO:** {estado}\n"
            f"📝 **PROTOCOLO:** {consejo}\n"
            f"----------------------------------------\n"
            f"📍 *Zonas: El Salto, Las Carditas, Valle del Sol, Dique.*"
        )
        return reporte
    except:
        return "❌ Error: Sensores fuera de línea. Consulte al 911."

# --- 3. FUNCIONES DEL BOT ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Teclado Principal (UX Optimizada)
    botones = [
        ['🏔️ ESTADO DE MONTAÑA'],
        ['🚨 EMERGENCIAS', '📝 CONSEJOS ZONDA'],
        ['☕ APOYAR PROYECTO (Propina)']
    ]
    reply_markup = ReplyKeyboardMarkup(botones, resize_keyboard=True)
    
    await update.message.reply_text(
        f"🛡️ **Sentinel Potrerillos v2.0**\n\n"
        f"Hola {update.effective_user.first_name}, soy tu sistema de Alerta Temprana.\n"
        f"Monitoreo constante de condiciones climáticas y seguridad vial.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def manejar_mensajes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text

    if msg == '🏔️ ESTADO DE MONTAÑA':
        await update.message.reply_text(obtener_analisis_montaña(), parse_mode='Markdown')

    elif msg == '🚨 EMERGENCIAS':
        emergencias = (
            "🚨 **NÚMEROS DE VIDA O MUERTE**\n\n"
            "📞 **Emergencias:** 911\n"
            "📞 **Defensa Civil:** 103\n"
            "📞 **Patrulla de Rescate:** (0261) 420-1313\n"
            "📞 **Centro de Salud Potrerillos:** 02624 48-2003\n\n"
            "📍 *Ubicación del Centro de Salud: Av. Los Cóndores s/n.*"
        )
        await update.message.reply_text(emergencias, parse_mode='Markdown')

    elif msg == '📝 CONSEJOS ZONDA':
        consejos = (
            "🌬️ **MANUAL DE SUPERVIVENCIA ZONDA**\n"
            "1. **FUEGO:** Cero tolerancia. Una chispa quema todo el cerro.\n"
            "2. **HOGAR:** Cierre herméticamente. Use trapos húmedos en rendijas.\n"
            "3. **TRANSPORTE:** Si hay nubes de polvo, deténgase lejos de árboles.\n"
            "4. **SALUD:** El aire seco irrita. Use gotas oculares e hidrátese."
        )
        await update.message.reply_text(consejos, parse_mode='Markdown')

    elif msg == '☕ APOYAR PROYECTO (Propina)':
        # Configuración de Wallet (Cambia los datos por los tuyos)
        mensaje_pago = (
            "🙏 **SOPORTE DE LA COMUNIDAD**\n\n"
            "Este bot es gratuito y se mantiene con servidores en la nube. "
            "Si te ha sido de utilidad para tu seguridad o viaje, puedes invitarme un café:\n\n"
            "💎 **UQCWySkNydeU3Sa_TeyeOLtaXUB5hQHh3oJ3GUR24knJjCIu**\n"
        
             "¡Gracias por ayudar a mantener Potrerillos seguro!"
        )
        # Botón de acceso rápido a tu Wallet
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Enviar vía @Wallet", url="https://t.me/wallet")]
        ])
        await update.message.reply_text(mensaje_pago, reply_markup=keyboard, parse_mode='Markdown')

# --- 4. LANZAMIENTO MAESTRO ---
if __name__ == '__main__':
    # Lanzar servidor Keep-Alive (Flask)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Obtener Token desde Render
    TOKEN_SECRET = os.environ.get("TOKEN_TELEGRAM")
    
    if not TOKEN_SECRET:
        print("FATAL ERROR: No se detectó TOKEN_TELEGRAM en las variables de entorno.")
    else:
        # Construir Aplicación
        application = Application.builder().token(TOKEN_SECRET).build()
        
        # Handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensajes))
        
        print("✅ SENTINEL POTRERILLOS INICIADO CON ÉXITO")
        application.run_polling()

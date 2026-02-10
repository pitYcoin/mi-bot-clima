# 🏔️ Potrerillos Emergency Monitor (Telegram Bot)

A professional Telegram bot designed to provide real-time safety data and weather alerts for the community of Potrerillos, Mendoza (Argentina). This system is specialized in **Zonda Wind** detection and local emergency contact management.

## 🚀 "Titanic" Features
- **Color-Coded Alerts:** Visual wind speed classification (🟢 Calm, 🟡 Caution, 🔴 Zonda Alert).
- **Extreme Resilience:** Implemented a **Self-Healing** retry loop that allows the bot to recover automatically from network or API outages.
- **24/7 Monitoring:** Deployed on Render's cloud infrastructure with an integrated Flask server for high availability.
- **Real-Time Data:** Direct integration with OpenWeather API for precise mountain weather telemetry.

## 🛠️ Tech Stack
- **Python 3.10+**
- **python-telegram-bot:** High-level interface for the Telegram Bot API.
- **Flask:** Used for server health-checks and keeping the Render instance active.
- **Requests & Asyncio:** For asynchronous data fetching and non-blocking execution.

## 🛡️ Architecture & Fault Tolerance
The project was built with a **Fault-Tolerant** philosophy. The system proved its stability even during major global infrastructure outages (like the GitHub incident on Feb 9, 2026), thanks to its resilience logic:

```python
while True:
    try:
        asyncio.run(main())
    except Exception as e:
        # Automatic self-recovery after 15 seconds
        logger.error(f"System failure: {e}. Retrying...")
 ---
## 🌍 Languages
- **Spanish:** Native
- **English:** Professional Working Proficiency
- **Italian:** Conversational / Professional
- **Slovenian:** Conversational / Professional       time.sleep(15)

import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== ТВОИ ДАННЫЕ (ВСТАВЬ СЮДА) =====
TELEGRAM_TOKEN = "8795799316:AAHJY-dMCxnr_jIx3jYuQZRRdsnc1TRNmEg"
API_KEY = "flx_live_5juKQTWMQ5qlqGeA0eYNwmYAv8WrPRboA96GuEjw"
SERVER_ID = "3427098"
# =====================================

BASE_URL = f"https://client.falixnodes.net/api/client"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

server_start_time = None

def get_server_details():
    url = f"{BASE_URL}/servers/{SERVER_ID}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            attrs = data.get('attributes', {})
            return {
                'status': attrs.get('current_state', 'unknown'),
                'player_count': 0,
                'cpu': attrs.get('usage', {}).get('cpu', 0),
                'memory': attrs.get('usage', {}).get('memory', 0),
                'disk': attrs.get('usage', {}).get('disk', 0),
                'memory_limit': attrs.get('limits', {}).get('memory', 0),
                'disk_limit': attrs.get('limits', {}).get('disk', 0),
            }
    except:
        return None

def power_action(signal):
    url = f"{BASE_URL}/servers/{SERVER_ID}/power"
    try:
        r = requests.post(url, json={"signal": signal}, headers=HEADERS, timeout=10)
        return r.status_code in (200, 204)
    except:
        return False

def send_command(command):
    url = f"{BASE_URL}/servers/{SERVER_ID}/command"
    try:
        r = requests.post(url, json={"command": command}, headers=HEADERS, timeout=10)
        return r.status_code in (200, 204)
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 *Бот для FalixNodes*\n"
        "/status — статус\n"
        "/start_server — запуск\n"
        "/stop_server — остановка\n"
        "/restart_server — перезапуск\n"
        "/console <команда> — консоль\n"
        "/uptime — время работы"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Получаю...")
    d = get_server_details()
    if not d:
        await update.message.reply_text("❌ Ошибка")
        return
    emoji = "🟢" if d['status'] == 'running' else "🔴"
    status_text = "Работает" if d['status'] == 'running' else "Остановлен"
    uptime_text = "Неизвестно"
    if d['status'] == 'running' and server_start_time:
        delta = datetime.now() - server_start_time
        h, rem = divmod(delta.seconds, 3600)
        m, s = divmod(rem, 60)
        uptime_text = f"{delta.days}д {h}ч {m}м {s}с"
    mem = d.get('memory', 0) / (1024*1024)
    mem_limit = d.get('memory_limit', 0) / (1024*1024)
    disk = d.get('disk', 0) / (1024*1024)
    disk_limit = d.get('disk_limit', 0) / (1024*1024)
    text = (
        f"{emoji} *Статус:* {status_text}\n"
        f"👥 Игроков: {d.get('player_count', 0)}\n"
        f"⏱ Время: {uptime_text}\n"
        f"CPU: {d.get('cpu', 0)}%\n"
        f"RAM: {mem:.1f}/{mem_limit:.1f} МБ\n"
        f"Диск: {disk:.1f}/{disk_limit:.1f} МБ"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def start_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Запускаю...")
    if power_action('start'):
        global server_start_time
        server_start_time = datetime.now()
        await update.message.reply_text("✅ Запущено!")
    else:
        await update.message.reply_text("❌ Ошибка")

async def stop_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Останавливаю...")
    if power_action('stop'):
        global server_start_time
        server_start_time = None
        await update.message.reply_text("✅ Остановлено")
    else:
        await update.message.reply_text("❌ Ошибка")

async def restart_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Перезапускаю...")
    if power_action('restart'):
        global server_start_time
        server_start_time = datetime.now()
        await update.message.reply_text("✅ Перезапущено!")
    else:
        await update.message.reply_text("❌ Ошибка")

async def console(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Укажи команду, например: /console list")
        return
    cmd = ' '.join(context.args)
    await update.message.reply_text(f"🔄 Отправляю `{cmd}`", parse_mode='Markdown')
    if send_command(cmd):
        await update.message.reply_text("✅ Отправлено")
    else:
        await update.message.reply_text("❌ Ошибка (может сервер не запущен)")

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not server_start_time:
        await update.message.reply_text("⏳ Сервер не запущен")
        return
    delta = datetime.now() - server_start_time
    h, rem = divmod(delta.seconds, 3600)
    m, s = divmod(rem, 60)
    await update.message.reply_text(f"⏱ Работает: {delta.days}д {h}ч {m}м {s}с")

if __name__ == '__main__':
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("start_server", start_server))
    app.add_handler(CommandHandler("stop_server", stop_server))
    app.add_handler(CommandHandler("restart_server", restart_server))
    app.add_handler(CommandHandler("console", console))
    app.add_handler(CommandHandler("uptime", uptime))
    print("✅ Бот запущен!")
    app.run_polling()

import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ НОВЫЕ КЛЮЧИ) =====
TELEGRAM_TOKEN = "ВАШ_НОВЫЙ_ТОКЕН_ОТ_BOTFATHER"
API_KEY = "flx_live_НОВЫЙ_КЛЮЧ"          # создайте новый в панели FalixNodes
SERVER_ID = "3427098"                     # ваш ID сервера
# =====================================================

BASE_URL = f"https://client.falixnodes.net/api/client"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Храним время запуска (сбросится при перезапуске бота)
server_start_time = None

def get_server_details():
    """Получает статус, ресурсы и список игроков (заглушка)."""
    url = f"{BASE_URL}/servers/{SERVER_ID}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            attrs = data.get('attributes', {})
            state = attrs.get('current_state', 'unknown')
            limits = attrs.get('limits', {})
            usage = attrs.get('usage', {})
            # Игроки пока заглушка (через WebSocket нужно, но для простоты оставим)
            return {
                'status': state,
                'player_count': 0,   # можно будет позже добавить через парсинг логов
                'cpu': usage.get('cpu', 0),
                'memory': usage.get('memory', 0),
                'disk': usage.get('disk', 0),
                'memory_limit': limits.get('memory', 0),
                'disk_limit': limits.get('disk', 0),
            }
    except:
        pass
    return None

def power_action(signal):
    """Отправляет сигнал start/stop/restart."""
    url = f"{BASE_URL}/servers/{SERVER_ID}/power"
    try:
        r = requests.post(url, json={"signal": signal}, headers=HEADERS, timeout=10)
        return r.status_code in (200, 204)
    except:
        return False

def send_command(command):
    """Отправляет команду в консоль."""
    url = f"{BASE_URL}/servers/{SERVER_ID}/command"
    try:
        r = requests.post(url, json={"command": command}, headers=HEADERS, timeout=10)
        return r.status_code in (200, 204)
    except:
        return False

async def start(update, context):
    text = (
        "🎮 *Бот для управления сервером FalixNodes*\n\n"
        "/status — статус, ресурсы\n"
        "/players — список игроков (пока заглушка)\n"
        "/start_server — запустить сервер\n"
        "/stop_server — остановить сервер\n"
        "/restart_server — перезапустить сервер\n"
        "/console <команда> — отправить команду в консоль\n"
        "/uptime — время работы сервера"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def status(update, context):
    await update.message.reply_text("🔄 Получаю статус...")
    d = get_server_details()
    if not d:
        await update.message.reply_text("❌ Ошибка получения данных.")
        return
    status_emoji = "🟢" if d['status'] == 'running' else "🔴"
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
        f"{status_emoji} *Статус:* {status_text}\n"
        f"👥 *Игроков:* {d.get('player_count', 0)}\n"
        f"⏱ *Время работы:* {uptime_text}\n"
        f"💻 CPU: {d.get('cpu', 0)}%\n"
        f"💾 RAM: {mem:.1f} / {mem_limit:.1f} МБ\n"
        f"💽 Диск: {disk:.1f} / {disk_limit:.1f} МБ"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def players(update, context):
    await update.message.reply_text("👥 Функция в разработке (пока показывает 0).")

async def start_server(update, context):
    await update.message.reply_text("🔄 Запускаю...")
    if power_action('start'):
        global server_start_time
        server_start_time = datetime.now()
        await update.message.reply_text("✅ Сервер запускается!")
    else:
        await update.message.reply_text("❌ Ошибка запуска.")

async def stop_server(update, context):
    await update.message.reply_text("🔄 Останавливаю...")
    if power_action('stop'):
        global server_start_time
        server_start_time = None
        await update.message.reply_text("✅ Сервер остановлен.")
    else:
        await update.message.reply_text("❌ Ошибка остановки.")

async def restart_server(update, context):
    await update.message.reply_text("🔄 Перезапускаю...")
    if power_action('restart'):
        global server_start_time
        server_start_time = datetime.now()
        await update.message.reply_text("✅ Сервер перезапускается!")
    else:
        await update.message.reply_text("❌ Ошибка перезапуска.")

async def console(update, context):
    if not context.args:
        await update.message.reply_text("❌ Укажите команду. Пример: `/console list`", parse_mode='Markdown')
        return
    cmd = ' '.join(context.args)
    await update.message.reply_text(f"🔄 Отправляю `{cmd}`", parse_mode='Markdown')
    if send_command(cmd):
        await update.message.reply_text("✅ Команда отправлена.")
    else:
        await update.message.reply_text("❌ Ошибка отправки (возможно сервер не запущен).")

async def uptime(update, context):
    if not server_start_time:
        await update.message.reply_text("⏳ Сервер не запущен или время сброшено.")
        return
    delta = datetime.now() - server_start_time
    h, rem = divmod(delta.seconds, 3600)
    m, s = divmod(rem, 60)
    await update.message.reply_text(f"⏱ Сервер работает: {delta.days}д {h}ч {m}м {s}с")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("players", players))
    app.add_handler(CommandHandler("start_server", start_server))
    app.add_handler(CommandHandler("stop_server", stop_server))
    app.add_handler(CommandHandler("restart_server", restart_server))
    app.add_handler(CommandHandler("console", console))
    app.add_handler(CommandHandler("uptime", uptime))
    print("✅ Бот запущен!")
    app.run_polling()

import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# ===== ТОЛЬКО ТОКЕН ВСТАВЬ =====
TELEGRAM_TOKEN = "ТВОЙ_НОВЫЙ_ТОКЕН"
# ================================

API_KEY = "8795799316:AAHJY-dMCxnr_jIx3jYuQZRRdsnc1TRNmEg"
SERVER_ID = "3427098"

BASE_URL = f"https://client.falixnodes.net/api/client"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

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

def start(update: Update, context: CallbackContext):
    text = "Бот для FalixNodes\n/status - статус\n/start_server - запуск\n/stop_server - остановка\n/restart_server - перезапуск\n/console <команда> - консоль\n/uptime - время работы"
    update.message.reply_text(text)

def status(update: Update, context: CallbackContext):
    update.message.reply_text("Получаю статус...")
    d = get_server_details()
    if not d:
        update.message.reply_text("Ошибка получения данных")
        return
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
        f"Статус: {status_text}\n"
        f"CPU: {d.get('cpu',0)}%\n"
        f"RAM: {mem:.1f}/{mem_limit:.1f} МБ\n"
        f"Диск: {disk:.1f}/{disk_limit:.1f} МБ\n"
        f"Время работы: {uptime_text}"
    )
    update.message.reply_text(text)

def start_server(update: Update, context: CallbackContext):
    update.message.reply_text("Запускаю сервер...")
    if power_action('start'):
        global server_start_time
        server_start_time = datetime.now()
        update.message.reply_text("Сервер запущен")
    else:
        update.message.reply_text("Ошибка запуска")

def stop_server(update: Update, context: CallbackContext):
    update.message.reply_text("Останавливаю сервер...")
    if power_action('stop'):
        global server_start_time
        server_start_time = None
        update.message.reply_text("Сервер остановлен")
    else:
        update.message.reply_text("Ошибка остановки")

def restart_server(update: Update, context: CallbackContext):
    update.message.reply_text("Перезапускаю сервер...")
    if power_action('restart'):
        global server_start_time
        server_start_time = datetime.now()
        update.message.reply_text("Сервер перезапущен")
    else:
        update.message.reply_text("Ошибка перезапуска")

def console(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Пример: /console list")
        return
    cmd = ' '.join(context.args)
    update.message.reply_text(f"Отправляю команду: {cmd}")
    if send_command(cmd):
        update.message.reply_text("Команда отправлена")
    else:
        update.message.reply_text("Ошибка отправки (возможно сервер не запущен)")

def uptime(update: Update, context: CallbackContext):
    if not server_start_time:
        update.message.reply_text("Сервер не запущен")
        return
    delta = datetime.now() - server_start_time
    h, rem = divmod(delta.seconds, 3600)
    m, s = divmod(rem, 60)
    update.message.reply_text(f"Сервер работает: {delta.days}д {h}ч {m}м {s}с")

if __name__ == '__main__':
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("start_server", start_server))
    dp.add_handler(CommandHandler("stop_server", stop_server))
    dp.add_handler(CommandHandler("restart_server", restart_server))
    dp.add_handler(CommandHandler("console", console))
    dp.add_handler(CommandHandler("uptime", uptime))
    print("Бот запущен")
    updater.start_polling()
    updater.idle()

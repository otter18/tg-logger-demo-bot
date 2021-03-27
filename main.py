#  Copyright (c) ChernV (@otter18), 2021.

import datetime
import logging
import os
import time

import pytz
import telebot
import tg_logger
from flask import Flask, request

# ------------- uptime var -------------
boot_time = time.time()
boot_date = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))

# ------------- flask config -------------
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
app = Flask(__name__)

# ------------- bot config -------------
WEBHOOK_TOKEN = os.environ.get('WEBHOOK_TOKEN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ------------- log ---------------
users = [int(os.environ.get("ADMIN_ID"))]

logger = logging.getLogger("alpha")
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

tg_logger.setup(logger, token=os.environ.get("LOG_BOT_TOKEN"), users=users)


# -------------- status webpage --------------
@app.route('/')
def status():
    password = request.args.get("password")
    if password != ADMIN_PASSWORD:
        logger.info('Status page loaded without password')
        return "<h1>Access denied!<h1>", 403

    return f"<h1>This is tg_logger demo bot server</h1>" \
           f"<p>Server uptime: {datetime.timedelta(seconds=time.time() - boot_time)}</p>" \
           f"<p>Server last boot at {boot_date}"


# ------------- webhook ----------------
@app.route('/' + WEBHOOK_TOKEN, methods=['POST'])
def getMessage():
    temp = request.stream.read().decode("utf-8")
    temp = telebot.types.Update.de_json(temp)
    logger.debug('New message received. raw: %s', temp)
    bot.process_new_updates([temp])
    return "!", 200


@app.route("/set_webhook")
def webhook_on():
    password = request.args.get("password")
    if password != ADMIN_PASSWORD:
        logger.info('Set_webhook page loaded without password')
        return "<h1>Access denied!<h1>", 403

    bot.remove_webhook()
    url = 'https://' + os.environ.get('HOST') + '/' + WEBHOOK_TOKEN
    bot.set_webhook(url=url)
    logger.info(f'Webhook is ON! Url: %s', url)
    return "<h1>WebHook is ON!</h1>", 200


@app.route("/remove_webhook")
def webhook_off():
    password = request.args.get("password")
    if password != ADMIN_PASSWORD:
        logger.info('Remove_webhook page loaded without password')
        return "<h1>Access denied!<h1>", 403

    bot.remove_webhook()
    logger.info('WebHook is OFF!')
    return "<h1>WebHook is OFF!</h1>", 200


# --------------- service functions -------------------
def get_logger(name, user_id):
    temp_logger = logging.getLogger(name)
    while temp_logger.handlers:
        temp_logger.removeHandler(temp_logger.handlers[0])
    temp_logger.setLevel(logging.INFO)
    tg_logger.setup(temp_logger, token=BOT_TOKEN, users=[user_id])

    return temp_logger


# --------------- bot -------------------
@bot.message_handler(commands=["example"])
def get_example(message):
    logger.info(f'</code>@{message.from_user.username} ({message.chat.id})<code> wants an example')

    bot.send_message(message.chat.id,
                     f'<b>This code will run and result will be shown below</b>\n\n'
                     f'<code>'
                     f'import logging\n'
                     f'import tg_logger\n\n'
                     f'token = YOUR_BOT_TOKEN_GOES_HERE\n'
                     f'users = [{message.chat.id}]\n\n'
                     f'logger = logging.getLogger("{message.from_user.username}")\n'
                     f'logger.setLevel(logging.INFO)\n'
                     f'tg_logger.setup(logger, token=token, users=users)\n\n'
                     f'logger.info("Hello from tg_logger by otter18")'
                     f'</code>',
                     parse_mode="HTML")

    user_logger = get_logger(message.from_user.username, message.chat.id)
    logger.debug("User logger obj: %s\nUser logger handlers: %s", user_logger, user_logger.handlers)

    user_logger.info("Hello from tg_logger by otter18")


@bot.message_handler(commands=["file"])
def get_file(message):
    logger.info(f'</code>@{message.from_user.username} ({message.chat.id})<code> used /file')

    bot.send_message(message.chat.id,
                     f'<b>This code will run and result will be shown below</b>\n\n'
                     f'<code>'
                     f'import logging\n'
                     f'import tg_logger\n\n'
                     f'token = YOUR_BOT_TOKEN_GOES_HERE\n'
                     f'users = [{message.chat.id}]\n\n'
                     f'tg_files_logger = tg_logger.TgFileLogger(token=token, users=users)\n\n'
                     f'file_name = "test.txt"\n'
                     f'with open(file_name, "w") as f:\n'
                     f'    f.write("Hello from tg_logger by otter18")\n\n'
                     f'tg_files_logger.send(file_name, "Test file")'
                     f'</code>',
                     parse_mode="HTML")

    user_logger = get_logger(message.from_user.username, message.chat.id)
    logger.debug("User logger obj: %s\nUser logger handlers: %s", user_logger, user_logger.handlers)

    tg_files_logger = tg_logger.TgFileLogger(token=BOT_TOKEN, users=[message.chat.id])

    file_name = "test.txt"
    with open(file_name, 'w') as f:
        f.write("Hello from tg_logger by otter18")

    tg_files_logger.send(file_name, "Test file")


@bot.message_handler(commands=["id"])
def get_id(message):
    logger.info(f'</code>@{message.from_user.username} ({message.chat.id})<code> used /id')
    bot.send_message(message.chat.id, f"<code>user_id = [{message.chat.id}]</code>", parse_mode='html')


@bot.message_handler(commands=["start", "help"])
def start(message):
    logger.info(f'</code>@{message.from_user.username} ({message.chat.id})<code> used /start or /help')
    bot.send_message(message.chat.id,
                     '<b>Hello! This bot shows how <a href="https://github.com/otter18/tg_logger">tg-logger library</a>'
                     ' works and helps to set it up.</b>\n\n'
                     '<b>You can use this commands:</b>\n'
                     '• /example - quickstart example\n'
                     '• /id - return your <b>user_id</b>\n'
                     '• /file - file logging example\n'
                     '• /help - shows this message\n\n'
                     'For support message me @chernykh_vladimir',
                     parse_mode='html')


if __name__ == '__main__':
    if "IS_PRODUCTION" in os.environ:
        app.run()
    else:
        bot.polling(none_stop=True)

import datetime
import logging
import os
import time

import pytz
import telebot
import tg_logger
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ------------- uptime var -------------
boot_time = time.time()
boot_date = datetime.datetime.now(tz=pytz.timezone("Europe/Moscow"))

# ------------- flask config -------------
app = Flask(__name__)

# ------------- bot config -------------
WEBHOOK_TOKEN = os.environ.get('WEBHOOK_TOKEN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# ------------- log ---------------
users = [int(os.environ.get("ADMIN_ID"))]

logger = logging.getLogger("root")
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

tg_logger.setup(logger, token=BOT_TOKEN, users=users)


# -------------- status webpage --------------
@app.route('/')
def status():
    logging.info('Status page loaded')

    return f"<h1>This is tg_logger demo bot server</h1>" \
           f"<p>Server uptime: {datetime.timedelta(seconds=time.time() - boot_time)}</p>" \
           f"<p>Server last boot at {boot_date}"


# ------------- webhook ----------------
@app.route('/' + WEBHOOK_TOKEN, methods=['POST'])
def getMessage():
    logging.info('New message received')
    temp = request.stream.read().decode("utf-8")
    temp = telebot.types.Update.de_json(temp)
    bot.process_new_updates([temp])
    return "!", 200


@app.route("/set_webhook")
def webhook_on():
    bot.remove_webhook()
    url = 'https://' + os.environ.get('HOST') + '/' + WEBHOOK_TOKEN
    bot.set_webhook(url=url)
    logging.info(f'Webhook is ON!')
    return "<h1>WebHook is ON!</h1>", 200


@app.route("/remove_webhook/" + WEBHOOK_TOKEN)
def webhook_off():
    bot.remove_webhook()
    logging.info('WebHook is OFF!')
    return "<h1>WebHook is OFF!</h1>", 200


def get_logger(name, user_id):
    temp_logger = logging.getLogger(name)
    while temp_logger.handlers:
        temp_logger.removeHandler(temp_logger.handlers[0])
    temp_logger.setLevel(logging.INFO)
    tg_logger.setup(temp_logger, token=BOT_TOKEN, users=[user_id])

    return temp_logger


# --------------- bot -------------------
@bot.message_handler(commands=["example"])
def new_queue(message, from_user=True):
    logging.info(f'{message.from_user.username} want example')

    user_logger = get_logger(message.from_user.username, message.chat.id)
    logger.debug("User logger obj: %s\nUser logger handlers: %s", user_logger, user_logger.handlers)
    
    # Test
    user_logger.info("Hello from tg_logger by otter18")

    # TgFileLogger example
    tg_files_logger = tg_logger.TgFileLogger(
        token=BOT_TOKEN,  # tg bot token
        users=[message.chat.id],  # list of user_id
        timeout=10  # default is 10 seconds
    )

    file_name = "test.txt"
    with open(file_name, 'w') as example_file:
        example_file.write("Hello from tg_logger by otter18")

    tg_files_logger.send(file_name, "Test file")

    # And one more time...
    user_logger.info("Finishing tg_logger demo")


@bot.message_handler(commands=["start"])
def start(message):
    logging.info(f'{message.from_user.username} used /start')
    bot.send_message(message.chat.id, "Hello! Use command to see examples", parse_mode='html')


if __name__ == '__main__':
    if "IS_PRODUCTION" in os.environ:
        app.run()
    else:
        bot.polling(none_stop=True)

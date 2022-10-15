from collections import defaultdict
from time import time

import yaml
from loguru import logger

from telebot import TeleBot, types  # для указание типов

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
    bot = TeleBot(cfg["token"])
    CHANEL_ID = str(cfg["chanel_id"])

user_message = defaultdict(dict)


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Этот бот создан, чтобы отправлять фото спящих ФКИшников в канал «Спящий космос». \n"
        "Чтобы отправить фото, просто загрузи его сюда, отправлять можно как *анонимно*, так и в *открытую*.",
        parse_mode="Markdown",
    )


@bot.message_handler(content_types=["photo"])
def handle_docs_photo(message):
    global user_message
    user_id = message.from_user.id
    if len(user_message[user_id]) < 2 or (time() - user_message[user_id]["last_time"] > 60):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="Открыто", callback_data="deanon"))
        markup.add(types.InlineKeyboardButton(text="Анонимно", callback_data="anon"))
        markup.add(types.InlineKeyboardButton(text="Я передумал(а)", callback_data="reset"))
        bot.send_message(message.chat.id, text="Как опубликовать спящего?", reply_markup=markup)
        user_message[user_id]["message"] = message
    else:
        text_2_send = (
            "Фото можно отправлять раз в минуту,"
            f" следующая отправка возможна через {round(60 - (time() - user_message[user_id]['last_time']))} секунд.\n"
            "Если вы считаете, что возникла ошибка – напишите @deetehreal."
        )
        bot.send_message(message.chat.id, text=text_2_send)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global user_message, CHANEL_ID
    if call.data == "reset":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        if call.data == "deanon":
            bot.forward_message(CHANEL_ID, call.from_user.id, user_message[call.from_user.id]["message"].message_id)
            logger.info(f"Бот открыто отправил  картинку от @{call.from_user.username}")
        elif call.data == "anon":
            bot.send_photo(
                CHANEL_ID,
                photo=user_message[call.from_user.id]["message"].photo[-1].file_id,
                caption=user_message[call.from_user.id]["message"].caption,
            )
            logger.info(f"Бот анонимно отправил  картинку от @{call.from_user.username}")
        user_message[call.from_user.id]["last_time"] = time()
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id, text="Фото успешно отправлено!"
        )


bot.infinity_polling()

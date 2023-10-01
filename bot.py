from collections import defaultdict
from time import sleep, time

import yaml
from loguru import logger
from requests import ConnectionError, ReadTimeout
from telebot import TeleBot, types  # для указание типов
from telebot.formatting import escape_markdown

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
    bot = TeleBot(cfg["token"])
    CHANEL_ID = str(cfg["chanel_id"])

user_message = defaultdict(lambda: defaultdict(int))
MESSAGE_DELAY = 60


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
    user_id = message.from_user.id
    if len(user_message[user_id]) < 2 or (time() - user_message[user_id]["last_time"] > MESSAGE_DELAY):
        if user_message[user_id]["handler_trigger"] == 0:
            user_message[user_id]["handler_trigger"] = 1
            user_message[user_id]["message"] = [message]
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text="Открыто", callback_data="deanon"))
            markup.add(types.InlineKeyboardButton(text="Анонимно", callback_data="anon"))
            markup.add(types.InlineKeyboardButton(text="Я передумал(а)", callback_data="reset"))
            bot.send_message(message.chat.id, text="Как опубликовать спящего?", reply_markup=markup)
        else:
            user_message[user_id]["message"].append(message)

    else:
        text_2_send = (
            "Фото можно отправлять раз в минуту,"
            " следующая отправка возможна через"
            f" {round(MESSAGE_DELAY - (time() - user_message[user_id]['last_time']))} секунд.\n"
            "Если вы считаете, что возникла ошибка – напишите @deetehreal."
        )
        bot.send_message(message.chat.id, text=text_2_send)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "reset":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        signiture = None
        caption = user_message[call.from_user.id]["message"][0].caption
        if call.data == "deanon":

            displayed_name = call.from_user.first_name
            if call.from_user.last_name is not None:
                displayed_name += f" {call.from_user.last_name}"

            signiture = f"\nПрислал [{displayed_name}](tg://user?id={call.from_user.id})"

        result_caption = ""

        if caption is not None:
            result_caption += escape_markdown(caption)
        if signiture is not None:
            result_caption += signiture

        if len(user_message[call.from_user.id]["message"]) > 1:
            media = []
            for idx, msg in enumerate(user_message[call.from_user.id]["message"]):
                result_caption = result_caption if idx == 0 else None
                media.append(
                    types.InputMediaPhoto(
                        media=msg.photo[-1].file_id,
                        caption=result_caption,
                        parse_mode="MarkdownV2",
                    )
                )
            bot.send_media_group(CHANEL_ID, media=media)
        else:
            bot.send_photo(
                CHANEL_ID,
                photo=user_message[call.from_user.id]["message"][0].photo[-1].file_id,
                caption=result_caption,
                parse_mode="MarkdownV2",
            )
        if call.data == "deanon":
            logger.info(f"Бот открыто отправил картинку от @{call.from_user.username}")
        else:
            logger.info(f"Бот анонимно отправил картинку от @{call.from_user.username}")
        user_message[call.from_user.id]["handler_trigger"] = 0
        user_message[call.from_user.id]["last_time"] = time()
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id, text="Фото успешно отправлено!"
        )


if __name__ == "__main__":
    while True:
        try:
            logger.info("TIME TO WORK")
            bot.infinity_polling()
        except (ConnectionError, ReadTimeout) as e:
            logger.warning(e)
            sleep(10)

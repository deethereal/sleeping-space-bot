import yaml

from telebot import TeleBot, types  # для указание типов

with open("config.yaml") as f:
    cfg = yaml.safe_load(f)
    bot = TeleBot(cfg["token"])
    CHANEL_ID = str(cfg["chanel_id"])
user_message = {}


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
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Открыто", callback_data="deanon"))
    markup.add(types.InlineKeyboardButton(text="Анонимно", callback_data="anon"))
    markup.add(types.InlineKeyboardButton(text="Я передумал(а)", callback_data="reset"))
    bot.send_message(message.chat.id, text="Как опубликовать спящего?", reply_markup=markup)
    user_message[message.from_user.id] = message


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global user_message, CHANEL_ID
    if call.data == "deanon":  # call.data это callback_data, которую мы указали при объявлении кнопки
        bot.forward_message(CHANEL_ID, call.from_user.id, user_message[call.from_user.id].message_id)
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id, text="Фото успешно отправлено!"
        )
    elif call.data == "anon":
        bot.send_photo(
            CHANEL_ID,
            photo=user_message[call.from_user.id].photo[-1].file_id,
            caption=user_message[call.from_user.id].caption,
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id, text="Фото успешно отправлено!"
        )
    elif call.data == "reset":
        bot.delete_message(call.message.chat.id, call.message.message_id)


bot.infinity_polling()

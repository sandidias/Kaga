from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import escape_markdown

from kaga import dispatcher
from kaga.modules.no_sql import get_collection
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import user_admin
from kaga.modules.helper_funcs.string_handling import markdown_parser


RULES_DATA = get_collection("RULES")


@typing_action
def get_rules(update, context):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat not found" and from_pm:
            bot.send_message(
                user.id,
                "Pintasan aturan untuk obrolan ini belum disetel dengan benar! Minta admin untuk "
                "memperbaiki ini.",
            )
            return
        else:
            raise

    rules = chat_rules(chat_id)
    text = "Aturan untuk *{}* adalah:\n\n{}".format(
        escape_markdown(chat.title), rules
    )

    if from_pm and rules:
        bot.send_message(user.id, text, parse_mode=ParseMode.MARKDOWN)
    elif from_pm:
        bot.send_message(
            user.id,
            "Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
            "Ini mungkin tidak berarti itu melanggar hukum...!",
        )
    elif rules:
        update.effective_message.reply_text(
            "Hubungi saya di PM untuk mendapatkan aturan grup ini.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Aturan",
                            url="t.me/{}?start={}".format(
                                bot.username, chat_id
                            ),
                        )
                    ]
                ]
            ),
        )
    else:
        update.effective_message.reply_text(
            "Admin grup belum menetapkan aturan apa pun untuk obrolan ini. "
            "Tini mungkin tidak berarti itu melanggar hukum...!"
        )


@user_admin
@typing_action
def set_rules(update, context):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    # use python's maxsplit to separate cmd and args
    args = raw_text.split(None, 1)
    if len(args) == 2:
        txt = args[1]
        # set correct offset relative to command
        offset = len(txt) - len(raw_text)
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset
        )

        RULES_DATA.find_one_and_update(
            {'_id': chat_id},
            {"$set": {'rules': markdown_rules}},
            upsert=True)
        update.effective_message.reply_text(
            "Berhasil menetapkan aturan untuk grup ini."
        )


@user_admin
@typing_action
def clear_rules(update, context):
    chat_id = update.effective_chat.id
    RULES_DATA.delete_one({'_id': chat_id})
    update.effective_message.reply_text("Aturan berhasil dihapus!")


def chat_rules(chat_id):
    data = RULES_DATA.find_one({'_id': int(chat_id)})  # ensure integer
    if data:
        return data["rules"]
    else:
        return False


def __stats__():
    count = RULES_DATA.count_documents({})
    return "× {} obrolan memiliki aturan yang ditetapkan.".format(count)


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    RULES_DATA.find_one_and_update(
        {'_id': chat_id},
        {"$set": {'rules': rules}},
        upsert=True)


def __migrate__(old_chat_id, new_chat_id):
    rules = RULES_DATA.find_one_and_delete({'_id':old_chat_id})
    if rules:
        RULES_DATA.insert_one(
            {'_id': new_chat_id, 'rules': rules["rules"]})


def __chat_settings__(chat_id, user_id):
    return "Obrolan ini telah menetapkan aturannya: `{}`".format(
        bool(chat_rules(chat_id))
    )


__help__ = """
Setiap obrolan bekerja dengan aturan yang berbeda; modul ini akan membantu memperjelas aturan tersebut!

 × /rules: dapatkan aturan untuk obrolan ini.

*Khusus Admin:*
 × /setrules <aturan Anda di sini>: Menetapkan aturan untuk obrolan.
 × /clearrules: Menghapus aturan yang disimpan untuk obrolan.
"""

__mod_name__ = "Rules"

GET_RULES_HANDLER = CommandHandler(
    "rules", get_rules, filters=Filters.chat_type.groups, run_async=True
)
SET_RULES_HANDLER = CommandHandler(
    "setrules", set_rules, filters=Filters.chat_type.groups, run_async=True
)
RESET_RULES_HANDLER = CommandHandler(
    "clearrules", clear_rules, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)

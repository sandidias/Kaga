from io import BytesIO
from time import sleep

from telegram import TelegramError
from telegram.error import BadRequest, TimedOut, Unauthorized
from telegram.ext import CommandHandler, Filters, MessageHandler

from kaga.modules.no_sql import users_db
import kaga.modules.sql.users_sql as sql
from kaga.modules.sql.users_sql import get_all_users
from kaga import LOGGER, OWNER_ID, dispatcher
from kaga.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4
CHAT_GROUP = 10


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = users_db.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0]["_id"]

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj["_id"])
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == "brolan tidak ditemukan":
                    pass
                else:
                    LOGGER.exception("Terjadi kesalahan saat mengekstrak ID pengguna")

    return None


def broadcast(update, context):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2:
        to_group = False
        to_user = False
        if to_send[0] == '/broadcastgroups':
            to_group = True
        if to_send[0] == '/broadcastusers':
            to_user = True
        else:
            to_group = to_user = True
        chats = users_db.get_all_chats() or []
        users = get_all_users()
        failed = 0
        failed_user = 0
        if to_group:
            for chat in chats:
                try:
                    context.bot.sendMessage(
                        int(chat["chat_id"]),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True)
                    sleep(0.1)
                except TelegramError:
                    failed += 1
        if to_user:
            for user in users:
                try:
                    context.bot.sendMessage(
                        int(user.user_id),
                        to_send[1],
                        parse_mode="MARKDOWN",
                        disable_web_page_preview=True)
                    sleep(0.1)
                except TelegramError:
                    failed_user += 1
        update.effective_message.reply_text(
            f"Siaran selesai.\nSiaran ke grup gagal: {failed}.\nSiaran ke pengguna gagal: {failed_user}."
        )


def log_user(update, context):
    chat = update.effective_chat
    msg = update.effective_message

    users_db.update_user(
        msg.from_user.id, msg.from_user.username, chat.id, chat.title
    )

    if msg.reply_to_message:
        users_db.update_user(
            msg.reply_to_message.from_user.id,
            msg.reply_to_message.from_user.username,
            chat.id,
            chat.title,
        )

    if msg.forward_from:
        users_db.update_user(msg.forward_from.id, msg.forward_from.username)


def chats(update, context):
    all_chats = users_db.get_all_chats() or []
    chatfile = "List of chats.\n"
    for chat in all_chats:
        chatfile += "{} - ({})\n".format(chat["chat_name"], chat["chat_id"])


    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="chatlist.txt",
            caption="Berikut adalah daftar obrolan di database saya.",
        )
        

def chat_checker(update, context):
    try:
        if (
            update.effective_message.chat.get_member(
                context.bot.id
            ).can_send_messages
            is False
        ):
            context.bot.leaveChat(update.effective_message.chat.id)
    except (TimedOut, Unauthorized, BadRequest):
        pass


def __user_info__(user_id):
    if user_id == dispatcher.bot.id:
        return """Saya telah melihat mereka di ... Wow. Apakah mereka menguntit saya? Mereka ada di semua tempat yang sama dengan saya ... oh. Ini aku."""
    num_chats = users_db.get_user_num_chats(user_id)
    return """Saya pernah melihat mereka dalam <code>{}</code> secara total.""".format(
        num_chats
    )


def __stats__():
    return "× {} users, across {} chats".format(
        users_db.num_users(), users_db.num_chats()
    )


def __migrate__(old_chat_id, new_chat_id):
    users_db.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler(
    ["broadcastall", "broadcastusers", "broadcastgroups"], broadcast, filters=Filters.user(OWNER_ID), run_async=True
)
USER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, log_user, run_async=True
)
CHATLIST_HANDLER = CommandHandler(
    "chatlist", chats, filters=CustomFilters.sudo_filter, run_async=True
)
CHAT_CHECKER_HANDLER = MessageHandler(
    Filters.all & Filters.chat_type.groups, chat_checker, run_async=True
)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)

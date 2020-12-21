import html
from typing import Optional

from telegram import Chat, ChatPermissions, Message, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import mention_html

from kaga import dispatcher
from kaga.modules.connection import connected
from kaga.modules.helper_funcs.alternate import send_message, typing_action
from kaga.modules.helper_funcs.chat_status import is_user_admin, user_admin
from kaga.modules.helper_funcs.string_handling import extract_time
from kaga.modules.log_channel import loggable
from kaga.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "Dilarang ukepada {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Dibisukan kepada {}".format(getvalue)
            tag = "TMUTE"
        send_message(
            update.effective_message,
            "Bagus, aku suka meninggalkan flood tapi, "
            "Anda hanya kecewa. {}!".format(execstrings),
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>Pengguna:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            )
        )

    except BadRequest:
        msg.reply_text(
            "Saya tidak bisa membatasi orang di sini, memberi saya izin terlebih dahulu! Sampai saat itu, aku akan menonaktifkan anti-flood."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nTidak memiliki cukup izin untuk membatasi pengguna sehingga secara otomatis menonaktifkan anti-flood".format(
                chat.title
            )
        )


@user_admin
@loggable
@typing_action
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan dalam grupPerintah ini dimaksudkan untuk digunakan dalam grup tidak dalam PM tidak dalam PM",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat_id, 0)
            if conn:
                text = message.reply_text(
                    "Antiflood telah dinon-fungsikan di {}.".format(chat_name)
                )
            else:
                text = message.reply_text("Antiflood telah dinon-fungsikan.")
            send_message(update.effective_message, text, parse_mode="markdown")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "Antiflood telah dinon-fungsikan di{}.".format(chat_name)
                    )
                else:
                    text = message.reply_text("Antiflood telah dinon-fungsikan.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                    )
                )

            elif amount < 3:
                send_message(
                    update.effective_message,
                    "Antiflood must be either 0 (disabled) or number greater than 3!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = (
                        "Anti-flood telah diatur ke {} dalam obrolan: {}".format(
                            amount, chat_name
                        )
                    )
                else:
                    text = (
                        "Berhasil memperbarui batas anti-flood ke {}!".format(
                            amount
                        )
                    )
                send_message(
                    update.effective_message, text, parse_mode="markdown"
                )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood to <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        amount,
                    )
                )

        else:
            message.reply_text(
                "Invalid argument please use a number, 'off' or 'no'"
            )
    else:
        message.reply_text(
            (
                "Gunakan `/setflood number` untuk mengaktifkan anti-flood.\nAtau gunakan `/setflood off` untuk menonaktifkan antiflood!."
            ),
            parse_mode="markdown",
        )
    return ""


@typing_action
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan dalam grup tidak dalam PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = msg.reply_text(
                "Aku tidak akan menegakkan pengendalian banjir di {}!".format(chat_name)
            )
        else:
            text = msg.reply_text("Aku tidak akan menegakkan pengendalian bflood di sini!")
        send_message(update.effective_message, text, parse_mode="markdown")
    else:
        if conn:
            text = msg.reply_text(
                "Saat ini saya membatasi anggota setelah {} pesan berturut-turut di {}.".format(
                    limit, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Saat ini saya membatasi anggota setelah {} pesan berturut-turut.".format(
                    limit
                )
            )
        send_message(update.effective_message, text, parse_mode="markdown")


@user_admin
@loggable
@typing_action
def set_flood_mode(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan dalam grup tidak dalam PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """Sepertinya Anda mencoba menetapkan nilai waktu untuk antiflood tetapi Anda tidak menentukan waktu; Coba `/setfloodmode tban <timevalue>`.
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tban for {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    update.effective_message,
                    """Sepertinya Anda mencoba menetapkan nilai waktu untuk antiflood tetapi Anda tidak menentukan waktu; Coba, `/setfloodmode tmute <timevalue>`.
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu.""",
                )
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return
            settypeflood = "tmute for {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "Saya hanya mengerti ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = msg.reply_text(
                "Melebihi batas flood berturut-turut akan mengakibatkan {} dalam {}!".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Melebihi batas flood berturut-turut akan {}!".format(
                    settypeflood
                )
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Has changed antiflood mode. User will {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban for {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute for {}".format(getvalue)
        if conn:
            text = msg.reply_text(
                "Mengirim lebih banyak pesan daripada batas flood akan mengakibatkan {} masuk {}.".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Mengirim lebih banyak pesan daripada batas flood akan mengakibatkan {}.".format(
                    settypeflood
                )
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing to flood control."
    else:
        return "Antiflood telah disetel ke`{}`.".format(limit)


__help__ = """
Kau tahu bagaimana kadang-kadang, orang bergabung, mengirim 100 pesan, dan merusak obrolan Anda? Dengan antiflood, itu tidak terjadi lagi!

Antiflood memungkinkan Anda mengambil tindakan pada pengguna yang mengirim lebih dari x pesan berturut-turut. Melebihi flood yang ditetapkan 
akan mengakibatkan pembatasan pengguna tersebut.

 × /flood: Dapatkan setelan pengendalian flood saat ini

*Khusus Admin*:

 × /setflood <int/'no'/'off'>: mengaktifkan atau menonaktifkan pengendalian flood.
 × /setfloodmode <ban/kick/mute/tban/tmute> <value>: Aksi yang harus dilakukan ketika pengguna telah melampaui batas flood. ban/kick/mute/tmute/tban

 *Catatan*:
 - Nilai harus diisi untuk tban dan tmute!

 Bisa seperti ini:
 5m = 5 menit
 6h = 6 jam
 3d = 3 hari
 1w = 1 minggu
 """

__mod_name__ = "Antiflood"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.chat_type.groups,
    check_flood,
    run_async=True,
)
SET_FLOOD_HANDLER = CommandHandler(
    "setflood", set_flood, pass_args=True, run_async=True
)  # , filters=Filters.chat_type.groups)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, pass_args=True, run_async=True
)  # , filters=Filters.chat_type.groups)
# , filters=Filters.chat_type.groups)
FLOOD_HANDLER = CommandHandler("flood", flood, run_async=True)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

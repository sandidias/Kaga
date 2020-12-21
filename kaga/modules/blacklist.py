import html
import re

from telegram import ChatPermissions, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.utils.helpers import mention_html

from kaga import LOGGER, dispatcher
from kaga.modules.connection import connected
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import send_message, typing_action
from kaga.modules.helper_funcs.chat_status import (
    user_admin,
    user_not_admin,
)
from kaga.modules.helper_funcs.extraction import extract_text
from kaga.modules.helper_funcs.misc import split_message
from kaga.modules.helper_funcs.string_handling import extract_time
from kaga.modules.no_sql import blacklist_db
from kaga.modules.log_channel import loggable
from kaga.modules.warns import warn

BLACKLIST_GROUP = 11


@user_admin
@typing_action
def blacklist(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title

    filter_list = "Kata-kata dalam daftar hitam saat ini dalam <b>{}</b>:\n".format(chat_name)

    all_blacklisted = blacklist_db.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    # for trigger in all_blacklisted:
    #     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if filter_list == "Kata-kata dalam daftar hitam saat ini dalam <b>{}</b>:\n".format(
            chat_name
        ):
            send_message(
                update.effective_message,
                "Tidak ada kata dalam daftar hitam <b>{}</b>!".format(chat_name),
                parse_mode=ParseMode.HTML,
            )
            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@user_admin
@typing_action
def add_blacklist(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            set(
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            )
        )
        for trigger in to_blacklist:
            blacklist_db.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            send_message(
                update.effective_message,
                "Menambahkan daftar hitam <code>{}</code> dalam obrolan: <b>{}</b>!".format(
                    html.escape(to_blacklist[0]), chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "Menambahkan pemicu daftar hitam: <code>{}</code> di <b>{}</b>!".format(
                    len(to_blacklist), chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            update.effective_message,
            "Beri tahu saya kata mana yang ingin Anda tambahkan ke daftar hitam.",
        )


@user_admin
@typing_action
def unblacklist(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            set(
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            )
        )
        successful = 0
        for trigger in to_unblacklist:
            success = blacklist_db.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    "Dihapus <code>{}</code> dari daftar hitam di <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), chat_name
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                send_message(
                    update.effective_message,
                    "Ini bukan pemicu daftar hitam!",
                )

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                "Dihapus <code>{}</code> dari daftar hitam di <b>{}</b>!".format(
                    successful, chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                update.effective_message,
                "Tidak satu pun pemicu ini ada sehingga tidak dapat dihapus.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "Dihapus <code>{}</code> dari daftar hitam. {} Tidak ada, "
                "jadi tidak dihapus.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        send_message(
            update.effective_message,
            "Beri tahu saya kata mana yang ingin Anda hapus dari daftar hitam!",
        )


@loggable
@user_admin
@typing_action
def blacklist_mode(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
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
                "Perintah ini hanya dapat digunakan di grup bukan di PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if (
            args[0].lower() == "off"
            or args[0].lower() == "nothing"
            or args[0].lower() == "no"
        ):
            settypeblacklist = "do nothing"
            blacklist_db.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() == "del" or args[0].lower() == "delete":
            settypeblacklist = "will delete blacklisted message"
            blacklist_db.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            blacklist_db.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            blacklist_db.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            blacklist_db.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            blacklist_db.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """Sepertinya Anda mencoba menyetel nilai waktu untuk daftar hitam tetapi Anda tidak menentukan waktu; Coba, `/blacklistmode tban <timevalue>`.
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Nilai waktu tidak valid!
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return ""
            settypeblacklist = "larangan sementara untuk {}".format(args[1])
            blacklist_db.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """Sepertinya Anda mencoba menyetel nilai waktu untuk daftar hitam tetapi Anda tidak menentukan waktu; Coba, `/blacklistmode tmute <timevalue>`.

Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Nilai waktu tidak valid!
Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu."""
                send_message(
                    update.effective_message, teks, parse_mode="markdown"
                )
                return ""
            settypeblacklist = "bisukan sementara untuk {}".format(args[1])
            blacklist_db.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "Saya hanya mengerti: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        if conn:
            text = "Modus daftar hitam diubah `{}` di *{}*!".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Modus daftar hitam diubah: `{}`!".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Changed the blacklist mode. will {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = blacklist_db.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "do nothing"
        elif getmode == 1:
            settypeblacklist = "delete"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = "temporarily ban for {}".format(getvalue)
        elif getmode == 7:
            settypeblacklist = "temporarily mute for {}".format(getvalue)
        if conn:
            text = "Mode daftar hitam saat ini: *{}* di *{}*.".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Mode daftar hitam saat ini: *{}*.".format(settypeblacklist)
        send_message(
            update.effective_message, text, parse_mode=ParseMode.MARKDOWN
        )
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


@user_not_admin
def del_blacklist(update, context):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    bot = context.bot
    to_match = extract_text(message)
    if not to_match:
        return

    getmode, value = blacklist_db.get_blacklist_setting(chat.id)

    chat_filters = blacklist_db.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    message.delete()
                elif getmode == 2:
                    message.delete()
                    warn(
                        update.effective_user,
                        chat,
                        ("Menggunakan pemicu daftar hitam: {}".format(trigger)),
                        message,
                        update.effective_user,
                    )
                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Dibisukan {user.first_name} untuk menggunakan kata dalam Daftar Hitam: {trigger}!",
                    )
                    return
                elif getmode == 4:
                    message.delete()
                    res = chat.unban_member(update.effective_user.id)
                    if res:
                        bot.sendMessage(
                            chat.id,
                            f"Ditendang {user.first_name} untuk menggunakan kata dalam Daftar Hitam: {trigger}!",
                        )
                    return
                elif getmode == 5:
                    message.delete()
                    chat.kick_member(user.id)
                    bot.sendMessage(
                        chat.id,
                        f"Dilarang {user.first_name} untuk menggunakan kata dalam Daftar Hitam: {trigger}",
                    )
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.kick_member(user.id, until_date=bantime)
                    bot.sendMessage(
                        chat.id,
                        f"Dilarang {user.first_name} sampai '{value}' untuk menggunakan kata dalam Daftar Hitam: {trigger}!",
                    )
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        until_date=mutetime,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Dibisukan {user.first_name} sampai '{value}' untuk menggunakan kata dalam Daftar Hitam {trigger}!",
                    )
                    return
            except BadRequest as excp:
                if excp.message == "Pesan untuk dihapus tidak ditemukan":
                    pass
                else:
                    LOGGER.exception("Kesalahan saat menghapus pesan daftar hitam.")
            break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        blacklist_db.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    blacklist_db.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = blacklist_db.num_blacklist_chat_filters(chat_id)
    return "Ada {} kata dalam daftar hitam.".format(blacklisted)


def __stats__():
    return "× {} pemicu daftar hitam, di {} obrolan.".format(
        blacklist_db.num_blacklist_filters(), blacklist_db.num_blacklist_filter_chats()
    )


__mod_name__ = "Blacklists"

__help__ = """

Daftar hitam digunakan untuk menghentikan pemicu tertentu diucapkan dalam kelompok. Setiap kali pemicu disebutkan, pesan akan segera dihapus. Kombo yang bagus terkadang memasangkan ini dengan filter peringatan!

*CATATAN*: Daftar Hitam tidak memengaruhi admin grup.

 × /blacklist: Lihat kata-kata dalam daftar hitam saat ini.

Admin only:
 × /addblacklist <triggers>: Tambahkan pemicu ke daftar hitam. Setiap baris dianggap sebagai satu pemicu, jadi menggunakan baris yang berbeda akan memungkinkan Anda menambahkan beberapa pemicu.
 × /unblacklist <triggers>: Hapus pemicu dari daftar hitam. Logika baris baru yang sama berlaku di sini, jadi Anda bisa menghapus beberapa pemicu sekaligus.
 × /rmblacklist <triggers>: Sama seperti di atas.
 × /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Tindakan yang harus dilakukan ketika seseorang mengirimkan kata-kata yang masuk daftar hitam.
"""
BLACKLIST_HANDLER = DisableAbleCommandHandler(
    "blacklist", blacklist, pass_args=True, admin_ok=True, run_async=True
)
ADD_BLACKLIST_HANDLER = CommandHandler(
    "addblacklist", add_blacklist, run_async=True
)
UNBLACKLIST_HANDLER = CommandHandler(
    ["unblacklist", "rmblacklist"], unblacklist, run_async=True
)
BLACKLISTMODE_HANDLER = CommandHandler(
    "blacklistmode", blacklist_mode, pass_args=True, run_async=True
)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo)
    & Filters.chat_type.groups,
    del_blacklist,
    run_async=True,
)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)

import html
import re

import telegram
from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    User,
)
from telegram.error import BadRequest
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    DispatcherHandlerStop,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import escape_markdown, mention_html

from kaga import dispatcher  # BAN_STICKER
from kaga.modules.connection import connected
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from kaga.modules.helper_funcs.extraction import (
    extract_text,
    extract_user,
    extract_user_and_text,
)
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.helper_funcs.misc import split_message
from kaga.modules.helper_funcs.string_handling import split_quotes
from kaga.modules.log_channel import loggable
from kaga.modules.sql import warns_sql as sql

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = (
    "<b>Filter peringatan saat ini dalam obrolan ini</b>\n"
)


# Not async
def warn(
    user: User, chat: Chat, reason: str, message: Message, warner: User = None
) -> str:
    if is_user_admin(chat, user.id):
        message.reply_text("Admin sialan, bahkan tidak bisa diperingatkan!")
        return ""

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Filter peringatan otomatis."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            chat.unban_member(user.id)
            reply = "Itu {} peringatan, {} telah ditendang!".format(
                limit, mention_html(user.id, user.first_name)
            )

        else:  # ban
            chat.kick_member(user.id)
            reply = "tu {} peringatan, {} telah dilarang!".format(
                limit, mention_html(user.id, user.first_name)
            )

        for warn_reason in reasons:
            reply += "\n - {}".format(html.escape(warn_reason))

        # message.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        keyboard = None
        log_reason = (
            "<b>{}:</b>"
            "\n#WARN_BAN"
            "\n<b>Admin:</b> {}"
            "\n<b>Pengguna:</b> {} (<code>{}</code>)"
            "\n<b>Alasan:</b> {}"
            "\n<b>Jumlah:</b> <code>{}/{}</code>".format(
                html.escape(chat.title),
                warner_tag,
                mention_html(user.id, user.first_name),
                user.id,
                reason,
                num_warns,
                limit,
            )
        )

    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Hapus peringatan ⚠️",
                        callback_data="rm_warn({})".format(user.id),
                    )
                ]
            ]
        )

        reply = "Pengguna {} memiliki {}/{} peringatan ... hati-hati!".format(
            mention_html(user.id, user.first_name), num_warns, limit
        )
        if reason:
            reply += "\nAlasan peringatan terakhir:\n{}".format(html.escape(reason))

        log_reason = (
            "<b>{}:</b>"
            "\n#WARN"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {} (<code>{}</code>)"
            "\n<b>Reason:</b> {}"
            "\n<b>Counts:</b> <code>{}/{}</code>".format(
                html.escape(chat.title),
                warner_tag,
                mention_html(user.id, user.first_name),
                user.id,
                reason,
                num_warns,
                limit,
            )
        )

    try:
        message.reply_text(
            reply, reply_markup=keyboard, parse_mode=ParseMode.HTML
        )
    except BadRequest as excp:
        if excp.message == "Pesan balasan tidak ditemukan":
            # Do not reply
            message.reply_text(
                reply,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
                quote=False,
            )
        else:
            raise
    return log_reason


@user_admin_no_reply
@bot_admin
@loggable
def button(update, context):
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Peringatan terakhir dihapus oleh {}.".format(
                    mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )
            user_member = chat.get_member(user_id)
            return (
                "<b>{}:</b>"
                "\n#UNWARN"
                "\n<b>Admin:</b> {}"
                "\n<b>User:</b> {} (<code>{}</code>)".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(
                        user_member.user.id, user_member.user.first_name
                    ),
                    user_member.user.id,
                )
            )
        else:
            update.effective_message.edit_text(
                "Pengguna ini sudah tidak memiliki peringatan.", parse_mode=ParseMode.HTML
            )

    return ""


@user_admin
@can_restrict
@loggable
@typing_action
def warn_user(update, context):
    message = update.effective_message
    chat = update.effective_chat
    warner = update.effective_user
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if (
            message.reply_to_message
            and message.reply_to_message.from_user.id == user_id
        ):
            return warn(
                message.reply_to_message.from_user,
                chat,
                reason,
                message.reply_to_message,
                warner,
            )
        else:
            return warn(
                chat.get_member(user_id).user, chat, reason, message, warner
            )
    else:
        message.reply_text("Tidak ada pengguna yang ditunjuk!")
    return ""


@user_admin
@bot_admin
@loggable
@typing_action
def reset_warns(update, context):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Peringatan telah disetel ulang!")
        warned = chat.get_member(user_id).user
        return (
            "<b>{}:</b>"
            "\n#RESETWARNS"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {} (<code>{}</code>)".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(warned.id, warned.first_name),
                warned.id,
            )
        )
    else:
        message.reply_text("Tidak ada pengguna yang telah ditunjuk!")
    return ""


@user_admin
@bot_admin
@loggable
@typing_action
def remove_warns(update, context):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    user_id = extract_user(message, args)

    if user_id:
        sql.remove_warn(user_id, chat.id)
        message.reply_text("Peringatan terakhir telah dihapus!")
        warned = chat.get_member(user_id).user
        return (
            "<b>{}:</b>"
            "\n#UNWARN"
            "\n<b>• Admin:</b> {}"
            "\n<b>• User:</b> {}"
            "\n<b>• ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(warned.id, warned.first_name),
                warned.id,
            )
        )
    else:
        message.reply_text("Tidak ada pengguna yang ditunjuk!")
    return ""


@typing_action
def warns(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args) or update.effective_user.id

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

    result = sql.get_warns(user_id, chat_id)

    num = 1
    if result and result[0] != 0:
        num_warns, reasons = result
        limit, _ = sql.get_warn_setting(chat_id)

        if reasons:
            if conn:
                text = "Pengguna ini memiliki {}/{} peringatan, dalam * {} * karena alasan berikut:".format(
                    num_warns, limit, chat_name
                )
            else:
                text = "Pengguna ini memiliki {}/{} peringatan, karena alasan berikut:".format(
                    num_warns,
                    limit,
                )
            for reason in reasons:
                text += "\n {}. {}".format(num, reason)
                num += 1

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg, parse_mode="markdown")
        else:
            update.effective_message.reply_text(
                "Pengguna memiliki peringatan {}/{}, tapi tidak ada alasan untuk itu.".format(
                    num_warns, limit
                ),
                parse_mode="markdown",
            )
    else:
        update.effective_message.reply_text(
            "Pengguna ini tidak mendapat peringatan apa pun!"
        )


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with
        # different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat_id, keyword, content)

    update.effective_message.reply_text(
        "Filter peringatan ditambahkan untuk `{}` di *{}*!".format(keyword, chat_name),
        parse_mode="markdown",
    )
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id

    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat_id)

    if not chat_filters:
        msg.reply_text("Tidak ada filter peringatan yang aktif di sini!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat_id, to_remove)
            msg.reply_text("YYa, saya akan berhenti memperingatkan orang untuk ituep, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    msg.reply_text(
        "Itu bukan filter peringatan saat ini - klik: /warnlist untuk semua filter peringatan aktif."
    )


def list_warn_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id

    all_handlers = sql.get_chat_warn_triggers(chat_id)

    if not all_handlers:
        update.effective_message.reply_text(
            "Tidak ada filter peringatan yang aktif di sini!"
        )
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = " - {}\n".format(html.escape(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(
                filter_list, parse_mode=ParseMode.HTML
            )
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(
            filter_list, parse_mode=ParseMode.HTML
        )


@loggable
def reply_filter(update, context) -> str:
    chat = update.effective_chat
    message = update.effective_message

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@user_admin
@loggable
@typing_action
def set_warn_limit(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("Batas peringatan minimum adalah 3!")
            else:
                sql.set_warn_limit(chat_id, int(args[0]))
                msg.reply_text(
                    "Memperbarui batas peringatan menjadi `{}` di *{}*".format(
                        escape_markdown(args[0]), chat_name
                    ),
                    parse_mode="markdown",
                )
                return (
                    "<b>{}:</b>"
                    "\n#SET_WARN_LIMIT"
                    "\n<b>Admin:</b> {}"
                    "\nSet the warn limit to <code>{}</code>".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        args[0],
                    )
                )
        else:
            msg.reply_text("Beri saya nomor sebagai argumen!")
    else:
        limit, _ = sql.get_warn_setting(chat_id)

        msg.reply_text(
            "Peringatan saat ini dalam batas {} adalah {}".format(chat_name, limit)
        )
    return ""


@user_admin
@typing_action
def set_warn_strength(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        else:
            chat_id = update.effective_chat.id
            chat_name = chat.title

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat_id, False)
            msg.reply_text("Terlalu banyak peringatan sekarang akan mengakibatkan pelarangan!")
            return (
                "<b>{}:</b>\n"
                "<b>Admin:</b> {}\n"
                "Telah mengaktifkan peringatan yang kuat. Pengguna akan diblokir.".format(
                    chat_name, mention_html(user.id, user.first_name)
                )
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat_id, True)
            msg.reply_text(
                "Terlalu banyak peringatan sekarang akan menghasilkan tendangan! Pengguna akan dapat bergabung lagi setelah itu."
            )
            return (
                "<b>{}:</b>\n"
                "<b>Admin:</b> {}\n"
                "Telah menonaktifkan peringatan yang kuat. Pengguna hanya akan ditendang.".format(
                    chat_name, mention_html(user.id, user.first_name)
                )
            )

        else:
            msg.reply_text("Saya hanya mengerti on/yes/no/off!")
    else:
        _, soft_warn = sql.get_warn_setting(chat_id)
        if soft_warn:
            msg.reply_text(
                "Peringatan saat ini disetel untuk *menendang* pengguna ketika mereka melebihi batas.",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            msg.reply_text(
                "Peringatan saat ini disetel untuk *melarang* pengguna ketika mereka melebihi batas.",
                parse_mode=ParseMode.MARKDOWN,
            )
    return ""


def __stats__():
    return (
        "× {} keseluruhan memperingatkan, di {} obrolan.\n"
        "× {} peringatkan filter, di {} obrolan.".format(
            sql.num_warns(),
            sql.num_warn_chats(),
            sql.num_warn_filters(),
            sql.num_warn_filter_chats(),
        )
    )


def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        "Obrolan ini memiliki filter peringatan `{}`. Dibutuhkan `{}` memperingatkan "
        "sebelum pengguna mendapatkannya *{}*.".format(
            num_warn_filters, limit, "kicked" if soft_warn else "banned"
        )
    )


__help__ = """
 Jika Anda mencari cara untuk memperingatkan pengguna secara otomatis ketika mereka mengatakan hal-hal tertentu, gunakan perintah /addwarn.
 Contoh pengaturan filter multiword memperingatkan:
 × `/addwarn "sangat marah" Ini adalah pengguna yang marah
 Ini secara otomatis akan memperingatkan pengguna yang memicu "sangat marah", dengan alasan 'Ini adalah pengguna yang marah'.
 Contoh cara menyetel peringatan multi kata baru:
`/warn @user Karena peringatan itu menyenangkan`

 × /warns <userhandle>: Mendapatkan nomor pengguna, dan alasan, peringatan.
 × /warnlist: Mencantumkan semua filter peringatan saat ini

*Khusus Admin:*
 × /warn <userhandle>: Memperingatkan pengguna. Setelah 3 peringatan, pengguna akan diblokir dari grup. Bisa juga digunakan sebagai balasan.
 × /resetwarn <userhandle>: Menyetel ulang peringatan untuk pengguna. Bisa juga digunakan sebagai balasan.
 × /rmwarn <userhandle>: Menghapus peringatan terbaru untuk pengguna. Itu juga bisa digunakan sebagai balasan.
 × /unwarn <userhandle>: Sama dengan /rmwarn
 × /addwarn <keyword> <reply message>: Menetapkan filter peringatan untuk kata kunci tertentu. Jika Anda ingin kata kunci Anda \
adilah kalimat, lengkapi dengan tanda kutip, seperti: `/addwarn" very angry "This is an angry user`.
 × /nowarn <keyword>: enghentikan filter peringatan
 × /warnlimit <num>: Menetapkan batas peringatan
 × /strongwarn <on/yes/off/no>: Jika disetel ke aktif, melebihi batas peringatan akan mengakibatkan larangan. Lain, hanya akan menendang.
"""

__mod_name__ = "Warnings"

WARN_HANDLER = CommandHandler(
    "warn", warn_user, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
RESET_WARN_HANDLER = CommandHandler(
    ["resetwarn", "resetwarns"],
    reset_warns,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
REMOVE_WARNS_HANDLER = CommandHandler(
    ["rmwarn", "unwarn"],
    remove_warns,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler(
    "warns", warns, pass_args=True, run_async=True
)
ADD_WARN_HANDLER = CommandHandler("addwarn", add_warn_filter, run_async=True)
RM_WARN_HANDLER = CommandHandler(
    ["nowarn", "stopwarn"], remove_warn_filter, run_async=True
)
LIST_WARN_HANDLER = DisableAbleCommandHandler(
    ["warnlist", "warnfilters"],
    list_warn_filters,
    admin_ok=True,
    run_async=True,
)
WARN_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & Filters.chat_type.groups, reply_filter, run_async=True
)
WARN_LIMIT_HANDLER = CommandHandler(
    "warnlimit", set_warn_limit, pass_args=True, run_async=True
)
WARN_STRENGTH_HANDLER = CommandHandler(
    "strongwarn", set_warn_strength, pass_args=True, run_async=True
)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(REMOVE_WARNS_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)

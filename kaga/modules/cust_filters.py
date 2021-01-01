import re
from html import escape

import telegram
from telegram import InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    CommandHandler,
    DispatcherHandlerStop,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import escape_markdown, mention_html

from kaga import LOGGER, dispatcher
from kaga.modules.connection import connected
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import send_message, typing_action
from kaga.modules.helper_funcs.chat_status import user_admin
from kaga.modules.helper_funcs.extraction import extract_text
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.helper_funcs.misc import build_keyboard_parser
from kaga.modules.helper_funcs.msg_types import get_filter_type
from kaga.modules.helper_funcs.string_handling import (
    button_markdown_parser,
    escape_invalid_curly_brackets,
    markdown_to_html,
    split_quotes,
)
from kaga.modules.sql import cust_filters_sql as sql

HANDLER_GROUP = 15

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    #  sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note,
}


@typing_action
def list_handlers(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        filter_list = "*Filter in {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
            filter_list = "*local filters:*\n"
        else:
            chat_name = chat.title
            filter_list = "*Filter in {}*:\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        send_message(
            update.effective_message,
            "Tidak ada filter yang disimpan di {}!".format(chat_name),
        )
        return

    for keyword in all_handlers:
        entry = " × `{}`\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            send_message(
                update.effective_message,
                filter_list.format(chat_name),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            filter_list = entry
        else:
            filter_list += entry

    send_message(
        update.effective_message,
        filter_list.format(chat_name),
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = connected(context.bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local filters"
        else:
            chat_name = chat.title

    if not msg.reply_to_message and len(args) < 2:
        send_message(
            update.effective_message,
            "Berikan kata kunci keyboard untuk membalas dengan filter ini!",
        )
        return

    if msg.reply_to_message:
        if len(args) < 2:
            send_message(
                update.effective_message,
                "Berikan kata kunci untuk membalas dengan filter ini!",
            )
            return
        else:
            keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with
        # different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()
        if not text:
            send_message(
                update.effective_message,
                "Tidak ada pesan catatan - Anda tidak HANYA bisa memiliki tombol, Anda perlu pesan untuk menyertainya!",
            )
            return

    elif msg.reply_to_message and len(args) >= 2:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(
            text_to_parsing
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()

    elif not text and not file_type:
        send_message(
            update.effective_message,
            "Harap berikan kata kunci untuk balasan filter ini dengan!",
        )
        return

    elif msg.reply_to_message:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(
            text_to_parsing
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()
        if (
            msg.reply_to_message.text or msg.reply_to_message.caption
        ) and not text:
            send_message(
                update.effective_message,
                "Tidak ada pesan catatan - Anda tidak bisa HANYA memiliki tombol, Anda perlu pesan untuk menyertainya!",
            )
            return

    else:
        send_message(update.effective_message, "Filter tidak valid!")
        return

    add = addnew_filter(
        update, chat_id, keyword, text, file_type, file_id, buttons
    )
    # This is an old method
    # sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video, buttons)

    if add:
        send_message(
            update.effective_message,
            "Filter '{}' disimpan di *{}*!".format(keyword, chat_name),
            parse_mode=telegram.ParseMode.MARKDOWN,
        )
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@user_admin
@typing_action
def stop_filter(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if not conn == False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
        else:
            chat_name = chat.title

    if len(args) < 2:
        send_message(update.effective_message, "Apa yang harus saya hentikan?")
        return

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        send_message(update.effective_message, "Tidak ada filter yang aktif di sini!")
        return

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            send_message(
                update.effective_message,
                "Oke, saya akan berhenti membalas filter itu *{}*.".format(
                    chat_name
                ),
                parse_mode=telegram.ParseMode.MARKDOWN,
            )
            raise DispatcherHandlerStop

    send_message(
        update.effective_message,
        "Itu bukan filter - Klik: /filters untuk mendapatkan filter yang sedang aktif.",
    )


def reply_filter(update, context):
    chat = update.effective_chat
    message = update.effective_message

    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            if filt.reply == "harus ada balasan baru":
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                VALID_WELCOME_FORMATTERS = [
                    "first",
                    "last",
                    "fullname",
                    "username",
                    "id",
                    "chatname",
                    "mention",
                ]
                if filt.reply_text:
                    valid_format = escape_invalid_curly_brackets(
                        filt.reply_text, VALID_WELCOME_FORMATTERS
                    )
                    if valid_format:
                        filtext = valid_format.format(
                            first=escape(message.from_user.first_name),
                            last=escape(
                                message.from_user.last_name
                                or message.from_user.first_name
                            ),
                            fullname=" ".join(
                                [
                                    escape(message.from_user.first_name),
                                    escape(message.from_user.last_name),
                                ]
                                if message.from_user.last_name
                                else [escape(message.from_user.first_name)]
                            ),
                            username="@" + escape(message.from_user.username)
                            if message.from_user.username
                            else mention_html(
                                message.from_user.id,
                                message.from_user.first_name,
                            ),
                            mention=mention_html(
                                message.from_user.id,
                                message.from_user.first_name,
                            ),
                            chatname=escape(message.chat.title)
                            if message.chat.type != "private"
                            else escape(message.from_user.first_name),
                            id=message.from_user.id,
                        )
                    else:
                        filtext = ""
                else:
                    filtext = ""

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        context.bot.send_message(
                            chat.id,
                            markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        error_catch = get_exception(excp, filt, chat)
                        if error_catch == "noreply":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    markdown_to_html(filtext),
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Error in filters: " + excp.message
                                )
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Failed to send message: " + excp.message
                                )
                else:
                    if (
                        ENUM_FUNC_MAP[filt.file_type]
                        == dispatcher.bot.send_sticker
                    ):
                        ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            reply_to_message_id=message.message_id,
                            reply_markup=keyboard,
                        )
                    else:
                        ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            caption=markdown_to_html(filtext),
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            reply_markup=keyboard,
                        )
                break
            else:
                if filt.is_sticker:
                    message.reply_sticker(filt.reply)
                elif filt.is_document:
                    message.reply_document(filt.reply)
                elif filt.is_image:
                    message.reply_photo(filt.reply)
                elif filt.is_audio:
                    message.reply_audio(filt.reply)
                elif filt.is_voice:
                    message.reply_voice(filt.reply)
                elif filt.is_video:
                    message.reply_video(filt.reply)
                elif filt.has_markdown:
                    buttons = sql.get_buttons(chat.id, filt.keyword)
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)

                    try:
                        send_message(
                            update.effective_message,
                            filt.reply,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        if excp.message == "Protokol url tidak didukung":
                            try:
                                send_message(
                                    update.effective_message,
                                    "Anda tampaknya mencoba menggunakan protokol url yang tidak didukung. "
                                    "Telegram tidak mendukung tombol untuk beberapa protokol, seperti tg://. Silakan coba "
                                    "lagi.",
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Error in filters: " + excp.message
                                )
                        elif excp.message == "Reply message not found":
                            try:
                                context.bot.send_message(
                                    chat.id,
                                    filt.reply,
                                    parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=keyboard,
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Error in filters: " + excp.message
                                )
                        else:
                            try:
                                send_message(
                                    update.effective_message,
                                    "Pesan ini tidak dapat dikirim karena formatnya salah.",
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Error in filters: " + excp.message
                                )
                            LOGGER.warning(
                                "Message %s could not be parsed",
                                str(filt.reply),
                            )
                            LOGGER.exception(
                                "Could not parse filter %s in chat %s",
                                str(filt.keyword),
                                str(chat.id),
                            )

                else:
                    # LEGACY - all new filters will have has_markdown set to
                    # True.
                    try:
                        send_message(update.effective_message, filt.reply)
                    except BadRequest as excp:
                        LOGGER.exception("Error in filters: " + excp.message)
                break


@user_admin
@typing_action
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    usermem = chat.get_member(user.id)
    if not usermem.status == "creator":
        msg.reply_text("Perintah ini hanya dapat digunakan oleh PEMILIK obrolan!")
        return

    allfilters = sql.get_chat_triggers(chat.id)

    if not allfilters:
        msg.reply_text("Tidak ada filter dalam obrolan ini, tidak ada yang bisa dihentikan!")
        return

    count = 0
    filterlist = []
    for x in allfilters:
        count += 1
        filterlist.append(x)

    for i in filterlist:
        sql.remove_filter(chat.id, i)

    return msg.reply_text(f"Cleaned {count} filters in {chat.title}")


# NOT ASYNC NOT A HANDLER
def get_exception(excp, filt, chat):
    if excp.message == "Unsupported url protocol":
        return "Anda tampaknya mencoba menggunakan protokol URL yang tidak didukung. Telegram tidak mendukung kunci untuk beberapa protokol, seperti tg://. Silakan coba lagi!"
    elif excp.message == "Reply message not found":
        return "noreply"
    else:
        LOGGER.warning("Message %s could not be parsed", str(filt.reply))
        LOGGER.exception(
            "Could not parse filter %s in chat %s",
            str(filt.keyword),
            str(chat.id),
        )
        return (
            "Data ini tidak dapat dikirim karena formatnya salah."
        )


# NOT ASYNC NOT A HANDLER
def addnew_filter(update, chat_id, keyword, text, file_type, file_id, buttons):
    msg = update.effective_message
    totalfilt = sql.get_chat_triggers(chat_id)
    if len(totalfilt) >= 50:  # Idk why i made this like function....
        msg.reply_text(
            "Anda tidak dapat memiliki lebih dari lima puluh filter sekaligus! coba hapus beberapa sebelum menambahkan filter baru."
        )
        return False
    else:
        sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)
        return True


def __stats__():
    return "× {} filter, di {} obrolan.".format(
        sql.num_filters(), sql.num_chats()
    )


def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get("filters", {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    try:
        sql.migrate_chat(old_chat_id, new_chat_id)
    except KeyError:
        pass


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "Ada `{}` filter ubahsuaian di sini.".format(len(cust_filters))


__help__ = """
 × /filters: Cantumkan semua filter aktif yang disimpan dalam obrolan.

*Khusus Admin:*
 × /filter <keyword> <reply message>: Tambahkan filter ke obrolan ini. Bot sekarang akan membalas pesan itu setiap kali 'kata kunci'\
disebutkan. Jika Anda membalas stiker dengan kata kunci, bot akan membalas dengan stiker itu. CATATAN: semua filter \
kata kunci menggunakan huruf kecil. Jika Anda ingin kata kunci Anda menjadi kalimat, gunakan tanda kutip. misal: /filter "hey there" Bagaimana kabarmu \
kawan?
 × /stop <filter keyword>: Hentikan filter itu.

*Pembuat obrolan saja:*
 × /rmallfilter: Hentikan semua filter obrolan sekaligus.

*Catatan*: Filter juga mendukung format penurunan harga seperti: {first}, {last} dll .. dan tombol.
Periksa `/markdownhelp` untuk mengetahui lebih lanjut!

"""

__mod_name__ = "Filters"

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter)  # Don't Use async for this
RMALLFILTER_HANDLER = CommandHandler(
    "rmallfilter", rmall_filters, filters=Filters.chat_type.groups, run_async=True
)
LIST_HANDLER = DisableAbleCommandHandler(
    "filters", list_handlers, admin_ok=True, run_async=True
)
CUST_FILTER_HANDLER = MessageHandler(
    CustomFilters.has_text & ~Filters.update.edited_message,
    reply_filter,
    run_async=True,
)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
dispatcher.add_handler(RMALLFILTER_HANDLER)

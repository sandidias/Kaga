from datetime import datetime
from functools import wraps

from kaga.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import Bot, ParseMode
    from telegram.error import BadRequest, Unauthorized
    from telegram.ext import CommandHandler
    from telegram.utils.helpers import escape_markdown

    from kaga import LOGGER, dispatcher
    from kaga.modules.helper_funcs.chat_status import user_admin
    from kaga.modules.sql import log_channel_sql as sql

    def loggable(func):
        @wraps(func)
        def log_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += (
                        "\n<b>Link:</b> "
                        '<a href="http://telegram.me/{}/{}">click here</a>'.format(
                            chat.username, message.message_id
                        )
                    )
                log_chat = db.get_chat_log_channel(chat.id)
                if log_chat:
                    try:
                        send_log(context.bot, log_chat, chat.id, result)
                    except Unauthorized:
                        db.stop_chat_logging(chat.id)

            elif result == "":
                pass
            else:
                LOGGER.warning(
                    "%s was set as loggable, but had no return statement.",
                    func,
                )

            return result

        return log_action
    
    def gloggable(func):

        @wraps(func)
        def glog_action(update, context, *args,
                        **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt))

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                log_chat = str(MESSAGE_DUMP)
                if log_chat:
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    def send_log(bot: Bot, log_chat_id: str, orig_chat_id: str, result: str):
        try:
            bot.send_message(log_chat_id, result, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id,
                    "Saluran log ini telah dihapus - tidak disetel.",
                )
                db.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nPemformatan telah dinonaktifkan karena kesalahan yang tidak terduga.",
                )

    @user_admin
    def logging(update, context):
        message = update.effective_message
        chat = update.effective_chat

        log_channel = db.get_chat_log_channel(chat.id)
        if log_channel:
            log_channel_info = context.bot.get_chat(log_channel)
            message.reply_text(
                "Grup ini memiliki semua log yang dikirim ke: {} (`{}`)".format(
                    escape_markdown(log_channel_info.title), log_channel
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            message.reply_text("Tidak ada saluran log yang disetel untuk grup ini!")

    @user_admin
    def setlog(update, context):
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Sekarang, teruskan /setlog ke grup yang ingin Anda kaitkan dengan saluran ini!"
            )

        elif message.forward_from_chat:
            db.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message == "Message to delete not found":
                    pass
                else:
                    LOGGER.exception(
                        "Error deleting message in log channel. Should work anyway though."
                    )

            try:
                context.bot.send_message(
                    message.forward_from_chat.id,
                    "Saluran ini telah ditetapkan sebagai saluran log untuk {}.".format(
                        chat.title or chat.first_name
                    ),
                )
            except Unauthorized as excp:
                if (
                    excp.message
                    == "Forbidden: bot is not a member of the channel chat"
                ):
                    context.bot.send_message(
                        chat.id, "Berhasil menyetel saluran log!"
                    )
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            context.bot.send_message(chat.id, "Berhasil menyetel saluran log!")

        else:
            message.reply_text(
                "Langkah-langkah untuk mengatur saluran log adalah:\n"
                " - tambahkan bot ke saluran yang diinginkan\n"
                " - kirim /setlog ke saluran\n"
                " - meneruskan /setlog ke grup\n"
            )

    @user_admin
    def unsetlog(update, context):
        message = update.effective_message
        chat = update.effective_chat

        log_channel = db.stop_chat_logging(chat.id)
        if log_channel:
            context.bot.send_message(
                log_channel,
                "Tautan saluran telah dibatalkan dari {}".format(chat.title),
            )
            message.reply_text("Saluran log telah dilepas.")

        else:
            message.reply_text("Belum ada saluran log yang disetel!")

    def __stats__():
        return "× {} saluran log telah terlihat.".format(db.num_logchannels())

    def __migrate__(old_chat_id, new_chat_id):
        db.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        log_channel = db.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return "Grup ini memiliki semua log yang dikirim ke: {} (`{}`)".format(
                escape_markdown(log_channel_info.title), log_channel
            )
        return "Tidak ada saluran log yang disetel untuk grup ini!"

    __help__ = """
Tindakan terbaru memang bagus, tetapi tidak membantu Anda mencatat setiap tindakan yang dilakukan oleh bot. Inilah mengapa Anda membutuhkan saluran log!

Saluran log dapat membantu Anda melacak dengan tepat apa yang dilakukan admin lain. \
Bans, Mutes, warns, notes - semuanya bisa dimoderasi.

*khusus Admin:*
× /logchannel: Dapatkan info saluran log
× /setlog: Atur saluran log.
× /unsetlog: Batalkan pengaturan saluran log.

Pengaturan saluran log dilakukan dengan:
× Tambahkan bot ke saluran Anda, sebagai admin. Ini dilakukan melalui tab "tambahkan administrator".
× Kirim /setlog ke saluran Anda
× Meneruskan /setlog perintah ke grup yang Anda ingin login.
× Selamat! Semua sudah siap!
"""

    __mod_name__ = "Logger"

    LOG_HANDLER = CommandHandler("logchannel", logging, run_async=True)
    SET_LOG_HANDLER = CommandHandler("setlog", setlog, run_async=True)
    UNSET_LOG_HANDLER = CommandHandler("unsetlog", unsetlog, run_async=True)

    dispatcher.add_handler(LOG_HANDLER)
    dispatcher.add_handler(SET_LOG_HANDLER)
    dispatcher.add_handler(UNSET_LOG_HANDLER)

else:
    # run anyway if module not loaded
    def loggable(func):
        return func
    
    def gloggable(func):
        return func

import html, time
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters
from telegram.utils.helpers import mention_html

from kaga import dispatcher, LOGGER
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.chat_status import user_admin, can_delete
from kaga.modules.helper_funcs.admin_rights import user_can_delete
from kaga.modules.log_channel import loggable


@user_admin
@loggable
def purge(update, context):
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    if msg.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if user_can_delete(chat, user, context.bot.id) == False:
           msg.reply_text("Anda tidak memiliki cukup hak untuk menghapus pesan!")
           return ""
        if can_delete(chat, context.bot.id):
            message_id = msg.reply_to_message.message_id
            delete_to = msg.message_id - 1
            if args and args[0].isdigit():
                new_del = message_id + int(args[0])
                # No point deleting messages which haven't been written yet.
                if new_del < delete_to:
                    delete_to = new_del

            for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    context.bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message == "Message can't be deleted":
                        context.bot.send_message(chat.id, "Tidak dapat menghapus semua pesan. Pesannya mungkin terlalu lama, saya mungkin "
                                                  "tidak memiliki hak hapus, atau ini mungkin bukan grup super.")

                    elif err.message != "Message to delete not found":
                        LOGGER.exception("Kesalahan saat membersihkan pesan obrolan.")

            try:
                msg.delete()
            except BadRequest as err:
                if err.message == "Message can't be deleted":
                    context.bot.send_message(chat.id, "Tidak dapat menghapus semua pesan. Pesannya mungkin terlalu lama, saya mungkin "
                                              "tidak memiliki hak hapus, atau ini mungkin bukan grup super.")

                elif err.message != "Message to delete not found":
                    LOGGER.exception("Kesalahan saat membersihkan pesan obrolan.")

            del_msg = context.bot.send_message(chat.id, "Pembersihan selesai.")
            time.sleep(2)

            try:
                del_msg.delete()

            except BadRequest:
                pass

            return "<b>{}:</b>" \
                   "\n#PURGE" \
                   "\n<b>Admin:</b> {}" \
                   "\nPurged <code>{}</code> messages.".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               delete_to - message_id)

    else:
        msg.reply_text("Balas pesan untuk memilih dari mana mulai membersihkan.")

    return ""

    
@user_admin
@loggable
def del_message(update, context) -> str:
    if update.effective_message.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        message = update.effective_message  # type: Optional[Message]
        if user_can_delete(chat, user, context.bot.id) == False:
           message.reply_text("Anda tidak memiliki cukup hak untuk menghapus pesan!")
           return ""
        if can_delete(chat, context.bot.id):
            update.effective_message.reply_to_message.delete()
            update.effective_message.delete()
            return "<b>{}:</b>" \
                   "\n#DEL" \
                   "\n<b>Admin:</b> {}" \
                   "\nMessage deleted.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))
    else:
        update.effective_message.reply_text("Walah, ingin menghapus?")

    return ""


__help__ = """
Menghapus pesan menjadi mudah dengan perintah ini. Pembersihan bot \
pesan semua bersama-sama atau satu per satu.

*Khusus Admin:*
 × /del: Menghapus pesan yang Anda balas
 × /purge: Menghapus semua pesan antara ini dan pesan yang dibalas.
 × /purge <integer X>: Menghapus pesan yang dibalas, dan X pesan mengikutinya.
"""

__mod_name__ = "Purges"

DELETE_HANDLER = DisableAbleCommandHandler("del", del_message, filters=Filters.chat_type.groups, run_async=True)
PURGE_HANDLER = DisableAbleCommandHandler("purge", purge, filters=Filters.chat_type.groups, pass_args=True,  run_async=True)

dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)

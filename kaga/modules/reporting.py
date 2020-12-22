import html
from typing import Optional

from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    User,
)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import mention_html

from kaga import LOGGER, dispatcher
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    user_admin,
    user_not_admin,
)
from kaga.modules.log_channel import loggable
from kaga.modules.no_sql import get_collection

REPORT_GROUP = 5

USER_REPORT_SETTINGS = get_collection("USER_REPORT_SETTINGS")
CHAT_REPORT_SETTINGS = get_collection("CHAT_REPORT_SETTINGS")


@user_admin
@typing_action
def report_setting(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on", "true"):
                USER_REPORT_SETTINGS.update_one(
                    {'user_id': int(chat.id)},
                    {"$set": {'should_report': True}},
                    upsert=True)
                msg.reply_text(
                    "Aktifkan pelaporan! Anda akan diberi tahu setiap kali ada yang melaporkan sesuatu."
                )

            elif args[0] in ("no", "off", "false"):
                USER_REPORT_SETTINGS.update_one(
                    {'user_id': int(chat.id)},
                    {"$set": {'should_report': False}},
                    upsert=True)
                msg.reply_text(
                    "Nonaktifkan pelaporan! Anda tidak akan mendapatkan laporan apapun."
                )
        else:
            msg.reply_text(
                "Preferensi laporan Anda saat ini adalah: `{}`".format(
                    user_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on", "true"):
                CHAT_REPORT_SETTINGS.update_one(
                    {'chat_id': int(chat.id)},
                    {"$set": {'should_report': True}},
                    upsert=True)
                msg.reply_text(
                    "Aktifkan pelaporan! Admin yang telah mengaktifkan laporan akan diberi tahu ketika /report "
                    "atau sebut @admin."
                )

            elif args[0] in ("no", "off", "false"):
                CHAT_REPORT_SETTINGS.update_one(
                    {'chat_id': int(chat.id)},
                    {"$set": {'should_report': False}},
                    upsert=True)
                msg.reply_text(
                    "Nonaktifkan pelaporan! Tidak ada admin yang akan diberitahukan pada /report atau @admin."
                )
        else:
            msg.reply_text(
                "Pengaturan obrolan saat ini adalah: `{}`".format(
                    chat_should_report(chat.id)
                ),
                parse_mode=ParseMode.MARKDOWN,
            )


@user_not_admin
@loggable
@typing_action
def report(update, context) -> str:
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat and message.reply_to_message and chat_should_report(chat.id):
        # type: Optional[User]
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()

        isadmeme = chat.get_member(reported_user.id).status
        if isadmeme == "administrator" or isadmeme == "creator":
            return ""  # No point of reporting admins!

        if user.id == reported_user.id:
            message.reply_text("Kenapa kamu melaporkan dirimu sendiri?")
            return ""

        if reported_user.id == context.bot.id:
            message.reply_text("Saya tidak akan melaporkan diri saya sendiri!")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"Dilaporkan {mention_html(reported_user.id, reported_user.first_name)} kepada admin!"

            msg = (
                f"<b>Laporan dari: </b>{html.escape(chat.title)}\n"
                f"<b> × Laporkan oleh:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> × engguna yang dilaporkan:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> × Pesan yang dilaporkan:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">klik disini</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "💬 Pesan",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    ),
                    InlineKeyboardButton(
                        "⚽ Tendang",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "⛔️ Melarang",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        "❎ Hapus pesan",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    ),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = f"Dilaporkan {mention_html(reported_user.id, reported_user.first_name)} kepada admin!"

            msg = f'{mention_html(user.id, user.first_name)} memanggil admin masuk "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True
            keyboard = [
                InlineKeyboardButton(
                    "⚽ Tendang",
                    callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                ),
                InlineKeyboardButton(
                    "⛔️ Larang",
                    callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                ),
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if user_should_report(admin.user.id):
                try:
                    context.bot.send_message(
                        admin.user.id,
                        msg + link,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                    )
                    if should_forward:
                        message.reply_to_message.forward(admin.user.id)

                        if (
                            len(message.text.split()) > 1
                        ):  # If user is giving a reason, send his message too
                            message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    if excp.message == "Message_id_invalid":
                        pass
                    else:
                        LOGGER.exception(
                            "Exception while reporting user " + excp.message
                        )

        message.reply_to_message.reply_text(
            reported, parse_mode=ParseMode.HTML
        )
        return msg
    else:
        message.reply_text("Hei ... Apa yang harus aku laporkan!")
        return ""


def report_buttons(update, context):
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            context.bot.kickChatMember(splitter[0], splitter[2])
            context.bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("Pengguna telah berhasil ditendang")
            return ""
        except Exception as err:
            query.answer("⚠️ Gagal menendang!")
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            context.bot.kickChatMember(splitter[0], splitter[2])
            query.answer("Pengguna telah berhasil diblokir")
            return ""
        except Exception as err:
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("⚠️ Gagal Mencekal")
    elif splitter[1] == "delete":
        try:
            context.bot.deleteMessage(splitter[0], splitter[3])
            query.answer("Pesan telah dihapus!")
            return ""
        except Exception as err:
            context.bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("⚠️ Gagal menghapus pesan!")


def user_should_report(user_id: int) -> bool:
    setting = USER_REPORT_SETTINGS.find_one({'user_id': user_id})
    if not setting:
        return True
    return setting["should_report"]


def chat_should_report(chat_id: int) -> bool:
    setting = CHAT_REPORT_SETTINGS.find_one({'chat_id': chat_id})
    if not setting:
        return True
    return setting["should_report"]


def __migrate__(old_chat_id, new_chat_id):
    CHAT_REPORT_SETTINGS.update_many(
        {'chat_id': old_chat_id},
        {"$set": {'chat_id': new_chat_id}}
    )


def __chat_settings__(chat_id, user_id):
    return "Obrolan ini disiapkan untuk mengirim laporan pengguna ke admin, melalui /report atau @admin: `{}`".format(
        chat_should_report(chat_id)
    )


def __user_settings__(user_id):
    return "Anda menerima laporan dari obrolan yang Anda kelola: `{}`.\nAlihkan ini dengan /reports di PM.".format(
        user_should_report(user_id)
    )


__mod_name__ = "Reporting"

__help__ = """
Kita semua adalah orang sibuk yang tidak punya waktu untuk memantau grup kita 24/7. Tapi bagaimana kabarmu \
bereaksi jika seseorang di grup Anda melakukan spamming?

Menyajikan laporan; jika seseorang di grup Anda berpikir seseorang perlu melaporkan, mereka sekarang punya \
cara mudah untuk memanggil semua admin.

*Khusus Admin:*
 × /reports <on/off>: Ubah setelan laporan, atau lihat status saat ini.
   • Jika selesai di pm, matikan status Anda.
   • Jika dalam obrolan, matikan status obrolan itu.

Untuk melaporkan pengguna, cukup balas pesan pengguna dengan @admin atau /report. \
Pesan ini menandai semua admin obrolan; sama seperti jika mereka telah @ 'ed.
Anda HARUS membalas pesan untuk melaporkan pengguna; Anda tidak bisa begitu saja menggunakan @admin untuk menandai admin tanpa alasan!

Perhatikan bahwa perintah laporan tidak berfungsi saat admin menggunakannya; atau saat digunakan untuk melaporkan admin. Bot mengasumsikan itu \
admin tidak perlu melaporkan, atau dilaporkan!
"""
REPORT_HANDLER = CommandHandler(
    "report", report, filters=Filters.chat_type.groups, run_async=True
)
SETTING_HANDLER = CommandHandler(
    "reports", report_setting, pass_args=True, run_async=True
)
ADMIN_REPORT_HANDLER = MessageHandler(
    Filters.regex("(?i)@admin(s)?"), report, run_async=True
)
REPORT_BUTTON_HANDLER = CallbackQueryHandler(
    report_buttons, pattern=r"report_"
)

dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_BUTTON_HANDLER)

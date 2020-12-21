import html
from typing import Optional

from telegram import Chat, ChatPermissions, Message, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from kaga import LOGGER, dispatcher
from kaga.modules.helper_funcs.admin_rights import user_can_ban
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    user_admin,
)
from kaga.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from kaga.modules.helper_funcs.string_handling import extract_time
from kaga.modules.log_channel import loggable


@bot_admin
@user_admin
@loggable
@typing_action
def mute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text(
            "Anda tidak memiliki cukup hak untuk membatasi seseorang agar tidak berbicara!"
        )
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Anda harus memberi saya nama pengguna untuk membungkam, atau membalas seseorang untuk dibungkam."
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yah... Aku tidak membungkam diriku sendiri!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text(
                "Yah, saya tidak akan menghentikan admin untuk berbicara!"
            )

        elif member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(
                chat.id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            message.reply_text("👍🏻 dibisukan! 🤐")
            return (
                "<b>{}:</b>"
                "\n#MUTE"
                "\n<b>Admin:</b> {}"
                "\n<b>User:</b> {}".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(member.user.id, member.user.first_name),
                )
            )

        else:
            message.reply_text("Pengguna ini sudah dibisukan 🤐")
    else:
        message.reply_text("Pengguna ini tidak sedang mengobrol!")

    return ""


@bot_admin
@user_admin
@loggable
@typing_action
def unmute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text("Anda tidak memiliki cukup hak untuk menyuarakan orang")
        return ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Anda harus memberi saya nama pengguna untuk menyuarakan, atau membalas seseorang untuk dibungkam."
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("Pengguna ini sudah memiliki hak untuk berbicara.")
        else:
            context.bot.restrict_chat_member(
                chat.id,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_send_polls=True,
                    can_change_info=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            message.reply_text("Ya! pengguna ini dapat mulai berbicara lagi...")
            return (
                "<b>{}:</b>"
                "\n#UNMUTE"
                "\n<b>Admin:</b> {}"
                "\n<b>User:</b> {}".format(
                    html.escape(chat.title),
                    mention_html(user.id, user.first_name),
                    mention_html(member.user.id, member.user.first_name),
                )
            )
    else:
        message.reply_text(
            "Pengguna ini bahkan tidak ada dalam obrolan, mengaktifkannya tidak akan membuat mereka berbicara lebih banyak daripada mereka "
            "sudah lakukan!"
        )

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_mute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if user_can_ban(chat, user, context.bot.id) == False:
        message.reply_text(
            "Anda tidak memiliki cukup hak untuk membatasi seseorang agar tidak berbicara!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Anda sepertinya tidak mengacu pada pengguna.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Sepertinya saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_admin(chat, user_id, member):
        message.reply_text("Saya benar-benar berharap dapat menonaktifkan admin...")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya tidak akan BISUKAN diri saya sendiri, apakah Anda sudah gila?")
        return ""

    if not reason:
        message.reply_text(
            "Anda belum menentukan waktu untuk menonaktifkan pengguna ini!"
        )
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        "<b>{}:</b>"
        "\n#TEMP MUTED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>Time:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            time_val,
        )
    )
    if reason:
        log += "\n<b>Alasan:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(
                chat.id,
                user_id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            message.reply_text("diam! 🤐 Dibisukan untuk {}!".format(time_val))
            return log
        else:
            message.reply_text("Pengguna ini telah dibungkam.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                "diam! 🤐 Dibisukan untuk {}!".format(time_val), quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Sial, saya tidak bisa menonaktifkan pengguna itu.")

    return ""


__help__ = """
Beberapa orang perlu dibungkam secara publik; spammer, gangguan, atau hanya troll.

Modul ini memungkinkan Anda melakukannya dengan mudah, dengan mengekspos beberapa tindakan umum, sehingga semua orang akan melihatnya!

*Khusus Admin:*
 × /mute <userhandle>: Membungkam pengguna. Bisa juga digunakan sebagai balasan, membungkam pengguna yang dibalas.
 × /tmute <userhandle> x(m/h/d): Membungkam pengguna selama x waktu. (melalui pegangan, atau balasan). m = menit, h = jam, d = hari.
 × /unmute <userhandle>: Menampilkan pengguna. Bisa juga digunakan sebagai balasan, membungkam pengguna yang dibalas.
Contoh membisukan sementara seseorang:
`/tmute @username 2h`; Ini membungkam pengguna selama 2 jam.
"""

__mod_name__ = "Muting"

MUTE_HANDLER = CommandHandler(
    "mute", mute, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNMUTE_HANDLER = CommandHandler(
    "unmute", unmute, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
TEMPMUTE_HANDLER = CommandHandler(
    ["tmute", "tempmute"],
    temp_mute,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

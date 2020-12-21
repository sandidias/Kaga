import html

from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import mention_html

from kaga import LOGGER, dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.admin_rights import user_can_ban
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
)
from kaga.modules.helper_funcs.extraction import extract_user_and_text
from kaga.modules.helper_funcs.string_handling import extract_time
from kaga.modules.log_channel import loggable


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def ban(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki cukup hak untuk melarang pengguna!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Setidaknya merujuk beberapa pengguna untuk melarang!")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Saya tampaknya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(
            "Saya tidak akan melarang admin, jangan mengejek diri sendiri!"
        )
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya tidak akan melarang diri saya sendiri, apakah Anda gila atau tidak?")
        return ""

    log = (
        "<b>{}:</b>"
        "\n#BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        context.bot.sendMessage(
            chat.id,
            "biarkan {} berjalan di papan.".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Sial, saya tidak bisa mencekal pengguna itu.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def temp_ban(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text(
            "Anda tidak memiliki cukup hak untuk memblokir seseorang untuk sementara!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Hai kawan! setidaknya rujuk beberapa pengguna untuk dicekal...")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Sepertinya saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Wow! mari kita mulai memblokir Admin sendiri?...")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Saya tidak akan melarang diri saya sendiri, apakah Anda gila atau tidak?")
        return ""

    if not reason:
        message.reply_text(
            "Anda belum menentukan waktu untuk mencekal pengguna ini!"
        )
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = (
        "<b>{}:</b>"
        "\n#TEMP BANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)"
        "\n<b>Time:</b> {}".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
            time_val,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        message.reply_text(
            "Dilarang! Pengguna akan diblokir {}.".format(time_val)
        )
        return log

    except BadRequest as excp:
        if excp.message == "Pesan balasan tidak ditemukan":
            # Do not reply
            message.reply_text(
                "Selamat tinggal .. kita akan bertemu setelah {}.".format(time_val), quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Sial, saya tidak bisa mencekal pengguna itu.")

    return ""


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def kick(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki cukup hak untuk menendang pengguna!")
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Sepertinya saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Yeahh ... mari kita mulai menendang admin?")
        return ""

    if user_id == context.bot.id:
        message.reply_text("Yah aku tidak akan melakukan itu")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        # context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie
        # sticker
        context.bot.sendMessage(
            chat.id,
            "Sampai kita bertemu lagi {}.".format(
                mention_html(member.user.id, member.user.first_name)
            ),
            parse_mode=ParseMode.HTML,
        )
        log = (
            "<b>{}:</b>"
            "\n#KICKED"
            "\n<b>Admin:</b> {}"
            "\n<b>User:</b> {} (<code>{}</code>)".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                mention_html(member.user.id, member.user.first_name),
                member.user.id,
            )
        )
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Get Out!.")

    return ""


@bot_admin
@can_restrict
@loggable
@typing_action
def banme(update, context):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Yeahhh .. tidak akan melarang admin.")
        return

    res = update.effective_chat.kick_member(user_id)
    if res:
        update.effective_message.reply_text("Ya kau benar! Kawan..")
        log = (
            "<b>{}:</b>"
            "\n#BANME"
            "\n<b>User:</b> {}"
            "\n<b>ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                user_id,
            )
        )
        return log

    else:
        update.effective_message.reply_text("Hah? Aku tidak bisa :/")


@bot_admin
@can_restrict
@typing_action
def kickme(update, context):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(
            "Yeahhh .. tidak akan menendang admin."
        )
        return

    res = update.effective_chat.unban_member(
        user_id
    )  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Ya, Anda benar. Keluar!..")
    else:
        update.effective_message.reply_text("Hah? Aku tidak bisa :/")


@bot_admin
@can_restrict
@user_admin
@loggable
@typing_action
def unban(update, context):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    if user_can_ban(chat, user, context.bot.id) is False:
        message.reply_text(
            "Anda tidak memiliki cukup hak untuk membatalkan pelarangan orang di sini!"
        )
        return ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Sepertinya saya tidak dapat menemukan pengguna ini")
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text("Bagaimana saya akan membatalkan pelarangan diri saya sendiri jika saya tidak ada di sini...?")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "Mengapa Anda mencoba membatalkan pelarangan seseorang yang sudah ada di obrolan ini?"
        )
        return ""

    chat.unban_member(user_id)
    message.reply_text("Selesai, mereka bisa bergabung lagi!")

    log = (
        "<b>{}:</b>"
        "\n#UNBANNED"
        "\n<b>Admin:</b> {}"
        "\n<b>User:</b> {} (<code>{}</code>)".format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            mention_html(member.user.id, member.user.first_name),
            member.user.id,
        )
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = """

Beberapa orang perlu dilarang secara publik; spammer, gangguan, atau hanya troll.
Modul ini memungkinkan Anda melakukannya dengan mudah, dengan mengekspos beberapa tindakan umum, sehingga semua orang akan melihatnya!
 × /kickme: Menendang pengguna yang mengeluarkan perintah
 × /banme: Larang pengguna yang mengeluarkan perintah
*Khusus Admin:*
 × /ban <userhandle>: Larang pengguna. (melalui pegangan, atau balasan)
 × /tban <userhandle> x(m/h/d): Memblokir pengguna selama x waktu. (melalui pegangan, atau balasan). m = menit, h = jam, d = hari.
 × /unban <userhandle>: Membatalkan pemblokiran pengguna. (melalui pegangan, atau balasan)
 × /kick <userhandle>: Menendang pengguna, (melalui pegangan, atau balasan)

Contoh pelarangan sementara seseorang:
`/tban @username 2h`; ini melarang pengguna selama 2 jam.
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler(
    "ban", ban, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
TEMPBAN_HANDLER = CommandHandler(
    ["tban", "tempban"],
    temp_ban,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
KICK_HANDLER = CommandHandler(
    "kick", kick, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
UNBAN_HANDLER = CommandHandler(
    "unban", unban, pass_args=True, filters=Filters.chat_type.groups, run_async=True
)
KICKME_HANDLER = DisableAbleCommandHandler(
    "kickme", kickme, filters=Filters.chat_type.groups, run_async=True
)
BANME_HANDLER = DisableAbleCommandHandler(
    "banme", banme, filters=Filters.chat_type.groups, run_async=True
)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(BANME_HANDLER)

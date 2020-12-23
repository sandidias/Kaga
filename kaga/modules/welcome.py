import re
import time
from html import escape
from functools import partial

from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
)
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.utils.helpers import (
    mention_html,
    mention_markdown,
    escape_markdown,
)

import kaga.modules.sql.welcome_sql as sql
from kaga import (
    DEV_USERS,
    LOGGER,
    MESSAGE_DUMP,
    OWNER_ID,
    dispatcher,
    spamwtc,
)
from kaga.modules.helper_funcs.alternate import send_message, typing_action
from kaga.modules.helper_funcs.chat_status import (
    is_user_ban_protected,
    user_admin,
    can_restrict,
)
from kaga.modules.helper_funcs.misc import (
    build_keyboard,
    build_keyboard_parser,
    revert_buttons,
)
from kaga.modules.helper_funcs.msg_types import get_welcome_type
from kaga.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
    markdown_to_html,
)
from kaga.modules.log_channel import loggable
from kaga.modules.no_sql.gban_db import is_user_gbanned

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}


VERIFIED_USER_WAITLIST = {}

# do not async
def send(update, message, keyboard, backup_message):
    chat = update.effective_chat
    cleanserv = sql.clean_service(chat.id)
    reply = update.message.message_id
    # Clean service welcome
    if cleanserv:
        try:
            dispatcher.bot.delete_message(chat.id, update.message.message_id)
        except BadRequest:
            pass
        reply = False
    try:
        msg = update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            reply_to_message_id=reply,
        )
    except BadRequest as excp:
        if excp.message == "Button_url_invalid":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nCatatan: pesan saat ini memiliki url yang tidak valid "
                    "di salah satu tombolnya. Harap perbarui."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Unsupported url protocol":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nCatatan: pesan saat ini memiliki tombol yang "
                    "gunakan protokol url yang tidak didukung oleh "
                    "telegram. Harap perbarui."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
        elif excp.message == "Wrong url host":
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nCatatan: pesan saat ini memiliki beberapa url yang buruk. "
                    "Harap perbarui."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Tidak bisa mengurai! mendapat kesalahan host url yang tidak valid")
        elif excp.message == "Tidak punya hak untuk mengirim pesan":
            return
        else:
            msg = update.effective_message.reply_text(
                markdown_parser(
                    backup_message
                    + "\nCatatan: Terjadi kesalahan saat mengirim "
                    "pesan khusus. Harap perbarui."
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=reply,
            )
            LOGGER.exception()
    return msg


 # loggable need add return statement
def new_member(update, context):

    bot, job_queue = context.bot, context.job_queue

    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(
        chat.id
    )
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(user.id, chat.id)

    new_members = update.effective_message.new_chat_members
    chat_name = chat.title or chat.first or chat.username

    for new_mem in new_members:

        welcome_log = None
        res = None
        sent = None
        should_mute = True
        media_wel = False
        welcome_bool = False
        keyboard = None
        backup_message = None
        reply = None

        if spamwtc != None:
            sw = spamwtc.get_ban(new_mem.id)
            if sw:
                return

        if should_welc:

            reply = update.message.message_id
            cleanserv = sql.clean_service(chat.id)
            # Clean service welcome
            if cleanserv:
                try:
                    dispatcher.bot.delete_message(
                        chat.id, update.message.message_id
                    )
                except BadRequest:
                    pass
                reply = False

            # Give the owner a special welcome
            if new_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "Pemilik saya baru saja bergabung ke dalam obrolan.",
                    reply_to_message_id=reply,
                )
                welcome_log = (
                    f"{escape(chat.title)}\n"
                    f"#USER_JOINED\n"
                    f"Pemilik Bot baru saja bergabung dalam obrolan"
                )
                continue

            # Welcome Devs
            elif new_mem.id in DEV_USERS:
                update.effective_message.reply_text(
                    "Dev Saya Di sini, mari kita lihat apa yang terjadi sekarang 🔥",
                    reply_to_message_id=reply,
                )
                continue

            # Welcome yourself
            elif new_mem.id == context.bot.id:
                try:
                    update.effective_message.reply_text(
                        "Hai 😍 {}, saya {}! Terima kasih telah menambahkan saya ke {}".format(
                            user.first_name, context.bot.first_name, chat_name
                        ),
                        reply_to_message_id=reply,
                    )
                except BadRequest as err:
                    if err.message == "Have no rights to send a message":
                        pass
                except Unauthorized:
                    return

            else:
                buttons = sql.get_welc_buttons(chat.id)
                keyb = build_keyboard(buttons)

                if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                    media_wel = True

                first_name = (
                    new_mem.first_name or "PersonWithNoName"
                )  # edge case of empty name - occurs for some bugs.

                if cust_welcome:
                    if cust_welcome == sql.DEFAULT_WELCOME:
                        cust_welcome = sql.DEFAULT_WELCOME.format(
                            first=escape_markdown(first_name)
                        )

                    if new_mem.last_name:
                        fullname = escape_markdown(
                            f"{first_name} {new_mem.last_name}"
                        )
                    else:
                        fullname = escape_markdown(first_name)
                    count = chat.get_members_count()
                    mention = mention_markdown(
                        new_mem.id, escape_markdown(first_name)
                    )
                    if new_mem.username:
                        username = "@" + escape_markdown(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome, VALID_WELCOME_FORMATTERS
                    )
                    res = valid_format.format(
                        first=escape_markdown(first_name),
                        last=escape_markdown(new_mem.last_name or first_name),
                        fullname=escape_markdown(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=escape_markdown(chat.title),
                        id=new_mem.id,
                    )

                else:
                    res = sql.DEFAULT_WELCOME.format(
                        first=escape_markdown(first_name)
                    )
                    keyb = []

                backup_message = sql.DEFAULT_WELCOME.format(
                    first=escape_markdown(first_name)
                )
                keyboard = InlineKeyboardMarkup(keyb)

        # User exceptions from welcomemutes
        if (
            is_user_ban_protected(
                chat, new_mem.id, chat.get_member(new_mem.id)
            )
            or human_checks
        ):
            should_mute = False
        # Join welcome: soft mute
        if new_mem.is_bot:
            should_mute = False

        if user.id == new_mem.id:
            if should_mute:
                if welc_mutes == "soft":
                    bot.restrict_chat_member(
                        chat.id,
                        new_mem.id,
                        permissions=ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_invite_users=False,
                            can_pin_messages=False,
                            can_send_polls=False,
                            can_change_info=False,
                            can_add_web_page_previews=False,
                        ),
                        until_date=(int(time.time() + 24 * 60 * 60)),
                    )
                if welc_mutes == "strong":
                    welcome_bool = False
                    if not media_wel:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "media_wel": False,
                                    "status": False,
                                    "update": update,
                                    "res": res,
                                    "keyboard": keyboard,
                                    "backup_message": backup_message,
                                }
                            }
                        )
                    else:
                        VERIFIED_USER_WAITLIST.update(
                            {
                                new_mem.id: {
                                    "should_welc": should_welc,
                                    "chat_id": chat.id,
                                    "status": False,
                                    "media_wel": True,
                                    "cust_content": cust_content,
                                    "welc_type": welc_type,
                                    "res": res,
                                    "keyboard": keyboard,
                                }
                            }
                        )
                    new_join_mem = f"[{escape_markdown(new_mem.first_name)}](tg://user?id={user.id})"
                    message = msg.reply_text(
                        f"{new_join_mem}, klik tombol di bawah untuk membuktikan bahwa Anda adalah manusia.\nAnda punya 120 detik.",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                {
                                    InlineKeyboardButton(
                                        text="Saya manusia.",
                                        callback_data=f"user_join_({new_mem.id})",
                                    )
                                }
                            ]
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_to_message_id=reply,
                    )
                    try:
                        bot.restrict_chat_member(
                            chat.id,
                            new_mem.id,
                            permissions=ChatPermissions(
                                can_send_messages=False,
                                can_invite_users=False,
                                can_pin_messages=False,
                                can_send_polls=False,
                                can_change_info=False,
                                can_send_media_messages=False,
                                can_send_other_messages=False,
                                can_add_web_page_previews=False,
                            ),
                        )
                        job_queue.run_once(
                            partial(
                                check_not_bot, new_mem, chat.id, message.message_id
                            ),
                            120,
                            name="welcomemute",
                        )
                    except BadRequest as err:
                        if err.message == "Tidak cukup hak untuk membatasi/tidak membatasi anggota obrolan":
                            pass
                        else:
                            raise

        if welcome_bool:
            if media_wel:
                if ENUM_FUNC_MAP[welc_type] == dispatcher.bot.send_sticker:
                    sent = ENUM_FUNC_MAP[welc_type](
                        chat.id,
                        cust_content,
                        reply_markup=keyboard,
                        reply_to_message_id=reply,
                    )
                else:
                    sent = ENUM_FUNC_MAP[welc_type](
                        chat.id,
                        cust_content,
                        caption=res,
                        reply_markup=keyboard,
                        reply_to_message_id=reply,
                        parse_mode="markdown",
                    )
            else:
                sent = send(update, res, keyboard, backup_message)
            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

        if welcome_log:
            return welcome_log

        return (
            f"{escape(chat.title)}\n"
            f"#USER_JOINED\n"
            f"<b>User</b>: {mention_html(user.id, user.first_name)}\n"
            f"<b>ID</b>: <code>{user.id}</code>"
        )

    return ""


def check_not_bot(member, chat_id, message_id, context):
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop(member.id)
    member_status = member_dict.get("status")
    if not member_status:
        try:
            bot.unban_chat_member(chat_id, member.id)
        except:
            pass

        try:
            bot.edit_message_text(
                "**Pengguna ini Tidak Memverifikasi dalam 120 detik**\nKicked Now!!!",
                chat_id=chat_id,
                message_id=message_id,
                parse_mode=ParseMode.MARKDOWN,
            )
        except:
            pass


def left_member(update, context):
    chat = update.effective_chat
    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)
    cust_goodbye = markdown_to_html(cust_goodbye)
    if should_goodbye:
        reply = update.message.message_id
        cleanserv = sql.clean_service(chat.id)
        # Clean service welcome
        if cleanserv:
            try:
                dispatcher.bot.delete_message(
                    chat.id, update.message.message_id
                )
            except Unauthorized:
                return
            except BadRequest:
                pass
            reply = False

        left_mem = update.effective_message.left_chat_member
        if left_mem:

            # Ignore gbanned users
            if is_user_gbanned(left_mem.id):
                return

            # Ignore spamwatch banned users
            try:
                sw = spamwtc.get_ban(int(left_mem.id))
                if sw:
                    return
            except BaseException:
                pass

            # Ignore bot being kicked
            if left_mem.id == context.bot.id:
                return

            # Give the owner a special goodbye
            if left_mem.id == OWNER_ID:
                update.effective_message.reply_text(
                    "Selamat jalan, masterku", reply_to_message_id=reply
                )
                return

            # if media goodbye, use appropriate function for it
            if (
                goodbye_type != sql.Types.TEXT
                and goodbye_type != sql.Types.BUTTON_TEXT
            ):
                ENUM_FUNC_MAP[goodbye_type](chat.id, cust_goodbye)
                return

            first_name = (
                left_mem.first_name or "PersonWithNoName"
            )  # edge case of empty name - occurs for some bugs.
            if cust_goodbye:
                if left_mem.last_name:
                    fullname = "{} {}".format(first_name, left_mem.last_name)
                else:
                    fullname = first_name
                count = chat.get_members_count()
                mention = mention_html(left_mem.id, first_name)
                if left_mem.username:
                    username = "@" + escape(left_mem.username)
                else:
                    username = mention

                valid_format = escape_invalid_curly_brackets(
                    cust_goodbye, VALID_WELCOME_FORMATTERS
                )
                res = valid_format.format(
                    first=escape(first_name),
                    last=escape(left_mem.last_name or first_name),
                    fullname=escape(fullname),
                    username=username,
                    mention=mention,
                    count=count,
                    chatname=escape(chat.title),
                    id=left_mem.id,
                )
                buttons = sql.get_gdbye_buttons(chat.id)
                keyb = build_keyboard(buttons)

            else:
                res = sql.DEFAULT_GOODBYE
                keyb = []

            keyboard = InlineKeyboardMarkup(keyb)

            send(update, res, keyboard, sql.DEFAULT_GOODBYE)


@user_admin
@typing_action
def welcome(update, context):
    args = context.args
    chat = update.effective_chat
    # if no args, show current replies.
    if not args or args[0].lower() == "noformat":
        noformat = True
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        update.effective_message.reply_text(
            f"This chat has it's welcome setting set to: `{pref}`.\n"
            f"*The welcome message (not filling the {{}}) is:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if welcome_type == sql.Types.BUTTON_TEXT or welcome_type == sql.Types.TEXT:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)
        else:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id, cust_content, caption=welcome_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                ENUM_FUNC_MAP[welcome_type](
                    chat.id,
                    cust_content,
                    caption=welcome_m,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "Okay! I'll greet members when they join.")

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "I'll go loaf around and not welcome anyone then.")

        else:
            update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!")



@user_admin
@typing_action
def goodbye(update, context):
    chat = update.effective_chat
    args = context.args

    if len(args) == 0 or args[0] == "noformat":
        noformat = args and args[0] == "noformat"
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        update.effective_message.reply_text(
            "Obrolan ini memiliki setelan selamat tinggal yang disetel ke: `{}`.\n*Pesan selamat tinggal "
            "(tidak mengisi {{}}):*".format(pref),
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard(buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

        else:
            if noformat:
                ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

            else:
                ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.MARKDOWN
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            update.effective_message.reply_text(
                "Saya akan menyesal ketika orang pergi!"
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            update.effective_message.reply_text(
                "Mereka pergi, mereka mati bagiku."
            )

        else:
            # idek what you're writing, say yes or no
            update.effective_message.reply_text(
                "Saya hanya mengerti 'on/yes' atau 'off/no' saja!"
            )


@user_admin
@loggable
@typing_action
def set_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("Anda tidak menentukan harus membalas dengan apa!")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    msg.reply_text("Berhasil menyetel pesan selamat datang kustom!")

    return (
        "<b>{}:</b>"
        "\n#SET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nAtur pesan selamat datang.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def reset_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Berhasil menyetel ulang pesan selamat datang ke default!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_WELCOME"
        "\n<b>Admin:</b> {}"
        "\nSetel ulang pesan selamat datang ke default.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def set_goodbye(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = get_welcome_type(msg)

    if data_type is None:
        msg.reply_text("Anda tidak menentukan harus membalas dengan apa!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    msg.reply_text("Berhasil menyetel pesan selamat tinggal kustom!")
    return (
        "<b>{}:</b>"
        "\n#SET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nAtur pesan selamat tinggal.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@loggable
@typing_action
def reset_goodbye(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    update.effective_message.reply_text(
        "Berhasil mengatur ulang pesan selamat tinggal ke default!"
    )
    return (
        "<b>{}:</b>"
        "\n#RESET_GOODBYE"
        "\n<b>Admin:</b> {}"
        "\nSetel ulang pesan selamat tinggal.".format(
            escape(chat.title), mention_html(user.id, user.first_name)
        )
    )


@user_admin
@can_restrict
@loggable
@typing_action
def welcomemute(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            msg.reply_text("Saya tidak akan lagi menonaktifkan orang saat bergabung!")
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nTelah mengaktifkan bisukan selamat datang ke <b>OFF</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        elif args[0].lower() in ("soft"):
            sql.set_welcome_mutes(chat.id, "soft")
            msg.reply_text(
                "Saya akan membatasi izin pengguna untuk mengirim media selama 24 jam"
            )
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nTelah mengaktifkan bisukan selamat datang ke <b>SOFT</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        elif args[0].lower() in ("strong"):
            sql.set_welcome_mutes(chat.id, "strong")
            msg.reply_text(
                "Sekarang saya akan menonaktifkan orang saat mereka bergabung dan"
                " klik tombol yang akan disuarakan."
            )
            return (
                "<b>{}:</b>"
                "\n#WELCOME_MUTE"
                "\n<b>• Admin:</b> {}"
                "\nTelah mengaktifkan bisukan selamat datang ke <b>STRONG</b>.".format(
                    escape(chat.title), mention_html(user.id, user.first_name)
                )
            )
        else:
            msg.reply_text(
                "Silahkan masukkan `off`/`on`/`soft`/`strong`!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        reply = "\n Beri aku pengaturan! Pilih salah satu: `off`/`no` atau `soft` atau `strong` saja! \nPengaturan saat ini: `{}`"
        msg.reply_text(
            reply.format(curr_setting), parse_mode=ParseMode.MARKDOWN
        )
        return ""


@user_admin
@loggable
@typing_action
def clean_welcome(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        if clean_pref:
            update.effective_message.reply_text(
                "Saya harus menghapus pesan selamat datang yang berumur maksimal dua hari."
            )
        else:
            update.effective_message.reply_text(
                "Saat ini saya tidak menghapus pesan selamat datang yang lama!"
            )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        update.effective_message.reply_text(
            "Saya akan mencoba menghapus pesan selamat datang yang lama!"
        )
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>ON</code>.".format(
                escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        update.effective_message.reply_text(
            "Saya tidak akan menghapus pesan selamat datang yang lama."
        )
        return (
            "<b>{}:</b>"
            "\n#CLEAN_WELCOME"
            "\n<b>Admin:</b> {}"
            "\nHas toggled clean welcomes to <code>OFF</code>.".format(
                escape(chat.title), mention_html(user.id, user.first_name)
            )
        )
    else:
        # idek what you're writing, say yes or no
        update.effective_message.reply_text(
            "Saya hanya mengerti 'on/yes' atau 'off/no' saja!"
        )
        return ""


@user_admin
@typing_action
def cleanservice(update, context):
    chat = update.effective_chat
    args = context.args
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no" or var == "off":
                sql.set_clean_service(chat.id, False)
                update.effective_message.reply_text(
                    "Matikan pembersihan pesan layanan."
                )
            elif var == "yes" or var == "on":
                sql.set_clean_service(chat.id, True)
                update.effective_message.reply_text(
                    "Mengaktifkan pembersihan pesan layanan!"
                )
            else:
                update.effective_message.reply_text(
                    "Opsi tidak valid", parse_mode=ParseMode.MARKDOWN
                )
        else:
            update.effective_message.reply_text(
                "Penggunaan on/yes atau off/no", parse_mode=ParseMode.MARKDOWN
            )
    else:
        curr = sql.clean_service(chat.id)
        if curr:
            update.effective_message.reply_text(
                "Selamat datang layanan bersih : on", parse_mode=ParseMode.MARKDOWN
            )
        else:
            update.effective_message.reply_text(
                "Selamat datang layanan bersih : off", parse_mode=ParseMode.MARKDOWN
            )


def user_button(update, context):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    join_user = int(match.group(1))

    if join_user == user.id:
        member_dict = VERIFIED_USER_WAITLIST.pop(user.id)
        member_dict["status"] = True
        VERIFIED_USER_WAITLIST.update({user.id: member_dict})
        query.answer(text="Yeet! Anda seorang manusia, disuarakan!")
        bot.restrict_chat_member(
            chat.id,
            user.id,
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
        try:
            bot.deleteMessage(chat.id, message.message_id)
        except BadRequest:
            pass
        if member_dict["should_welc"]:
            if member_dict["media_wel"]:
                sent = ENUM_FUNC_MAP[member_dict["welc_type"]](
                    member_dict["chat_id"],
                    member_dict["cust_content"],
                    caption=member_dict["res"],
                    reply_markup=member_dict["keyboard"],
                    parse_mode="markdown",
                )
            else:
                sent = send(
                    member_dict["update"],
                    member_dict["res"],
                    member_dict["keyboard"],
                    member_dict["backup_message"],
                )

            prev_welc = sql.get_clean_pref(chat.id)
            if prev_welc:
                try:
                    bot.delete_message(chat.id, prev_welc)
                except BadRequest:
                    pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

    else:
        query.answer(text="Anda tidak diizinkan melakukan ini!")


WELC_HELP_TXT = (
    "Pesan selamat datang/selamat tinggal grup Anda dapat dipersonalisasi dengan berbagai cara. Jika Anda menginginkan pesan"
    " untuk dibuat satu per satu, seperti pesan selamat datang default, Anda dapat menggunakan variabel *ini*:\n"
    " - `{{first}}`: ini mewakili nama *depan* pengguna\n"
    " - `{{last}}`: ini mewakili nama *terakhir* pengguna. Default-nya adalah *nama depan* jika pengguna tidak memiliki "
    "last name.\n"
    " - `{{fullname}}`: ini mewakili nama *lengkap* pengguna. Default-nya adalah *nama depan* jika pengguna tidak memiliki "
    "nama terakhir.\n"
    " - `{{username}}`: ini mewakili *username* pengguna. Secara default, *sebutan* pengguna "
    "nama depan jika tidak memiliki nama pengguna.\n"
    " - `{{mention}}`: ini hanya *menyebutkan* pengguna - memberi tag mereka dengan nama depan mereka.\n"
    " - `{{id}}`: ini mewakili *id* pengguna\n"
    " - `{{count}}`: ini mewakili *nomor anggota* pengguna.\n"
    " - `{{chatname}}`: ini mewakili *nama obrolan saat ini*.\n"
    "\nSetiap variabel HARUS diapit oleh `{{}}` untuk diganti.\n"
    "Pesan selamat datang juga mendukung markdown, sehingga Anda dapat membuat elemen apa pun seperti bold/italic/code/links. "
    "Tombol juga didukung, sehingga Anda dapat membuat sambutan Anda terlihat luar biasa dengan beberapa tombol intro yang "
    "bagus.\n"
    "Untuk membuat tombol yang menautkan ke aturan Anda, gunakan ini: `[Rules](buttonurl://t.me/{}?start=group_id)`. "
    "Cukup ganti `group_id` dengan id grup Anda, yang dapat diperoleh melalui /id, dan Anda siap melakukannya. "
    "Perhatikan bahwa id grup biasanya diawali dengan tanda `-`; ini diperlukan, jadi tolong jangan "
    "hapus itu.\n"
    "Jika Anda merasa senang, Anda bahkan dapat mengatur gambar /gif/video/pesan suara sebagai pesan selamat datang "
    "lalu membalas media yang diinginkan, dan menelepon /setwelcome.".format(
        dispatcher.bot.username
    )
)


@user_admin
@typing_action
def welcome_help(update, context):
    update.effective_message.reply_text(
        WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN
    )


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    clean_welc_pref = sql.get_clean_pref(chat_id)
    welc_mutes_pref = sql.get_welc_mutes_pref(chat_id)
    return (
        "Obrolan ini memiliki preferensi selamat datang yang disetel ke `{}`.\n"
        "Ini preferensi selamat tinggal `{}`. \n\n"
        "*Preferensi layanan:*\n"
        "\nSelamat datang dibersihkan: `{}`"
        "\nSelamat datang dibisukan: `{}`".format(
            welcome_pref, goodbye_pref, clean_welc_pref, welc_mutes_pref
        )
    )


__help__ = """
{}

*Khusus Admin:*
 × /welcome <on/off>: aktifkan/nonaktifkan pesan selamat datang.
 × /welcome: Menunjukkan pengaturan selamat datang saat ini.
 × /welcome noformat: Menunjukkan pengaturan selamat datang saat ini, tanpa pemformatan - berguna untuk mendaur ulang pesan selamat datang Anda!
 × /goodbye -> Penggunaan dan argumen yang sama seperti /welcome.
 × /setwelcome <sometext>: Setel pesan selamat datang khusus. Jika digunakan membalas media, gunakan media itu.
 × /setgoodbye <sometext>: Setel pesan selamat tinggal khusus. Jika digunakan membalas media, gunakan media itu.
 × /resetwelcome: Menyetel ulang ke pesan selamat datang default.
 × /resetgoodbye: Menyetel ulang ke pesan selamat tinggal default.
 × /cleanwelcome <on/off>: Pada anggota baru, coba hapus pesan selamat datang sebelumnya untuk menghindari spamming pada obrolan.
 × /cleanservice <on/off>: Bersihkan pesan layanan 'pengguna bergabung' secara otomatis.
 × /welcomemute <off/soft/strong>: Semua pengguna yang bergabung, dibungkam; sebuah tombol akan ditambahkan ke pesan selamat datang bagi mereka untuk menyuarakan dirinya sendiri. \
Ini membuktikan mereka bukan bot! lunak - membatasi kemampuan pengguna untuk mengirim media selama 24 jam. kuat - bisu saat bergabung sampai mereka membuktikan bahwa mereka bukan bot.
 × /welcomehelp: Lihat lebih banyak informasi pemformatan untuk pesan selamat datang / selamat tinggal khusus.

Tombol dalam pesan selamat datang menjadi mudah, semua orang tidak suka URL terlihat. Dengan tautan tombol, Anda dapat membuat obrolan Anda lebih terlihat \
rapi dan sederhana.

Contoh penggunaan tombol:
Anda dapat membuat tombol menggunakan `[Tombol Teks](buttonurl://example.com)`.

Jika Anda ingin menambahkan lebih dari 1 tombol, cukup lakukan hal berikut:
`[Tombol 1](buttonurl://example.com)`
`[Tombol 2](buttonurl://github.com:same)`
`[Tombol 3](buttonurl://google.com)`

Ujung tautan `:sama` menggabungkan 2 tombol pada baris yang sama dengan 1 tombol, sehingga tombol ke-3 akan dipisahkan \
dari baris yang sama.

Tip: Tombol harus ditempatkan di akhir pesan selamat datang.
""".format(
    WELC_HELP_TXT
)

__mod_name__ = "Greetings"

NEW_MEM_HANDLER = MessageHandler(
    Filters.status_update.new_chat_members, new_member, run_async=True
)
LEFT_MEM_HANDLER = MessageHandler(
    Filters.status_update.left_chat_member, left_member, run_async=True
)
WELC_PREF_HANDLER = CommandHandler(
    "welcome",
    welcome,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
GOODBYE_PREF_HANDLER = CommandHandler(
    "goodbye",
    goodbye,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
SET_WELCOME = CommandHandler(
    "setwelcome", set_welcome, filters=Filters.chat_type.groups, run_async=True
)
SET_GOODBYE = CommandHandler(
    "setgoodbye", set_goodbye, filters=Filters.chat_type.groups, run_async=True
)
RESET_WELCOME = CommandHandler(
    "resetwelcome",
    reset_welcome,
    filters=Filters.chat_type.groups,
    run_async=True,
)
RESET_GOODBYE = CommandHandler(
    "resetgoodbye",
    reset_goodbye,
    filters=Filters.chat_type.groups,
    run_async=True,
)
CLEAN_WELCOME = CommandHandler(
    "cleanwelcome",
    clean_welcome,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
WELCOMEMUTE_HANDLER = CommandHandler(
    "welcomemute",
    welcomemute,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
CLEAN_SERVICE_HANDLER = CommandHandler(
    "cleanservice",
    cleanservice,
    pass_args=True,
    filters=Filters.chat_type.groups,
    run_async=True,
)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help, run_async=True)
BUTTON_VERIFY_HANDLER = CallbackQueryHandler(
    user_button, pattern=r"user_join_", run_async=True
)

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(WELCOMEMUTE_HANDLER)
dispatcher.add_handler(CLEAN_SERVICE_HANDLER)
dispatcher.add_handler(BUTTON_VERIFY_HANDLER)
dispatcher.add_handler(WELCOME_HELP)

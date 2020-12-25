import html, time
import re
from typing import Optional, List

import kaga.modules.helper_funcs.cas_api as cas

from telegram import Message, Chat, Update, Bot, User, CallbackQuery, ChatMember, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from telegram.error import BadRequest
from kaga import dispatcher, OWNER_ID, DEV_USERS, LOGGER
from telegram.ext import MessageHandler, Filters, CommandHandler, CallbackContext
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown

import kaga.modules.sql.welcome_sql as sql
import kaga.modules.sql.global_bans_sql as gbansql
import kaga.modules.sql.users_sql as userssql

from kaga import dispatcher, OWNER_ID, LOGGER
from kaga.modules.helper_funcs.chat_status import user_admin, can_delete, is_user_ban_protected
from kaga.modules.helper_funcs.misc import build_keyboard, revert_buttons, send_to_list
from kaga.modules.helper_funcs.msg_types import get_welcome_type
from kaga.modules.helper_funcs.extraction import extract_user
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.helper_funcs.string_handling import markdown_parser, escape_invalid_curly_brackets
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.log_channel import loggable


@typing_action
@user_admin
def setcas(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg)!= 2:
        msg.reply_text("Argumen tidak valid!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_status(chat.id, True)
        msg.reply_text("Konfigurasi berhasil diperbarui.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_status(chat.id, False)
        msg.reply_text("Konfigurasi berhasil diperbarui.")
        return
    else:
        msg.reply_text("Status tidak valid untuk disetel!") #on or off ffs
        return

@typing_action
@user_admin
def setban(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg)!= 2:
        msg.reply_text("Argumen tidak valid!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_autoban(chat.id, True)
        msg.reply_text("Konfigurasi berhasil diperbarui.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_autoban(chat.id, False)
        msg.reply_text("Konfigurasi berhasil diperbarui.")
        return
    else:
        msg.reply_text("Definisi kendaraan otomatis tidak valid untuk disetel!") #on or off ffs
        return

@typing_action
@user_admin
def get_current_setting(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    stats = sql.get_cas_status(chat.id)
    autoban = sql.get_cas_autoban(chat.id)
    rtext = "<b>CAS Preferences</b>\n\nCAS Checking: {}\nAutoban: {}".format(stats, autoban)
    msg.reply_text(rtext, parse_mode=ParseMode.HTML)
    return

@typing_action
@user_admin
def getTimeSetting(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    timeSetting = sql.getKickTime(chat.id)
    text = "Grup ini secara otomatis akan mengeluarkan orang " + str(timeSetting) + " seconds."
    msg.reply_text(text)
    return

@typing_action
@user_admin
def setTimeSetting(update, context) -> str:
    args = context.args
    chat = update.effective_chat
    msg = update.effective_message
    if (not args) or len(args) != 1 or (not args[0].isdigit()):
        msg.reply_text("Beri saya nilai yang valid untuk ditetapkan! 30 hingga 900 detik")
        return
    value = int(args[0])
    if value < 30 or value > 900:
        msg.reply_text("Nilai tidak valid! Harap gunakan nilai antara 30 dan 900 detik (15 menit)")
        return
    sql.setKickTime(str(chat.id), value)
    msg.reply_text("Berhasil! Pengguna yang tidak mengonfirmasi akan ditendang setelahnya " + str(value) + " seconds.")
    return

@typing_action
def get_version(update, context):
    msg = update.effective_message
    ver = cas.vercheck()
    msg.reply_text("CAS API version: "+ver)
    return

@typing_action
def caschecker(update, context) -> str:
    #/info logic
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    if user_id and int(user_id) != 777000:
        user = bot.get_chat(user_id)
    elif user_id and int(user_id) == 777000:
        msg.reply_text("Ini Telegram. Kecuali Anda memasukkan ID akun yang dipesan ini secara manual, kemungkinan besar itu adalah siaran dari saluran tertaut.")
        return
    elif not msg.reply_to_message and not args:
        user = msg.from_user
    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        msg.reply_text("Saya tidak dapat mengekstrak pengguna dari ini.")
        return
    else:
        return

    text = "<b>CAS Check</b>:" \
           "\nID: <code>{}</code>" \
           "\nFirst Name: {}".format(user.id, html.escape(user.first_name))
    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))
    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))
    text += "\n\nCAS Banned: "
    result = cas.banchecker(user.id)
    text += str(result)
    if result:
        parsing = cas.offenses(user.id)
        if parsing:
            text += "\nTotal of Offenses: "
            text += str(parsing)
        parsing = cas.timeadded(user.id)
        if parsing:
            parseArray=str(parsing).split(", ")
            text += "\nDay added: "
            text += str(parseArray[1])
            text += "\nTime added: "
            text += str(parseArray[0])
            text += "\n\nAll times are in UTC"
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)



#this sends direct request to combot server. Will return true if user is banned, false if
#id invalid or user not banned
@typing_action
def casquery(update, context) -> str:
    bot = context.bot
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    try:
        user_id = msg.text.split(' ')[1]
    except:
        msg.reply_text("Terjadi masalah saat mengurai kueri.")
        return
    text = "Permintaan Anda kembali: "
    result = cas.banchecker(user_id)
    text += str(result)
    msg.reply_text(text)        


@typing_action
def gbanChat(update, context) -> str:
    bot = context.bot
    args = context.args
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            send_to_list(bot, SUDO_USERS,
                     "<b>Chat Blacklist</b>" \
                     "\n#BLCHAT" \
                     "\n<b>Status:</b> <code>Blacklisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), html=True)
            sql.blacklistChat(chat_id)
            update.effective_message.reply_text("Obrolan berhasil masuk daftar hitam!")
            try:
                bot.leave_chat(int(chat_id))
            except:
                pass
        except:
            update.effective_message.reply_text("Terjadi kesalahan saat memasukkan obrolan ke daftar hitam!")
    else:
        update.effective_message.reply_text("Beri saya id obrolan yang valid!") 

@typing_action
def ungbanChat(update, context) -> str:
    bot = context.bot
    args = context.args
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            send_to_list(bot, SUDO_USERS,
                     "<b>Regression of Chat Blacklist</b>" \
                     "\n#UNBLCHAT" \
                     "\n<b>Status:</b> <code>Un-Blacklisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), html=True)
            sql.unblacklistChat(chat_id)
            update.effective_message.reply_text("Obrolan berhasil dihapus dari daftar hitam!")
        except:
            update.effective_message.reply_text("Terjadi kesalahan saat membatalkan daftar obrolan!")
    else:
        update.effective_message.reply_text("Beri saya id obrolan yang valid!") 

@typing_action
@user_admin
def setDefense(update, context) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    msg = update.effective_message
    if len(args)!=1:
        msg.reply_text("Argumen tidak valid!")
        return
    param = args[0]
    if param == "on" or param == "true":
        sql.setDefenseStatus(chat.id, True)
        msg.reply_text("Mode pertahanan telah diaktifkan, grup ini sedang diserang. Setiap pengguna yang sekarang bergabung akan otomatis ditendang.")
        return
    elif param == "off" or param == "false":
        sql.setDefenseStatus(chat.id, False)
        msg.reply_text("Mode pertahanan telah dimatikan, grup tidak lagi diserang.")
        return
    else:
        msg.reply_text("Status tidak valid untuk disetel!") #on or off ffs
        return 

@typing_action
@user_admin
def getDefense(update, context) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    msg = update.effective_message
    stat = sql.getDefenseStatus(chat.id)
    text = "<b>Defense Status</b>\n\nCurrently, this group has the defense setting set to: <b>{}</b>".format(stat)
    msg.reply_text(text, parse_mode=ParseMode.HTML)

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
ABOUT_CAS = "<b>Combot Anti-Spam System (CAS)</b>" \
            "\n\nCAS adalah singkatan dari Combot Anti-Spam, sistem otomatis yang dirancang untuk mendeteksi pengirim spam dalam grup Telegram."\
            "\nJika pengguna dengan catatan spam terhubung ke grup yang diamankan oleh CAS, sistem CAS akan segera melarang pengguna tersebut."\
            "\n\n<i>Larangan CAS bersifat permanen, tidak dapat dinegosiasikan, dan tidak dapat dihapus oleh manajer komunitas Combot.</i>" \
            "\n<i>Jika larangan CAS ditetapkan telah dikeluarkan dengan tidak benar, maka secara otomatis akan dihapus.</i>"

@typing_action
def about_cas(update, context) -> str:
    bot = context.bot
    args = context.args
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]

    if chat.type == "private":
        update.effective_message.reply_text(ABOUT_CAS, parse_mode=ParseMode.HTML)

    else:
        try:
            bot.send_message(user.id, ABOUT_CAS, parse_mode=ParseMode.HTML)

            update.effective_message.reply_text("Anda akan menemukan di PM info lebih lanjut tentang CAS")
        except Unauthorized:
            update.effective_message.reply_text("Hubungi saya di PM dulu untuk mendapatkan informasi CAS.")


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

def __chat_settings__(chat_id, user_id):
    welcome_pref, _, _ = sql.get_welc_pref(chat_id)
    goodbye_pref, _, _ = sql.get_gdbye_pref(chat_id)
    return "This chat has it's welcome preference set to `{}`.\n" \
           "It's goodbye preference is `{}`.".format(welcome_pref, goodbye_pref)

__help__ = """
{}
Perintah:
 - /casver: Mengembalikan versi API yang saat ini dijalankan bot
 - /cascheck: Memeriksa Anda atau pengguna lain untuk CAS BAN
*Khusus Admin:*
 - /setcas <on/off/true/false>: Mengaktifkan/menonaktifkan Pengecekan CAS pada sambutan
 - /getcas: Mendapat pengaturan CAS saat ini
 - /setban <on/off/true/false>: Mengaktifkan/menonaktifkan autoban pada CAS yang melarang pengguna terdeteksi.
 - /setdefense <on/off/true/false>: Mengaktifkan mode pertahanan, akan menendang pengguna baru secara otomatis.
 - /getdefense:mendapatkan pengaturan pertahanan saat ini
 - /kicktime: mendapatkan pengaturan waktu tendangan otomatis
 - /setkicktime: menetapkan nilai waktu tendangan otomatis baru (antara 30 dan 900 detik)
 - /cas: Info tentang CAS. (Apa itu CAS?)
"""

__mod_name__ = "CAS"

SETCAS_HANDLER = CommandHandler("setcas", setcas, filters=Filters.group, run_async=True)
GETCAS_HANDLER = CommandHandler("getcas", get_current_setting, filters=Filters.group, run_async=True)
GETVER_HANDLER = DisableAbleCommandHandler("casver", get_version, run_async=True)
CASCHECK_HANDLER = CommandHandler("cascheck", caschecker, pass_args=True, run_async=True)
CASQUERY_HANDLER = CommandHandler("casquery", casquery, pass_args=True ,filters=CustomFilters.sudo_filter, run_async=True)
SETBAN_HANDLER = CommandHandler("setban", setban, filters=Filters.group, run_async=True)
GBANCHAT_HANDLER = CommandHandler("blchat", gbanChat, pass_args=True, filters=CustomFilters.sudo_filter, run_async=True)
UNGBANCHAT_HANDLER = CommandHandler("unblchat", ungbanChat, pass_args=True, filters=CustomFilters.sudo_filter, run_async=True)
DEFENSE_HANDLER = CommandHandler("setdefense", setDefense, pass_args=True, run_async=True)
GETDEF_HANDLER = CommandHandler("defense", getDefense, run_async=True)
GETTIMESET_HANDLER = CommandHandler("kicktime", getTimeSetting, run_async=True)
SETTIMER_HANDLER = CommandHandler("setkicktime", setTimeSetting, pass_args=True, run_async=True)
ABOUT_CAS_HANDLER = CommandHandler("cas",  about_cas, run_async=True)





dispatcher.add_handler(SETCAS_HANDLER)
dispatcher.add_handler(GETCAS_HANDLER)
dispatcher.add_handler(GETVER_HANDLER)
dispatcher.add_handler(CASCHECK_HANDLER)
dispatcher.add_handler(CASQUERY_HANDLER)
dispatcher.add_handler(SETBAN_HANDLER)
dispatcher.add_handler(GBANCHAT_HANDLER)
dispatcher.add_handler(UNGBANCHAT_HANDLER)
dispatcher.add_handler(DEFENSE_HANDLER)
dispatcher.add_handler(GETDEF_HANDLER)
dispatcher.add_handler(GETTIMESET_HANDLER)
dispatcher.add_handler(SETTIMER_HANDLER)
dispatcher.add_handler(ABOUT_CAS_HANDLER)

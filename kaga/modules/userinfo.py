import html
from typing import Optional

from telegram import MAX_MESSAGE_LENGTH, Message, ParseMode, User
from telegram.utils.helpers import escape_markdown

from kaga import DEV_USERS, dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.no_sql import get_collection
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.extraction import extract_user


USER_INFO = get_collection("USER_INFO")
USER_BIO = get_collection("USER_BIO")


@typing_action
def about_me(update, context):
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    user_id = extract_user(message, args)

    if user_id:
        user = context.bot.get_chat(user_id)
    else:
        user = message.from_user

    info = USER_INFO.find_one({'_id': user.id})["info"]

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            username + "Informasi tentang dia saat ini tidak tersedia !"
        )
    else:
        update.effective_message.reply_text(
            "Anda belum menambahkan informasi apa pun tentang diri Anda !"
        )


@typing_action
def set_about_me(update, context):
    message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    if user_id == 1087968824:
        message.reply_text(
            "Anda tidak dapat mengatur bio Anda sendiri saat Anda berada dalam mode admin anonim!"
        )
        return

    text = message.text
    info = text.split(
        None, 1
    )  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            USER_INFO.update_one(
                {'_id': user_id},
                {"$set": {'info': info[1]}},
                upsert=True)
            message.reply_text("Biografi Anda berhasil disimpan")
        else:
            message.reply_text(
                " Tentang Anda {} Untuk dibatasi pada huruf ".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])
                )
            )


@typing_action
def about_bio(update, context):
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id = extract_user(message, args)
    if user_id:
        user = context.bot.get_chat(user_id)
    else:
        user = message.from_user

    info = USER_BIO.find_one({'_id': user.id})

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info["bio"])),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            "{} Belum ada detail tentang dia yang disimpan !".format(username)
        )
    else:
        update.effective_message.reply_text(
            " Biografi Anda tentang Anda telah disimpan !"
        )


@typing_action
def set_about_bio(update, context):
    message = update.effective_message  # type: Optional[Message]
    sender = update.effective_user  # type: Optional[User]
    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id == message.from_user.id:
            message.reply_text(
                "Apakah Anda ingin mengubah milik Anda sendiri ... ?? Itu dia."
            )
            return
        elif user_id == context.bot.id and sender.id not in DEV_USERS:
            message.reply_text("Hanya PENGGUNA DEV yang dapat mengubah informasi saya.")
            return
        elif user_id == 1087968824:
            message.reply_text("Anda tidak dapat mengatur bio pengguna anonim!")
            return

        text = message.text
        # use python's maxsplit to only remove the cmd, hence keeping newlines.
        bio = text.split(None, 1)
        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                USER_BIO.update_one(
                    {'_id': user_id},
                    {"$set": {'bio': bio[1]}},
                    upsert=True)
                message.reply_text(
                    "{} bio berhasil disimpan!".format(
                        repl_message.from_user.first_name
                    )
                )
            else:
                message.reply_text(
                    "Tentang Anda {} Harus tetap berpegang pada surat! Jumlah karakter yang baru saja Anda coba {}.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])
                    )
                )
    else:
        message.reply_text(
            " Bio-nya hanya bisa disimpan jika seseorang mengirim pesan lalu dibalas"
        )


def __user_info__(user_id):
    bdata = USER_BIO.find_one({'_id': user_id})
    if bdata:
        bio = html.escape(bdata["bio"])
    idata = USER_INFO.find_one({'_id': user_id})
    if idata:
        me = html.escape(idata["info"])

    if bdata and idata:
        return "<b>Tentang pengguna:</b>\n{me}\n\n<b>Apa yang dikatakan orang lain:</b>\n{bio}".format(
            me=me, bio=bio
        )
    elif bdata:
        return "<b>Apa yang dikatakan orang lain:</b>\n{}\n".format(bio)
    elif idata:
        return "<b>Tentang Pengguna:</b>\n{}".format(me)
    else:
        return ""


__help__ = """
Menulis sesuatu tentang diri Anda itu keren, entah untuk membuat orang tahu tentang diri Anda atau \
mempromosikan profil Anda.

Semua bio ditampilkan pada perintah /info.

 × /setbio <text>: Saat membalas, akan menyimpan bio pengguna lain
 × /bio: Akan mendapatkan bio Anda atau pengguna lain. Ini tidak dapat diatur sendiri.
 × /setme <text>: Akan mengatur info Anda
 × /me: Akan mendapatkan info Anda atau pengguna lain

Contoh pengaturan bio untuk diri Anda sendiri:
`/setme Saya bekerja untuk Telegram`; Bio diatur untuk diri Anda sendiri.

Contoh penulisan biodata orang lain:
Balas pesan pengguna: `/setbio Dia orang yang sangat keren`.

*Perhatian:* Jangan gunakan /setbio untuk melawan diri sendiri!
"""

__mod_name__ = "Bios/Abouts"

SET_BIO_HANDLER = DisableAbleCommandHandler(
    "setbio", set_about_bio, run_async=True
)
GET_BIO_HANDLER = DisableAbleCommandHandler(
    "bio", about_bio, pass_args=True, run_async=True
)

SET_ABOUT_HANDLER = DisableAbleCommandHandler(
    "setme", set_about_me, run_async=True
)
GET_ABOUT_HANDLER = DisableAbleCommandHandler(
    "me", about_me, pass_args=True, run_async=True
)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

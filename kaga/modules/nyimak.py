import random, html

from kaga import dispatcher
from kaga.modules.disable import (DisableAbleCommandHandler,
                                          DisableAbleMessageHandler)
from kaga.modules.sql import nyimak_sql as sql
from kaga.modules.users import get_user_id
from kaga.modules.helper_funcs.alternate import typing_action
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler

NYIMAK_GROUP = 7
NYIMAK_REPLY_GROUP = 8


@typing_action
def nyimak(update, context):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user

    if not user:  # ignore channels
        return

    if user.id in [777000, 1087968824]:
        return

    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nAlasan Anda akan disingkat menjadi 100 karakter."
    else:
        reason = ""

    sql.set_nyimak(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text("{} sekarang menyimak di dalam grup!{}".format(
            fname, notice))
    except BadRequest:
        pass


@typing_action
def no_longer_nyimak(update, context):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = sql.rm_nyimak(user.id)
    if res:
        if message.new_chat_members:  #dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                '{} sudah ada!', '{} telah kembali!', '{} mau ngobrol lagi di grup!',
            ]
            chosen_option = random.choice(options)
            update.effective_message.reply_text(chosen_option.format(firstname))
        except:
            return


@typing_action
def reply_nyimak(update, context):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION])

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(message.text[ent.offset:ent.offset +
                                                   ent.length])
                if not user_id:
                    # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print("Error: Could not fetch userid {} for AFK module"
                          .format(user_id))
                    return
                fst_name = chat.first_name

            else:
                return

            check_nyimak(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_nyimak(update, context, user_id, fst_name, userc_id):
    if sql.is_nyimak(user_id):
        user = sql.check_nyimak_status(user_id)
        if not user.reason:
            if int(userc_id) == int(user_id):
                return
            res = "{} is afk".format(fst_name)
            update.effective_message.reply_text(res)
        else:
            if int(userc_id) == int(user_id):
                return
            res = "{} is afk.\nReason: <code>{}</code>".format(
                html.escape(fst_name), html.escape(user.reason))
            update.effective_message.reply_text(res, parse_mode="html")


NYIMAK_HANDLER = DisableAbleCommandHandler("nyimak", nyimak)
NO_NYIMAK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_nyimak)
NYIMAK_REPLY_HANDLER = MessageHandler(Filters.all & Filters.group, reply_nyimak)

dispatcher.add_handler(NYIMAK_HANDLER, NYIMAK_GROUP)
dispatcher.add_handler(NO_NYIMAK_HANDLER, NYIMAK_GROUP)
dispatcher.add_handler(NYIMAK_REPLY_HANDLER, NYIMAK_REPLY_GROUP)

__command_list__ = ["nyimak"]
__handlers__ = [(NYIMAK_HANDLER, NYIMAK_GROUP),
                (NO_NYIMAK_HANDLER, NYIMAK_GROUP),
                (NYIMAK_REPLY_HANDLER, NYIMAK_REPLY_GROUP)]

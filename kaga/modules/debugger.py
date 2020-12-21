import os
import datetime
from telegram.ext import CommandHandler
from telegram import Update
from kaga import dispatcher
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.helper_funcs.alternate import typing_action


@typing_action
def logs(update, context):
    user = update.effective_user
    with open("kagarobot-log.txt", "rb") as f:
        context.bot.send_document(
            document=f,
            filename=f.name,
            chat_id=user.id,
            caption="Log ini yang saya simpan",
        )
        update.effective_message.reply_text("Saya mengirim log ke pm Anda 💌")


LOG_HANDLER = CommandHandler(
    "logs", logs, filters=CustomFilters.dev_filter, run_async=True
)
dispatcher.add_handler(LOG_HANDLER)

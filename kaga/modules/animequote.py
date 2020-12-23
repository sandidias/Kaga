# animequote Module Developed and Provided by @uday_gondaliya

import html
import random
import kaga.modules.animequote_string as animequote_string
from kaga import dispatcher
from telegram import ParseMode, Update, Bot
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action

@typing_action
def aq(update, context):
    args = context.args
    update.effective_message.reply_text(random.choice(animequote_string.ANIMEQUOTE))

AQ_HANDLER = DisableAbleCommandHandler("aq", aq)

dispatcher.add_handler(AQ_HANDLER)

import requests
from telegram import Bot, Message, Update, ParseMode
from ubotindo.modules.helper_funcs.alternate import typing_action

from kaga import dispatcher


@typing_action
def define(update, context):
    msg = update.effective_message
    word = " ".join(args)
    res = requests.get(f"https://googledictionaryapi.id-gb.mybluemix.net/?define={word}")
    if res.status_code == 200:
        info = res.json()[0].get("meaning")
        if info:
            meaning = ""
            for count, (key, value) in enumerate(info.items(), start=1):
                meaning += f"<b>{count}. {word}</b> <i>({key})</i>\n"
                for i in value:
                    defs = i.get("definition")
                    meaning += f"• <i>{defs}</i>\n"
            msg.reply_text(meaning, parse_mode=ParseMode.HTML)
        else:
            return 
    else:
        msg.reply_text("Tidak ada hasil yang ditemukan!")
        
        
__help__ = """
Ever stumbled upon a word that you didn't know of and wanted to look it up?
With this module, you can find the definitions of words without having to leave the app!
*Available commands:*
 - /define <word>: returns the definition of the word.
 """
 
__mod_name__ = "DICTIONARY"
        
        
DEFINE_HANDLER = CommandHandler("define", define, pass_args=True)

dispatcher.add_handler(DEFINE_HANDLER)

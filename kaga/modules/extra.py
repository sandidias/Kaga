from kaga.modules.helper_funcs.chat_status import user_admin
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action
from kaga import dispatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, Filters, CommandHandler

MARKDOWN_HELP = f"""
Markdown adalah alat pemformatan yang sangat kuat yang didukung oleh telegram. {dispatcher.bot.first_name} memiliki beberapa penyempurnaan, untuk memastikannya \
pesan yang disimpan diurai dengan benar, dan untuk memungkinkan Anda membuat tombol.
• <code>_italic_</code>: membuat teks dengan '_' akan menghasilkan teks miring
• <code>*bold*</code>: membuat teks dengan '*' akan menghasilkan teks tebal
• <code>`code`</code>: membuat teks dengan '`' akan menghasilkan teks berspasi tunggal, juga dikenal sebagai 'kode'
• <code>[sometext](someURL)</code>: ini akan membuat tautan - pesan itu hanya akan ditampilkan <code>sometext</code>, \
dan mengetuknya akan membuka halaman di <code>someURL</code>.
<b>Contoh:</b><code>[test](example.com)</code>
• <code>[buttontext](buttonurl:someURL)</code>: ini adalah peningkatan khusus untuk memungkinkan pengguna memiliki telegram \
tombol di markdown mereka. <code>buttontext</code> akan menjadi apa yang ditampilkan pada tombol, dan <code>someurl</code> \
akan menjadi url yang dibuka.
<b>Contoh:</b> <code>[Ini adalah sebuah tombol](buttonurl:example.com)</code>
Jika Anda ingin beberapa tombol pada baris yang sama, gunakan: sama, seperti:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
Ini akan membuat dua tombol pada satu baris, bukan satu tombol per baris.
Ingatlah bahwa pesan Anda <b>HARUS</b> berisi teks selain hanya tombol!
"""


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Coba teruskan pesan berikut kepada saya, dan Anda akan melihat, dan Gunakan #test!"
    )
    update.effective_message.reply_text(
        "/save test Ini adalah tes markdown. _italics_, *bold*, code, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)")


@typing_action
def markdown_help(update, context):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            'Hubungi saya di PM',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Bantuan Markdown",
                    url=f"t.me/{context.bot.username}?start=markdownhelp")
            ]]))
        return
    markdown_help_sender(update)


MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)

dispatcher.add_handler(MD_HELP_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["id"]
__handlers__ = [
    MD_HELP_HANDLER,
]

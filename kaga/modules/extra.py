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

NEKOS_HELP = """
Commands :
× /neko: Mengirim Gambar sumber SFW Neko Acak.
× /feet: Mengirim Gambar Acak Anime Feet.
× /yuri: Mengirim Gambar sumber Yuri Acak.
× /trap: Mengirim Gambar sumber Perangkap Acak.
× /futanari: Mengirim Gambar sumber Futanari Acak.
× /hololewd: Mengirimkan Random Holo Lewds.
× /lewdkemo: Mengirimkan Random Kemo Lewds.
× /sologif: Mengirim GIF Solo Acak.
× /cumgif: Mengirim GIF Cum Acak.
× /erokemo: Mengirim Gambar Random Ero-Kemo.
× /lesbian: Mengirim Gambar Sumber Les Acak.
× /lewdk: Mengirim Random Kitsune Lewds.
× /ngif: Mengirim GIF Neko Acak.
× /tickle: Mengirim GIF Gelitik Acak.
× /lewd: Mengirim Cabul Acak.
× /feed: Mengirim GIF Pemberian Makan Acak.
× /eroyuri: Mengirim Gambar sumber Ero-Yuri Acak.
× /eron: Mengirim Gambar sumber Ero-Neko Acak.
× /cum: Mengirim Gambar Cum Acak.
× /bjgif: Mengirim GIF Pekerjaan Pukulan Acak.
× /bj: Mengirim Gambar sumber Pekerjaan Pukulan Acak.
× /nekonsfw: Mengirim Gambar sumber NSFW Neko Acak.
× /solo: Mengirim GIF Neko NSFW Acak.
× /kemonomimi: Mengirim Gambar sumber KemonoMimi Acak.
× /avatarlewd: Mengirim Stiker Cabul Pembalas Acak.
× /gasm: Mengirim Stiker Orgasme Acak.
× /poke: Mengirim GIF Poke Acak.
× /anal: Mengirim GIF Anal Acak.
× /hentai: Mengirim Gambar sumber Hentai Acak.
× /avatar: Mengirim Stiker Avatar Acak.
× /erofeet: Mengirim Gambar sumber Ero-Feet Acak.
× /holo: Mengirim Gambar sumber Random Holo.
× /tits: Mengirim Gambar sumber Tits Acak.
× /pussygif: Mengirim GIF Pussy Acak.
× /holoero: Mengirim Gambar sumber Ero-Holo Acak.
× /pussy: Mengirim Gambar sumber Pussy Acak.
× /hentaigif: Mengirim GIF Hentai Acak.
× /classic: Mengirim GIF Hentai Klasik Acak.
× /kuni: Mengirim GIF Random Pussy Lick.
× /waifu: Mengirim Stiker Waifu Acak.
× /kiss: Mengirim GIF Ciuman Acak.
× /femdom: Mengirim Gambar sumber Femdom Acak
× /cuddle: Mengirim GIF Cuddle Acak.
× /erok: Mengirim Gambar sumber Ero-Kitsune Acak.
× /foxgirl: Mengirim Gambar sumber FoxGirl Acak.
× /titsgif: Mengirim GIF Payudara Acak.
× /ero: Mengirim Gambar sumber Ero Acak.
× /smug: Mengirim GIF Sombong Acak.
× /baka: Mengirim GIF Teriakan Baka Acak.
× /dva: Mengirim Gambar sumber DVA Acak.
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
    
    
    
def nekos_help_sender(update: Update):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Harap gunakan dengan bijak :D"
    )
    
    
@typing_action
def nekos_help(update, context):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            'Hubungi saya di PM',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Bantuan Modul Nekos",
                    url=f"t.me/{context.bot.username}?start=nekoshelp")
            ]]))
        return
    nekos_help_sender(update)



MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help)
NEKOS_HELP_HANDLER = CommandHandler("nekoshelp", nekos_help)

dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(NEKOS_HELP_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["id"]
__handlers__ = [
    MD_HELP_HANDLER,
    NEKOS_HELP_HANDLER,
]

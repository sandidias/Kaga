from kaga import dispatcher
from telegram import ParseMode, Update
from kaga.modules.helper_funcs.alternate import typing_action

NEKOS_HELP = (
    Module credits: [Dank-del](https://github.com/Dank-del/Chizuru/) ,
    Also thanks to [EverythingSuckz](https://t.me/EverythingSuckz) for NSFW filter.
    
    Penggunaan:
    
    /addnsfw : Mengaktifkan mode NSFW
    /rmnsfw : MEnonaktifkan mode NSFW
 
    Commands :   
     - /neko: Mengirim Gambar sumber SFW Neko Acak.
     - /feet: Mengirim Gambar Acak Anime Feet.
     - /yuri: Mengirim Gambar sumber Yuri Acak.
     - /trap: Mengirim Gambar sumber Perangkap Acak.
     - /futanari: Mengirim Gambar sumber Futanari Acak.
     - /hololewd: Mengirimkan Random Holo Lewds.
     - /lewdkemo: Mengirimkan Random Kemo Lewds.
     - /sologif: Mengirim GIF Solo Acak.
     - /cumgif: Mengirim GIF Cum Acak.
     - /erokemo: Mengirim Gambar Random Ero-Kemo.
     - /lesbian: Mengirim Gambar Sumber Les Acak.
     - /lewdk: Mengirim Random Kitsune Lewds.
     - /ngif: Mengirim GIF Neko Acak.
     - /tickle: Mengirim GIF Gelitik Acak.
     - /cabul: Mengirim Cabul Acak.
     - /feed: Mengirim GIF Pemberian Makan Acak.
     - /eroyuri: Mengirim Gambar sumber Ero-Yuri Acak.
     - /eron: Mengirim Gambar sumber Ero-Neko Acak.
     - /cum: Mengirim Gambar Cum Acak.
     - /bjgif: Mengirim GIF Pekerjaan Pukulan Acak.
     - /bj: Mengirim Gambar sumber Pekerjaan Pukulan Acak.
     - /nekonsfw: Mengirim Gambar sumber NSFW Neko Acak.
     - /olo: Mengirim GIF Neko NSFW Acak.
     - /kemonomimi: Mengirim Gambar sumber KemonoMimi Acak.
     - /avatarlewd: Mengirim Stiker Cabul Pembalas Acak.
     - /gasm: Mengirim Stiker Orgasme Acak.
     - /poke: Mengirim GIF Poke Acak.
     - /anal: Mengirim GIF Anal Acak.
     - /Hentai: Mengirim Gambar sumber Hentai Acak.
     - /avatar: Mengirim Stiker Avatar Acak.
     - /erofeet: Mengirim Gambar sumber Ero-Feet Acak.
     - /holo: Mengirim Gambar sumber Random Holo.
     - /tits: Mengirim Gambar sumber Tits Acak.
     - /pussygif: Mengirim GIF Pussy Acak.
     - /holoero: Mengirim Gambar sumber Ero-Holo Acak.
     - /vagina: Mengirim Gambar sumber Pussy Acak.
     - /hentaigif: Mengirim GIF Hentai Acak.
     - /classic: Mengirim GIF Hentai Klasik Acak.
     - /kuni: Mengirim GIF Random Pussy Lick.
     - /waifu: Mengirim Stiker Waifu Acak.
     - /kiss: Mengirim GIF Ciuman Acak.
     - /femdom: Mengirim Gambar sumber Femdom Acak.
     - /cuddle: Mengirim GIF Cuddle Acak.
     - /erok: Mengirim Gambar sumber Ero-Kitsune Acak.
     - /foxgirl: Mengirim Gambar sumber FoxGirl Acak.
     - /titsgif: Mengirim GIF Payudara Acak.
     - /ero: Mengirim Gambar sumber Ero Acak.
     - /smug: Mengirim GIF Sombong Acak.
     - /baka: Mengirim GIF Teriakan Baka Acak.
     - /dva: Mengirim Gambar sumber D.VA Acak.)
     
@typing_action
def nekos_help(update, context):
    update.effective_message.reply_text(
        NEKOS_HELP, parse_mode=ParseMode.MARKDOWN)
        
NEKOS_HELP = CommandHandler("nekoshelp", nekos_help, run_async=True)

dispatcher.add_handler(NEKOS_HELP)

__help__: """
*Anime Quote*
  × /aq: Mengirim Quotes Anime Acak.
*Black Out*
  Originally Made By [Ayan Ansari](t.me/TechnoAyanOfficial)
  × /blackout <text>: Terapkan Blackout Style ke teks Anda.
*GPS*
  × /gps: <lokasi> Dapatkan lokasi GPS.
*Insult*
  × /insult: Membalas teks untuk insult.
*Nekos*
  × /nekoshelp: lihat lebih banyak command.
*React*
  × /react: Mengirim react acak.
*Truth and Dare*
  × /truth: mengirimkan sebuah tantangan kebenaran.
  × /dare: Memberikan tantangan ke kamu.
*Text to Speech*
  × /tts <teks>
*Urban Dictionary*
  × /ud: kamus online crowdsourced untuk kata dan frasa gaul, beroperasi di bawah moto *Define Your World.*
*Weebify*
/weebify <teks>

__mod_name__ = "💖Special💖"







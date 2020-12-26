import codecs
import datetime
import codecs
import html
import os
import random
import re
from io import BytesIO
from random import randint
from typing import Optional

import requests as r
import wikipedia
from covid import Covid
from requests import get, post
from telegram import (
    Chat,
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ParseMode,
    TelegramError,
)
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from kaga import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WALL_API,
    WHITELIST_USERS,
    dispatcher,
    spamwtc,
)
from kaga.__main__ import GDPR, STATS, USER_INFO
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.global_bans import check_cas
from kaga.modules.helper_funcs.alternate import send_action, typing_action
from kaga.modules.helper_funcs.extraction import extract_user
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.no_sql.afk_db import is_afk


@typing_action
def get_id(update, context):
    args = context.args
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if (
            update.effective_message.reply_to_message
            and update.effective_message.reply_to_message.forward_from
        ):
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_text(
                "Pengirim asli, {}, memiliki ID `{}`.\nPenerusan, {}, memiliki ID dari `{}`.".format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            user = context.bot.get_chat(user_id)
            update.effective_message.reply_text(
                "ID {} adalah `{}`.".format(
                    escape_markdown(user.first_name), user.id
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_text(
                "Id kamu `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            update.effective_message.reply_text(
                "Id Grup ini adalah `{}`.".format(chat.id),
                parse_mode=ParseMode.MARKDOWN,
            )


@typing_action
def info(update, context):
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat

    if user_id:
        user = context.bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not msg.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        msg.reply_text("Saya tidak dapat mengekstrak pengguna dari ini.")
        return

    else:
        return

    del_msg = msg.reply_text(
        "Tunggu sebentar sementara saya mencuri beberapa data dari <b>Database FBI</b>...",
        parse_mode=ParseMode.HTML,
    )

    text = (
        "<b>USER INFO</b>:"
        "\n<b>ID:</b> <code>{}</code>"
        "\n<b>Nama Depan:</b> <code>{}</code>".format(
            user.id, html.escape(user.first_name)
        )
    )

    if user.last_name:
        text += "\n<b>Nama Belakang:</b> <code>{}</code>".format(
            html.escape(user.last_name)
        )

    if user.username:
        text += "\n<b>Nama pengguna:</b> @{}".format(html.escape(user.username))

    text += "\n<b>Tautan pengguna permanen:</b> {}".format(
        mention_html(user.id, "link")
    )

    text += "\n<b>Jumlah foto profil:</b> <code>{}</code>".format(
        context.bot.get_user_profile_photos(user.id).total_count
    )

    if chat.type != "private":
        status = context.bot.get_chat_member(chat.id, user.id).status
        if status:
            _stext = "\n<b>Status:</b> <code>{}</code>"

        afk_st = is_afk(user.id)
        if afk_st:
            text += _stext.format("Away From Keyboard")
        else:
            status = context.bot.get_chat_member(chat.id, user.id).status
            if status:
                if status in {"left", "kicked"}:
                    text += _stext.format("Absent")
                elif status == "member":
                    text += _stext.format("Present")
                elif status in {"administrator", "creator"}:
                    text += _stext.format("Admin")

    try:
        sw = spamwtc.get_ban(int(user.id))
        if sw:
            text += "\n\n<b>Orang ini dilarang di Spamwatch!</b>"
            text += f"\n<b>Alasan:</b> <pre>{sw.reason}</pre>"
            text += "\nAda yang salah coba tanyakan di @SpamWatchSupport"
        else:
            pass
    except BaseException:
        pass  # don't crash if api is down somehow...

    cas_banned = check_cas(user.id)
    if cas_banned:
        text += "\n\n<b>Orang ini Dilarang di CAS!</b>"
        text += f"\n<b>Alasan: </b> <a href='{cas_banned}'>CAS Banned</a>"
        text += "\nAda yang salah coba tanyakan di @cas_discussion"

    if user.id == OWNER_ID:
        text += "\n\nAye, orang ini adalah pemilikku.\nSaya tidak akan pernah melakukan apa pun untuk melawannya!"

    elif user.id in DEV_USERS:
        text += (
            "\n\nOrang ini adalah salah satu pengguna dev saya! "
            "\nDia memiliki perintah paling banyak untuk saya setelah pemilik saya."
        )

    elif user.id in SUDO_USERS:
        text += (
            "\n\nOrang ini adalah salah satu pengguna sudo saya! "
            "Hampir sekuat pemilik saya - jadi tontonlah."
        )

    elif user.id in SUPPORT_USERS:
        text += (
            "\n\nOrang ini adalah salah satu pengguna dukungan saya! "
            "Bukan pengguna sudo, tetapi masih bisa membuat Anda keluar dari peta."
        )

    elif user.id in WHITELIST_USERS:
        text += (
            "\n\nOrang ini telah masuk daftar putih! "
            "Itu artinya saya tidak boleh melarang / menendang mereka."
        )

    elif user.id == int(1087968824):
        text += "\n\nIni adalah admin anonim di grup ini. "

    try:
        memstatus = chat.get_member(user.id).status
        if memstatus == "administrator" or memstatus == "creator":
            result = context.bot.get_chat_member(chat.id, user.id)
            if result.custom_title:
                text += f"\n\nPengguna ini memiliki judul khusus <b>{result.custom_title}</b> di obrolan ini."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    try:
        profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
        context.bot.sendChatAction(chat.id, "upload_photo")
        context.bot.send_photo(
            chat.id,
            photo=profile,
            caption=(text),
            parse_mode=ParseMode.HTML,
        )
    except IndexError:
        context.bot.sendChatAction(chat.id, "typing")
        msg.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
    finally:
        del_msg.delete()


@typing_action
def echo(update, context):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    message.delete()


@typing_action
def gdpr(update, context):
    update.effective_message.reply_text("Menghapus data yang dapat diidentifikasi...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    update.effective_message.reply_text(
        "Data pribadi Anda telah dihapus.\n\nPerhatikan bahwa ini tidak akan membatalkan pelarangan "
        "Anda dari obrolan apa pun, karena itu adalah data telegram, bukan data KagaRobot. "
        "Flood, peringatan, dan gban juga dipertahankan, mulai dari "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "yang dengan jelas menyatakan bahwa hak untuk menghapus tidak berlaku "
        '"untuk pelaksanaan tugas yang dilakukan untuk kepentingan umum", sebagaimana adanya '
        "kasus untuk potongan data tersebut di atas.",
        parse_mode=ParseMode.MARKDOWN,
    )


MARKDOWN_HELP = """
Markdown adalah alat pemformatan yang sangat kuat yang didukung oleh telegram. {} memiliki beberapa peningkatan, untuk memastikannya \
pesan yang disimpan diurai dengan benar, dan untuk memungkinkan Anda membuat tombol.

- <code>_italic_</code>: membungkus teks dengan '_' akan menghasilkan teks miring
- <code>*bold*</code>: membungkus teks dengan '*' akan menghasilkan teks tebal
- <code>`code`</code>: membungkus teks dengan '"' akan menghasilkan teks berspasi tunggal, juga dikenal sebagai 'kode'
- <code>~strike~</code> membungkus teks dengan '~' akan menghasilkan teks coretan
- <code>--underline--</code> membungkus teks dengan '-' akan menghasilkan teks garis bawah
- <code>[sometext](someURL)</code>:ini akan membuat tautan - pesan itu hanya akan ditampilkan <code>sometext</code>, \
dan mengetuknya akan membuka halaman di <code>someURL</code>.
Misal: <code>[test](contoh.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: ini adalah peningkatan khusus untuk memungkinkan pengguna memiliki telegram \
tombol di markdown mereka. <code>buttontext</code> akan menjadi apa yang ditampilkan pada tombol, dan <code>someurl</code> \
akan menjadi url yang dibuka.
Misal: <code>[Ini sebuah tombol](buttonurl:contoh.com)</code>

ika Anda ingin beberapa tombol pada baris yang sama, gunakan: sama, seperti:
<code>[satu](buttonurl://contoh.com)
[dua](buttonurl://google.com:same)</code>
Ini akan membuat dua tombol pada satu baris, bukan satu tombol per baris.

Ingatlah bahwa pesan Anda <b>HARUS</b> berisi teks selain hanya tombol!
""".format(
    dispatcher.bot.first_name
)

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
× /cabul: Mengirim Cabul Acak.
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
× /Hentai: Mengirim Gambar sumber Hentai Acak.
× /avatar: Mengirim Stiker Avatar Acak.
× /erofeet: Mengirim Gambar sumber Ero-Feet Acak.
× /holo: Mengirim Gambar sumber Random Holo.
× /tits: Mengirim Gambar sumber Tits Acak.
× /pussygif: Mengirim GIF Pussy Acak.
× /holoero: Mengirim Gambar sumber Ero-Holo Acak.
× /vagina: Mengirim Gambar sumber Pussy Acak.
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
     """.format(
    dispatcher.bot.first_name
)

@typing_action
def markdown_help(update, context):
    update.effective_message.reply_text(
        MARKDOWN_HELP, parse_mode=ParseMode.HTML
    )
    update.effective_message.reply_text(
        "Coba teruskan pesan berikut kepada saya, dan Anda akan melihatnya!"
    )
    update.effective_message.reply_text(
        "<code>/save tes Ini adalah tes markdown. _italics_, --underline--, *bold*, `code`, ~strike~ "
        "[URL](example.com) [tombol](buttonurl:github.com) "
        "[tombol2](buttonurl://google.com:same)</code>"
    )
    
@typing_action
def nekos_help(update, context):
    update.effective_message.reply_text(
        NEKOS_HELP, parse_mode=ParseMode.HTML
    )
    update.effective_message.reply_text(
        "Harap gunakan dengan baik!"
    )

@typing_action
def wiki(update, context):
    kueri = re.split(pattern="wiki", string=update.effective_message.text)
    wikipedia.set_lang("id")
    if len(str(kueri[1])) == 0:
        update.effective_message.reply_text("Masukkan kata kunci!")
    else:
        try:
            pertama = update.effective_message.reply_text("🔄 Harap bersabar...")
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="🔧 Info lebih lanjut...",
                            url=wikipedia.page(kueri).url,
                        )
                    ]
                ]
            )
            context.bot.editMessageText(
                chat_id=update.effective_chat.id,
                message_id=pertama.message_id,
                text=wikipedia.summary(kueri, sentences=10),
                reply_markup=keyboard,
            )
        except wikipedia.PageError as e:
            update.effective_message.reply_text(f"⚠ Error: {e}")
        except BadRequest as et:
            update.effective_message.reply_text(f"⚠ Error: {et}")
        except wikipedia.exceptions.DisambiguationError as eet:
            update.effective_message.reply_text(
                f"⚠ Kesalahan\nPermintaan terlalu banyak! Ekspresikan lebih banyak!\nKemungkinan hasil permintaan:\n{eet}"
            )


@typing_action
def ud(update, context):
    msg = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    if not text:
        msg.reply_text("Harap masukkan kata kunci untuk pencarian!")
        return
    elif text == "starry":
        msg.reply_text("Sialan!")
        return
    try:
        results = get(
            f"http://api.urbandictionary.com/v0/define?term={text}"
        ).json()
        reply_text = (
            f'Kata: {text}\nDefinisi: {results["list"][0]["definition"]}'
        )
        reply_text += f'\n\nContoh: {results["list"][0]["example"]}'
    except IndexError:
        reply_text = f"Kata: {text}\nHasil: Maaf tidak dapat menemukan hasil yang cocok!"
    ignore_chars = "[]"
    reply = reply_text
    for chars in ignore_chars:
        reply = reply.replace(chars, "")
    if len(reply) >= 4096:
        reply = reply[:4096]  # max msg lenth of tg.
    try:
        msg.reply_text(reply)
    except BadRequest as err:
        msg.reply_text(f"Error! {err.message}")


@typing_action
def src(update, context):
    update.effective_message.reply_text(
        "Hei yang disana! Anda dapat menemukan apa yang membuat saya mengklik [here](https://github.com/HayakaRyu/KagaRobot.git).",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


@send_action(ChatAction.UPLOAD_PHOTO)
def wall(update, context):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    msg_id = update.effective_message.message_id
    args = context.args
    query = " ".join(args)
    if not query:
        msg.reply_text("Please enter a query!")
        return
    else:
        caption = query
        term = query.replace(" ", "%20")
        json_rep = r.get(
            f"https://wall.alphacoders.com/api2.0/get.php?auth={WALL_API}&method=search&term={term}"
        ).json()
        if not json_rep.get("success"):
            msg.reply_text("Terjadi kesalahan!")

        else:
            wallpapers = json_rep.get("wallpapers")
            if not wallpapers:
                msg.reply_text("Tidak ada hasil yang ditemukan! Persempit pencarian Anda.")
                return
            else:
                index = randint(0, len(wallpapers) - 1)  # Choose random index
                wallpaper = wallpapers[index]
                wallpaper = wallpaper.get("url_image")
                wallpaper = wallpaper.replace("\\", "")
                context.bot.send_photo(
                    chat_id,
                    photo=wallpaper,
                    caption="Preview",
                    reply_to_message_id=msg_id,
                    timeout=60,
                )
                context.bot.send_document(
                    chat_id,
                    document=wallpaper,
                    filename="wallpaper",
                    caption=caption,
                    reply_to_message_id=msg_id,
                    timeout=60,
                )


@typing_action
def getlink(update, context):
    args = context.args
    message = update.effective_message
    if args:
        pattern = re.compile(r"-\d+")
    else:
        message.reply_text("Anda sepertinya tidak mengacu pada obrolan apa pun.")
    links = "Undang tautan:\n"
    for chat_id in pattern.findall(message.text):
        try:
            chat = context.bot.getChat(chat_id)
            bot_member = chat.get_member(context.bot.id)
            if bot_member.can_invite_users:
                invitelink = context.bot.exportChatInviteLink(chat_id)
                links += str(chat_id) + ":\n" + invitelink + "\n"
            else:
                links += (
                    str(chat_id)
                    + ":\nSaya tidak memiliki akses ke tautan undangan."
                    + "\n"
                )
        except BadRequest as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"
        except TelegramError as excp:
            links += str(chat_id) + ":\n" + excp.message + "\n"

    message.reply_text(links)


def staff_ids(update, context):
    sfile = "Daftar pengguna SUDO & SUPPORT:\n"
    sfile += f"× DEV USER ID; {DEV_USERS}\n"
    sfile += f"× SUDO USER ID; {SUDO_USERS}\n"
    sfile += f"× SUPPORT USER ID; {SUPPORT_USERS}"
    with BytesIO(str.encode(sfile)) as output:
        output.name = "staff-ids.txt"
        update.effective_message.reply_document(
            document=output,
            filename="staff-ids.txt",
            caption="Berikut adalah daftar pengguna SUDO & SUPPORTS.",
        )


def stats(update, context):
    update.effective_message.reply_text(
        "Statistik saat ini:\n" + "\n".join([mod.__stats__() for mod in STATS])
    )


@typing_action
def covid(update, context):
    message = update.effective_message
    country = str(message.text[len(f"/covid ") :])
    data = Covid(source="worldometers")

    if country == "":
        country = "world"
        link = "https://www.worldometers.info/coronavirus"
    elif country.lower() in ["south korea", "korea"]:
        country = "s. korea"
        link = "https://www.worldometers.info/coronavirus/country/south-korea"
    else:
        link = f"https://www.worldometers.info/coronavirus/country/{country}"
    try:
        c_case = data.get_status_by_country_name(country)
    except Exception:
        message.reply_text(
            "Telah terjadi kesalahan! Apakah Anda yakin nama negaranya benar?"
        )
        return
    total_tests = c_case["total_tests"]
    if total_tests == 0:
        total_tests = "N/A"
    else:
        total_tests = format_integer(c_case["total_tests"])

    date = datetime.datetime.now().strftime("%d %b %Y")

    output = (
        f"<b>Statistik Virus Corona di {c_case['country']}</b>\n"
        f"<b>pada {date}</b>\n\n"
        f"<b>Kasus terkonfirmasi :</b> <code>{format_integer(c_case['confirmed'])}</code>\n"
        f"<b>Kasus aktif :</b> <code>{format_integer(c_case['active'])}</code>\n"
        f"<b>Meninggal :</b> <code>{format_integer(c_case['deaths'])}</code>\n"
        f"<b>Sembuh :</b> <code>{format_integer(c_case['recovered'])}</code>\n\n"
        f"<b>Kasus Baru :</b> <code>{format_integer(c_case['new_cases'])}</code>\n"
        f"<b>Kematian Baru :</b> <code>{format_integer(c_case['new_deaths'])}</code>\n"
        f"<b>Kasus Kritis :</b> <code>{format_integer(c_case['critical'])}</code>\n"
        f"<b>Tes Totals :</b> <code>{total_tests}</code>\n\n"
        f"Data disediakan oleh <a href='{link}'>Worldometer</a>"
    )

    message.reply_text(
        output, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


def format_integer(number, thousand_separator="."):
    def reverse(string):
        string = "".join(reversed(string))
        return string

    s = reverse(str(number))
    count = 0
    result = ""
    for char in s:
        count = count + 1
        if count % 3 == 0:
            if len(s) == count:
                result = char + result
            else:
                result = thousand_separator + char + result
        else:
            result = char + result
    return result


@typing_action
def paste(update, context):
    msg = update.effective_message

    if msg.reply_to_message and msg.reply_to_message.document:
        file = context.bot.get_file(msg.reply_to_message.document)
        file.download("file.txt")
        text = codecs.open("file.txt", "r+", encoding="utf-8")
        paste_text = text.read()
        link = (
            post(
                "https://nekobin.com/api/documents",
                json={"content": paste_text},
            )
            .json()
            .get("result")
            .get("key")
        )
        text = "**Pasted to Nekobin!!!**"
        buttons = [
            [
                InlineKeyboardButton(
                    text="Lihat Link", url=f"https://nekobin.com/{link}"
                ),
                InlineKeyboardButton(
                    text="Lihat Raw",
                    url=f"https://nekobin.com/raw/{link}",
                ),
            ]
        ]
        msg.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        os.remove("file.txt")
    else:
        msg.reply_text("Beri saya file teks untuk ditempel di nekobin")
        return


__help__ = """
Module"odds and ends" untuk perintah kecil dan sederhana yang tidak muat di mana pun

 × /id: Dapatkan id grup saat ini. Jika digunakan dengan membalas pesan, dapatkan id pengguna itu.
 × /info: Dapatkan informasi tentang pengguna.
 × /wiki : Cari artikel wikipedia.
 × /ud <query> : Cari barang di kamus perkotaan.
 × /wall <query> : Dapatkan wallpaper acak langsung dari bot!
 × /reverse : Mencari gambar atau stiker di google.
 × /covid <nama negara>: Berikan statistik tentang COVID-19.
 × /paste : Tempel file teks apa pun ke Nekobin.
 × /gdpr: Menghapus informasi Anda dari database bot. Obrolan pribadi saja.
 × /markdownhelp: Ringkasan cepat tentang cara kerja markdown di telegram - hanya dapat dipanggil dalam obrolan pribadi.
"""

__mod_name__ = "Miscs"

ID_HANDLER = DisableAbleCommandHandler(
    "id", get_id, pass_args=True, run_async=True
)
INFO_HANDLER = DisableAbleCommandHandler(
    "info", info, pass_args=True, run_async=True
)
ECHO_HANDLER = CommandHandler(
    "echo", echo, filters=CustomFilters.sudo_filter, run_async=True
)
MD_HELP_HANDLER = CommandHandler(
    "markdownhelp", markdown_help, filters=Filters.private, run_async=True
)
NEKOS_HELP_HANDLER = CommandHandler(
    "nekoshelp", nekos_help, filters=Filters.private, run_async=True
)
STATS_HANDLER = CommandHandler(
    "stats", stats, filters=CustomFilters.dev_filter, run_async=True
)
GDPR_HANDLER = CommandHandler(
    "gdpr", gdpr, filters=Filters.private, run_async=True
)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki, run_async=True)
WALLPAPER_HANDLER = DisableAbleCommandHandler(
    "wall", wall, pass_args=True, run_async=True
)
UD_HANDLER = DisableAbleCommandHandler("ud", ud, run_async=True)
GETLINK_HANDLER = CommandHandler(
    "getlink",
    getlink,
    pass_args=True,
    filters=CustomFilters.dev_filter,
    run_async=True,
)
STAFFLIST_HANDLER = CommandHandler(
    "staffids", staff_ids, filters=Filters.user(OWNER_ID), run_async=True
)
# SRC_HANDLER = CommandHandler("source", src, filters=Filters.private)
COVID_HANDLER = CommandHandler("covid", covid, run_async=True)
PASTE_HANDLER = CommandHandler("paste", paste, run_async=True)

dispatcher.add_handler(WALLPAPER_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(NEKOS_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GDPR_HANDLER)
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(STAFFLIST_HANDLER)
# dispatcher.add_handler(SRC_HANDLER)
dispatcher.add_handler(COVID_HANDLER)
dispatcher.add_handler(PASTE_HANDLER)

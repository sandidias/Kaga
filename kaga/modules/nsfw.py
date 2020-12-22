import requests
import nekos
from PIL import Image
import os

from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode
from telegram.ext import CommandHandler

from kaga import dispatcher, updater
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.helper_funcs.chat_status import is_user_in_chat


@typing_action
def neko(update, context):
    msg = update.effective_message
    target = "neko"
    msg.reply_photo(nekos.img(target))


@typing_action
def feet(update, context):
    msg = update.effective_message
    target = "feet"
    msg.reply_photo(nekos.img(target))


@typing_action
def yuri(update, context):
    msg = update.effective_message
    target = "yuri"
    msg.reply_photo(nekos.img(target))


@typing_action
def trap(update, context):
    msg = update.effective_message
    target = "trap"
    msg.reply_photo(nekos.img(target))


@typing_action
def futanari(update, context):
    msg = update.effective_message
    target = "futanari"
    msg.reply_photo(nekos.img(target))


@typing_action
def hololewd(update, context):
    msg = update.effective_message
    target = "hololewd"
    msg.reply_photo(nekos.img(target))


@typing_action
def lewdkemo(update, context):
    msg = update.effective_message
    target = "lewdkemo"
    msg.reply_photo(nekos.img(target))


@typing_action
def sologif(update, context):
    msg = update.effective_message
    target = "solog"
    msg.reply_video(nekos.img(target))


@typing_action
def feetgif(update, context):
    msg = update.effective_message
    target = "feetg"
    msg.reply_video(nekos.img(target))


@typing_action
def cumgif(update, context):
    msg = update.effective_message
    target = "cum"
    msg.reply_video(nekos.img(target))


@typing_action
def erokemo(update, context):
    msg = update.effective_message
    target = "erokemo"
    msg.reply_photo(nekos.img(target))


@typing_action
def lesbian(update, context):
    msg = update.effective_message
    target = "les"
    msg.reply_video(nekos.img(target))


@typing_action
def wallpaper(update, context):
    msg = update.effective_message
    target = "wallpaper"
    msg.reply_photo(nekos.img(target))


@typing_action
def lewdk(update, context):
    msg = update.effective_message
    target = "lewdk"
    msg.reply_photo(nekos.img(target))


@typing_action
def ngif(update, context):
    msg = update.effective_message
    target = "ngif"
    msg.reply_video(nekos.img(target))


@typing_action
def tickle(update, context):
    msg = update.effective_message
    target = "tickle"
    msg.reply_video(nekos.img(target))


@typing_action
def lewd(update, context):
    msg = update.effective_message
    target = "lewd"
    msg.reply_photo(nekos.img(target))


@typing_action
def feed(update, context):
    msg = update.effective_message
    target = "feed"
    msg.reply_video(nekos.img(target))


@typing_action
def eroyuri(update, context):
    msg = update.effective_message
    target = "eroyuri"
    msg.reply_photo(nekos.img(target))


@typing_action
def eron(update, context):
    msg = update.effective_message
    target = "eron"
    msg.reply_photo(nekos.img(target))


@typing_action
def cum(update, context):
    msg = update.effective_message
    target = "cum_jpg"
    msg.reply_photo(nekos.img(target))


@typing_action
def bjgif(update, context):
    msg = update.effective_message
    target = "bj"
    msg.reply_video(nekos.img(target))


@typing_action
def bj(update, context):
    msg = update.effective_message
    target = "blowjob"
    msg.reply_photo(nekos.img(target))


@typing_action
def nekonsfw(update, context):
    msg = update.effective_message
    target = "nsfw_neko_gif"
    msg.reply_video(nekos.img(target))


@typing_action
def solo(update, context):
    msg = update.effective_message
    target = "solo"
    msg.reply_photo(nekos.img(target))


@typing_action
def kemonomimi(update, context):
    msg = update.effective_message
    target = "kemonomimi"
    msg.reply_photo(nekos.img(target))


@typing_action
def avatarlewd(update, context):
    msg = update.effective_message
    target = "nsfw_avatar"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


@typing_action
def gasm(update, context):
    msg = update.effective_message
    target = "gasm"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


@typing_action
def poke(update, context):
    msg = update.effective_message
    target = "poke"
    msg.reply_video(nekos.img(target))


@typing_action
def anal(update, context):
    msg = update.effective_message
    target = "anal"
    msg.reply_video(nekos.img(target))


@typing_action
def hentai(update, context):
    msg = update.effective_message
    target = "hentai"
    msg.reply_photo(nekos.img(target))


@typing_action
def avatar(update, context):
    msg = update.effective_message
    target = "nsfw_avatar"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


@typing_action
def erofeet(update, context):
    msg = update.effective_message
    target = "erofeet"
    msg.reply_photo(nekos.img(target))


@typing_action
def holo(update, context):
    msg = update.effective_message
    target = "holo"
    msg.reply_photo(nekos.img(target))


# def keta(update, context):
#     msg = update.effective_message
#     target = 'keta'
#     if not target:
#         msg.reply_text("No URL was received from the API!")
#         return
#     msg.reply_photo(nekos.img(target))


@typing_action
def pussygif(update, context):
    msg = update.effective_message
    target = "pussy"
    msg.reply_video(nekos.img(target))


@typing_action
def tits(update, context):
    msg = update.effective_message
    target = "tits"
    msg.reply_photo(nekos.img(target))


@typing_action
def holoero(update, context):
    msg = update.effective_message
    target = "holoero"
    msg.reply_photo(nekos.img(target))


@typing_action
def pussy(update, context):
    msg = update.effective_message
    target = "pussy_jpg"
    msg.reply_photo(nekos.img(target))


@typing_action
def hentaigif(update, context):
    msg = update.effective_message
    target = "random_hentai_gif"
    msg.reply_video(nekos.img(target))


@typing_action
def classic(update, context):
    msg = update.effective_message
    target = "classic"
    msg.reply_video(nekos.img(target))


@typing_action
def kuni(update, context):
    msg = update.effective_message
    target = "kuni"
    msg.reply_video(nekos.img(target))


@typing_action
def waifu(update, context):
    msg = update.effective_message
    target = "waifu"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


@typing_action
def kiss(update, context):
    msg = update.effective_message
    target = "kiss"
    msg.reply_video(nekos.img(target))


@typing_action
def femdom(update, context):
    msg = update.effective_message
    target = "femdom"
    msg.reply_photo(nekos.img(target))


@typing_action
def cuddle(update, context):
    msg = update.effective_message
    target = "cuddle"
    msg.reply_video(nekos.img(target))


@typing_action
def erok(update, context):
    msg = update.effective_message
    target = "erok"
    msg.reply_photo(nekos.img(target))


@typing_action
def foxgirl(update, context):
    msg = update.effective_message
    target = "fox_girl"
    msg.reply_photo(nekos.img(target))


@typing_action
def titsgif(update, context):
    msg = update.effective_message
    target = "boobs"
    msg.reply_video(nekos.img(target))


@typing_action
def ero(update, context):
    msg = update.effective_message
    target = "ero"
    msg.reply_photo(nekos.img(target))


@typing_action
def smug(update, context):
    msg = update.effective_message
    target = "smug"
    msg.reply_video(nekos.img(target))


@typing_action
def baka(update, context):
    msg = update.effective_message
    target = "baka"
    msg.reply_video(nekos.img(target))


@typing_action
def dva(update, context):
    msg = update.effective_message
    nsfw = requests.get("https://api.computerfreaker.cf/v1/dva").json()
    url = nsfw.get("url")
    # do shit with url if you want to
    if not url:
        msg.reply_text("No URL was received from the API!")
        return
    msg.reply_photo(url)


__help__ = """
 - /neko: Sends Random SFW Neko source Images.
 - /erokemo: Sends Random Ero-Kemo Images.
 - /wallpaper: Sends Random Wallpapers.
 - /ngif: Sends Random Neko GIFs.
 - /tickle: Sends Random Tickle GIFs.
 - /feed: Sends Random Feeding GIFs.
 - /kemonomimi: Sends Random KemonoMimi source Images.
 - /gasm: Sends Random Orgasm Stickers.
 - /poke: Sends Random Poke GIFs.
 - /waifu: Sends Random Waifu Stickers.
 - /kiss: Sends Random Kissing GIFs.
 - /cuddle: Sends Random Cuddle GIFs.
 - /foxgirl: Sends Random FoxGirl source Images.
 - /smug: Sends Random Smug GIFs.
 - /baka: Sends Random Baka Shout GIFs.
"""

__mod_name__ = "Nekos"

LEWDKEMO_HANDLER = DisableAbleCommandHandler("lewdkemo", lewdkemo, run_async=True)
NEKO_HANDLER = DisableAbleCommandHandler("neko", neko, run_async=True)
FEET_HANDLER = DisableAbleCommandHandler("feet", feet, run_async=True)
YURI_HANDLER = DisableAbleCommandHandler("yuri", yuri, run_async=True)
TRAP_HANDLER = DisableAbleCommandHandler("trap", trap, run_async=True)
FUTANARI_HANDLER = DisableAbleCommandHandler("futanari", futanari, run_async=True)
HOLOLEWD_HANDLER = DisableAbleCommandHandler("hololewd", hololewd, run_async=True)
SOLOGIF_HANDLER = DisableAbleCommandHandler("sologif", sologif, run_async=True)
CUMGIF_HANDLER = DisableAbleCommandHandler("cumgif", cumgif, run_async=True)
EROKEMO_HANDLER = DisableAbleCommandHandler("erokemo", erokemo, run_async=True)
LESBIAN_HANDLER = DisableAbleCommandHandler("lesbian", lesbian, run_async=True)
WALLPAPER_HANDLER = DisableAbleCommandHandler("wallpaper", wallpaper, run_async=True)
LEWDK_HANDLER = DisableAbleCommandHandler("lewdk", lewdk, run_async=True)
NGIF_HANDLER = DisableAbleCommandHandler("ngif", ngif, run_async=True)
TICKLE_HANDLER = DisableAbleCommandHandler("tickle", tickle, run_async=True)
LEWD_HANDLER = DisableAbleCommandHandler("lewd", lewd, run_async=True)
FEED_HANDLER = DisableAbleCommandHandler("feed", feed, run_async=True)
EROYURI_HANDLER = DisableAbleCommandHandler("eroyuri", eroyuri, run_async=True)
ERON_HANDLER = DisableAbleCommandHandler("eron", eron, run_async=True)
CUM_HANDLER = DisableAbleCommandHandler("cum", cum, run_async=True)
BJGIF_HANDLER = DisableAbleCommandHandler("bjgif", bjgif, run_async=True)
BJ_HANDLER = DisableAbleCommandHandler("bj", bj, run_async=True)
NEKONSFW_HANDLER = DisableAbleCommandHandler("nekonsfw", nekonsfw, run_async=True)
SOLO_HANDLER = DisableAbleCommandHandler("solo", solo, run_async=True)
KEMONOMIMI_HANDLER = DisableAbleCommandHandler("kemonomimi", kemonomimi, run_async=True)
AVATARLEWD_HANDLER = DisableAbleCommandHandler("avatarlewd", avatarlewd, run_async=True)
GASM_HANDLER = DisableAbleCommandHandler("gasm", gasm, run_async=True)
POKE_HANDLER = DisableAbleCommandHandler("poke", poke, run_async=True)
ANAL_HANDLER = DisableAbleCommandHandler("anal", anal, run_async=True)
HENTAI_HANDLER = DisableAbleCommandHandler("hentai", hentai, run_async=True)
AVATAR_HANDLER = DisableAbleCommandHandler("avatar", avatar, run_async=True)
EROFEET_HANDLER = DisableAbleCommandHandler("erofeet", erofeet, run_async=True)
HOLO_HANDLER = DisableAbleCommandHandler("holo", holo, run_async=True)
TITS_HANDLER = DisableAbleCommandHandler("tits", tits, run_async=True)
PUSSYGIF_HANDLER = DisableAbleCommandHandler("pussygif", pussygif, run_async=True)
HOLOERO_HANDLER = DisableAbleCommandHandler("holoero", holoero, run_async=True)
PUSSY_HANDLER = DisableAbleCommandHandler("pussy", pussy, run_async=True)
HENTAIGIF_HANDLER = DisableAbleCommandHandler("hentaigif", hentaigif, run_async=True)
CLASSIC_HANDLER = DisableAbleCommandHandler("classic", classic, run_async=True)
KUNI_HANDLER = DisableAbleCommandHandler("kuni", kuni, run_async=True)
WAIFU_HANDLER = DisableAbleCommandHandler("waifu", waifu, run_async=True)
LEWD_HANDLER = DisableAbleCommandHandler("lewd", lewd, run_async=True)
KISS_HANDLER = DisableAbleCommandHandler("kiss", kiss, run_async=True)
FEMDOM_HANDLER = DisableAbleCommandHandler("femdom", femdom, run_async=True)
CUDDLE_HANDLER = DisableAbleCommandHandler("cuddle", cuddle, run_async=True)
EROK_HANDLER = DisableAbleCommandHandler("erok", erok, run_async=True)
FOXGIRL_HANDLER = DisableAbleCommandHandler("foxgirl", foxgirl, run_async=True)
TITSGIF_HANDLER = DisableAbleCommandHandler("titsgif", titsgif, run_async=True)
ERO_HANDLER = DisableAbleCommandHandler("ero", ero, run_async=True)
SMUG_HANDLER = DisableAbleCommandHandler("smug", smug, run_async=True)
BAKA_HANDLER = DisableAbleCommandHandler("baka", baka, run_async=True)
DVA_HANDLER = DisableAbleCommandHandler("dva", dva, run_async=True)

dispatcher.add_handler(LEWDKEMO_HANDLER)
dispatcher.add_handler(NEKO_HANDLER)
dispatcher.add_handler(FEET_HANDLER)
dispatcher.add_handler(YURI_HANDLER)
dispatcher.add_handler(TRAP_HANDLER)
dispatcher.add_handler(FUTANARI_HANDLER)
dispatcher.add_handler(HOLOLEWD_HANDLER)
dispatcher.add_handler(SOLOGIF_HANDLER)
dispatcher.add_handler(CUMGIF_HANDLER)
dispatcher.add_handler(EROKEMO_HANDLER)
dispatcher.add_handler(LESBIAN_HANDLER)
dispatcher.add_handler(WALLPAPER_HANDLER)
dispatcher.add_handler(LEWDK_HANDLER)
dispatcher.add_handler(NGIF_HANDLER)
dispatcher.add_handler(TICKLE_HANDLER)
dispatcher.add_handler(LEWD_HANDLER)
dispatcher.add_handler(FEED_HANDLER)
dispatcher.add_handler(EROYURI_HANDLER)
dispatcher.add_handler(ERON_HANDLER)
dispatcher.add_handler(CUM_HANDLER)
dispatcher.add_handler(BJGIF_HANDLER)
dispatcher.add_handler(BJ_HANDLER)
dispatcher.add_handler(NEKONSFW_HANDLER)
dispatcher.add_handler(SOLO_HANDLER)
dispatcher.add_handler(KEMONOMIMI_HANDLER)
dispatcher.add_handler(AVATARLEWD_HANDLER)
dispatcher.add_handler(GASM_HANDLER)
dispatcher.add_handler(POKE_HANDLER)
dispatcher.add_handler(ANAL_HANDLER)
dispatcher.add_handler(HENTAI_HANDLER)
dispatcher.add_handler(AVATAR_HANDLER)
dispatcher.add_handler(EROFEET_HANDLER)
dispatcher.add_handler(HOLO_HANDLER)
dispatcher.add_handler(TITS_HANDLER)
dispatcher.add_handler(PUSSYGIF_HANDLER)
dispatcher.add_handler(HOLOERO_HANDLER)
dispatcher.add_handler(PUSSY_HANDLER)
dispatcher.add_handler(HENTAIGIF_HANDLER)
dispatcher.add_handler(CLASSIC_HANDLER)
dispatcher.add_handler(KUNI_HANDLER)
dispatcher.add_handler(WAIFU_HANDLER)
dispatcher.add_handler(LEWD_HANDLER)
dispatcher.add_handler(KISS_HANDLER)
dispatcher.add_handler(FEMDOM_HANDLER)
dispatcher.add_handler(CUDDLE_HANDLER)
dispatcher.add_handler(EROK_HANDLER)
dispatcher.add_handler(FOXGIRL_HANDLER)
dispatcher.add_handler(TITSGIF_HANDLER)
dispatcher.add_handler(ERO_HANDLER)
dispatcher.add_handler(SMUG_HANDLER)
dispatcher.add_handler(BAKA_HANDLER)
dispatcher.add_handler(DVA_HANDLER)

__handlers__ = [
    NEKO_HANDLER,
    FEET_HANDLER,
    YURI_HANDLER,
    TRAP_HANDLER,
    FUTANARI_HANDLER,
    HOLOLEWD_HANDLER,
    SOLOGIF_HANDLER,
    CUMGIF_HANDLER,
    EROKEMO_HANDLER,
    LESBIAN_HANDLER,
    WALLPAPER_HANDLER,
    LEWDK_HANDLER,
    NGIF_HANDLER,
    TICKLE_HANDLER,
    LEWD_HANDLER,
    FEED_HANDLER,
    EROYURI_HANDLER,
    ERON_HANDLER,
    CUM_HANDLER,
    BJGIF_HANDLER,
    BJ_HANDLER,
    NEKONSFW_HANDLER,
    SOLO_HANDLER,
    KEMONOMIMI_HANDLER,
    AVATARLEWD_HANDLER,
    GASM_HANDLER,
    POKE_HANDLER,
    ANAL_HANDLER,
    HENTAI_HANDLER,
    AVATAR_HANDLER,
    EROFEET_HANDLER,
    HOLO_HANDLER,
    TITS_HANDLER,
    PUSSYGIF_HANDLER,
    HOLOERO_HANDLER,
    PUSSY_HANDLER,
    HENTAIGIF_HANDLER,
    CLASSIC_HANDLER,
    KUNI_HANDLER,
    WAIFU_HANDLER,
    LEWD_HANDLER,
    KISS_HANDLER,
    FEMDOM_HANDLER,
    LEWDKEMO_HANDLER,
    CUDDLE_HANDLER,
    EROK_HANDLER,
    FOXGIRL_HANDLER,
    TITSGIF_HANDLER,
    ERO_HANDLER,
    SMUG_HANDLER,
    BAKA_HANDLER,
    DVA_HANDLER,
]

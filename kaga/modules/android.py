import time

from bs4 import BeautifulSoup
from hurry.filesize import size as sizee
from requests import get
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest

from kaga import dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action

GITHUB = "https://github.com"
DEVICES_DATA = "https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json"


@typing_action
def magisk(update, context):
    url = "https://raw.githubusercontent.com/topjohnwu/magisk_files/"
    releases = ""
    for type, branch in {
        "Stable": ["master/stable", "master"],
        "Beta": ["master/beta", "master"],
        "Canary": ["canary/canary", "canary"],
    }.items():
        data = get(url + branch[0] + ".json").json()
        if str(type) == "Canary":
            data["magisk"]["link"] = (
                "https://github.com/topjohnwu/magisk_files/raw/canary/"
                + data["magisk"]["link"]
            )
            data["app"]["link"] = (
                "https://github.com/topjohnwu/magisk_files/raw/canary/"
                + data["app"]["link"]
            )
            data["uninstaller"]["link"] = (
                "https://github.com/topjohnwu/magisk_files/raw/canary/"
                + data["uninstaller"]["link"]
            )
        releases += (
            f"*{type}*: \n"
            f"• [Changelog](https://github.com/topjohnwu/magisk_files/blob/{branch[1]}/notes.md)\n"
            f'• Zip - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["magisk"]["link"]}) \n'
            f'• App - [{data["app"]["version"]}-{data["app"]["versionCode"]}]({data["app"]["link"]}) \n'
            f'• Uninstaller - [{data["magisk"]["version"]}-{data["magisk"]["versionCode"]}]({data["uninstaller"]["link"]})\n\n'
        )

    del_msg = update.message.reply_text(
        "*Versi Magisk Terbaru:*\n{}".format(releases),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    time.sleep(300)
    try:
        del_msg.delete()
        update.effective_message.delete()
    except BadRequest as err:
        if (err.message == "Message to delete not found") or (
            err.message == "Message can't be deleted"
        ):
            return


@typing_action
def device(update, context):
    args = context.args
    if len(args) == 0:
        reply = (
            "Tidak ada codename yang disediakan, tulis codename untuk mengambil informasi."
        )
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    device = " ".join(args)
    db = get(DEVICES_DATA).json()
    newdevice = device.strip("lte") if device.startswith("beyond") else device
    try:
        reply = f"Hasil pencarian {device}:\n\n"
        brand = db[newdevice][0]["brand"]
        name = db[newdevice][0]["name"]
        model = db[newdevice][0]["model"]
        codename = newdevice
        reply += (
            f"<b>{brand} {name}</b>\n"
            f"Model: <code>{model}</code>\n"
            f"Codename: <code>{codename}</code>\n\n"
        )
    except KeyError:
        reply = f"Tidak dapat menemukan info tentang {device}!\n"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    update.message.reply_text(
        "{}".format(reply),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@typing_action
def twrp(update, context):
    args = context.args
    if len(args) == 0:
        reply = (
            "Tidak ada codename yang disediakan, tulis codename untuk mengambil informasi."
        )
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest:
            pass
        return

    device = " ".join(args)
    url = get(f"https://eu.dl.twrp.me/{device}/")
    if url.status_code == 404:
        reply = f"Tidak dapat menemukan unduhan twrp untuk {device}!\n"
        del_msg = update.effective_message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        time.sleep(5)
        try:
            del_msg.delete()
            update.effective_message.delete()
        except BadRequest as err:
            if (err.message == "Message to delete not found") or (
                err.message == "Message can't be deleted"
            ):
                return
    else:
        reply = f"*TWRP Resmi terbaru untuk {device}*\n"
        db = get(DEVICES_DATA).json()
        newdevice = (
            device.strip("lte") if device.startswith("beyond") else device
        )
        try:
            brand = db[newdevice][0]["brand"]
            name = db[newdevice][0]["name"]
            reply += f"*{brand} - {name}*\n"
        except KeyError:
            pass
        page = BeautifulSoup(url.content, "lxml")
        date = page.find("em").text.strip()
        reply += f"*Updated:* {date}\n"
        trs = page.find("table").find_all("tr")
        row = 2 if trs[0].find("a").text.endswith("tar") else 1
        for i in range(row):
            download = trs[i].find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = trs[i].find("span", {"class": "filesize"}).text
            reply += f"[{dl_file}]({dl_link}) - {size}\n"

        update.message.reply_text(
            "{}".format(reply),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


@typing_action
def los(update, context) -> str:
    message = update.effective_message
    update.effective_chat
    args = context.args
    try:
        device = args[0]
    except Exception:
        device = ""

    if device == "":
        reply_text = (
            "*Silakan Ketikkan codename Perangkat Anda*\nContoh : `/los lavender`"
        )
        message.reply_text(
            reply_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    fetch = get(f"https://download.lineageos.org/api/v1/{device}/nightly/*")
    if fetch.status_code == 200 and len(fetch.json()["response"]) != 0:
        usr = fetch.json()
        data = len(usr["response"]) - 1  # the latest rom are below
        response = usr["response"][data]
        filename = response["filename"]
        url = response["url"]
        buildsize_a = response["size"]
        buildsize_b = sizee(int(buildsize_a))
        version = response["version"]

        reply_text = f"*Download :* [{filename}]({url})\n"
        reply_text += f"*Build Size :* `{buildsize_b}`\n"
        reply_text += f"*Version :* `{version}`\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    text="Klik Di Sini Untuk Mengunduh", url=f"{url}"
                )
            ]
        ]
        message.reply_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    else:
        message.reply_text(
            "`Tidak dapat menemukan hasil apa pun yang cocok dengan kueri Anda.`",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


@typing_action
def gsi(update, context):
    message = update.effective_message
    update.effective_chat

    usr = get(
        f"https://api.github.com/repos/phhusson/treble_experimentations/releases/latest"
    ).json()
    reply_text = "*Rilis terbaru Gsi*\n"
    for i in range(len(usr)):
        try:
            name = usr["assets"][i]["name"]
            url = usr["assets"][i]["browser_download_url"]
            reply_text += f"[{name}]({url})\n"
        except IndexError:
            continue
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


@typing_action
def bootleg(update, context) -> str:
    message = update.effective_message
    update.effective_chat
    args = context.args
    try:
        codename = args[0]
    except Exception:
        codename = ""

    if codename == "":
        message.reply_text(
            "*Silakan Ketikkan codename Perangkat Anda*\nContoh : `/bootleg lavender`",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    fetch = get("https://bootleggersrom-devices.github.io/api/devices.json")
    if fetch.status_code == 200:
        data = fetch.json()

        if codename.lower() == "x00t":
            device = "X00T"
        elif codename.lower() == "rmx1971":
            device = "RMX1971"
        else:
            device = codename.lower()

        try:
            fullname = data[device]["fullname"]
            filename = data[device]["filename"]
            buildate = data[device]["buildate"]
            buildsize = data[device]["buildsize"]
            buildsize = sizee(int(buildsize))
            downloadlink = data[device]["download"]
            if data[device]["mirrorlink"] != "":
                mirrorlink = data[device]["mirrorlink"]
            else:
                mirrorlink = None
        except KeyError:
            message.reply_text(
                "`Tidak dapat menemukan hasil apa pun yang cocok dengan kueri Anda.`",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            return

        reply_text = f"*BootlegersROM for {fullname}*\n"
        reply_text += f"*Download :* [{filename}]({downloadlink})\n"
        reply_text += f"*Size :* `{buildsize}`\n"
        reply_text += f"*Tanggal Build :* `{buildate}`\n"
        if mirrorlink is not None:
            reply_text += f"[Mirror link]({mirrorlink})"

        keyboard = [
            [
                InlineKeyboardButton(
                    text="Klik Di Sini Untuk Mengunduh", url=f"{downloadlink}"
                )
            ]
        ]

        message.reply_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    elif fetch.status_code == 404:
        message.reply_text(
            "`Couldn't reach api`",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return


__help__ = """
Dapatkan relese magisk terbaru, Twrp untuk perangkat Anda atau info tentang beberapa perangkat yang menggunakan codename-nya, Langsung dari Bot!

*Perintah terkait Android:*

 × /magisk - Mendapat rilis magisk terbaru untuk Stable/Beta/Canary.
 × /device <codename> - Mendapat info dasar perangkat android dari codename-nya.
 × /twrp <codename> -  Mendapat twrp terbaru untuk perangkat android menggunakan codename.
 × /los <codename> - Mendapat build los terbaru.
"""

__mod_name__ = "Android"

MAGISK_HANDLER = DisableAbleCommandHandler("magisk", magisk, run_async=True)
DEVICE_HANDLER = DisableAbleCommandHandler(
    "device", device, pass_args=True, run_async=True
)
TWRP_HANDLER = DisableAbleCommandHandler(
    "twrp", twrp, pass_args=True, run_async=True
)
LOS_HANDLER = DisableAbleCommandHandler(
    "los", los, pass_args=True, run_async=True
)
BOOTLEG_HANDLER = DisableAbleCommandHandler(
    "bootleg", bootleg, pass_args=True, run_async=True
)
GSI_HANDLER = DisableAbleCommandHandler(
    "gsi", gsi, pass_args=True, run_async=True
)


dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(DEVICE_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(LOS_HANDLER)
dispatcher.add_handler(GSI_HANDLER)
dispatcher.add_handler(BOOTLEG_HANDLER)

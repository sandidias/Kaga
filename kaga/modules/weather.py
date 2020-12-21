import json
import time

import requests
from pytz import country_names as cname
from telegram import ParseMode
from telegram.error import BadRequest

from kaga import API_WEATHER as APPID
from kaga import dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action


@typing_action
def weather(update, context):
    args = context.args
    if len(args) == 0:
        reply = "Tulis lokasi untuk memeriksa cuaca."
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

        return

    CITY = " ".join(args)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={APPID}"
    request = requests.get(url)
    result = json.loads(request.text)
    if request.status_code != 200:
        reply = "Lokasi tidak valid."
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
        return

    try:
        cityname = result["name"]
        curtemp = result["main"]["temp"]
        feels_like = result["main"]["feels_like"]
        humidity = result["main"]["humidity"]
        wind = result["wind"]["speed"]
        weath = result["weather"][0]
        icon = weath["id"]
        condmain = weath["main"]
        conddet = weath["description"]
        country_name = cname[f"{result['sys']['country']}"]
    except KeyError:
        update.effective_message.reply_text("Lokasi Tidak Valid!")
        return

    if icon <= 232:  # Rain storm
        icon = "⛈"
    elif icon <= 321:  # Drizzle
        icon = "🌧"
    elif icon <= 504:  # Light rain
        icon = "🌦"
    elif icon <= 531:  # Cloudy rain
        icon = "⛈"
    elif icon <= 622:  # Snow
        icon = "❄️"
    elif icon <= 781:  # Atmosphere
        icon = "🌪"
    elif icon <= 800:  # Bright
        icon = "☀️"
    elif icon <= 801:  # A little cloudy
        icon = "⛅️"
    elif icon <= 804:  # Cloudy
        icon = "☁️"
    kmph = str(wind * 3.6).split(".")

    def celsius(c):
        k = 273.15
        c = k if (c > (k - 1)) and (c < k) else c
        temp = str(round((c - k)))
        return temp

    def fahr(c):
        c1 = 9 / 5
        c2 = 459.67
        tF = c * c1 - c2
        if tF < 0 and tF > -1:
            tF = 0
        temp = str(round(tF))
        return temp

    reply = f"*Cuaca saat ini untuk {cityname}, {country_name} adalah*:\n\n*Temperatur:* `{celsius(curtemp)}°C ({fahr(curtemp)}ºF), terasa seperti {celsius(feels_like)}°C ({fahr(feels_like)}ºF) \n`*Kondisi:* `{condmain}, {conddet}` {icon}\n*Kelembaban:* `{humidity}%`\n*Angin:* `{kmph[0]} km/h`\n"
    del_msg = update.effective_message.reply_text(
        "{}".format(reply),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    time.sleep(30)
    try:
        del_msg.delete()
        update.effective_message.delete()
    except BadRequest as err:
        if (err.message == "Message to delete not found") or (
            err.message == "Message can't be deleted"
        ):
            return


__help__ = """
Modul cuaca:

 × /weather <city>: Mendapat informasi cuaca dari tempat tertentu!

 \* Untuk mencegah perintah cuaca spam dan hasilnya akan dihapus setelah 30 detik
"""

__mod_name__ = "Weather"

WEATHER_HANDLER = DisableAbleCommandHandler(
    "weather", weather, pass_args=True, run_async=True
)

dispatcher.add_handler(WEATHER_HANDLER)

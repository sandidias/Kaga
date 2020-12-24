import math

import pynewtonmath as newton
from kaga import dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from telegram import Update
from kaga.modules.helper_funcs.alternate import typing_action


@typing_action
def simplify(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.simplify('{}'.format(args[0])))


@typing_action
def factor(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.factor('{}'.format(args[0])))


@typing_action
def derive(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.derive('{}'.format(args[0])))


@typing_action
def integrate(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.integrate('{}'.format(args[0])))


@typing_action
def zeroes(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.zeroes('{}'.format(args[0])))


@typing_action
def tangent(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.tangent('{}'.format(args[0])))


@typing_action
def area(update, contextupdate, context):
    args = context.args
    message = update.effective_message
    message.reply_text(newton.area('{}'.format(args[0])))


@typing_action
def cos(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.cos(int(args[0])))


@typing_action
def sin(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.sin(int(args[0])))


@typing_action
def tan(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.tan(int(args[0])))


@typing_action
def arccos(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.acos(int(args[0])))


@typing_action
def arcsin(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.asin(int(args[0])))


@typing_action
def arctan(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.atan(int(args[0])))


@typing_action
def abs(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.fabs(int(args[0])))


@typing_action
def log(update, context):
    args = context.args
    message = update.effective_message
    message.reply_text(math.log(int(args[0])))


__help__ = """
Memecahkan masalah matematika yang rumit menggunakan https://newton.now.sh
 • /math*:* Math `/math 2^2+2(2)`
 • /factor*:* Factor `/factor x^2 + 2x`
 • /derive*:* Derive `/derive x^2+2x`
 • /integrate*:* Integrate `/integrate x^2+2x`
 • /zeroes*:* Find 0's `/zeroes x^2+2x`
 • /tangent*:* Find Tangent `/tangent 2lx^3`
 • /area*:* Area Under Curve `/area 2:4lx^3`
 • /cos*:* Cosine `/cos pi`
 • /sin*:* Sine `/sin 0`
 • /tan*:* Tangent `/tan 0`
 • /arccos*:* Inverse Cosine `/arccos 1`
 • /arcsin*:* Inverse Sine `/arcsin 0`
 • /arctan*:* Inverse Tangent `/arctan 0`
 • /abs*:* Absolute Value `/abs -1`
 • /log*:* Logarithm `/log 2l8`

_Keep di mind_: Untuk menemukan garis tangen fungsi pada nilai x tertentu, kirim permintaan sebagai c|f(x) di mana c adalah nilai x yang diberikan dan f(x) adalah ekspresi fungsi, pemisah adalah bilah vertikal '|'. Lihat tabel di atas untuk contoh permintaan.
Untuk menemukan area di bawah fungsi, kirim permintaan sebagai c:d|f(x) di mana c adalah nilai awal x, d adalah nilai akhir x, dan f(x) adalah fungsi di mana Anda menginginkan kurva antara dua nilai x.
Untuk menghitung pecahan, masukkan ekspresi sebagai penyebut angka(over). Misalnya, untuk memproses 2/4 Anda harus mengirim ekspresi Anda sebagai 2(atas)4. Ekspresi hasil akan berada dalam notasi matematika standar (1/2, 3/4).
"""

__mod_name__ = "Math"

SIMPLIFY_HANDLER = DisableAbleCommandHandler("math", simplify)
FACTOR_HANDLER = DisableAbleCommandHandler("factor", factor)
DERIVE_HANDLER = DisableAbleCommandHandler("derive", derive)
INTEGRATE_HANDLER = DisableAbleCommandHandler("integrate", integrate)
ZEROES_HANDLER = DisableAbleCommandHandler("zeroes", zeroes)
TANGENT_HANDLER = DisableAbleCommandHandler("tangent", tangent)
AREA_HANDLER = DisableAbleCommandHandler("area", area)
COS_HANDLER = DisableAbleCommandHandler("cos", cos)
SIN_HANDLER = DisableAbleCommandHandler("sin", sin)
TAN_HANDLER = DisableAbleCommandHandler("tan", tan)
ARCCOS_HANDLER = DisableAbleCommandHandler("arccos", arccos)
ARCSIN_HANDLER = DisableAbleCommandHandler("arcsin", arcsin)
ARCTAN_HANDLER = DisableAbleCommandHandler("arctan", arctan)
ABS_HANDLER = DisableAbleCommandHandler("abs", abs)
LOG_HANDLER = DisableAbleCommandHandler("log", log)

dispatcher.add_handler(SIMPLIFY_HANDLER)
dispatcher.add_handler(FACTOR_HANDLER)
dispatcher.add_handler(DERIVE_HANDLER)
dispatcher.add_handler(INTEGRATE_HANDLER)
dispatcher.add_handler(ZEROES_HANDLER)
dispatcher.add_handler(TANGENT_HANDLER)
dispatcher.add_handler(AREA_HANDLER)
dispatcher.add_handler(COS_HANDLER)
dispatcher.add_handler(SIN_HANDLER)
dispatcher.add_handler(TAN_HANDLER)
dispatcher.add_handler(ARCCOS_HANDLER)
dispatcher.add_handler(ARCSIN_HANDLER)
dispatcher.add_handler(ARCTAN_HANDLER)
dispatcher.add_handler(ABS_HANDLER)
dispatcher.add_handler(LOG_HANDLER)

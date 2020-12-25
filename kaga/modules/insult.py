import random
from telegram.ext import run_async, Filters
from telegram import Message, Chat, Update, Bot, MessageEntity
from kaga import dispatcher
from kaga.modules.disable import DisableAbleCommandHandler
from kaga.modules.helper_funcs.alternate import typing_action

SFW_STRINGS = (
    "Owww ... Dasar idiot yang bodoh.",
    "Jangan minum dan mengetik.",
    "Saya pikir Anda harus pulang atau lebih baik ke rumah sakit jiwa.",
    "Perintah tidak ditemukan. Sama seperti otak Anda.",
    "Apakah kamu sadar bahwa kamu membodohi dirimu sendiri? Ternyata tidak.",
    "Anda bisa mengetik lebih baik dari itu.",
    "Aturan bot 544 bagian 9 mencegah saya membalas orang bodoh seperti Anda.",
    "Maaf, kami tidak menjual otak.",
    "Percayalah kamu tidak normal.",
    "Saya yakin otak Anda terasa seperti baru, mengingat Anda tidak pernah menggunakannya.",
    "Jika saya ingin bunuh diri, saya akan meningkatkan ego Anda dan melompat ke IQ Anda.",
    "Zombie memakan otak ... kamu aman.",
    "Anda tidak berevolusi dari kera, mereka berevolusi dari Anda.",
    "Kembalilah dan bicara padaku ketika IQ mu melebihi umurmu.",
    "Saya tidak mengatakan Anda bodoh, saya hanya mengatakan Anda mendapat nasib buruk dalam hal berpikir.",
    "Kamu berbicara bahasa apa? Karena terdengar seperti omong kosong.",
    "Kebodohan bukanlah kejahatan jadi kamu bebas pergi.",
    "Anda adalah bukti bahwa evolusi BISA mundur.",
    "Aku akan bertanya berapa umurmu tapi aku tahu kamu tidak bisa menghitung setinggi itu.",
    "Sebagai orang luar, apa pendapat Anda tentang ras manusia?",
    "Otak bukanlah segalanya. Dalam kasusmu mereka bukan apa-apa.",
    "Biasanya orang hidup dan belajar. Kamu hidup saja.",
    "Aku tidak tahu apa yang membuatmu begitu bodoh, tapi itu benar-benar berhasil.",
    "Teruslah bicara, suatu hari nanti kamu akan mengatakan sesuatu yang cerdas! (Meskipun aku ragu)",
    "Shock saya, katakan sesuatu yang cerdas.",
    "IQ Anda lebih rendah dari ukuran sepatu Anda.",
    "Aduh! Neurotransmiter Anda tidak lagi bekerja.",
    "Apakah kamu gila kamu bodoh.",
    "Setiap orang berhak untuk menjadi bodoh tetapi Anda menyalahgunakan hak istimewa tersebut.",
    "Maaf aku menyakiti perasaanmu saat menyebutmu bodoh. Kupikir kamu sudah tahu itu.",
    "Anda harus mencoba mencicipi sianida.",
    "Enzim Anda dimaksudkan untuk mencerna racun tikus.",
    "Kamu harus mencoba tidur selamanya.",
    "Anda bisa membuat rekor dunia dengan melompat dari pesawat tanpa parasut.",
    "Berhenti berbicara BS dan melompat di depan kereta peluru yang sedang berjalan.",
    "Cobalah mandi dengan Hydrochloric Acid daripada air.",
    "Coba ini: jika Anda menahan napas di bawah air selama satu jam, Anda dapat menahannya selamanya.",
    "Go Green! Berhenti menghirup Oksigen.",
    "Tuhan sedang mencarimu. Kamu harus pergi untuk bertemu dengannya.",
    "berikan 100% mu. Sekarang, pergi donor darah.",
    "Cobalah melompat dari gedung seratus lantai tetapi Anda hanya dapat melakukannya sekali.",
    "Anda harus menyumbangkan otak Anda melihat bahwa Anda tidak pernah menggunakannya.",
    "Relawan untuk target dalam jarak tembak.",
    "Tembak kepala itu menyenangkan. Dapatkan dirimu sendiri.",
    "Anda harus mencoba berenang dengan hiu putih besar.",
    "Anda harus mengecat diri Anda dengan warna merah dan berlari dalam bull marathon.",
    "Anda bisa tetap di bawah air selama sisa hidup Anda tanpa harus kembali lagi.",
    "Bagaimana kalau kamu berhenti bernapas selama 1 hari? Itu akan bagus.",
    "Cobalah memprovokasi harimau saat kalian berdua berada di dalam sangkar.",
    "Sudahkah Anda mencoba menembak diri Anda sendiri setinggi 100m menggunakan kanon.",
    "Anda harus mencoba menahan TNT di mulut Anda dan menyalakannya.",
    "Coba mainkan tangkap dan lempar dengan RDX itu menyenangkan.",
    "Saya dengar phogine beracun tapi saya rasa Anda tidak keberatan menghirupnya untuk bersenang-senang.",
    "Luncurkan diri Anda ke luar angkasa sambil melupakan oksigen di Bumi.",
    "Anda harus mencoba bermain ular tangga, dengan ular asli dan tanpa tangga.",
    "Menari telanjang di beberapa kabel HT.",
    "Gunung Berapi Aktif adalah kolam renang terbaik untuk Anda.",
    "Anda harus mencoba mandi air panas di gunung berapi.",
    "Cobalah untuk menghabiskan satu hari di peti mati dan itu akan menjadi milikmu selamanya.",
    "Pukul Uranium dengan neutron yang bergerak lambat di hadapanmu. Ini akan menjadi pengalaman yang berharga.",
    "Anda bisa menjadi orang pertama yang menginjak matahari. Selamat mencoba.",
     "🤭.",
)

@typing_action
def insult(update, context):
    bot = context.bot
    bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
    message = update.effective_message
    if message.reply_to_message:
      message.reply_to_message.reply_text(random.choice(SFW_STRINGS))
    else:
      message.reply_text(random.choice(SFW_STRINGS))

INSULT_HANDLER = DisableAbleCommandHandler("insult", insult, run_async=True)

dispatcher.add_handler(INSULT_HANDLER)

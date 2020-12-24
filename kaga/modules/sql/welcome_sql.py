import random
import threading
from typing import Union

from kaga.modules.helper_funcs.msg_types import Types
from kaga.modules.sql import BASE, SESSION
from sqlalchemy import (BigInteger, Boolean, Column, Integer, String,
                        UnicodeText)

DEFAULT_WELCOME = 'Selamat datang {frist}'
DEFAULT_GOODBYE = 'Sampai jumpa kembali {frist}!'

DEFAULT_WELCOME_MESSAGES = [
    "{first} ada di sini!", #Discord selamat datang disalin
    "Pemain siap {first}",
    "Genos, {first} ada di sini.",
    "A liar {first} muncul.",
    "{pertama} datang seperti Singa!",
    "{first} telah bergabung dengan partai Anda.",
    "{pertama} baru bergabung. Dapatkah saya mendapatkan penyembuhan?",
    "{first} baru saja bergabung dengan obrolan - asdgfhak!",
    "{pertama} baru bergabung. Semuanya, terlihat sibuk!",
    "Selamat datang, {first}. Tinggal sebentar dan mendengarkan .",
    "Selamat datang, {first}. Kami mengharapkan Anda ( ͡° ͜ʖ ͡°) ",
    "Selamat datang, {first}. Kami harap Anda membawa pizza.",
    "Selamat datang, {first}. Tinggalkan senjata anda di dekat pintu.",
    "Swoooosh. [pertama] baru saja mendarat.",
    "Persiapkan diri kalian. {first} baru saja bergabung dengan obrolan.",
    "{pertama} baru bergabung. Sembunyikan pisang Anda.",
    "{pertama} baru saja tiba. Tampaknya OP - silakan nerf.",
    "{first} baru saja meluncur ke obrolan.",
    "{first} telah muncul dalam obrolan.",
    "Big {first} muncul!",
    "Dimana {first}? Dalam obrolan!",
    "{first} melompat ke obrolan. Kanguru!!",
    "{pertama} baru saja muncul. Pegang birku.",
    "Penantang mendekat! [pertama} telah muncul!",
    "Ini burung! Ini pesawat! Nevermind, itu hanya {first}.",
    "Ini {first}! Pujilah matahari! o/",
    "Jangan pernah memberikan {first} up. Tidak akan pernah membiarkan {first} turun.",
    "Ha! [pertama} telah bergabung! Anda mengaktifkan kartu perangkap saya !",
    "Hei! Mendengarkan! {first} telah bergabung!",
    "Kami sudah menunggumu {first}",
    "Sangat berbahaya untuk pergi sendiri, ambil {first}!",
    "{first} telah bergabung dengan obrolan! Ini sangat efektif!",
    "Bersurak-sorai, cinta! [pertama} ada di sini!",
    "{first} ada di sini, seperti ramalan yang diramalkan.",
    "{first} telah tiba. Pestanya sudah berakhir.",
    "{pertama} di sini untuk menendang pantat dan mengunyah gelembung. Dan [pertama} adalah semua keluar dari permen karet.",
    "Halo. Apakah {first} Anda cari?",
    "{first} telah bergabung. Tinggal sebentar dan mendengarkan!",
    "Mawar berwarna merah, violet berwarna biru, {first} bergabung dengan obrolan ini denganmu",
    "Selamat datang {first}, Hindari Pukulan jika anda bisa!",
    "Ini burung! Ini pesawat! - Tidak, itu {first}!",
    "{first} Bergabung! - Ok.", #Discord selamat datang berakhir.
    "All Hail {first}!",
    "Hai, {pertama}. Jangan mengintai, hanya Villans yang melakukan itu.",
    "{first} telah bergabung dengan bus pertempuran.",
    "Penantang baru masuk!", #Tekken
    "Ok!",
    "{pertama} baru saja jatuh ke dalam obrolan!*",
    "Sesuatu baru saja jatuh dari langit! - Oh, itu {first}.*",
    "{first} Baru saja diteleportasi ke dalam obrolan!*",
    "Hai, {first}, tunjukkan Lisensi Hunter-mu!*", #Hunter Hunter
    "Aku cari Garo, oh tunggu nvm itu {first}.*", #One Punch man s2
    "Selamat datang {first}, pergi bukanlah pilihan!*",
    "Jalankan Hutan! .. Maksudku... [pertama}.*",
    "{first} lakukan 100 push-up, 100 sit-up, 100 squat, dan 10km berjalan SETIAP HARI!!! *", #One Punch ma
    "Huh?nDid seseorang dengan tingkat bencana baru saja bergabung?nOh tunggu, itu hanya {first}.*", #One Punch ma
    "Hei, {first}, pernah mendengar King Engine?*", #One Punch ma
    "Hei, {first}, kosongkan kantongmu.*",
    "Hei, {first}!, apakah anda kuat?*",
    "Panggil Avengers! - [pertama} baru saja bergabung dengan obrolan.*",
    "{first} bergabung. Anda harus membangun tiang tambahan.*",
    "Ermagherd. [pertama} ada di sini.*",
    "Datanglah untuk Balap Siput, Tetap untuk Chimichangas!*",
    "Siapa yang butuh Google? Anda adalah segala sesuatu yang kami cari .*",
    "Tempat ini harus memiliki WiFi gratis, karena saya merasakan koneksi.*",
    "Bicaralah dengan teman dan masuklah.*",
    "Selamat datang anda*",
    "Selamat datang {first}, putrimu ada di kastil lain.*",
    "Hai {first}, selamat datang di sisi gelap.*",
    "Hola {first}, waspadalah terhadap orang-orang dengan tingkat bencana*",
    "Hei {first}, kami memiliki droid yang Anda cari.*",
    "Hai {first}nIni bukan tempat yang aneh, ini adalah rumah saya, itu adalah orang-orang yang aneh.*",
    "Oh, hei {first} apa kata sandinya?*",
    "Hei {first}, aku tahu apa yang akan kita lakukan hari ini*",
    "{first} baru saja bergabung, waspadalah mereka bisa menjadi mata-mata.*",
    "{first} bergabung dengan grup, dibaca oleh Mark Zuckerberg, CIA dan 35 lainnya.*",
    "Selamat datang {first}, hati-hati dengan monyet yang jatuh.*",
    "Semua orang menghentikan apa yang Anda lakukan, Kami sekarang berada di hadapan {first}.*",
    "Hei {first}, apakah Anda ingin tahu bagaimana saya mendapatkan bekas luka ini?*",
    "Selamat datang {first}, jatuhkan senjata anda dan lanjutkan ke pemindai mata-mata.*",
    "Tetap aman {first}, Jaga jarak sosial 3 meter di antara pesan anda.*", #Corona meme lmao
    "Hei {first}, Kau tahu aku pernah satu pukulan meteorit?*",
    "Anda di sini sekarang {first}, Perlawanan sia-sia*",
    "{first} baru saja tiba, kekuatannya kuat dengan yang satu ini.*",
    "{first} baru saja bergabung atas perintah presiden.*",
    "Hai {first}, apakah gelas setengah penuh atau setengah kosong?*",
    "Yipee Kayaye {first} tiba.*",
    "*Welcome {first}, if you’re a secret agent press 1, otherwise start a conversation*",
    "*{first}, I have a feeling we’re not in Kansas anymore.*",
    "*They may take our lives, but they’ll never take our {first}.*",
    "*Coast is clear! You can come out guys, it’s just {first}.*",
    "*Welcome {first}, pay no attention to that guy lurking.*",
    "*Welcome {first}, may the force be with you.*",
    "*May the {first} be with you.*",
    "*{first} just joined. Hey, where's Perry?*",
    "*{first} just joined. Oh, there you are, Perry.*",
    "*Ladies and gentlemen, I give you ...  {first}.*",
    "*Behold my new evil scheme, the {first}-Inator.*",
    "*Ah, {first} the Platypus, you're just in time... to be trapped.*",
    "*snaps fingers and teleports {first} here*",
    "*{first}! What is a fish and a rabbit combined?*",  #Lifereload - kaizoku member.
    "*{first} just arrived. Diable Jamble!*",  #One Piece Sanji
    "*{first} just arrived. Aschente!*",  #No Game No Life
    "*{first} say Aschente to swear by the pledges.*",  #No Game No Life
    "*{first} just joined. El Psy congroo!*",  #Steins Gate
    "*Irasshaimase {first}!*",  #weeabo shit
    "*Hi {first}, what is 1000-7?*",  #tokyo ghoul
    "*Come. I don't want to destroy this place*",  #hunter x hunter
    "*I... am... Whitebeard!...wait..wrong anime.*",  #one Piece
    "*Hey {first}...have you ever heard these words?*",  #BNHA
    "*Can't a guy get a little sleep around here?*",  #Kamina Falls – Gurren Lagann
    "*It's time someone put you in your place, {first}.*",  #Hellsing
    "*Unit-01's reactivated..*",  #Neon Genesis: Evangelion
    "*Prepare for trouble...And make it double*",  #Pokemon
    "*Hey {first}, are You Challenging Me?*",  #Shaggy
    "*Oh? You're Approaching Me?*",  #jojo
    "*{first} just warped into the group!*",
    "*I..it's..it's just {first}.*",
    "*Sugoi, Dekai. {first} Joined!*",
    "*{first}, do you know gods of death love apples?*",  #Death Note owo
    "*I'll take a potato chip.... and eat it*",  #Death Note owo
    "*Oshiete oshiete yo sono shikumi wo!*",  #Tokyo Ghoul
    "*Kaizoku ou ni...nvm wrong anime.*",  #op
    "*{first} just joined! Gear.....second!*",  #Op
    "*Omae wa mou....shindeiru*",
    "*Hey {first}, the leaf village lotus blooms twice!*",  #Naruto stuff begins from here
    "*{first} Joined! Omote renge!*",
    "*{first} joined!, Gate of Opening...open!*",
    "*{first} joined!, Gate of Healing...open!*",
    "*{first} joined!, Gate of Life...open!*",
    "*{first} joined!, Gate of Pain...open!*",
    "*{first} joined!, Gate of Limit...open!*",
    "*{first} joined!, Gate of View...open!*",
    "*{first} joined!, Gate of Shock...open!*",
    "*{first} joined!, Gate of Death...open!*",
    "*{first}! I, Madara! declare you the strongest*",
    "*{first}, this time I'll lend you my power.*",  #Kyuubi to naruto
    "*{first}, welcome to the hidden leaf village!*",  # Naruto thingies end here
    "*In the jungle, you must wait...until the dice read five or eight.*",  #Jumanji stuff
    "*Dr.{first} Famed archeologist and international explorer,\nWelcome to Jumanji!\nJumanji's Fate is up to you now.*",
    "*{first}, this will not be an easy mission - monkeys slow the expedition.*",  #End of Jumanji stuff
]
DEFAULT_GOODBYE_MESSAGES = [
    "{first} will be missed.",
    "{first} just went offline.",
    "{first} has left the lobby.",
    "{first} has left the clan.",
    "{first} has left the game.",
    "{first} has fled the area.",
    "{first} is out of the running.",
    "Nice knowing ya, {first}!",
    "It was a fun time {first}.",
    "We hope to see you again soon, {first}.",
    "I donut want to say goodbye, {first}.",
    "Goodbye {first}! Guess who's gonna miss you :')",
    "Goodbye {first}! It's gonna be lonely without ya.",
    "Please don't leave me alone in this place, {first}!",
    "Good luck finding better shit-posters than us, {first}!",
    "You know we're gonna miss you {first}. Right? Right? Right?",
    "Congratulations, {first}! You're officially free of this mess.",
    "{first}. You were an opponent worth fighting.",
    "You're leaving, {first}? Yare Yare Daze.",
    "Bring him the photo",
    "Go outside!",
    "Ask again later",
    "Think for yourself",
    "Question authority",
    "You are worshiping a sun god",
    "Don't leave the house today",
    "Give up!",
    "Marry and reproduce",
    "Stay asleep",
    "Wake up",
    "Look to la luna",
    "Steven lives",
    "Meet strangers without prejudice",
    "A hanged man will bring you no luck today",
    "What do you want to do today?",
    "You are dark inside",
    "Have you seen the exit?",
    "Get a baby pet it will cheer you up.",
    "Your princess is in another castle.",
    "You are playing it wrong give me the controller",
    "Trust good people",
    "Live to die.",
    "When life gives you lemons reroll!",
    "Well, that was worthless",
    "I fell asleep!",
    "May your troubles be many",
    "Your old life lies in ruin",
    "Always look on the bright side",
    "It is dangerous to go alone",
    "You will never be forgiven",
    "You have nobody to blame but yourself",
    "Only a sinner",
    "Use bombs wisely",
    "Nobody knows the troubles you have seen",
    "You look fat you should exercise more",
    "Follow the zebra",
    "Why so blue?",
    "The devil in disguise",
    "Go outside",
    "Always your head in the clouds",
]
# Line 111 to 152 are references from https://bindingofisaac.fandom.com/wiki/Fortune_Telling_Machine


class Welcome(BASE):
    __tablename__ = "welcome_pref"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)
    should_goodbye = Column(Boolean, default=True)
    custom_content = Column(UnicodeText, default=None)

    custom_welcome = Column(
        UnicodeText, default=random.choice(DEFAULT_WELCOME_MESSAGES))
    welcome_type = Column(Integer, default=Types.TEXT.value)

    custom_leave = Column(
        UnicodeText, default=random.choice(DEFAULT_GOODBYE_MESSAGES))
    leave_type = Column(Integer, default=Types.TEXT.value)

    clean_welcome = Column(BigInteger)

    def __init__(self, chat_id, should_welcome=True, should_goodbye=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome
        self.should_goodbye = should_goodbye

    def __repr__(self):
        return "<Chat {} should Welcome new users: {}>".format(
            self.chat_id, self.should_welcome)


class WelcomeButtons(BASE):
    __tablename__ = "welcome_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.name = name
        self.url = url
        self.same_line = same_line


class GoodbyeButtons(BASE):
    __tablename__ = "leave_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.name = name
        self.url = url
        self.same_line = same_line


class WelcomeMute(BASE):
    __tablename__ = "welcome_mutes"
    chat_id = Column(String(14), primary_key=True)
    welcomemutes = Column(UnicodeText, default=False)

    def __init__(self, chat_id, welcomemutes):
        self.chat_id = str(chat_id)  # ensure string
        self.welcomemutes = welcomemutes
        
        
class CombotCASStatus(BASE):
    __tablename__ = "cas_stats"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=True)
    autoban = Column(Boolean, default=False)

    
class DefenseMode(BASE):
    __tablename__ = "defense_mode"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=False)
    
    def __init__(self, chat_id, status):
        self.chat_id = str(chat_id)
        self.status = status

        
class AutoKickSafeMode(BASE):
    __tablename__ = "autokicks_safemode"
    chat_id = Column(String(14), primary_key=True)
    timeK = Column(Integer, default=90)
    
    def __init__(self, chat_id, timeK):
        self.chat_id = str(chat_id)
        self.timeK = timeK
        
class WelcomeMuteUsers(BASE):
    __tablename__ = "human_checks"
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    human_check = Column(Boolean)

    def __init__(self, user_id, chat_id, human_check):
        self.user_id = (user_id)  # ensure string
        self.chat_id = str(chat_id)
        self.human_check = human_check


class CleanServiceSetting(BASE):
    __tablename__ = "clean_service"
    chat_id = Column(String(14), primary_key=True)
    clean_service = Column(Boolean, default=True)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return "<Chat used clean service ({})>".format(self.chat_id)


Welcome.__table__.create(checkfirst=True)
WelcomeButtons.__table__.create(checkfirst=True)
GoodbyeButtons.__table__.create(checkfirst=True)
WelcomeMute.__table__.create(checkfirst=True)
WelcomeMuteUsers.__table__.create(checkfirst=True)
CleanServiceSetting.__table__.create(checkfirst=True)
CombotCASStatus.__table__.create(checkfirst=True)
DefenseMode.__table__.create(checkfirst=True)
AutoKickSafeMode.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()
WELC_BTN_LOCK = threading.RLock()
LEAVE_BTN_LOCK = threading.RLock()
WM_LOCK = threading.RLock()
CS_LOCK = threading.RLock()
CAS_LOCK = threading.RLock()
DEFENSE_LOCK = threading.RLock()
AUTOKICK_LOCK = threading.RLock()

def welcome_mutes(chat_id):
    try:
        welcomemutes = SESSION.query(WelcomeMute).get(str(chat_id))
        if welcomemutes:
            return welcomemutes.welcomemutes
        return False
    finally:
        SESSION.close()


def set_welcome_mutes(chat_id, welcomemutes):
    with WM_LOCK:
        prev = SESSION.query(WelcomeMute).get((str(chat_id)))
        if prev:
            SESSION.delete(prev)
        welcome_m = WelcomeMute(str(chat_id), welcomemutes)
        SESSION.add(welcome_m)
        SESSION.commit()


def set_human_checks(user_id, chat_id):
    with INSERTION_LOCK:
        human_check = SESSION.query(WelcomeMuteUsers).get(
            (user_id, str(chat_id)))
        if not human_check:
            human_check = WelcomeMuteUsers(user_id, str(chat_id), True)

        else:
            human_check.human_check = True

        SESSION.add(human_check)
        SESSION.commit()

        return human_check


def get_human_checks(user_id, chat_id):
    try:
        human_check = SESSION.query(WelcomeMuteUsers).get(
            (user_id, str(chat_id)))
        if not human_check:
            return None
        human_check = human_check.human_check
        return human_check
    finally:
        SESSION.close()


def get_welc_mutes_pref(chat_id):
    welcomemutes = SESSION.query(WelcomeMute).get(str(chat_id))
    SESSION.close()

    if welcomemutes:
        return welcomemutes.welcomemutes

    return False


def get_welc_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    if welc:
        return welc.should_welcome, welc.custom_welcome, welc.custom_content, welc.welcome_type

    else:
        # Welcome by default.
        return True, DEFAULT_WELCOME, None, Types.TEXT


def get_gdbye_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    if welc:
        return welc.should_goodbye, welc.custom_leave, welc.leave_type
    else:
        # Welcome by default.
        return True, DEFAULT_GOODBYE, Types.TEXT


def set_clean_welcome(chat_id, clean_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id))
        if not curr:
            curr = Welcome(str(chat_id))

        curr.clean_welcome = int(clean_welcome)

        SESSION.add(curr)
        SESSION.commit()


def get_clean_pref(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()

    if welc:
        return welc.clean_welcome

    return False


def set_welc_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id))
        if not curr:
            curr = Welcome(str(chat_id), should_welcome=should_welcome)
        else:
            curr.should_welcome = should_welcome

        SESSION.add(curr)
        SESSION.commit()


def set_gdbye_preference(chat_id, should_goodbye):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id))
        if not curr:
            curr = Welcome(str(chat_id), should_goodbye=should_goodbye)
        else:
            curr.should_goodbye = should_goodbye

        SESSION.add(curr)
        SESSION.commit()


def set_custom_welcome(chat_id,
                       custom_content,
                       custom_welcome,
                       welcome_type,
                       buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)

        if custom_welcome or custom_content:
            welcome_settings.custom_content = custom_content
            welcome_settings.custom_welcome = custom_welcome
            welcome_settings.welcome_type = welcome_type.value

        else:
            welcome_settings.custom_welcome = DEFAULT_WELCOME
            welcome_settings.welcome_type = Types.TEXT.value

        SESSION.add(welcome_settings)

        with WELC_BTN_LOCK:
            prev_buttons = SESSION.query(WelcomeButtons).filter(
                WelcomeButtons.chat_id == str(chat_id)).all()
            for btn in prev_buttons:
                SESSION.delete(btn)

            for b_name, url, same_line in buttons:
                button = WelcomeButtons(chat_id, b_name, url, same_line)
                SESSION.add(button)

        SESSION.commit()


def get_custom_welcome(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = DEFAULT_WELCOME
    if welcome_settings and welcome_settings.custom_welcome:
        ret = welcome_settings.custom_welcome

    SESSION.close()
    return ret


def set_custom_gdbye(chat_id, custom_goodbye, goodbye_type, buttons=None):
    if buttons is None:
        buttons = []

    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)

        if custom_goodbye:
            welcome_settings.custom_leave = custom_goodbye
            welcome_settings.leave_type = goodbye_type.value

        else:
            welcome_settings.custom_leave = DEFAULT_GOODBYE
            welcome_settings.leave_type = Types.TEXT.value

        SESSION.add(welcome_settings)

        with LEAVE_BTN_LOCK:
            prev_buttons = SESSION.query(GoodbyeButtons).filter(
                GoodbyeButtons.chat_id == str(chat_id)).all()
            for btn in prev_buttons:
                SESSION.delete(btn)

            for b_name, url, same_line in buttons:
                button = GoodbyeButtons(chat_id, b_name, url, same_line)
                SESSION.add(button)

        SESSION.commit()


def get_custom_gdbye(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = DEFAULT_GOODBYE
    if welcome_settings and welcome_settings.custom_leave:
        ret = welcome_settings.custom_leave

    SESSION.close()
    return ret


def get_welc_buttons(chat_id):
    try:
        return SESSION.query(WelcomeButtons).filter(
            WelcomeButtons.chat_id == str(chat_id)).order_by(
                WelcomeButtons.id).all()
    finally:
        SESSION.close()


def get_gdbye_buttons(chat_id):
    try:
        return SESSION.query(GoodbyeButtons).filter(
            GoodbyeButtons.chat_id == str(chat_id)).order_by(
                GoodbyeButtons.id).all()
    finally:
        SESSION.close()

        
def get_cas_status(chat_id):
    try:
        resultObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if resultObj:
            return resultObj.status
        return True
    finally:
        SESSION.close()       

        
def set_cas_status(chat_id, status):
    with CAS_LOCK:
        ban = False
        prevObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if prevObj:
            ban = prevObj.autoban
            SESSION.delete(prevObj)
        newObj = CombotCASStatus(str(chat_id), status, ban)
        SESSION.add(newObj)
        SESSION.commit()

        
def get_cas_autoban(chat_id):
    try:
        resultObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if resultObj and resultObj.autoban:
            return resultObj.autoban
        return False
    finally:
        SESSION.close()
        

def set_cas_autoban(chat_id, autoban):
    with CAS_LOCK:
        status = True
        prevObj = SESSION.query(CombotCASStatus).get(str(chat_id))
        if prevObj:
            status = prevObj.status
            SESSION.delete(prevObj)
        newObj = CombotCASStatus(str(chat_id), status, autoban)
        SESSION.add(newObj)
        SESSION.commit()
        
                
def clean_service(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(CleanServiceSetting).get(str(chat_id))
        if chat_setting:
            return chat_setting.clean_service
        return False
    finally:
        SESSION.close()


def set_clean_service(chat_id: Union[int, str], setting: bool):
    with CS_LOCK:
        chat_setting = SESSION.query(CleanServiceSetting).get(str(chat_id))
        if not chat_setting:
            chat_setting = CleanServiceSetting(chat_id)

        chat_setting.clean_service = setting
        SESSION.add(chat_setting)
        SESSION.commit()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)

        with WELC_BTN_LOCK:
            chat_buttons = SESSION.query(WelcomeButtons).filter(
                WelcomeButtons.chat_id == str(old_chat_id)).all()
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)

        with LEAVE_BTN_LOCK:
            chat_buttons = SESSION.query(GoodbyeButtons).filter(
                GoodbyeButtons.chat_id == str(old_chat_id)).all()
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)

        SESSION.commit()
# ANYONE LOOKING AT THIS COMMIT... YOU ARE ALLOWED TO FUCK ME

def getDefenseStatus(chat_id):
    try:
        resultObj = SESSION.query(DefenseMode).get(str(chat_id))
        if resultObj:
            return resultObj.status
        return False #default
    finally:
        SESSION.close()

def setDefenseStatus(chat_id, status):
    with DEFENSE_LOCK:
        prevObj = SESSION.query(DefenseMode).get(str(chat_id))
        if prevObj:
            SESSION.delete(prevObj)
        newObj = DefenseMode(str(chat_id), status)
        SESSION.add(newObj)
        SESSION.commit()

def getKickTime(chat_id):
    try:
        resultObj = SESSION.query(AutoKickSafeMode).get(str(chat_id))
        if resultObj:
            return resultObj.timeK
        return 90 #90 seconds
    finally:
        SESSION.close()

def setKickTime(chat_id, value):
    with AUTOKICK_LOCK:
        prevObj = SESSION.query(AutoKickSafeMode).get(str(chat_id))
        if prevObj:
            SESSION.delete(prevObj)
        newObj = AutoKickSafeMode(str(chat_id), int(value))
        SESSION.add(newObj)
        SESSION.commit()

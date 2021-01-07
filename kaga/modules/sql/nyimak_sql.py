import threading

from kaga.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, Integer, UnicodeText


class NYIMAK(BASE):
    __tablename__ = "nyimak_users"

    user_id = Column(Integer, primary_key=True)
    is_nyimak = Column(Boolean)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason="", is_nyimak=True):
        self.user_id = user_id
        self.reason = reason
        self.is_nyimak = is_nyimak

    def __repr__(self):
        return "nyimak_status for {}".format(self.user_id)


NYIMAK.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()

NYIMAK_USERS = {}


def is_nyimak(user_id):
    return user_id in NYIMAK_USERS


def check_nyimak_status(user_id):
    try:
        return SESSION.query(NYIMAK).get(user_id)
    finally:
        SESSION.close()


def set_nyimak(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(NYIMAK).get(user_id)
        if not curr:
            curr = NYIMAK(user_id, reason, True)
        else:
            curr.is_nyimak = True

        NYIMAK_USERS[user_id] = reason

        SESSION.add(curr)
        SESSION.commit()


def rm_nyimak(user_id):
    with INSERTION_LOCK:
        curr = SESSION.query(NYIMAK).get(user_id)
        if curr:
            if user_id in NYIMAK_USERS:  # sanity check
                del NYIMAK_USERS[user_id]

            SESSION.delete(curr)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def toggle_nyimak(user_id, reason=""):
    with INSERTION_LOCK:
        curr = SESSION.query(NYIMAK).get(user_id)
        if not curr:
            curr = NYIMAK(user_id, reason, True)
        elif curr.is_nyimak:
            curr.is_nyimak = False
        elif not curr.is_nyimak:
            curr.is_nyimak = True
        SESSION.add(curr)
        SESSION.commit()


def __load_nyimak_users():
    global NYIMAK_USERS
    try:
        all_nyimak = SESSION.query(NYIMAK).all()
        NYIMAK_USERS = {
            user.user_id: user.reason for user in all_nyimak if user.is_nyimak
        }
    finally:
        SESSION.close()


__load_nyimak_users()

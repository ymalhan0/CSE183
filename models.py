"""
This file defines the database models
"""
import datetime
from pydal.validators import *
from .common import Field, auth, db, session

def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None


def get_time():
    return datetime.datetime.utcnow()

# Tables here

db.define_table(
    'trade',
    Field('trade_user_id'),
    Field('trade_username', requires=IS_NOT_EMPTY()),
    Field('trade_friend_code', requires=IS_NOT_EMPTY()),
    Field('trade_discord'),
    Field('trade_reddit'),
)

db.define_table(
    'parts',
    Field('trade_id', 'reference trade'),
    Field('part_name', requires=IS_NOT_EMPTY()),
    Field('reserved_by', default='none'),
    Field('have_or_seeking'),
    Field('original_owner'),
    Field('original_trade_friend_code'),
    Field('original_trade_discord'),
    Field('original_trade_reddit'),
)

# table for flight planner
db.define_table(
    'flight_planner',
    Field('planner_id', 'reference auth_user', default=lambda: auth.user_id),
    Field('city_A'),
    Field('city_B'),
)

db.commit()


def del_table():
    db(db.trade).delete()
    db.commit()
    return

# Deletes all entries in the user table, for testing purposes.
# Comment out if not using
# del_table()

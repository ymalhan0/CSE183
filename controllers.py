import uuid
import math

from py4web import URL, Field, abort, action, redirect, request, HTTP
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.url_signer import URLSigner
from .models import get_user_email
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET

from .common import T, auth, cache, db, session, signed_url

from .settings import APP_FOLDER

import os
import json

url_signer = URLSigner(session)

# Grab the city json
filename = os.path.join(APP_FOLDER, "data", "cities.json")
with open(filename, "r") as stream:
    cities = json.load(stream)

# For add_leg controller
cityList = []
for city in cities:
    cityList.append(city["city"])

# Make an object so we can easily access the data within the controllers
fullCityData = {obj["city"]: obj for obj in cities}

# Grab the plane json
plane_filename = os.path.join(APP_FOLDER, "data", "planes.json")
with open(plane_filename, "r") as plane_stream:
    planes = json.load(plane_stream)

# Make an object so we can easily access the data within the controllers
fullPlaneData = {obj["plane"]: obj for obj in planes}


# The auth.user below forces login.
@action("index", method=["GET", "POST"])
@action.uses("index.html", auth.user, url_signer, db, session)
def index():
    return dict()


# ==== TRADING ====

# Part trading page
@action("trading", method=["GET", "POST"])
@action.uses("trading.html", auth.user, url_signer, db, session)
def trading():
    return dict()


# Get all user entries for the main trading table
@action("get_entries", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def get_entries():
    # We don't want to display the current user's entry
    rows = db(db.trade.trade_user_id !=
              auth.current_user.get("id")).select().as_list()
    for row in rows:
        row['have'] = db((db.parts.trade_id == row['id']) & (
            db.parts.have_or_seeking == 'have')).select().as_list()
        row['seeking'] = db((db.parts.trade_id == row['id']) & (
            db.parts.have_or_seeking == 'seeking')).select().as_list()
    return dict(rows=rows)


# Get only the current user's entry for their personal table
@action("get_curr_user_entry", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def get_curr_user_entry():
    rows = db(db.trade.trade_user_id ==
              auth.current_user.get("id")).select().as_list()
    return dict(rows=rows)


# Get the current user's have and seeking parts
@action("get_curr_user_parts", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def get_curr_user_parts():
    userEntry = db(db.trade.trade_user_id ==
                   auth.current_user.get("id")).select().first()
    if userEntry:
        have = db((db.parts.trade_id == userEntry['id']) & (
            db.parts.have_or_seeking == 'have')).select().as_list()
        seeking = db((db.parts.trade_id == userEntry['id']) & (
            db.parts.have_or_seeking == 'seeking')).select().as_list()
        return dict(have=have, seeking=seeking)
    else:
        return dict(have=None, seeking=None)


# Form for editing the user information
@ action("edit_user", method=["GET", "POST"])
@ action.uses("edit_user.html", auth.user, url_signer, db, session)
def edit_user():
    userID = auth.current_user.get("id")
    data = db(db.trade.trade_user_id == userID).select().first()
    if data:
        form = Form([Field('username', requires=IS_NOT_EMPTY()), Field('friendcode', requires=IS_NOT_EMPTY()), Field('discord', requires=IS_NOT_EMPTY()), Field('reddit', requires=IS_NOT_EMPTY())], record=dict(username=data['trade_username'],
                    friendcode=data['trade_friend_code'], discord=data['trade_discord'], reddit=data['trade_reddit']), deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    else:
        form = Form([Field('username', requires=IS_NOT_EMPTY()), Field('friendcode', requires=IS_NOT_EMPTY()), Field('discord', requires=IS_NOT_EMPTY()), Field(
            'reddit', requires=IS_NOT_EMPTY())], deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        db.trade.update_or_insert(db.trade.trade_user_id == userID,
                                  trade_user_id=userID,
                                  trade_username=form.vars['username'],
                                  trade_friend_code=form.vars['friendcode'],
                                  trade_discord=form.vars['discord'],
                                  trade_reddit=form.vars['reddit']
                                  )
        redirect(URL('trading'))
    return dict(form=form)


# Form for adding a 'have' part
@ action("add_have", method=["GET", "POST"])
@ action.uses("add_part.html", auth.user, url_signer, db, session)
def add_have():
    user_id = auth.current_user.get("id")
    userEntry = db(db.trade.trade_user_id == user_id).select().first()
    if userEntry is None:
        print(f"No userEntry for id {user_id}")
        return dict(form=None)
    refID = userEntry['id']
    form = Form([Field('part')], csrf_session=session,
                formstyle=FormStyleBulma)
    if form.accepted:
        db.parts.insert(trade_id=refID,
                        part_name=form.vars['part'],
                        part_owner=userEntry['trade_username'],
                        reserved_by='none',
                        have_or_seeking='have',
                        )
        redirect(URL('trading'))
    return dict(form=form)


# Form for adding a 'seeking' part
@ action("add_seeking", method=["GET", "POST"])
@ action.uses("add_part.html", auth.user, url_signer, db, session)
def add_seeking():
    user_id = auth.current_user.get("id")
    userEntry = db(db.trade.trade_user_id == user_id).select().first()
    if userEntry is None:
        print(f"No userEntry for id {user_id}")
        return dict(form=None)
    refID = userEntry['id']
    form = Form([Field('part')], csrf_session=session,
                formstyle=FormStyleBulma)
    if form.accepted:
        db.parts.insert(trade_id=refID,
                        part_name=form.vars['part'],
                        part_owner=userEntry['trade_username'],
                        reserved_by='none',
                        have_or_seeking='seeking',
                        )
        redirect(URL('trading'))
    return dict(form=form)


# Removes a part
@ action("remove_part", method=["GET", "POST"])
@ action.uses(auth.user, url_signer, db, session)
def remove_part():
    part_id = request.params.get('part_id')
    db(db.parts.id == part_id).delete()
    return 'done'


# ==== FLIGHT PLANNER ====

# Page to show flight planner table
@action("planner", method=["GET", "POST"])
@action.uses("planner.html", auth.user, url_signer, db, session)
def planner():
    rows = db(db.flight_planner.planner_id == auth.get_user()['id']).select()
    for row in rows:
        plans = db(db.flight_planner.planner_id == row.id).select()
        row.plans = plans.as_list()
    return dict(rows=rows, url_signer=url_signer)

# form to add legs to planner, need to add distance


@action("add_leg", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def add_leg():
    citya = request.params.get("citya")
    cityb = request.params.get("cityb")
    db.flight_planner.update_or_insert(
        city_A=citya,
        city_B=cityb)
    rows = db(db.flight_planner).select()
    return dict()

# edit a leg of plan


@action('edit_plan/<plan_id:int>', method=["GET", "POST"])
@action.uses('edit_plan.html', url_signer, db, session, auth.user)
def edit_plan(plan_id):
    # user check w/out url signer
    use = db.flight_planner[plan_id]
    if not use or use.planner_id != auth.user_id:
        raise HTTP(400)
    p = db.flight_planner[plan_id]
    form = Form([Field('Starting_City', default=p.city_A, requires=IS_IN_SET(cityList)),
                 Field('Ending_City', default=p.city_B, requires=IS_IN_SET(cityList))], deletable=False, csrf_session=session, formstyle=FormStyleBulma)
    if form.accepted:
        p.update_record(
            city_A=form.vars['Starting_City'], city_B=form.vars['Ending_City'])
        redirect(URL('planner'))
    rows = db(db.flight_planner).select()
    return dict(form=form, rows=rows)

# delete a row


@action('delete_plan/<plan_id:int>')
@action.uses(db, session, auth.user)
def delete_plan(plan_id):
    # user check w/out url signer
    use = db.flight_planner[plan_id]
    if not use or use.planner_id != auth.user_id:
        raise HTTP(400)
    db(db.flight_planner.id == plan_id).delete()
    redirect(URL('planner'))

# delete entire plan data


@action('delete_plan_table')
@action.uses(db, session, auth.user)
def delete_plan_table():
    db(db.flight_planner.planner_id == auth.current_user.get("id")).delete()
    redirect(URL('planner'))

# Page to show flight planner table


@action("get_planner", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def get_planner():
    rows = db(db.flight_planner.planner_id == auth.get_user()['id']).select()
    for row in rows:
        plans = db(db.flight_planner.planner_id == row.id).select()
        row.plans = plans.as_list()

        # Calc and add the distance
        row["distance"] = (math.floor(math.sqrt(math.pow(int(fullCityData[row.city_B]['x']) - int(fullCityData[row.city_A]
                           ['x']), 2) + math.pow(int(fullCityData[row.city_B]['y']) - int(fullCityData[row.city_A]['y']), 2))) * 4)
    return dict(rows=rows, url_signer=url_signer)

# Grab information so we can generate flight stats


@action("planner_get_info", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def planner_get_info():
    cities = request.params.get("cities").split(',')
    plane = request.params.get("plane")

    cityReturn = []
    for city in cities:
        cityReturn.append(fullCityData[city])

    planeReturn = fullPlaneData[plane]

    return dict(cityReturn=cityReturn, planeReturn=planeReturn)


# ==== DISTANCE CALCULATOR ====

# Distance calculation page
@ action("distance", method=["GET", "POST"])
@ action.uses("distance.html", auth.user, url_signer, db, session)
def distance():
    return dict()

# Used to get cities


@ action("get_cities", method=["GET", "POST"])
@ action.uses(auth.user, url_signer, db, session)
def get_cities():
    # Return the city dict we pull from the json file
    return dict(cities=cities, planes=planes)


# ==== OFFERS AND RESERVATIONS ====

# Swaps reservation status
@action("swap_reservation", method=["GET", "POST"])
@action.uses(auth.user, url_signer, db, session)
def swap_reservation():
    part_id = request.params.get('part_id')
    entry = db(db.parts.id == part_id).select().first()

    userEntry = db(db.trade.trade_user_id ==
                   auth.current_user.get("id")).select().first()

    # check if the current user is the owner of the part
    if entry.trade_id == userEntry['id']:
        return dict(error="You can't reserve your own part")

    reserveStatus = entry['reserved_by']

    if reserveStatus == 'none':
        db(db.parts.id == part_id).update(
            reserved_by=userEntry['trade_username'], part_owner=userEntry['trade_username'])
    else:
        db(db.parts.id == part_id).update(
            reserved_by='none', part_owner=entry['original_owner'])

    entryFinal = db(db.parts.id == part_id).select().first()

    offers = db((db.parts.reserved_by == userEntry['trade_username']) & (
        db.parts.trade_id != userEntry['id'])).select().as_list()
    reservations = db((db.parts.trade_id == userEntry['id']) & (
        db.parts.reserved_by != 'none')).select().as_list()

    return dict(reserved_by=entryFinal['reserved_by'], offers=offers, reservations=reservations)


# Gets the current user's username in order to properly show
# reservation statuses
@ action("get_current_user", method=["GET", "POST"])
@ action.uses(auth.user, url_signer, db, session)
def get_current_user():
    entry = db(db.trade.trade_user_id ==
               auth.current_user.get("id")).select().first()
    if entry:
        return dict(current_user=entry['trade_username'])
    else:
        return dict(current_user=None)


@action("offers_reservations", method=["GET", "POST"])
@action.uses("offers_reservations.html", auth.user, url_signer, db, session)
def offers_reservations():
    return dict()


@action("get_offers_reservations", method=["GET"])
@action.uses(auth.user, db, session, url_signer)
def get_offers_reservations():
    userEntry = db(db.trade.trade_user_id ==
                   auth.current_user.get("id")).select().first()
    if userEntry:
        username = userEntry['trade_username']
        offers = []
        for part in db((db.parts.reserved_by != 'none') & (db.parts.reserved_by != username) & (
                db.parts.trade_id == userEntry['id'])).select():
            part_dict = part.as_dict()
            reserved_by_user = db(db.trade.trade_username ==
                                  part.reserved_by).select().first()
            part_dict['friend_code'] = reserved_by_user.trade_friend_code
            part_dict['discord_username'] = reserved_by_user.trade_discord
            part_dict['reddit_username'] = reserved_by_user.trade_reddit

            offers.append(part_dict)

        reservations = []
        for part in db((db.parts.reserved_by == username) & (db.parts.trade_id != userEntry['id'])).select():
            part_dict = part.as_dict()
            part_dict['original_owner'] = db(
                db.trade.id == part.trade_id).select().first().trade_username
            part_dict['original_friend_code'] = db(
                db.trade.id == part.trade_id).select().first().trade_friend_code
            part_dict['original_discord_username'] = db(
                db.trade.id == part.trade_id).select().first().trade_discord
            part_dict['original_reddit_username'] = db(
                db.trade.id == part.trade_id).select().first().trade_reddit
            reservations.append(part_dict)

        return dict(offers=offers, reservations=reservations)
    else:
        return dict(offers=[], reservations=[])


@action("complete_offer", method=["POST"])
@action.uses(auth.user, db, session, url_signer)
def complete_offer():
    offer_id = request.json.get('id')
    db(db.parts.id == offer_id).delete()
    return "done"


@action("decline_trade", method=["POST"])
@action.uses(auth.user, db, session, url_signer)
def decline_trade():
    offer_id = request.json.get('id')
    db(db.parts.id == offer_id).update(reserved_by='none')
    return "done"


@action("unreserve_trade", method=["POST"])
@action.uses(auth.user, db, session, url_signer)
def unreserve_trade():
    part_id = request.json.get('id')
    db(db.parts.id == part_id).update(reserved_by='none')
    return "done"

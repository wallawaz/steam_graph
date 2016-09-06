#!/usr/bin/env python
from __future__ import absolute_import

import logging
import os
import yaml

import flask
from flask import g
from time import sleep

import simplejson as json
import sqlite3
import requests

from queries import queries
from datetime import datetime
import steamdb_v2

steam = steamdb_v2.SteamDB()

app = flask.Flask(
    "steamdb",
    template_folder="templates",
    static_folder="static",
)

cursor_execute = steamdb_v2.cursor_execute
DETAILS_COUNTER = 0
DETAILS_MAX = 60

@app.errorhandler(404)
def page_not_found(error):
    return flask.render_template("404.html")


@app.errorhandler(500)
def internal_server_error(error):
    return flask.render_template("500.html")


@app.route("/list")
def list():
    if app.debug:
        query = queries.genre_counts
    else:
        pass
        #query = queries.list()

    result = {
        "genres": []
    }

    with cursor_execute(connection, query) as cursor:
        for row in cursor:
            result["genres"].append( (row[0], row[1], row[2]) )

    return json.dumps(result)


@app.route("/top_games/<genre_id>")
def top_games(genre_id):
    genre_id = int(genre_id)
    query = queries.genre_top_games.format(genre_id=genre_id)

    result = {
        "top_games": []
    }

    with cursor_execute(connection, query) as cursor:
        for rank, row in enumerate(cursor):
            obj = {
                "rank": rank + 1,
                "id": row[0],
                "game": row[1],
                "players": row[2],
            }
            result["top_games"].append(obj)

    return json.dumps(result)


@app.route("/as_of")
def as_of():
    query = """
    select
        ts
    from
        steam_last_call"""

    result = {
        "ts": [],
    }
    with cursor_execute(connection, query) as cursor:
        for row in cursor:
            ts = row[0]
            ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
            ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            result["ts"].append(ts)

    return json.dumps(result)


@app.route("/details/<id>")
def details(id):

    # the will pause the request if DETAILS COUNTER == MAX
    api_counter()

    id = str(id)
    url = steam.steam_url + id
    response = requests.get(url)
    if response.status_code != 200:
        return json.dumps({
            "error": str(response)
        })

    response = response.json()

    response = response[id]
    try:
        data = response[u"data"]
    except KeyError:
        return json.dumps(response)

    platforms = "platforms" in data
    metacritic = "metacritic" in data
    header_image = "header_image" in data

    out = {}
    if platforms:
        out["platforms"] = data["platforms"]
    if metacritic:
        out["metacritic"] = data["metacritic"]
    if header_image:
        out["header_image"] = data["header_image"]

    return json.dumps(out)


def api_counter():
    global DETAILS_COUNTER
    global DETAILS_MAX

    DETAILS_COUNTER += 1

    #print DETAILS_COUNTER

    less_than = DETAILS_COUNTER <= DETAILS_MAX

    if less_than:
        return less_than
    else:
        while not less_than:
            print "pausing 1 second and decreasing counter by 1"
            sleep(1.08)
            DETAILS_COUNTER -= 1
            less_than = DETAILS_COUNTER <= DETAILS_MAX
        return less_than


@app.route("/")
def index():
    if app.debug:
        return flask.render_template("dev.html")
    return flask.render_template("prod.html")

if __name__ == "__main__":
    connection = sqlite3.connect(steamdb_v2.db_path, check_same_thread=False)
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=steam.debug
    )

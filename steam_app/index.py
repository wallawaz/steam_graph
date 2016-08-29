#!/usr/bin/env python
from __future__ import absolute_import

import logging
import os
import yaml

import flask
import simplejson as json
#from sqlalchemy import create_engine
import sqlite3

from contextlib import contextmanager
from queries import queries
from datetime import datetime


config = {}
with open(os.environ.get("STEAM_CONFIG", "/etc/steam/steam.yaml")) as f:
    config = yaml.load(f)


app = flask.Flask(
    # __name__,
    "steamdb",
    template_folder="templates",
    static_folder="static",
)

def connect():
    """connect to sqlite db with steam data"""
    url = config["db"]["main_url"]
    return sqlite3.connect(url, check_same_thread=False)


@contextmanager
def cursor_execute(connection, sql):
    curr = connection.cursor()
    curr.execute(sql)
    connection.commit()
    yield curr
    curr.close()


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
                "game": row[0],
                "players": row[1],
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


@app.route("/")
def index():
    if app.debug:
        return flask.render_template("dev.html")
    return flask.render_template("prod.html")

if __name__ == "__main__":
    connection = connect()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=config["general"]["in_dev_mode"],
    )

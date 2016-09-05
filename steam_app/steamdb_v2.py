import requests
import sqlite3
import time
import os
import yaml

from contextlib import contextmanager
from collections import Counter
from datetime import datetime
from random import randrange

from bs4 import BeautifulSoup
import data.iso_codes as iso_codes

import schema

#current_dir = os.path.dirname(os.path.realpath(__file__))
#data_dir = current_dir + "/data/"
#db_path = data_dir + "steamdb.sqlite"

confg = {}
with open(os.environ.get("STEAM_CONFIG", "/etc/steam/steam.yaml")) as f:
    config = yaml.load(f)

db_path = config["db"]["main_url"]
top_url = "https://steamdb.info/graph/"
steam_url = "http://store.steampowered.com/api/appdetails?appids="
sleep = lambda x: time.sleep(x)
debug = config["general"]["in_dev_mode"]

@contextmanager
def cursor_execute(connection, sql, params=[]):
    curr = connection.cursor()
    curr.execute(sql, params)
    connection.commit()
    yield curr
    curr.close()


class SteamDB(object):

    def __init__(self):
        self.dbh = sqlite3.connect(db_path)
        self.top_url = top_url
        self.steam_url = steam_url
        self.missing_ids = Counter()
        self.debug = debug

    def create_tables(self):
        for s in schema.schema_statements:
            cursor_execute(self.dbh, s)


    def get_element_values(self, elem):
        elem = elem.contents
        id = elem[1]["data-appid"]
        name = elem[5].text
        peak_count = elem[7]["data-sort"]
        return (id, name, peak_count)


    def process_id(self, id, name, peak_count):
        try:
            id = int(id)
            peak_count = int(peak_count)
        except ValueError:
            return 0

        insert_query = """
            insert or replace into steam_apps (
                    id,
                    name,
                    peak_count
                ) values (
                    ?,
                    ?,
                    ?
                )
            """
        params = [id, name, peak_count]
        with cursor_execute(self.dbh, insert_query, params=params) as curr:
            return curr.rowcount

    def get_current_top_games(self):
        response = requests.get(self.top_url)
        if response.status_code != 200:
        # logging
            print "Status error %s for %s" % (steamdb_url, response.status_code)
            yield None

        else:
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.find_all(class_ = "app hidden")
            for elem in elements:
                yield elem

    def get_ids_missing_genres(self):
        query = """
            select id from steam_apps where not exists (
                select steam_id
                from steam_apps_genres
                where steam_id = steam_apps.id)

                and not exists (
                    select steam_id
                    from steam_apps_no_genre
                    where steam_apps_no_genre.steam_id = steam_apps.id)
        """
        with cursor_execute(self.dbh, query) as curr:
            for result in curr:
                yield result[0]


    def get_genres(self, ids=None, cc=False):
        """
        200 requests per 5 minutes and multi-appid support removed.
        """
        if ids == None:
            ids = [ i for i in self.get_ids_missing_genres() ]

        counter = 0
        max_counter = 190
        max_seconds = 300

        def time_check(threshold):
            curr = self.dbh.cursor()
            ts = curr.execute("select ts from steam_last_call").fetchone()
            ts = ts[0]
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")
            seconds = (datetime.now() - dt).seconds
            if seconds <= threshold:
                return False
            return True

        first_check = False
        while not first_check:
            first_check = time_check(max_seconds)
            # logging
            if not first_check:
                print "already ran genres within threshold - pausing 1 min"
                sleep(60)

        for i in ids:
            if counter == max_counter:
                second_check = time_check(max_seconds)
                if not second_check:
                    log =  "got: {0} started at: {1} - waiting"
                    print log.format(counter, str(datetime.now()))
                    random_extra_seconds = randrange(1, 9)
                    sleep(max_seconds + random_extra_seconds)
                    counter = 0

            else:
                counter += 1
                id_str = str(i)
                url = self.steam_url + id_str

                if cc:
                    random_cc = iso_codes.get_random_top_iso_code()
                    url_append = "&cc=" + random_cc

                    print "%s: cc=%s" % (id_str, random_cc)
                    url += url_append

                if counter == 1:
                    now = datetime.now()
                    curr = self.dbh.cursor()
                    # logging
                    print "Starting %s at: %s" % (max_counter, str(now))
                    curr.execute("delete from steam_last_call")
                    curr.execute("insert into steam_last_call (ts) values (?)"
                                , [now])
                    self.dbh.commit()
                    curr.close()

                response = requests.get(url)

                if response.status_code != 200:
                # logging
                    print "steampowered error: %s : %s" (id_str,
                                                     response.status_code)
                else:
                    self.process_genre(response)

    def process_genre(self, response):
        """
        1. gather genre info from json
        2. if genre doesn't exist insert into db
        3. insert steam_id and genre_id into `steam_apps_genres`
        """
        data = None
        response = response.json()
        response_id = response.keys()[0]
        response_id_int = int(response_id)
        try:
            data = response[response_id]["data"]
        except KeyError:
            # logging
            print "data not found for id:  %s" % response_id
            self.missing_ids.update([response_id])
            sleep(1)
            return None

        if data:
            try:
                genres = data["genres"]
            except KeyError:
                # logging
                print "genres not found for id: %s" % response_id
                # this steam id was found on `store.steampowered.com`, but does
                # not have a genre... we don't want to query for it again.
                self.set_no_genre(response_id_int)
                sleep(1)
                return None

            for genre in genres:

                genre_id = int(genre["id"])
                description = genre["description"]
                params = [genre_id, description]
                query = """
                    select id
                    from steam_genres
                    where id = ? and genre = ?
                """

                found = 0
                with cursor_execute(self.dbh, query, params=params) as curr:
                    for row in curr:
                        found +=1

                if found == 0:
                    print "new genre found: %s" % description
                    query = """
                        insert or replace into steam_genres (
                        id,
                        genre
                    ) values (
                        ?,
                        ?
                    )"""

                    with cursor_execute(self.dbh, query, params=params) as curr:
                        inserted = curr.rowcount

                # If we got a response for an id that we initially missed.
                if response_id in self.missing_ids:
                    del self.missing_ids[response_id]

            sleep(1)

    def other_territories_counter(self):
        send_out_again = []
        for i in self.missing_ids:
            attempts = self.missing_ids[i]
            if attempts < 4:
                send_out_again.append(i)
            else:
                # logging
                print "%s: checked 4 times ..." % i
                self.set_no_genre(i)

        if send_out_again:
            print "steam ids still checked < 4 times. retrying"
            return send_out_again
        return None

    # continously run...#XXX may to need to fix
    def check_other_territories(self):
        query_again = [True]
        while query_again:
            query_again = self.other_territories_counter()
            if query_again:
                self.get_genres(query_again, cc=True)
        return 1

    def set_no_genre(self, steam_id):
        insert_query = """
            insert or replace into steam_apps_no_genre (steam_id) values (?)
        """
        params = [steam_id]
        with cursor_execute(self.dbh, insert_query, params=params) as curr:
            return curr.rowcount


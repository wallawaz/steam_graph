import requests
import os
import sys
import sqlite3
import time


from collections import Counter
from datetime import datetime
from random import randrange

from bs4 import BeautifulSoup
import data.iso_codes as iso_codes

current_dir = os.path.dirname(os.path.realpath(__file__))
#current_dir = current_dir.split("/")
#parent_dir = "/".join(current_dir[:-1])
data_dir = current_dir + "/data/"

db_path = data_dir + "steamdb.sqlite"
top_url = "https://steamdb.info/graph/"
steam_url = "http://store.steampowered.com/api/appdetails?appids="
sleep = lambda x: time.sleep(x)

class SteamDB(object):

    def __init__(self):
        self.dbh = sqlite3.connect(db_path)
        self.top_url = top_url
        self.steam_url = steam_url
        self.missing_ids = Counter()

    def create_tables(self):
        stmts = ["""
            create table if not exists steam_apps (
                id integer,
                name text,
                peak_count integer,
                primary key(id, name)
            )""",
            """
            create table if not exists steam_genres (
                id integer,
                genre text,
                primary key(id, genre)
            )""",
            """
            create table if not exists steam_apps_genres (
                steam_id integer,
                genre_id integer,
                primary key(steam_id, genre_id),
                foreign key(steam_id) references steam_apps(id),
                foreign key(genre_id) references genres(id)
            )""",
            """
            create table if not exists steam_last_call (
                 ts datetime
            )""",
            """
            create table if not exists steam_apps_no_genre (
                 steam_id integer,
                 primary key(steam_id),
                 foreign key(steam_id) references steam_apps(id)
            )""",
        ]
        for s in stmts:
            curr = self.dbh.cursor()
            curr.execute(s)
        self.dbh.commit()


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

        curr = self.dbh.cursor()
        curr.execute("""
                insert or replace into steam_apps (
                    id,
                    name,
                    peak_count
                ) values (
                    ?,
                    ?,
                    ?
                )
                """,[id, name, peak_count])

        self.dbh.commit()
        curr.close()


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

    def get_ids(self):
        curr = self.dbh.cursor()
        curr.execute("""
            select id from steam_apps where not exists (
                select steam_id
                from steam_apps_genres
                where steam_id = steam_apps.id)

                and not exists (
                    select steam_id
                    from steam_apps_no_genre
                    where steam_apps_no_genre.steam_id = steam_apps.id)
                """)
        self.dbh.commit()
        return curr


    def get_genres(self, ids=None, cc=False):
        """
        200 requests per 5 minutes and multi-appid support removed.
        """
        if ids == None:
            ids = self.get_ids()
            ids = [i[0] for i in ids]

        #results_left = True

        counter = 0
        max_counter = 180
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
                    random_extra_seconds = randrange(1, 11)
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
        gather genre info from json
        if genre doesn't exist insert into db
        insert steam_id and genre_id into `steam_apps_genres`
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

                curr = self.dbh.cursor()
                curr.execute("""
                    insert or replace into steam_genres (
                        id,
                        genre

                    ) values (
                        ?,
                        ?
                    )""", [genre_id, description])
                #self.dbh.commit()
                #curr.close()

                # logging
                print "%s : %s" % (response_id_int, genre_id)
                #curr = self.dbh.cursor()
                curr.execute("""
                    insert or replace into steam_apps_genres (
                        steam_id,
                        genre_id
                    ) values (
                         ?,
                         ?
                    )""", [response_id_int, genre_id])
                self.dbh.commit()
                curr.close()

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
        curr = self.dbh.cursor()
        curr.execute("""
            insert or replace into steam_apps_no_genre (steam_id) values (?)
        """, [steam_id])
        self.dbh.commit()
        curr.close()


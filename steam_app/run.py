from __future__ import absolute_import

import argparse
import sys
from steamdb_v2 import SteamDB

parser = argparse.ArgumentParser()
parser.add_argument("--top-games", help="run get_current_top_games()",
                    action="store_true")
parser.add_argument("--genres", help="run get_genres", action="store_true")
parser.add_argument("--tables", help="create tables in sqlitedb",
                    action="store_true")
args = parser.parse_args()

if __name__ == "__main__":
    if not (args.top_games or args.genres or args.tables):
        sys.exit(1)

    steam = SteamDB()

    if args.tables:
        steam.create_tables()
        steam.dbh.commit()

    if args.top_games:
        for elem in steam.get_current_top_games():
            if elem:
                values = steam.get_element_values(elem)
                steam.process_id(values[0], values[1], values[2])
    if args.genres:
        steam.get_genres()
        steam.check_other_territories()

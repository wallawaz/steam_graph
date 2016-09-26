# -*- coding: utf-8 -*-

import sqlite3
import steamdb_v2

from index import create_app

steam = steamdb_v2.SteamDB()
application = create_app(steam)

if __name__ == "__main__":    
    #connection = sqlite3.connect(steamdb_v2.db_path, check_same_thread=False)
    application.run("0.0.0.0", port=8000)
    

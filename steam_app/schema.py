schema_statements = ["""
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


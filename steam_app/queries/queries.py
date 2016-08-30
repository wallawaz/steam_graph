genre_counts = """
    select
        a.id as genre_id,
        a.genre,
        sum(peak_count) as player_count
    from
        steam_genres a join steam_apps_genres b
        on a.id  = b.genre_id
        join steam_apps c
        on b.steam_id = c.id

    group by
        a.genre
    order by
        1
"""

genre_top_games = """
    select
        a.id,
        a.name,
        a.peak_count as players
    from
        steam_apps a join steam_apps_genres b
        on a.id = b.steam_id
    where
        b.genre_id = {genre_id}
    order by
        peak_count desc
    limit 10
"""

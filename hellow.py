import polars as pl
import sportsdataverse.pwhl as pwhl
from sportsdataverse.errors import AssetFetchError, NoDataError


# The inaugural season is 2024; this helper tracks the latest known season.
def safe(label, thunk):
    try:
        out = thunk()
        print(f"✅ {label}")
        return out
    except (NoDataError, AssetFetchError) as e:
        print(f"\u23ed\ufe0f  {label}: {type(e).__name__}: {e}")
        return None
    

schedule = pwhl.load_pwhl_schedule(seasons=[2026])
schedule.select([
    'game_id', 'game_date', 'home_team', 'away_team',
    'home_score', 'away_score', 'winner', 'game_type',
]).head()

rosters = pwhl.load_pwhl_rosters(seasons=[2026])
rosters.select([
    'team', 'team_abbr', 'player_type', 'first_name', 'last_name',
    'jersey_number', 'position',
]).head()

skater_box = pwhl.load_pwhl_skater_box(seasons=[2026])
skater_box.select([
    'game_id', 'first_name', 'last_name', 'position',
    'goals', 'assists', 'points', 'shots', 'plus_minus', 'time_on_ice',
]).head()

goalie_box = pwhl.load_pwhl_goalie_box(seasons=[2026])
goalie_box.select([
    'game_id', 'first_name', 'last_name',
    'saves', 'shots_against', 'goals_against', 'time_on_ice',
]).head()

# print(rosters.filter(pl.col('team_id') == 3).head(15)[:, :8])

games = (schedule
    .filter(pl.col('game_type') == 'regular')
    )

regwinners = (games
    .filter(pl.col('game_status') == 'Final')
    .group_by('winner')
    .agg(pl.len().alias('wins')))

regwinners = regwinners.rename({'winner':'team'})

otwinners = (games 
    .filter(pl.col('game_status') != 'Final')
    .group_by('winner')
    .agg(pl.len().alias('OT wins')))

otwinners = otwinners.rename({'winner':'team'})

otlosers = (
    games
    .filter(pl.col('game_status') != 'Final')
    .with_columns(
        pl.when(pl.col("home_team") == pl.col("winner"))
        .then(pl.col("away_team"))
        .otherwise(pl.col("home_team"))
        .alias('team')
    )
    .group_by('team')
    .agg(pl.len().alias('OT losses'))

)

standings = (
    regwinners
    .join(otwinners, on='team', how='full', coalesce=True)
    .join(otlosers, on='team', how='full', coalesce=True)
    .with_columns(
        pl.col("wins").fill_null(0),
        pl.col("OT wins").fill_null(0),
        pl.col("OT losses").fill_null(0),
    )
    .with_columns(
        (30 - (pl.col('wins') + pl.col('OT wins') + pl.col('OT losses')))
        .alias('losses')
    )
    .with_columns(
        (3 * pl.col('wins') + 2 * pl.col('OT wins') + pl.col('OT losses'))
        .alias('points')
    )
    .sort('points', descending=True)
) 

#print(schedule.head(10)[:,:8])
print(regwinners)
print(otwinners)
print(otlosers)
print(standings)

#first job: print the actual point rankings 
#do I want to do this ^ or should I instead do win% differential vs. E(win%)?
#both need to get done. Doing the point rankings requires me to parse the winner strings. 
#it seems more proper to get real rankings up in this bitch so .. 

def pointify():

    return

#point_rankings = (schedule
#    .filter())

# scoring_leads = (skater_box
#     .group_by(['player_id', 'first_name', 'last_name'])
#     .agg(
#         pl.col('goals').sum().alias('goals'),
#         pl.col('assists').sum().alias('assists'),
#         pl.col('points').sum().alias('points'),
#     )
#     .sort('points', descending=True)
#     .select(['first_name', 'last_name', 'goals', 'assists', 'points'])
#     .head(10))

# print(scoring_leads)

# goalie_leads = (goalie_box
#     .group_by(['player_id', 'first_name', 'last_name'])
#     .agg(
#         pl.col('saves').sum().alias('saves'),
#         pl.col('shots_against').sum().alias('shots_against'),
#         pl.col('goals_against').sum().alias('goals_against'),
#     )
#     .filter(pl.col('shots_against') >= 100)
#     .with_columns(
#         (pl.col('saves') / pl.col('shots_against')).round(3).alias('save_pct')
#     )
#     .sort('save_pct', descending=True)
#     .select(['first_name', 'last_name', 'shots_against', 'goals_against', 'save_pct'])
#     .head(10))

# print(goalie_leads)
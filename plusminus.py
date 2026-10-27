import polars as pl
import sportsdataverse.pwhl as pwhl
from sportsdataverse.errors import AssetFetchError, NoDataError

pl.Config.set_tbl_cols(12)
pl.Config.set_tbl_rows(24)

# The inaugural season is 2024; this helper tracks the latest known season.
def safe(label, thunk):
    try:
        out = thunk()
        print(f"✅ {label}")
        return out
    except (NoDataError, AssetFetchError) as e:
        print(f"\u23ed\ufe0f  {label}: {type(e).__name__}: {e}")
        return None

skater_box = pwhl.load_pwhl_skater_box(seasons=[2026])
skater_box.select([
    'game_id', 'first_name', 'last_name', 'position',
    'goals', 'assists', 'points', 'plus_minus', 'time_on_ice',
])

def cumulativePM(stats):
    tot = 0.0
    for game in stats.iter_rows(named=True): 
        tot += game['weighted_PM']
    return tot


def parseToi(time):
    tmp = time.split(':')
    toi =  int(tmp[0]) + int(tmp[1])/ 60
    return toi

abbys_stats = (skater_box
    .filter(pl.col('last_name') == 'Roque')
    .filter(pl.col('game_id') < 338)
    .select('game_id','first_name','last_name','toi', 'plus_minus')
    .with_columns(
        pl.col('toi').map_elements(parseToi, return_dtype=pl.Float64).alias('adj_toi')
    )
    .with_columns(
        (pl.col('plus_minus') / pl.col('adj_toi'))
        .alias('weighted_PM') 
    )
)

def generatestats(name): 
    return (skater_box
    .filter(pl.col('last_name') == name)
    .filter(pl.col('game_id') < 338)
    .select('game_id','first_name','last_name','toi', 'plus_minus')
    .with_columns(
        pl.col('toi').map_elements(parseToi, return_dtype=pl.Float64).alias('adj_toi')
    )
    .with_columns(
        (pl.col('plus_minus') / pl.col('adj_toi'))
        .alias('weighted_PM') 
    )
)

#print(abbys_stats)

favplayers = ['Roque', 'Poulin', 'Stacey', 'Watts', 'Fillier', 'Jenner', 'Bilka', 'Van Wieren']
pm = [[0] * 2 for _ in range(8)]
i = 0 
for player in favplayers:
    stats = generatestats(player)
    pm [i][0] = player
    pm [i][1] = cumulativePM(stats)
    i+=1

pmCharts = pl.DataFrame(pm, schema=['name', 'cumulative +/-'])
print(pmCharts)

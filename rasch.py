import polars as pl
import sportsdataverse.pwhl as pwhl
from sportsdataverse.errors import AssetFetchError, NoDataError

pl.Config.set_tbl_cols(12)
pl.Config.set_tbl_rows(24)

def safe(label, thunk):
    try:
        out = thunk()
        print(f"✅ {label}")
        return out
    except (NoDataError, AssetFetchError) as e:
        print(f"\u23ed\ufe0f  {label}: {type(e).__name__}: {e}")
        return None

schedule = pwhl.load_pwhl_schedule(seasons=[2026])

#we're going to end up with beta = (X^TX)^-1 * X^Ty
#where X = (1, xO, xD)

#vector of observed team scores
y = (schedule
    .filter(pl.col('game_id').cast(pl.Int32) < 338)
    .sort(pl.col('game_id'))
    .select(['home_score', 'away_score'])
    )

def matMaker(type):
    tmp = (schedule
        .sort(pl.col('game_id'))
        .filter(pl.col('game_id').cast(pl.Int32) < 338)
        .select(['home_team_id', 'away_team_id'])
        .with_columns(pl.col('home_team_id').replace(9,7))
        .with_columns(pl.col('away_team_id').replace(9,7))
    )
    
    x = [[0] * 8 for _ in range(120)]

    if (type == 'offense'):
        index = 0
    elif(type == 'defense'):
        index = 1
    else:
        return ValueError
    
    i = 0
    print(tmp)
    for row in x: 
        teamid = int(tmp[i, index])
        row[teamid - 1] = 1
        i+=1

    x = pl.DataFrame(x)
    print(x)
    
matMaker(type='offense')

#sparse matrix indicating offensive teams per game 
xO = (schedule
    .filter(pl.col('game_id').cast(pl.Int32) < 338)
    .select(['game_id', 'away_team_id'])
    )



#print(y)
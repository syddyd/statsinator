import polars as pl
import sportsdataverse.pwhl as pwhl
import numpy as np
from sportsdataverse.errors import AssetFetchError, NoDataError


pl.Config.set_tbl_cols(15)
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
    
    x = [[0] * 7 for _ in range(240)]

    if (type == 'offense'):
        index = 0
    elif(type == 'defense'):
        index = 1
    else:
        return ValueError
    
    i = 0
    for row in x: 
        teamid = int(tmp[i, index]) - 1 
        if (teamid > 0):
            row[teamid - 1] = 1
        i+=1
        if (i == 120): i = 0

    x = pl.DataFrame(x)
    return x

def ymaker():
    y1 = (schedule
        .sort(pl.col('game_id'))
        .filter(pl.col('game_id').cast(pl.Int32) < 338)
        .select(['home_score'])
        .rename({'home_score':'team_score'})
        )
    
    y2 = (schedule
        .sort(pl.col('game_id'))
        .filter(pl.col('game_id').cast(pl.Int32) < 338)
        .select(['away_score'])
        .rename({'away_score':'team_score'})
        )
        
    y = pl.concat([y1, y2], how='vertical')
    return y 

def xMaker():
    ones = pl.DataFrame([1] * 240).rename({'column_0' : 'intercept'})
    xO = matMaker(type='offense').transpose().rename( lambda col : col.lower().replace("n", "nO"))
    xD = matMaker(type='defense').transpose()

    X = pl.concat([ones, xO, xD], how='horizontal')
    return X

def rasch(X : pl.DataFrame, y : pl.DataFrame) -> pl.DataFrame:
    xT = X.transpose().to_numpy()
    xn = X.to_numpy()
    yn = y.to_numpy().astype(int)

    print(yn.dtype)

    tmp = np.dot(xT, xn)
    tmp = np.linalg.inv(tmp)
    tmp = np.dot(tmp, xT)
    print(tmp.shape)
    beta = pl.DataFrame(np.dot(tmp, yn))
    return beta 
    
#print(matMaker(type='offense'))
#print(ymaker())

x = xMaker()
y = ymaker()
print(rasch(x, y))
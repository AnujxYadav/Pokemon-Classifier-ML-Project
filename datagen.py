import json
import os
import pandas as pd
from pandas.errors import EmptyDataError

with open('datasets/clean/battlestats.json') as stats:
  battlestats = json.load(stats)
  
def newcol(old_colname: str, pnum: int) -> str:
  if old_colname.startswith(f'p{pnum}'):
    return old_colname.partition(f'_')[-1]
  elif old_colname.startswith(f'p{1-pnum}'):
    if old_colname == f'p{1-pnum}_pokemon':
      return f'opponent'
    else:
      return f'opp_{old_colname.partition("_")[-1]}'
  else:
    return old_colname

def gen_pokemon(alldata: list[pd.DataFrame], pokemon_name: str):
  final_df: pd.DataFrame = None
  for df_ in alldata:
    df = df_.copy()
    if pokemon_name in df['p0_pokemon'].values:
      df.columns = [newcol(x, 0) for x in df.columns.tolist()]
    elif pokemon_name in df['p1_pokemon'].values:
      df.columns = [newcol(x, 1) for x in df.columns.tolist()]
    else:
      continue
      
    df['opp_usage'] = df['opponent'].apply(lambda x: battlestats.get(x, {'usage': 0})['usage'])
    df = df[df['pokemon']==pokemon_name].drop('pokemon', axis=1)
    
    if final_df is not None:
      final_df = pd.concat([final_df, df], axis=0)
    else: final_df = df
  try:
    final_df.to_csv(f'datasets/clean/pokelogs/{pokemon_name}.tsv', sep='\t', index=False)
  except: pass
  
if __name__ == '__main__':
  with open('datasets/raw/viability.json') as fl:
    viability = json.load(fl)
  alldata = []
  for log in os.listdir('datasets/clean/logs'):
    try:
      if os.path.getsize(f'datasets/clean/logs/{log}') < 20: continue
      df = pd.read_csv(f'datasets/clean/logs/{log}', sep='\t')
      alldata.append(df)
    except EmptyDataError:
      pass
    
  for pokelist in viability.values():
    for pokemon in pokelist:
      gen_pokemon(alldata, pokemon)

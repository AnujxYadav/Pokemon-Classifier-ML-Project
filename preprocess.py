import json
import math
from operator import itemgetter

# >> BATTLESTATS PARSE << #
with open('datasets/raw/battlestats.json') as fl:
  f = json.load(fl)
  data = f['data']
  N = f['info']['number of battles']

def corr(freq_a, freq_b, freq_ab):
  return (freq_ab - freq_a * freq_b) / math.sqrt((freq_a * freq_b) * (1 - freq_a) * (1 - freq_b))


clean = {}
usages = {pokemon: entry['usage'] for pokemon, entry in data.items()}
rawcnts = {pokemon: entry['Raw count'] for pokemon, entry in data.items()}
for pokemon, entry in data.items():
  if entry['usage'] < 0.01: continue
  n = entry['usage']*N
  
  moves_cutoff = (n * 4) * 0.05  # moves need to be used at least on 5% of kits
  moves = {name: usage / (4*n) for name, usage in entry['Moves'].items() if usage > moves_cutoff}
  moves = dict(sorted(moves.items(), key=itemgetter(1), reverse=True))
  
  teammates_base = {}
  for name, matches in entry['Teammates'].items():
    try:
      teammates_base[name] = corr(usages[pokemon], usages[name], matches / N)
      teammates_base[name] = min(teammates_base[name], 0.9)
    except KeyError: pass
  teammates = sorted(teammates_base.items(), key=itemgetter(1), reverse=True)
  # teammates = teammates_base
  teammates = dict(teammates[:5]+teammates[-5:])
  
  cnc = dict(sorted(entry['Checks and Counters'].items(), key=lambda x: x[1][1], reverse=True)[:7])
  cnc = {k: v[1] for k, v in cnc.items()}
  
  players = entry['Viability Ceiling'][0]
  vdecay = entry['Viability Ceiling'][1:4]
  
  clean[pokemon] = {
    "usage": usages[pokemon],
    "moves": moves,
    "teammates": teammates,
    "cnc": cnc,
    "players": players,
    "vdecay": vdecay
  }
  
with open('datasets/clean/battlestats.json', 'w+') as fl:
  json.dump(clean, fl, indent=2)


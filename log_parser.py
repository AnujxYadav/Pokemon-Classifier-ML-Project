import csv
import json
import os
import re
undetected_effects = []
undetected_switch_effects = []
undetected_actions = []
ignored_hanging_actions = []

with open('datasets/clean/moves.json') as fl:
  moves = json.load(fl)
import json
with open('datasets/clean/dex.json', encoding='utf-8') as fl:
  pokes = json.load(fl)
  
def pdict_factory():
  return {'pokemon': '', 'switch': 0, 'damage_dealt': 0, 'effectiveness': 1, 'damage_taken': 0, 'heal': 0,
   'faint': 0, 'boost_off': 0, 'boost_def': 0, 'boost_spe': 0, 'unboost_off': 0, 'unboost_def': 0,
   'unboost_spe': 0, 'basepower': 0, 'accuracy': 0, 'stab': 0, 'priority': 0, 'first': 0}

class PokeTracker():
  def __init__(self):
    self.pokemon_hp: dict[str, int] = {}
    self.nicknames: dict[str, str] = {}
    self.alive = 0

  def faint(self):
    self.alive -= 1
    
  def get_pokemon_hp(self, name: str) -> int:
    if truename := self.nicknames.get(name): name = truename
    return self.pokemon_hp[name]
  
  def set_pokemon_hp(self, name: str, hp: int) -> None:
    if truename := self.nicknames.get(name): name = truename
    self.pokemon_hp[name] = hp

  def attack(self, pokemon: str, new_hp: int) -> int:
    dmg = self.get_pokemon_hp(pokemon) - new_hp
    self.set_pokemon_hp(pokemon, new_hp)
    return dmg
  
  def heal(self, pokemon: str, new_hp: int) -> int:
    heal = new_hp - self.get_pokemon_hp(pokemon)
    self.set_pokemon_hp(pokemon, new_hp)
    return heal
  
  def init(self, pokemons: list[str]):
    pokemons = [pokemon.rstrip('-*') for pokemon in pokemons]
    self.pokemon_hp = {pokemon: 100 for pokemon in pokemons}
    self.alive = 6

  def register_nickname(self, canon_name: str, nickname: str):
    self.nicknames[nickname] = canon_name
teams = [PokeTracker(), PokeTracker()]

def team_detect(log: str) -> tuple[list[str], list[str], str]:
  basestr = log[log.find('|poke|'): log.find('|teampreview')]
  log = log[log.find('|teampreview'):]
  p1_mons = re.findall(r'\|poke\|p1\|([\w\-\s\']+)', basestr)
  p2_mons = re.findall(r'\|poke\|p2\|([\w\-\s\']+)', basestr)
  return p1_mons, p2_mons, log

def rating_check(log: str) -> tuple[bool, list[int]]:
  if '|rated|' not in log or '|rated|Tournament' in log:
    return False, []
  log = log[log.find('|rated|'):]
  
  ratings = re.findall(r': (\d+)', log[log.find("'s rating"):])
  return True, [int(x) for x in ratings]

def winner_check(log: str) -> float:
  try:
    playernick = log[log.rindex('|win|'):].split('|')[2]
    if f'|player|p1|{playernick}' in log: return 0
    else: return 1
  except:
    return 0.5

def last_turn(log: str) -> int:
  return int(re.search(r'(\d+)', log.rpartition('|turn|')[-1]).groups()[0])
  
def game_parse(log: str):  # parses overall game data
  leftovers = log
  rated, ratings = rating_check(leftovers)
  p1_team, p2_team, leftovers = team_detect(leftovers)
  
  teams[0].init(p1_team)
  teams[1].init(p2_team)
  turn_count = last_turn(leftovers)
  
def effect_handle(effect_line: str, targetint: int):
  player_info = [pdict_factory(), pdict_factory()]
  match effect := re.search(r'\|-(\w+)', effect_line).groups()[0]:
    # |-damage|p1a: Orthworm|50/100
    case 'supereffective':
      player_info[targetint]['effectiveness'] = 2
    case 'resisted':
      player_info[targetint]['effectiveness'] = 0.5
    case 'immune':
      player_info[targetint]['effectiveness'] = 0
    case 'activate' | 'enditem' | 'start' | 'startitem' | 'end' | 'weather' | 'item' | 'sidestart':
      pass  # too complex to express here
    case 'crit' | 'status' | 'terastallize':
      pass  # i dont consider this worth logging
    case 'boost':
      _, poke, stat, count, *_ = effect_line.split('|')[1:]
      player, pokemon = int(poke[1]) - 1, poke.partition(': ')[-1]
      match stat:
        case 'spa' | 'atk':
          cat = 'off'
        case 'spd' | 'def':
          cat = 'def'
        case _:
          cat = 'spe'
      player_info[player][f'boost_{cat}'] += int(count)
    case 'unboost':
      _, poke, stat, count, *_ = effect_line.split('|')[1:]
      player, pokemon = int(poke[1]) - 1, poke.partition(': ')[-1]
      match stat:
        case 'spa' | 'atk':
          cat = 'off'
        case 'spd' | 'def':
          cat = 'def'
        case _:
          cat = 'spe'
      player_info[player][f'unboost_{cat}'] += int(count)
    case 'damage':
      _, poke, hp, *_ = effect_line.split('|')[1:]
      player, pokemon = int(poke[1]) - 1, poke.partition(': ')[-1]
      hp = int(hp.partition(' ')[0].partition('/')[0])
      dmg = teams[player].attack(pokemon, hp)
      player_info[player]['damage_taken'] += dmg
      player_info[1 - player]['damage_dealt'] += dmg
    case 'heal':
      _, poke, hp, *_ = effect_line.split('|')[1:]
      player, pokemon = int(poke[1]) - 1, poke.partition(': ')[-1]
      hp = int(hp.partition('/')[0])
      player_info[player]['heal'] += teams[player].heal(pokemon, hp)
    case _:
      if effect not in undetected_effects:
        undetected_effects.append(effect)
        print(f'undetected move effect `{effect}`')
  return player_info

def action_blocks(turn_log: str) -> list[str]:
  # will return a 'hanging' set of effect lines if no action present.
  # this is intended.
  turn_units = []
  curr_unit = ""
  for line in turn_log.splitlines():
    if len(line) < 5 or (len(line.split('|')) > 1 and line.split('|')[1] in ['t:', 'c', 'j', 'upkeep']):
      continue  # skip comments, time, empty lines
    if line.startswith('|-') or curr_unit == '':
      curr_unit+=line+'\n'
    else:
      turn_units.append(curr_unit)
      curr_unit = line+'\n'
  turn_units.append(curr_unit)
  return turn_units

def turns(log: str) -> list[list[str]]:
  log = log[log.find('|start')+len('|start\n'):log.rfind('|win|')]
  turns = [x for x in log.split('|upkeep') if '|turn|' in x]
  turnpieces = [turn.split('\n|\n') for turn in turns]
  newpieces = []
  for pieces in turnpieces:
    newpieces.append([piece for piece in pieces if piece != ''])
  return newpieces

def move_handle(block: str) -> list[dict]:
  # |move|p1a: Of|Toxic Spikes|p2a: Corviknight
  header, *effects = block.splitlines()
  mover = 'p1' if '|move|p1' in header else'p2'
  moverint = 1 if mover == 'p2' else 0
  targetint = moverint - 1
  
  pokename = teams[moverint].nicknames[header.split('|')[2].partition(': ')[2]]
  
  movename = header.split('|')[3]
  movedata = moves[movename]
  
  accuracy = movedata['accuracy']
  accuracy = 100 if (accuracy and type(accuracy) == bool) else accuracy
  
  basepower = movedata['basePower']
  try:
    stab = int(movedata['type'] in pokes[pokename]['types'])
  except KeyError:
    stab = 0
  priority = movedata['priority']
  
  player_info = [pdict_factory(), pdict_factory()]
  player_info[moverint] |= {'accuracy': accuracy, 'basepower': basepower, 'stab': stab, 'priority': priority,
                            'first': 1 - player_info[1 - moverint]['first']}
  
  for line in effects:
    player_info = merge_pdicts(player_info, effect_handle(line, targetint))
  return player_info


def switch_handle(block: str) -> list[dict]:
  # |switch|p1a: terragon|Hydreigon, F, shiny|100/100
  player_info = [pdict_factory(), pdict_factory()]
  header, *effects = block.splitlines()
  switchin, canon_name, hp, *_ = header.partition('|switch|')[-1].split('|')
  player = int(switchin[1])-1
  nickname = switchin.partition(': ')[-1]
  canon_name = canon_name.split(',')[0]
  teams[player].register_nickname(canon_name, nickname)
  
  hp = int(hp.partition(' ')[0].partition('/')[0])
  teams[player].pokemon_hp[canon_name] = hp
  player_info[player]['pokemon'] = canon_name
  player_info[player]['switch'] = 1
  for line in effects:
    player_info = merge_pdicts(player_info, effect_handle(line, player))
  return player_info


def faint_handle(block: str):
  # |faint|p1a: torbich
  player_info = [pdict_factory(), pdict_factory()]
  header, *effects = block.splitlines()
  
  target = header.partition('|faint|')[-1]
  player = int(target[1])-1
  
  player_info[player]['faint']=1
  teams[player].faint()
  
  for line in effects:
    player_info = merge_pdicts(player_info, effect_handle(line, player))
    
  return player_info


def replace_drag_handle(block):
  # |replace|p1a: Zoroark|Zoroark-Hisui, F|
  # |drag|p2a: good boi|Arcanine, F| 100 / 100
  player_info = [pdict_factory(), pdict_factory()]
  header, *effects = block.splitlines()
  splitter = '|drag|' if '|drag|' in header else '|replace|'
  switchin, canon_name, *_ = header.partition(splitter)[-1].split('|')
  player = int(switchin[1]) - 1
  nickname = switchin.partition(': ')[-1]
  canon_name = canon_name.split(',')[0]
  teams[player].register_nickname(canon_name, nickname)
  player_info[player]['pokemon']=canon_name
  return player_info

def action_handle(block: str) -> list[dict]:
  resp = [pdict_factory(), pdict_factory()]
  if 'offering a tie.\n' in block or 'the tie.\n' in block: return resp
  if block=='': return resp
  if re.search(r'\|([-\w]+)', block) is None: return resp
  match action := re.search(r'\|([-\w]+)', block).groups()[0]:
    case 'move': resp = move_handle(block)
    case 'switch': resp = switch_handle(block)
    case 'faint': resp = faint_handle(block)
    case 'replace' | 'drag': resp = replace_drag_handle(block)
    case 'cant' | 'inactive': pass  # not worth observing
    case 'turn': pass  # trivial
    case _:
      if action.startswith('-'):
        for line in block.splitlines():
          resp = merge_pdicts(resp, effect_handle(line, -1))
        
      elif action not in undetected_actions:
        undetected_actions.append(action)
        print(f'undetected action `{action}`')
  
  return resp


def flatten_dicts(p0_info: dict, p1_info: dict, turn_info: dict) -> dict:
  toret = {f'p0_{k}': v for k, v in p0_info.items()}
  toret |= {f'p1_{k}': v for k, v in p1_info.items()}
  toret |= turn_info
  return toret

def merge_pdict(pdict_old, pdict_new):
  new_dict = pdict_factory()
  if pdict_old['pokemon']: new_dict['pokemon'] = pdict_old['pokemon']
  else: new_dict['pokemon'] = pdict_new['pokemon']
  
  OR_KEYS = ['switch', 'faint', 'stab']
  SUM_KEYS = ['boost_off', 'boost_def', 'boost_spe', 'unboost_off', 'unboost_def', 'unboost_spe', 'damage_dealt', 'damage_taken', 'heal']
  REPLACE_KEYS = ['effectiveness']
  REPLACE_IF_ZERO = ['basepower', 'accuracy', 'stab', 'priority', 'first']
  
  for key in OR_KEYS:
    new_dict[key] = pdict_old[key] | pdict_new[key]
  for key in SUM_KEYS:
    new_dict[key] = pdict_old[key] + pdict_new[key]
  for key in REPLACE_KEYS:
    new_dict[key] = max(min(pdict_new[key]*pdict_old[key], 2), 0.5)
  for key in REPLACE_IF_ZERO:
    new_dict[key] = pdict_new[key] if pdict_old[key] == 0 else pdict_old[key]

  return new_dict

def merge_pdicts(pdicts_old, pdicts_new):
  return merge_pdict(pdicts_old[0], pdicts_new[0]), merge_pdict(pdicts_old[1], pdicts_new[1])

def turn_handle(turn: list[str], nturns: int, prev_step: dict = None, weight: float = 0.2, winner: float = 0):
  player_info = [pdict_factory(), pdict_factory()]
  if prev_step:
    if '|switch|p1' not in ''.join(turn):
      player_info[0]['pokemon'] = prev_step['p0_pokemon']
    if '|switch|p2' not in ''.join(turn):
      player_info[1]['pokemon'] = prev_step['p1_pokemon']
  
  actionset_blocks = [action_blocks(actionset) for actionset in turn]
  # this differentiation may be relevant later
  
  all_blocks = [item for sublist in actionset_blocks for item in sublist]
  
  turn_num = int(re.search(r'\|turn\|(\d+)', ''.join(turn)).groups()[0])
  
  for block in all_blocks:
    player_info = merge_pdicts(player_info, action_handle(block))
  
  return flatten_dicts(*player_info, {'turn': turn_num, 'turn_norm': turn_num/nturns,
                                      'p0_alive': teams[0].alive, 'p1_alive': teams[1].alive,
                                      'weight': weight, 'p1_winner': winner, 'p0_winner': 1-winner})

def turns_parse(log: str, weight: float, winner: float):
  rows = []
  nturns = last_turn(log)
  turnpieces = turns(log)
  prevrow = None
  for pieces in turnpieces:
    rows.append(prevrow := turn_handle(pieces, nturns, prevrow, weight, winner))
  return rows

if __name__ == '__main__':
  for logname in os.listdir('datasets/logs'):
    with open(f'datasets/logs/{logname}', encoding='utf-8') as fl:
      log = fl.read()
      if '|teampreview' not in log or 'Dudunsparce' in log or 'Mimikyu' in log or 'Urshifu' in log or 'Eiscue' in log: continue
      game_parse(log)
      rated, weights = rating_check(log)
      winner = winner_check(log)
      if rated: weight = max(min(0.2 + (((weights[0]+weights[1])/2)-1000)/500, 1), 0.2)
      else: weight = 0.2
      assert 0.2 <= weight <= 1
      outdict = turns_parse(log, weight, winner)
    if len(outdict) < 5:  # equal to number of turns
      continue
    with open(f'datasets/clean/logs/{os.path.splitext(logname)[0]}.csv', mode='w+', encoding='utf-8') as fl:
      writer = csv.DictWriter(fl, fieldnames=outdict[0].keys(), delimiter='\t', lineterminator='\n')
      writer.writeheader()
      writer.writerows(outdict)

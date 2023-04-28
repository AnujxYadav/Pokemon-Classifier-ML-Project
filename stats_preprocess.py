import json

tiers = {}
with open('datasets/raw/viability.json') as fl:
  data = json.load(fl)

# Map from grade to rating
grade_to_rating = {
  'S': 1,
  'S-': 0.95,
  'A+': 0.85,
  'A': 0.75,
  'A-': 0.65,
  'B+': 0.55,
  'B': 0.45,
  'B-': 0.35,
  'C+': 0.2,
  'C': 0.1,
  'C-': 0
}

# Extract ratings for each Pokemon and store in a dictionary
pokemon_ratings = {}
for grade, pokemon_list in data.items():
  for pokemon_name in pokemon_list:
    pokemon_ratings[pokemon_name] = grade_to_rating[grade]

with open('datasets/clean/viability.json', 'w+') as fl:
  json.dump(pokemon_ratings, fl, indent='\t')

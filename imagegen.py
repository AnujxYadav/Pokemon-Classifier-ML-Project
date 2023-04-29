import json
import os
import random
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

random.seed(144)

with open('datasets/clean/viability.json') as fl:
  viability_map = json.load(fl)

IMG_ROWS = 5
CHUNK_SIZE = 5

train_keys, test_keys = train_test_split(list(viability_map.keys()), train_size=0.8, test_size=0.2)

poke_dfs = defaultdict(list)

for pokelog in os.listdir('datasets/clean/pokelogs'):
  df = pd.read_csv(f'datasets/clean/pokelogs/{pokelog}', sep='\t')
  if df.isnull().values.any():
    print('uh')
  if df.shape[0] < IMG_ROWS*CHUNK_SIZE: continue
  # df = shuffle(df.drop('opponent', axis=1)).reset_index(drop=True)
  df = df.drop('opponent', axis=1)
  pokename = os.path.splitext(pokelog)[0]
  label = viability_map[pokename]
  
  surplus = df.shape[0] % (IMG_ROWS * CHUNK_SIZE)
  if surplus > 0: df = df.loc[:df.shape[0]-surplus-1, :]
  
  for chunk in np.split(df, df.shape[0] // (IMG_ROWS * CHUNK_SIZE)):
    batch = []
    for image in np.split(chunk, CHUNK_SIZE):
      temp_image = image.sort_values(by='turn_norm', axis=0).values
      batch.append(temp_image)
      
    mean_image = np.mean(batch, axis=0).tolist()
    
    poke_dfs[pokename].append(mean_image)

scores = [0.95, 1, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.2, 0.1, 0]
TRAINING = 0.8
TESTING = 1-TRAINING

testing_images, training_images = [], []
testing_pokes, training_pokes = [], []
testing_labels, training_labels = [], []
for score in scores:
  pokenames = [pokename for pokename, sc in viability_map.items() if sc == score]
  data = [(pokename, poke_dfs[pokename]) for pokename in pokenames]
  
  data.sort(key=lambda x: len(x[1]))
  class_size = sum([len(x[1]) for x in data])
  
  _testing_images, _training_images = [], []
  
  for pokename, images in data:
    if len(images) >= 300:
      images = images[:300]
      
    if len(_training_images) >= 600:
      TEST=True
    elif len(_testing_images) / class_size >= TESTING:
      TEST=False
    elif len(_training_images) / class_size >= TRAINING:
      TEST=True
    elif random.random() <= 0.5:
      TEST=True
    else:
      TEST=False
    
    if TEST:
      if len(_testing_images) < 300:
        _testing_images.extend(images)
        testing_pokes.extend([pokename]*len(images))
        testing_labels.extend([score]*len(images))
      elif len(_training_images) < 600:
        _training_images.extend(images)
        training_pokes.extend([pokename]*len(images))
        training_labels.extend([score]*len(images))
    else:
      _training_images.extend(images)
      training_pokes.extend([pokename]*len(images))
      training_labels.extend([score]*len(images))

  testing_images.extend(_testing_images)
  training_images.extend(_training_images)

def pair_shuffle(a, b, c):
  toret = list(zip(a, b, c))
  random.shuffle(toret)
  return list(zip(*toret))
train_images, train_labels, train_poke = pair_shuffle(training_images, training_labels, training_pokes)
test_images, test_labels, test_poke = pair_shuffle(testing_images, testing_labels, testing_pokes)

with open('datasets/clean/images.json', mode='w+') as fl:
  json.dump({
    'train_images': train_images,
    'train_labels': train_labels,
    'train_poke': train_poke,
    'test_images': test_images,
    'test_labels': test_labels,
    'test_poke': test_poke
  }, fl)

import json
import os
import random

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle

with open('datasets/clean/viability.json') as fl:
  viability_map = json.load(fl)

IMG_ROWS = 8
CHUNK_SIZE = 15

train_keys, test_keys = train_test_split(list(viability_map.keys()), train_size=0.8, test_size=0.2)
train_images, train_labels, test_images, test_labels = [], [], [], []
train_poke, test_poke = [], []

for pokelog in os.listdir('datasets/clean/pokelogs'):
  df = pd.read_csv(f'datasets/clean/pokelogs/{pokelog}', sep='\t')
  if df.isnull().values.any():
    print('uh')
  if df.shape[0] < IMG_ROWS*CHUNK_SIZE: continue
  df = shuffle(df.drop('opponent', axis=1)).reset_index(drop=True)
  # df = df.drop('opponent', axis=1)
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
    
    if pokename in train_keys:
      train_images.append(mean_image)
      train_labels.append(label)
      train_poke.append(pokename)
    else:
      test_images.append(mean_image)
      test_labels.append(label)
      test_poke.append(pokename)

def pair_shuffle(a, b, c):
  toret = list(zip(a, b, c))
  random.shuffle(toret)
  return list(zip(*toret))
train_images, train_labels, train_poke = pair_shuffle(train_images, train_labels, train_poke)
test_images, test_labels, test_poke = pair_shuffle(test_images, test_labels, test_poke)

with open('datasets/clean/images.json', mode='w+') as fl:
  json.dump({
    'train_images': train_images,
    'train_labels': train_labels,
    'train_poke': train_poke,
    'test_images': test_images,
    'test_labels': test_labels,
    'test_poke': test_poke
  }, fl)

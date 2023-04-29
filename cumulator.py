import json
import os
import random

import pandas as pd
from sklearn.model_selection import train_test_split

random.seed(144)

for SLICESIZE in [5, 10, 15, 20]:
  slices = []
  labels = []
  for filename in random.choices(os.listdir('datasets/clean/logs'), k=1500):
    log_ = pd.read_csv(f'datasets/clean/logs/{filename}', sep='\t')
    log = log_.drop(['p0_pokemon', 'p1_pokemon', 'turn_norm', 'p0_winner'], axis=1)
    
    winner = log['p1_winner'][0]
    log = log.drop('p1_winner', axis=1)
    for i in range(SLICESIZE, log.values.shape[0]):
      slices.append(log.loc[i-SLICESIZE: i-1].values.astype(int).tolist())
      labels.append(int(winner))
    
  train_slices, test_slices, train_labels, test_labels = train_test_split(slices, labels, train_size=0.7, shuffle=True, random_state=144)

  with open(f'datasets/clean/slices_{SLICESIZE}.json', mode='w+') as fl:
    json.dump({
      'train_X': train_slices,
      'train_y': train_labels,
      'test_X': test_slices,
      'test_y': test_labels
    }, fl)
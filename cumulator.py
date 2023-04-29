import json
import os
import random

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

random.seed(144)

for SLICESIZE in [5, 10, 15, 20]:
  train_slices = []
  train_labels = []
  train_cuml_slices = []
  test_slices = []
  test_labels = []
  test_cuml_slices = []
  
  for filename in random.choices(os.listdir('datasets/clean/logs'), k=1500):
    if random.random() < 0.7: GOTO='train'
    else: GOTO='test'
    log_ = pd.read_csv(f'datasets/clean/logs/{filename}', sep='\t')
    log = log_.drop(['p0_pokemon', 'p1_pokemon', 'turn_norm', 'p0_winner'], axis=1)
    
    winner = log['p1_winner'][0]
    log = log.drop('p1_winner', axis=1)
    for i in range(SLICESIZE, log.values.shape[0]):
      if GOTO == 'test':
        test_slices.append(log.loc[i-SLICESIZE: i-1].values.astype(float).tolist())
        test_labels.append(int(winner))
        test_cuml_slices.append(np.sum(log.loc[i-SLICESIZE: i-1].values.astype(float), axis=0).tolist())
      else:
        train_slices.append(log.loc[i-SLICESIZE: i-1].values.astype(float).tolist())
        train_labels.append(int(winner))
        train_cuml_slices.append(np.sum(log.loc[i-SLICESIZE: i-1].values.astype(float), axis=0).tolist())
  
  def pair_shuffle(a, b, c):
    toret = list(zip(a, b, c))
    random.shuffle(toret)
    return list(zip(*toret))
  
  train_slices, train_labels, train_cuml_slices = pair_shuffle(train_slices, train_labels, train_cuml_slices)
  test_slices, test_labels, test_cuml_slices = pair_shuffle(test_slices, test_labels, test_cuml_slices)

  with open(f'datasets/clean/slices_{SLICESIZE}.json', mode='w+') as fl:
    json.dump({
      'train_X': train_slices,
      'train_y': train_labels,
      'train_sum_X': train_cuml_slices,
      'test_X': test_slices,
      'test_y': test_labels,
      'test_sum_X': test_cuml_slices
    }, fl)
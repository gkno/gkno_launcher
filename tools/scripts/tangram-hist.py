#!/bin/bash/python

from __future__ import print_function

import json
import os
import stat
import sys

# Determine if the input is a file or a stream.
mode   = os.fstat(0).st_mode
isPipe = True if stat.S_ISFIFO(mode) else False

# Open the file.
if isPipe: jsonData = sys.stdin
else:
  filename = sys.argv[1]
  try: jsonData = open(filename)
  except: exit(1)

try: configurationData = json.load(jsonData)
except: exit(1)

# Initialise dictionaries.
allBins = []
for dataSet in configurationData:
  if dataSet['bin']:
    for binValue in dataSet['bin']:
      if binValue not in allBins: allBins.append(binValue)

# Print a header line.
print('bin', end = '')
for count in range(1, len(configurationData) + 1): print('\trg', str(count), sep = '', end = '')
print()

for binValue in sorted(allBins):
  values = []
  print(binValue, end = '')
  for dataSet in configurationData:
    positionList = [position for position, testBinValue in enumerate(dataSet['bin']) if testBinValue == binValue]
    print('\t', dataSet['freq'][positionList[0]], sep = '', end = '') if len(positionList) != 0 else print('\t0', end = '')
  print()

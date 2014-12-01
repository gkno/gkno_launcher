#!/bin/bash/python

from __future__ import print_function

import json
import os
import stat
import sys

# Get input arguments.
try: sequencesFile = sys.argv[1]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <normalise>'); exit(1)
try: filename = sys.argv[2]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <normalise>'); exit(1)
try: maxCoverage = sys.argv[3]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <normalise>'); exit(1)

try: optionA = sys.argv[4]
except: optionA = None
try: optionB = sys.argv[5]
except: optionB = None

# Check if the values need to be normalised or if the zero bin should be included.
isNormalise = False
isUseZero   = False
if optionA == 'normalise' or optionB == 'normalise': isNormalise = True
if optionA == 'useZero' or optionB == 'useZero': isUseZero = True

# Open the reference sequences file.
try: sequences = open(sequencesFile)
except: print('ERROR: file ', sequencesFile, ' does not exist.', sep = ''); exit(1)

# Store all the sequences that should be processed.
requiredSequences = []
for sequence in sequences: requiredSequences.append(sequence.strip())

# Open the coverage file.
try: coverage = open(filename)
except: print('ERROR: file ', filename, ' does not exist.', sep = ''); exit(1)

# Keep track of reference sequence lengths.
refLengths = {}
maxRefSize = 0
minRefSize = 0

# Parse the file.
refs       = {}
lastRef    = None
for line in coverage:

  # Only process if the reference sequence is in the requiredSequences list.
  ref, valueBin, count, length, fraction = line.strip().split("\t")
  if ref in requiredSequences:

    # If this is a new reference sequence, record that this is not longer the first.
    if lastRef and ref != lastRef: isFirstRef = False
    lastRef = ref

    # Initialise the array.
    if ref not in refs: refs[ref] = {}

    if int(valueBin) <= int(maxCoverage):

      # Keep track of the minimum and maximum reference size.
      if int(length) > int(maxRefSize): maxRefSize = length
      if int(minRefSize) == 0 or int(length) < int(minRefSize): minRefSize = length
      if ref not in refLengths: refLengths[ref] = int(length)

      # Store the count.
      refs[ref][valueBin] = count

# Loop over each reference sequence and fill in missing values with zeros.
fullRefs = {}
for ref in requiredSequences:
  fullRefs[ref] = [ref]
  for counter in range(0, int(maxCoverage) + 1, 1):
    try: readCount = refs[ref][str(counter)]
    except: readCount = 0
    fullRefs[ref].append(readCount)

# Include the 'bin' reference sequence to provide the first column in the output.
requiredSequences = ['bin'] + requiredSequences
bins              = ['bin'] + [valueBin for valueBin in range(0, int(maxCoverage) + 1, 1)]
fullRefs['bin']   = bins

# Write the ouptut, normalising if necessary.
for counter in range(0, int(maxCoverage) + 1, 1):
  for ref in requiredSequences:
    value = fullRefs[ref][counter]

    # Normalise the values if required.
    if isNormalise and ref != 'bin' and counter != 0:

      # Calculate the normalising factor.
      factor = float(float(refLengths[ref]) / float(minRefSize))
      value  = float(float(value) / float(factor))

    # Write out the values.
    if counter == 1 and not isUseZero: pass
    else: print(value, end = '\t')
  if counter == 1 and not isUseZero: pass
  else: print()

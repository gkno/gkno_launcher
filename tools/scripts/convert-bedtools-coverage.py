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
bins       = []
isFirstRef = True
lastRef    = None
for line in coverage:

  # Only process if the reference sequence is in the requiredSequences list.
  ref, valueBin, count, length, fraction = line.strip().split("\t")
  if ref in requiredSequences:

    # If this is a new reference sequence, record that this is not longer the first.
    if lastRef and ref != lastRef: isFirstRef = False
    lastRef = ref

    if int(valueBin) <= int(maxCoverage):
  
      # Store the name of the reference sequence.
      if ref not in refs: refs[ref] = [ref]

      # Keep track of the minimum and maximum reference size.
      if int(length) > int(maxRefSize): maxRefSize = length
      if int(minRefSize) == 0 or int(length) < int(minRefSize): minRefSize = length
      if ref not in refLengths: refLengths[ref] = int(length)

      # Store the bin values.
      if isFirstRef: bins.append(valueBin)

      # Store the count.
      refs[ref].append(count)

# Check that all of the reference seqeunce lists have the same number of values.
length = len(refs[refs.keys()[0]])
for ref in refs:
  if len(refs[ref]) != length: print('ERROR: Not all reference sequences have the same number of bins.'); exit(0)

# Include the 'bin' reference sequence to provide the first column in the output.
requiredSequences = ['bin'] + requiredSequences
bins              = ['bin'] + bins
refs['bin']       = bins

# Write the ouptut, normalising if necessary.
for counter in range(0, length, 1):
  for ref in requiredSequences:
    value = refs[ref][counter]

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

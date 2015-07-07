#!/bin/bash/python

from __future__ import print_function

import json
import os
import stat
import sys

# Get input arguments.
try: sequencesFile = sys.argv[1]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <percent> <normalise> <use-zero>'); exit(1)
try: filename = sys.argv[2]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <percent> <normalise> <use-zero>'); exit(1)
try: maxCoverage = sys.argv[3]
except: print('Usage: python convert-bedtools-coverage.py <sequences.txt> <filename.cov> <max coverage> <percent> <normalise> <use-zero>'); exit(1)

try: optionA = sys.argv[4]
except: optionA = None
try: optionB = sys.argv[5]
except: optionB = None
try: optionC = sys.argv[6]
except: optionC = None

# Determine the output file names.
outputA = filename.replace('.cov', '.coverage.txt')
outputB = filename.replace('.cov', '.coverage.proportional.txt')

# Check if the values need to be normalised or if the zero bin should be included, or percentage values
# should be used.
isNormalise  = False
isUseZero    = False
isPercentage = True
if optionA == 'normalise' or optionB == 'normalise' or optionC == 'normalise': isNormalise = True
if optionA == 'useZero' or optionB == 'useZero' or optionC == 'useZero': isUseZero = True
if optionA == 'read-counts' or optionB == 'read-counts' or optionC == 'read-counts': isPercentage = False

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
refs        = {}
lastRef     = None
totalCount  = 0
totalCounts = {}
for line in coverage:

  # Only process if the reference sequence is in the requiredSequences list.
  ref, valueBin, count, length, fraction = line.strip().split("\t")
  if ref in requiredSequences:

    # If this is a new reference sequence, record that this is not longer the first.
    if lastRef and ref != lastRef:
      isFirstRef           = False
      totalCounts[lastRef] = totalCount
      totalCount           = 0
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

    # Keep track of the total count.
    totalCount += int(count)

# The totalCount for the last processed reference needs to be added to the dictionary.
totalCounts[lastRef] = totalCount

# Loop over each reference sequence and fill in missing values with zeros.
fullRefs = {}
for ref in requiredSequences:
  fullRefs[ref]    = [ref]
  for counter in range(0, int(maxCoverage) + 1, 1):
    try: readCount = refs[ref][str(counter)]
    except: readCount = 0
    fullRefs[ref].append(readCount)

# Loop over all the references and build up an array containing data on the percentage of
# bases with greater than or equal to a given coverage.
greaterThan = {}
for ref in requiredSequences:
  if ref in fullRefs:
    greaterThan[ref]    = {}
    greaterThan[ref][0] = ref
    isFirst             = True

    #for value in reversed(fullRefs[ref]):
    for counter in range(len(fullRefs[ref]) - 2, 0, -1):
      value = fullRefs[ref][counter]

      # If the value is zero, add zero to greaterThan.
      if value == 0: greaterThan[ref][counter] = 0
      else:

        # Store the percentage of bases with greater than this coverage.
        if isFirst:
          greaterThan[ref][counter] = float( float(value) / float(totalCounts[ref]) )
          isFirst                   = False
        else:
          greaterThan[ref][counter] = float(greaterThan[ref][counter + 1]) + float( float(value) / float(totalCounts[ref]))
      counter -= 1

# Include the 'bin' reference sequence to provide the first column in the output.
requiredSequences  = ['bin'] + requiredSequences
bins               = ['bin'] + [valueBin for valueBin in range(0, int(maxCoverage) + 1, 1)]
fullRefs['bin']    = bins
greaterThan['bin'] = bins

# Open the output files.
outHandleA = open(outputA, 'w')
outHandleB = open(outputB, 'w')

# Write the ouptut, normalising if necessary.
for counter in range(0, int(maxCoverage) + 1, 1):
  for ref in requiredSequences:
    value = fullRefs[ref][counter]

    # If the percentage values are being printed.
    if isPercentage:
      if counter != 0 and ref != 'bin' and ref in totalCounts: value = 100 * float(float(value) / float(totalCounts[ref]))

    # Normalise the values if required.
    elif isNormalise and ref != 'bin' and counter != 0 and ref in totalCounts:

      # Calculate the normalising factor.
      factor = float(float(refLengths[ref]) / float(minRefSize))
      value  = float(float(value) / float(factor))

    # Write out the values.
    if counter == 1 and not isUseZero: pass
    else: print(value, end = '\t', file = outHandleA)
  if counter == 1 and not isUseZero: pass
  else: print(file = outHandleA)

# Write out the information showing which bases have a greater coverage.
for counter in range(0, int(maxCoverage) + 1, 1):
  for ref in requiredSequences:
    if ref != 'bin' and counter != 0: value = float( 100. * greaterThan[ref][counter])
    else: value = greaterThan[ref][counter]

    # Write out the values.
    print(value, end = '\t', file = outHandleB)
  print(file = outHandleB)

# Close the opened files.
coverage.close()
outHandleA.close()
outHandleB.close()

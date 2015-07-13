#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import json
import os
import stat
import sys

def main():

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
  
  # Determine the output file names.
  outputA = filename.replace('.cov', '.coverage.txt')
  outputB = filename.replace('.cov', '.coverage.scaled.txt')
  outputC = filename.replace('.cov', '.coverage.proportional.txt')
  outputD = filename.replace('.cov', '.coverage.proportional.scaled.txt')
  
  # Check if the the zero bin should be included, or percentage values should be used.
  isUseZero    = False
  isPercentage = True
  if optionA == 'useZero' or optionB == 'useZero': isUseZero = True
  if optionA == 'read-counts' or optionB == 'read-counts': isPercentage = False
  
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
    refId, bin, count, length, fraction = line.strip().split("\t")
    if refId in requiredSequences:
  
      # If this is a new reference sequence, record that this is not longer the first.
      if lastRef and refId != lastRef:
        isFirstRef           = False
        totalCounts[lastRef] = totalCount
        totalCount           = 0
      lastRef = refId
  
      # Initialise the array.
      if refId not in refs: refs[refId] = {}
  
      if int(bin) <= int(maxCoverage):
  
        # Keep track of the minimum and maximum reference size.
        if int(length) > int(maxRefSize): maxRefSize = length
        if int(minRefSize) == 0 or int(length) < int(minRefSize): minRefSize = length
        if refId not in refLengths: refLengths[refId] = int(length)
  
        # Store the count.
        refs[refId][bin] = count
  
      # Keep track of the total count.
      totalCount += int(count)
  
  # The totalCount for the last processed reference needs to be added to the dictionary.
  totalCounts[lastRef] = totalCount
  
  # Loop over each reference sequence and fill in missing values with zeros.
  fullRefs = {}
  for refId in requiredSequences:
    fullRefs[refId] = [refId]
    for counter in range(0, int(maxCoverage) + 1, 1):
      try: readCount = refs[refId][str(counter)]
      except: readCount = 0
      fullRefs[refId].append(readCount)
  
  # Loop over all the references and build up an array containing data on the percentage of
  # bases with greater than or equal to a given coverage.
  greaterThan = getProportional(requiredSequences, fullRefs, totalCounts)
  
  # Generate a version of the total counts dictionary, where the number of bases with zero
  # coverage have been substracted from the total.
  scaledTotalCounts = deepcopy(totalCounts)
  for refId in scaledTotalCounts: scaledTotalCounts[refId] = int(scaledTotalCounts[refId]) - int(fullRefs[refId][1])
  
  # Get the proportional coverage scaled by removing the zero coverage bases.
  greaterThanScaled = getProportional(requiredSequences, fullRefs, scaledTotalCounts)
  
  # Include the 'bin' reference sequence to provide the first column in the output.
  requiredSequences        = ['bin'] + requiredSequences
  bins                     = ['bin'] + [bin for bin in range(0, int(maxCoverage) + 1, 1)]
  fullRefs['bin']          = bins
  greaterThan['bin']       = bins
  greaterThanScaled['bin'] = bins
  
  # Open the output files.
  outHandleA = open(outputA, 'w')
  outHandleB = open(outputB, 'w')
  outHandleC = open(outputC, 'w')
  outHandleD = open(outputD, 'w')
  
  # Write the ouptut for the basic plot.
  for counter in range(0, int(maxCoverage) + 1, 1):
    for refId in requiredSequences:
      value = fullRefs[refId][counter]
  
      # If the percentage values are being printed.
      if isPercentage:
        if counter != 0 and refId != 'bin' and refId in totalCounts: value = 100 * float(float(value) / float(totalCounts[refId]))
  
      # Write out the values.
      if counter == 1 and not isUseZero: pass
      else: print(value, end = '\t', file = outHandleA)
  
    # Write the end of line.
    if counter == 1 and not isUseZero: pass
    else: print(file = outHandleA)
  
  # Write the output, scaled by the number of bases with zero coverage.
  for counter in range(0, int(maxCoverage) + 1, 1):
    for refId in requiredSequences:
      value = fullRefs[refId][counter]
  
      # If the percentage values are being printed.
      if isPercentage:
        if counter != 0 and refId != 'bin' and refId in scaledTotalCounts: value = 100 * float(float(value) / float(scaledTotalCounts[refId]))
  
      # Write out the values.
      if counter == 1: pass
      else: print(value, end = '\t', file = outHandleB)
  
    # Write the end of line.
    if counter == 1: pass
    else: print(file = outHandleB)
  
  # Write out the information showing which bases have a greater coverage.
  for counter in range(0, int(maxCoverage), 1):
  
    # Do not include the zero coverage line.
    if counter != 1:
      for refId in requiredSequences:
        if refId != 'bin' and counter != 0:
          valueA = float( 100. * greaterThan[refId][counter])
          valueB = float( 100. * greaterThanScaled[refId][counter])
        else:
          valueA = greaterThan[refId][counter]
          valueB = greaterThanScaled[refId][counter]
    
        # Write out the values.
        print(valueA, end = '\t', file = outHandleC)
        print(valueB, end = '\t', file = outHandleD)
      print(file = outHandleC)
      print(file = outHandleD)
  
  # Close the opened files.
  coverage.close()
  outHandleA.close()
  outHandleB.close()
  outHandleC.close()
  outHandleD.close()

##########################
### ADDITIONAL METHODS ###
##########################

# Get the percentage of bases with greater than or equal to coverage.
def getProportional(sequences, refs, counts):
  temp = {}
  for refId in sequences:
    if refId in refs:
      temp[refId]    = {}
      temp[refId][0] = refId
      isFirst        = True
  
      for counter in range(len(refs[refId]) - 2, 0, -1):
        value = refs[refId][counter]
  
        # If the value is zero, add zero to greaterThan.
        if value == 0: temp[refId][counter] = 0
        else:
  
          # Store the percentage of bases with greater than this coverage.
          if isFirst:
            temp[refId][counter] = float( float(value) / float(counts[refId]) )
            isFirst              = False
          else:
            temp[refId][counter] = float(temp[refId][counter + 1]) + float( float(value) / float(counts[refId]) )
        counter -= 1

  # Return the dictionary.
  return temp

if __name__ == "__main__":
  main()

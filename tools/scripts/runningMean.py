#!/usr/bin/python

from __future__ import print_function
import fileinput
from math import sqrt
import sys

# Get the output file name.
outputFile = sys.argv[1]

# Open the output file.
filehandle = open(outputFile, 'w')

array = []
n     = 0
total = 0
isFirst = True

# Variables for Welfords method.
MOld = 0
MNew = 0
SOld = 0
SNew = 0
k    = 0
minC = 0
maxC = 0

for line in sys.stdin:
  value = int(line.rstrip('\n').split('\t')[3])

  # Increment the values.
  MOld = MNew
  SOld = SNew

  # If this is the first value, initialise.
  if isFirst:
    isFirst = False
    MNew   = value
    SNew   = 0
    k      = 1
    minC   = value
    maxC   = value

  # Otherwise, use the recursion relations.
  else:
    k += 1
    MNew = float(MOld) + float((float((value - MOld)) / float(k)))
    SNew = float(SOld) + float(float(value - MOld) * float(value - MNew))

    # Check if this is smaller or larger than the min / max observed coverage.
    minC = value if value < minC else minC
    maxC = value if value > maxC else maxC

  # Store values for the median calculation.
  array.append(value)

# Get the number of values and determine if there are an even number of values.
length = len(array)
isEven = True if (length % 2) == 0 else False

# Calculate the median.
if length == 0: median = 0
elif isEven:
  index  = length / 2
  first  = sorted(array)[index - 1]
  second = sorted(array)[index]
  median = (first + second) / 2
else: 
  if length == 1: median = array[0]
  else: median = sorted(array)[(length - 1) / 2]

# Calculate the mean and standard deviation.
mean = MNew
if k > 1: var  = float(SNew / (float(k - 1)))
else: var  = float(SOld)
sd   = sqrt(var)

# Output the mean, standard deviation and median.
print(MNew, '\t', median, '\t', sd, '\t', minC, '\t', maxC, '\t', length, file = filehandle)

# Close the output file.
filehandle.close()

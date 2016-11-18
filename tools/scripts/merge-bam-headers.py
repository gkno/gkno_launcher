#!/bin/python

from __future__ import print_function
import sys

# The output file is the last argument in the list.
output = open(sys.argv[-1], 'w')

# The input files are all others (skipping the command line argument).
inputs = sys.argv[1:-1]

# Extract the non read group lines from the first header and add to the output.
filehandle = open(inputs[0])
for line in filehandle:
  text = line.rstrip('\n')
  if not text.startswith('@RG'): print(text, file = output)
filehandle.close()

# Loop over all the files and add the read groups to the output.
for file in inputs:
  filehandle = open(file)
  for line in filehandle:
    text = line.rstrip('\n')
    if text.startswith('@RG'): print(text, file = output)
  filehandle.close()

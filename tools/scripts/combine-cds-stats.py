#!/usr/bin/python

from __future__ import print_function
import sys

# Open the output file and add a header line.
outputFilehandle = open('cds-stats.txt', 'w')
print('#gene_name\ttranscript_id\tcds_id\tmean\tmedian\tstandard_deviation', file = outputFilehandle)

# Open the file containing the transcript ids.
filehandle = open(sys.argv[1], 'r')

# Loop over all transcripts.
for line in filehandle.readlines():
  line         = line.rstrip('.pileup\n')
  filename     = line + '.txt'
  info         = line.split('_')
  geneName     = info[0]
  transcriptId = info[1]
  exonId       = info[2]

  # Open the file containing the stats and get the values.
  tempHandle = open(filename, 'r')
  line       = tempHandle.readline()
  stats      = (line.rstrip('\n')).split('\t')
  mean       = stats[0]
  median     = stats[1]
  sd         = stats[2]

  # Close the stats file.
  tempHandle.close()
  print(geneName, '\t', transcriptId, '\t', exonId, '\t', mean, '\t', median, '\t', sd, file = outputFilehandle)

# Close the files.
filehandle.close()
outputFilehandle.close()

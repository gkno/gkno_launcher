#!/usr/bin/python

from __future__ import print_function
import gzip
import sys

# Get the name of the input file.
inputFile  = sys.argv[1]

# If the file is zipped, open with gzip.
if inputFile.endswith('.gz'): filehandle = gzip.open(inputFile, 'rb')
else: filehandle = open(inputFile, 'r')

# Open files for output.
regionFilehandle = open("gene_regions.list", "w")
idFilehandle     = open("gene_transcripts.list", "w")

# Initialise variables.
cdsId            = 1
lastTranscriptId = None

for line in filehandle.readlines():
  line = line.rstrip('\n')
  if not line.startswith('#'):
    array    = line.split('\t')
    info     = array[8].split(';')
    feature  = array[2]

    # If the feature is a gene, get the name and start a loop over transcripts.
    if feature == 'CDS' and (info[4].split('='))[1] == "protein_coding":

      # Strip 'chr' from the chromosome name if it exists.
      if array[0].startswith('chr'): chromosome = array[0].strip('chr')
      start           = array[3]
      end             = array[4]
      foundGene       = False
      foundTranscript = False
      for entry in info:
        infoField = entry.split('=')
        if infoField[0] == 'gene_name':
          foundGene = True
          geneName  = infoField[1]
        elif infoField[0] == 'transcript_id':
          foundTranscript = True
          transcriptId    = infoField[1]

      # Terminate if the gene name or transcript id could not be found.
      if not foundGene or not foundTranscript:
        print('ERROR: Couldn\'t find gene name or transcript id.')
        print('Chromosome:' + chromosome + ', start: ' + start + ', end: ' + end + '.')
        exit(1)

      if transcriptId == lastTranscriptId: cdsId += 1
      else: cdsId = 1

      print(chromosome + ':' + start + '-' + end, file = regionFilehandle)
      print(geneName + '_' + transcriptId + '_' + str(cdsId) + '.pileup', file = idFilehandle)

      lastTranscriptId = transcriptId

# Close files.
filehandle.close()
regionFilehandle.close()
idFilehandle.close()

#!/usr/bin/python

from __future__ import print_function
import gzip
import sys

# Function for processing a line.
def processLine(start, end, info, lastTranscriptId, cdsId, regionFilehandle, idFilehandle):
  foundGene       = False
  foundTranscript = False
  foundType       = False
  for entry in info:
    infoField = entry.split('=')
    if infoField[0] == 'gene_name':
      foundGene = True
      geneName  = infoField[1]
    elif infoField[0] == 'transcript_id':
      foundTranscript = True
      transcriptId    = infoField[1]
    elif infoField[0] == 'gene_type':
      foundType = True
      geneType  = infoField[1]

  # Terminate if the gene name or transcript id could not be found.
  if not foundGene or not foundTranscript or not foundType:
    print('ERROR: Couldn\'t find gene name or transcript id.')
    print('Chromosome:' + chromosome + ', start: ' + start + ', end: ' + end + '.')
    exit(1)

  # If the feature is a gene, get the name and start a loop over transcripts.
  if array[2] == 'CDS' and geneType == "protein_coding":
    if transcriptId == lastTranscriptId: cdsId += 1
    else: cdsId = 1

    print(chromosome + ':' + start + '-' + end, file = regionFilehandle)
    print(geneName + '_' + transcriptId + '_' + str(cdsId) + '.pileup', file = idFilehandle)

    # Return the transcript id and cds number.
    return transcriptId, cdsId

  # If the transcript was not process, return the unchanged transcript and cds ids.
  else: return lastTranscriptId, cdsId

# Get the name of the input files.
gffFile      = sys.argv[1]
sequenceFile = sys.argv[2]

# If the file is zipped, open with gzip.
if gffFile.endswith('.gz'): filehandle = gzip.open(gffFile, 'rb')
else: filehandle = open(gffFile, 'r')

# Open files for output.
regionFilehandle = open("gene_regions.list", "w")
idFilehandle     = open("gene_transcripts.list", "w")

# Initialise variables.
cdsId            = 1
lastTranscriptId = None

# Get the list of requested reference sequences.
sequenceFilehandle = open(sequenceFile, 'r')
sequences          = []
for sequence in sequenceFilehandle.readlines():
  sequences.append(sequence.rstrip('\n'))
sequenceFilehandle.close()

for line in filehandle.readlines():
  line = line.rstrip('\n')
  if not line.startswith('#'):
    array = line.split('\t')
    info  = array[8].split(';')

    # Strip 'chr' from the chromosome name if it exists and check that the chromosome is present in
    # the input list.
    chromosome = array[0]
    isValid    = False
    if chromosome.strip('chr') in sequences:
      chromosome = chromosome.strip('chr')
      lastTranscriptId, cdsId = processLine(array[3], array[4], info, lastTranscriptId, cdsId, regionFilehandle, idFilehandle)
    elif chromosome in sequences:
      lastTranscriptId, cdsId = processLine(array[3], array[4], info, lastTranscriptId, cdsId, regionFilehandle, idFilehandle)

# Close files.
filehandle.close()
regionFilehandle.close()
idFilehandle.close()

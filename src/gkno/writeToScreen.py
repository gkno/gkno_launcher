#!/usr/bin/python

from __future__ import print_function

import helpInformation as hi
import errors as errors

import inspect
from inspect import currentframe, getframeinfo
import os
import sys

# For most of the usage requests, the version number and date are printed out
# at the start of the message.  Print these here.
def printHeader(version, date, gknoCommitID):
  print(file = sys.stdout)
  commitLength = len(gknoCommitID) + 16
  length       = max(commitLength, 29)
  print('=' * length, file = sys.stdout)
  print('  University of Utah gkno package', file = sys.stdout)
  print(file = sys.stdout)
  print('  version:    ', version, sep = '', file = sys.stdout)
  print('  date:       ', date, sep = '', file = sys.stdout)
  print('  git commit: ', gknoCommitID, sep = '', file = sys.stdout)
  print('=' * length, file = sys.stdout)
  print(file = sys.stdout)
  
# Write a line of text followed by an ellipsis and do not end the line.
def unterminatedText(text):
  print(text, '...', sep = '', end = '', file = sys.stdout)

# Terminate a line.
def terminate():
  print('done.', file = sys.stdout)
  sys.stdout.flush()

# Write the pipeline workflow to screen.
def workflow(superpipeline, workflow):

  # Define a help information object to make use of its methods for writing formatted text.
  helpInfo = hi.helpInformation(None, None, None)

  # Determine the length of the longest tool name.
  length = 0
  for task in workflow: length = (len(task) + len(superpipeline.tasks[task])) if (len(task) + len(superpipeline.tasks[task])) > length else length

  print(file = sys.stdout)
  print('Workflow:', sep = '', file = sys.stdout)
  for task in workflow:
    tool        = superpipeline.tasks[task]
    description = superpipeline.toolConfigurationData[tool].description
    helpInfo.writeComplexLine([task + ' (' + tool + '):', description], [length + 8, 0], noLeadingTabs = 1)
  print(file = sys.stdout)
  sys.stdout.flush()

# If any input values have been reordered, warn the user.
def reordered(graph, reorderedLists):

  # Only write a warning if values were reordered.
  if len(reorderedLists) > 0:
    text = []
    text.append('Input values have been reordered.')
    text.append('At least one of the tasks in the pipeline has arguments that are linked together. ' + \
    'This is usually the case, when there are two arguments whose values need to be connected with one ' + \
    'another (for example, the two fastq files from paired end sequencing). In constructing the pipeline, ' + \
    'gkno reordered the values supplied to some tasks, outlined below:')
    text.append('\t')
    for task, nodeId, linkedNodeId, originalList, reorderedList, referenceList in reorderedLists:
      longFormArgument = graph.getGraphNodeAttribute(nodeId, 'longFormArgument')
      text.append('-  task: ' + task + ', argument: ' + longFormArgument)
      string = originalList[0]
      for i in range(1, len(originalList)): string += ', ' + originalList[i]
      text.append('\toriginally:  ' + string)
      string = reorderedList[0]
      for i in range(1, len(reorderedList)): string += ', ' + reorderedList[i]
      text.append('\tmodified to: ' + string)
      string = referenceList[0]
      for i in range(1, len(referenceList)): string += ', ' + referenceList[i]
      text.append('\tto match:    ' + string)
      text.append('\t')

    text.append('Please check that these files are ordered correctly. To disable reordering of input values, ' + \
    'include the argument \'--do-not-reorder (-dnr)\' on the command line.')

    # Write the warning to screen.
    errors.errors().writeFormattedText(text, 'warning')

#!/usr/bin/python

from __future__ import print_function

import helpInformation as hi

import inspect
from inspect import currentframe, getframeinfo
import os
import sys

# For most of the usage requests, the version number and date are printed out
# at the start of the message.  Print these here.
def printHeader(version, date, gknoCommitID):
  print(file = sys.stdout)
  commitLength = len(gknoCommitID) + 14
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

#  def writeTracking(self, ID):
#    print("Logging gkno usage with ID: ", ID, "...", sep = '', end = '', file = sys.stdout)
#    sys.stdout.flush()
#  
#  def writeExecuting(self, filename):
#    print('Executing makefile: ', filename, '...', sep = '', file = sys.stdout)
#    sys.stdout.flush()
#  
#  def writeComplete(self, success):
#    if success != 0:
#      print('.failed', file = sys.stdout)
#      print('\ngkno failed to complete successfully.  Please check the output files to identify the cause of the problem.', file = sys.stderr)
#      self.errors.terminate()
#      sys.stdout.flush()
#
#  # Write debugging text.
#  def writeDebug(self, text):
#    frameInfo = getframeinfo(currentframe().f_back)
#    print('\tdebugging - ', frameInfo.filename, ' line ', frameInfo.lineno, ': ', text, sep = '', file = sys.stdout)
#    sys.stdout.flush()

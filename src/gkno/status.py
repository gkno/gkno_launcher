#!/usr/bin/python

from __future__ import print_function

import gknoErrors
from gknoErrors import *

import os
import sys

class gknoStatus:
  def __init__(self):
    self.errors = gknoErrors()

  # Determine the status of all makefiles.
  def getStatus(self, graph, config, makefileNames):
    completedMakefiles    = {}
    notCompletedMakefiles = {}
    hasCompletedMakefiles = False

    # Determine if all the incomplete makefiles need to be written out.
    writeIncomplete = True if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-WRITE-INCOMPLETE', 'values')[1][0] == 'set' else False

    # Loop over all phases.
    for phaseID in makefileNames:
      if phaseID not in completedMakefiles: completedMakefiles[phaseID] = []
      if phaseID not in notCompletedMakefiles: notCompletedMakefiles[phaseID] = []

      # Loop over all makefiles in the phase.
      for makefileName in makefileNames[phaseID]:
        complete = makefileName.replace('.make', '.ok')

        # Store the makefile name as either successfully completed or not.
        if os.path.exists(complete):
          hasCompletedMakefiles = True
          completedMakefiles[phaseID].append(makefileName)
        else: notCompletedMakefiles[phaseID].append(makefileName)

    # List all makefiles that have not yet been successfully executed.
    if writeIncomplete or hasCompletedMakefiles:
      printPhaseInfo = True if len(completedMakefiles.keys()) > 1 else False
      print(file = sys.stdout)
      print('=========================', file = sys.stdout)
      print('  gkno execution status', file = sys.stdout)
      print('=========================', file = sys.stdout)
      print(file = sys.stdout)

    if writeIncomplete:
      print('Following is a list of makefiles that have not yet been succesfully', file = sys.stdout)
      print('executed. This may be because they have not been submitted for execution, ', file = sys.stdout)
      print('they are currently being executed, or they have failed.', file = sys.stdout)
      print(file = sys.stdout)
      for phaseID in notCompletedMakefiles.keys():
        if printPhaseInfo: print('Phase ', phaseID, ': ', sep = '', file = sys.stdout)

        # If no makefiles have been completed, just state that all makefiles for the phase have not
        # successfully completed.
        if len(completedMakefiles[phaseID]) == 0:
          if printPhaseInfo: print('\t', end = '', file = sys.stdout)
          print('No makefiles for this phase have been successfully completed.', file = sys.stdout)
        else:
          for makefileName in notCompletedMakefiles[phaseID]:
            if printPhaseInfo: print('\t', end = '', file = sys.stdout)
            print(makefileName, file = sys.stdout)
      print(file = sys.stdout)

    # Only print out status if some jobs have been completed.
    if hasCompletedMakefiles:
      print('Summary:', file = sys.stdout)
      print(file = sys.stdout)

      # Print a summary of the number of executed makefiles.
      for phaseID in completedMakefiles.keys():
        numberOfComplete   = len(completedMakefiles[phaseID])
        numberOfIncomplete = len(notCompletedMakefiles[phaseID])
        totalNumber        = numberOfComplete + numberOfIncomplete
        if printPhaseInfo: print('Phase ', phaseID, ': ', sep = '', end = '', file = sys.stdout)
        print('Successfully executed makefiles: ', numberOfComplete, '/', totalNumber, sep = '', file = sys.stdout)

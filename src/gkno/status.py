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
  def getStatus(self, makefileNames):
    completedMakefiles    = {}
    notCompletedMakefiles = {}
    hasCompletedMakefiles = False

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

    # Only print out status if some jobs have been completed.
    if hasCompletedMakefiles:

      print(file = sys.stdout)
      print('=========================', file = sys.stdout)
      print('  gkno execution status', file = sys.stdout)
      print('=========================', file = sys.stdout)
      print(file = sys.stdout)
      printPhaseInfo = True if len(completedMakefiles.keys()) > 1 else False

      # Print a summary of the number of executed makefiles.
      for phaseID in completedMakefiles.keys():
        numberOfComplete   = len(completedMakefiles[phaseID])
        numberOfIncomplete = len(notCompletedMakefiles[phaseID])
        totalNumber        = numberOfComplete + numberOfIncomplete
        if printPhaseInfo: print('Phase ', phaseID, ': ', sep = '', end = '', file = sys.stdout)
        print('Successfully executed makefiles: ', numberOfComplete, '/', totalNumber, sep = '', file = sys.stdout)

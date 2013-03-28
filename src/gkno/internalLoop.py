#!/usr/bin/python

from __future__ import print_function
import sys

import dataChecking
from dataChecking import *

import errors
from errors import *

import files
from files import *

class internalLoop:

  # Constructor.
  def __init__(self):
    self.arguments          = {}
    self.argumentList       = []
    self.data               = []
    self.errors             = errors()
    self.ID                 = 0
    self.numberOfIterations = 0
    self.tasks              = []
    self.usingInternalLoop  = False

  # Check for existence of the requested file.
  def checkLoopFile(self, arguments):
    self.filename = arguments['--internal-loop']
    if self.filename != '':
      io                     = files()
      self.data              = io.getJsonData(self.filename, True)
      self.usingInternalLoop = True

  # Check that the information contained in the internal loop information file is
  # valid and store in the 'information' structure.
  def checkInformation(self, argumentInformation, shortForms, verbose):

    # First check that there is a list of command line arguments that will be applied in
    # each iteration of the loop and a section containing the values for each iteration.
    if 'arguments' not in self.data:
      self.errors.missingSectionsInternalLoop(verbose, 'arguments', self.filename)
      self.errors.terminate()

    if 'values' not in self.data:
      self.errors.missingSectionsInternalLoop(verbose, 'values', self.filename)
      self.errors.terminate()

    # Parse through all of the arguments in the arguments section of the internal loop
    # file and check if they are short forms.  Reset the structure with long form arguments.
    for argument in self.data['arguments']:
      if argument in shortForms: self.argumentList.append(shortForms[argument])
      else: self.argumentList.append(argument)

    # Read through all of the arguments and check that they link to arguments in tasks
    # listed as in an internal loop.
    for argument in self.argumentList:
      if argument in argumentInformation:
        linkedTask = argumentInformation[argument]['link to this task']
        if linkedTask not in self.tasks:
          self.errors.argumentForTaskOutsideInternalLoop(verbose, argument, argumentInformation[argument]['short form argument'], linkedTask, self.filename)
          self.errors.terminate()
      else:
        self.errors.unknownArgumentInternalLoop(verbose, argument, self.filename)
        self.errors.terminate()

    # Now loop through the supplied values.  Check that there are values for each of the
    # arguments and that the supplied values are valid.
    for blockID in self.data['values']:
      valueBlock = self.data['values'][blockID]
      if len(valueBlock) != len(self.argumentList):
        self.errors.incorrectNumberOfValuesInInternalLoopFile(verbose, blockID, len(valueBlock), len(self.argumentList), self.filename)
        self.errors.terminate()

      for argument, value in zip(self.argumentList, valueBlock):
        dataType = argumentInformation[argument]['type']
        success  = checkDataType(dataType, value)
        if not success: 
          self.errors.incorrectDataTypeinInternalLoop(verbose, blockID, argument, value, dataType, self.filename)
          self.errors.terminate()

        # Store the arguments.
        linkedTask     = argumentInformation[argument]['link to this task']
        linkedArgument = argumentInformation[argument]['link to this argument']
        if linkedTask not in self.arguments: self.arguments[linkedTask] = {}
        if linkedArgument not in self.arguments[linkedTask]: self.arguments[linkedTask][linkedArgument] = {}
        if blockID not in self.arguments[linkedTask][linkedArgument]: self.arguments[linkedTask][linkedArgument][blockID] = []
        self.arguments[linkedTask][linkedArgument][blockID].append(value)

    # Store the number of iterations in the internal loop.
    self.numberOfIterations = len(self.data['values'])
    if self.numberOfIterations == 0: self.numberOfIterations = 1

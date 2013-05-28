#!/usr/bin/python

from __future__ import print_function
import sys

import dataChecking
from dataChecking import *

import errors
from errors import *

import files
from files import *

class multipleRuns:

  # Constructor.
  def __init__(self):
    self.allArguments    = {}
    self.arguments       = {}
    self.argumentFormats = []
    self.argumentData    = {}
    self.filename        = ''
    self.hasMultipleRuns = False
    self.numberDataSets  = 1

  # Check if the pipeline is going to be run multiple times.
  def checkForMultipleRuns(self, uniqueArguments, argumentList, verbose):
    er = errors()

    # First, check if multiple runs have been requested.
    if '--multiple-runs' in uniqueArguments:
      self.hasMultipleRuns = True

      # Get the name of the file containing the required information for the multiple runs and check that
      # the file exists and is a valid json.
      for argument, value in argumentList:
        if argument == '--multiple-runs':
          self.filename = value
          break

      # If the --multiple-runs argument was not given a value on the command line, terminate.
      if self.filename == '':
        er.missingArgumentValue(verbose, '', 'pipeline', '--multiple-runs', '-mr', '', '', 'string')
        er.terminate()

  # Get all of the information required for performing multiple runs.
  def getInformation(self, verbose):
    er = errors()

    # Attempt to open the json file containing the information.
    io = files()
    data = io.getJsonData(self.filename, False)
    if data == '':
      er.noMultipleRunFile(verbose, self.filename)
      er.terminate()

    # The multiple runs file should contain two sections: 'format of data list' and 'data list'.
    # Check that these exist and store the information
    if 'arguments' not in data:
      er.missingSectionMultipleRunsFile(verbose, self.filename, 'arguments')
      er.terminate()

    if 'values' not in data:
      er.missingSectionMultipleRunsFile(verbose, self.filename, 'values')
      er.terminate()

    # Check that the "format of data list" is well formed and store.
    givenType = type(data['arguments'])
    if givenType != list:
      er.differentDataTypeInConfig(verbose, self.filename, '', 'values', list, givenType)
      er.terminate()

    # Ensure that the long form of the argument is used in the argumentFormats structure.
    for argument in data['arguments']:
      self.argumentFormats.append(argument)

    # Now check the data for the "data list" and store the information.
    givenType = type(data['values'])
    if givenType != dict:
      er.differentDataTypeInConfig(verbose, self.filename, '', 'values', dict, givenType)
      er.terminate()

    # Parse and check each set of data.
    count               = 0
    self.numberDataSets = 0
    for dataSetID in data['values']:
      self.numberDataSets += 1
      dataSet = data['values'][dataSetID]
      givenType = type(dataSet)
      if givenType != list:
        er.differentDataTypeInConfig(verbose, self.filename, '', 'values', list, givenType)
        er.terminate()

      # Check that there is a valid number of entries in the list.  For example, if the argumentFormats list
      # has two entries, the data list must contain two entries for each run (i.e. one value for each argument
      # defined in the formats for each run).  Thus the number of entries in the 'data list' must be a
      # multiple of the number of entries in the 'format of data list' section.
      if len(data['values'][dataSetID]) != len(self.argumentFormats) != 0:
        er.incorrectNumberOfEntriesInMultipleJson(verbose, dataSetID, self.filename)
        er.terminate()

      for argument in data['values'][dataSetID]:
        if self.argumentFormats[count] not in self.argumentData: self.argumentData[self.argumentFormats[count]] = []
        self.argumentData[self.argumentFormats[count]].append(argument)
        count += 1
        if count == len(self.argumentFormats): count = 0

  # Check that the arguments in the argumentFormats list are valid command line arguments and that
  # the associated data is valid.
  def checkInformation(self, singleTask, arguments, shortForms, verbose):
    er              = errors()
    longFormFormats = []
    longFormData    = {}

    for argument in self.argumentData:
      values = self.argumentData[argument]

      # Check that the argument is valid.
      if argument in arguments:
        longForm  = argument
        shortForm = arguments[argument]['short form argument']
      elif argument in shortForms: 
        longForm  = shortForms[argument]
        shortForm = argument
      else:
        er.unknownArgumentInMultipleRuns(False, self.filename, argument)
        er.terminate()

      if 'link to this task' in arguments[longForm]:
        task = arguments[longForm]['link to this task']
        link = arguments[longForm]['link to this argument']
      else:
        task = singleTask
        link = longForm

      # Now check the data associated with this argument.
      dataType = arguments[longForm]['type']
      for value in self.argumentData[argument]:
        success = checkDataType(dataType, value)
        if not success:
          if dataType == 'flag': er.flagGivenInvalidValueMultiple(verbose, self.filename, argument, shortForm, value)
          elif dataType == 'bool': er.incorrectBooleanValueInMultiple(verbose, self.filename, argument, shortForm, value)
          elif dataType == 'integer': er.incorrectDataTypeInMultiple(verbose, self.filename, argument, shortForm, value, dataType)
          elif dataType == 'float': er.incorrectDataTypeInMultiple(verbose, self.filename, argument, shortForm, value, dataType)
          elif dataType == 'string': er.incorrectDataTypeInMultiple(verbose, self.filename, argument, shortForm, value, dataType)
          else: print('error with data type 2')
          er.terminate()

      # Add the values to the data structures.
      longFormFormats.append(longForm)
      longFormData[longForm] = self.argumentData[argument]
      if task not in self.allArguments: self.allArguments[task] = {}
      self.allArguments[task][link] = self.argumentData[argument]

    # Replace the original argumentFormats structure with the longFormFormats to ensure that 
    # the list only contains the long forms of the arguments.
    self.argumentFormats = longFormFormats
    self.argumentData    = longFormData

  # Get the next set of arguments from the data structures.
  def getArguments(self):
    self.arguments = {}
    for task in self.allArguments:
      if task not in self.arguments: self.arguments[task] = {}
      for argument in self.allArguments[task]:
        self.arguments[task][argument] = []
        self.arguments[task][argument].append(self.allArguments[task][argument].pop(0))

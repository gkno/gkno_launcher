#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class parameterSetErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '14'

  ##################################
  ## General parameter set errors ##
  ##################################

  # An invalid parameter set name was specified on the command line.
  def invalidParameterSet(self, name, available):
    self.text.append('Unknown parameter set.')
    self.text.append('The parameter set \'' + name + '\' was requested on the command line, but this is not a valid parameter set for this ' + \
    'pipeline. Please ensure that either no parameter set, or a set from the following list is requested.')
    self.text.append('\t')
    for parameterSet in available: self.text.append('\t' + parameterSet)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Invalid argument in the parameter set.
  def invalidArgumentInTool(self, task, tool, name, argument):
    self.text.append('Invalid argument in tool parameter set.')
    self.text.append('As part of the pipeline, the task \'' + task + '\' uses the tool \'' + tool + '\'. In the configuration file ' + \
    'for this tool, the parameter set \'' + name + '\' has a value set for the argument \'' + argument + '\', but this is not a ' + \
    'valid argument for this tool. Please check the tool configuration file and ensure that all the arguments in the parameters ' + \
    'sets are valid.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ########################################
  ## Errors with defined parameter sets ##
  ########################################

  # If a parameter set includes an invalid node ID.
  def invalidNodeInPipelineParameterSet(self, pipeline, pSet, nodeId, ID):
    self.text.append('Invalid node ID in parameter set.')
    self.text.append('The configuration file for pipeline \'' + pipeline + '\' contains information for the parameter set with the ID \'' + pSet + \
    '\'. Within this set, the data with the ID \'' + ID + '\' contains the node ID \'' + nodeId + '\', which is not a valid node ID in the ' + \
    'pipeline. Please ensure that all parameter set data points to a valid node within this pipeline, or has the correct address to point to a ' + \
    'node in a contained pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ###############################################
  ## Errors reading in external parameter sets ##
  ###############################################

  # If an external parameter set has the same name as a parameter set in the primary configuration file.
  def externalSetRepeat(self, pipeline, parameterSet):
    self.text.append('Error with external parameter sets.')
    self.text.append('The pipeline \'' + pipeline + '\' has an external file holding user defined parameter sets (' + pipeline + '-parameter-' + \
    'sets.json). This file contains a parameter set with the name \'' + parameterSet + '\', but a set with this name is already present in the ' + \
    'main configuration file. Please ensure that all parameter sets are given unique names.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ###########################################
  ## Errors with exporting a parameter set ##
  ###########################################

  def exportToDefinedSet(self, pipeline, setName):
    self.text.append('Error exporting a parameter set.')
    self.text.append('The defined parameter set name to export (' + setName + ') is already a defined parameter set for the current pipeline (' + \
    pipeline + '). When exporting a parameter set, the name of the user defined set must be unique, i.e. not present in both \'' + pipeline + \
    '.json\' or \'' + pipeline + '-parameter-sets.json\', if it exists.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

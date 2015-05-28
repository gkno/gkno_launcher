#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class graphErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '8'

  # A general entry in the configuration file is invalid.
  def missingStubExtensionForSharedNode(self, task, argument):
    self.text.append('Cannot construct shared graph nodes.')
    self.text.append('The task \'' + task + '\', argument \'' + argument + '\' is defined as being shared with other nodes in the pipeline. ' + \
    'At least one of the nodes that this is being shared with is a stub, and since this argument is not a stub, the extension associated with ' + \
    'the stub must be included in the pipeline configuration file.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the number of subphases is inconsistent with the number of output files.
  def outputsSubphases(self, task, argument, outputs, subphases):

    # Define text for use in the message based on whether there needs to plurals or not.
    subphasesPlural= {}
    if subphases == 1:
      subphasesPlural['is'] = 'is'
      subphasesPlural['file'] = 'file'
      subphasesPlural['time'] = 'time'
    else:
      subphasesPlural['is'] = 'are'
      subphasesPlural['file'] = 'files'
      subphasesPlural['time'] = 'times'

    outputsPlural= {}
    if outputs == 1:
      outputsPlural['file'] = 'file'
    else:
      outputsPlural['file'] = 'files'

    self.text.append('Number of output files inconsistent with the number of subphases.')
    self.text.append('As part of the pipeline, task \'' + task + '\' produces ' + str(outputs) + ' output ' + outputsPlural['file'] + \
    '. There ' + subphasesPlural['is'] + ', however, ' + str(subphases) + ' input ' + subphasesPlural['file'] + ' supplied to the task. ' + \
    'Since the task is not greedy, the task is run ' + str(subphases) + ' '  + subphasesPlural['time'] + ', which requires that there ' + \
    'are exactly this many output files defined. Please check all of the arguments supplied to the pipeline and ensure that if multiple ' + \
    'input arguments have been specified, this many output files are also specified. Alternatively, if no output files are specified, ' + \
    'gkno will construct the correct number of output files (if instructions are included in the configuration files).')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##################################
  ## Errors with node connections ##
  ##################################

  # A connection is requested, but either the source or target node is not present in the graph.
  def connectionToInvalidNode(self, tier, pipeline, definition, source, target, nodeIds):

    # Tailor the message based on whether this is a nested pipeline.
    text = 'nested ' if tier != 1 else ''

    # Write the message.
    self.text.append('Error connecting nodes.')
    self.text.append('The "connect nodes" section of the pipeline configuration file defines which nodes should be connected with an edge. The ' + \
    text + 'pipeline \'' + pipeline + '\' contains a connection between the nodes:')
    self.text.append('\t')
    self.text.append('\t' + source + ' --> ' + target)
    self.text.append('\t')
    self.text.append('The ' + definition + ' node does not exist in the graph. Please ensure that connections are only made between defined ' + \
    'nodes in the graph. Below is a list of all nodes in this pipeline graph:')
    self.text.append('\t')
    for nodeId in nodeIds: self.text.append('\t' + nodeId)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

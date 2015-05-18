#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class constructFilenameErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '15'

  ##################################
  ## Errors with top level fields ##
  ##################################

  # If the extension could not be identified.
  def unableToRetrieveExtension(self, task, argument, filename, extensions):
    self.text.append('Unable to identify filename extension when constructing filename.')
    self.text.append('The file associated with the pipeline task \'' + task + '\', argument \'' + argument + \
    '\' is constructed using the name of a file already used in the pipeline. The file used as a template ' + \
    'for the construction has the name \'' + filename + '\'.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If values from a different argument are being added to the filename, but the argument is invalid.
  def invalidArgument(self, task, tool, argument, useArgument):
    self.text.append('Invalid argument in construction instructions')
    self.text.append('As part of the pipeline, the task \'' + task + '\' uses the tool \'' + tool + '\'. The ' + \
    'argument \'' + argument + '\' has its values constructed using instructions contained in the tool configuration ' + \
    'file. As part of the construction, values from other tool arguments are used. In particular, the argument \'' + \
    useArgument + '\' is specified, but this is not a valid argument for the tool. Please ensure that all construction ' + \
    'instructions in the configuration file contain valid information.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Values from another argument are to be built into the filename, but the argument whose values are to be used
  # has not been set.
  def noArgumentValuesToBuild(self, task, argument, constructionArgument):
    self.text.append('Error constructing values for argument.')
    self.text.append('No values for the argument \'' + argument + '\' used by the task \'' + task + '\' were set on the ' + \
    'command line and so values are constructed using instructions from the configuration file. The instructions use ' + \
    'the values given to another argument \'' + constructionArgument + '\' (note that this is the argument defined for the tool ' + \
    'and may be different, or even not present, at the pipeline level), but no values were specified for this argument.')
    self.text.append('\tIt is preferable to ensure that this error cannot occur, so ensure that the value required to ' + \
    'construct the filename is listed as required in either the tool or the pipeline configuration file, or that a default' + \
    'value is provided in the parameter sets.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The number of base values being used to construct the output filenames have a different number of values than the
  # number of subphases. This would result in constructing the wrong number of output files.
  def numberBaseValues(self, task, argument, shortFormArgument, numberBaseValues, subphases):
    plural = {}
    plural['time'] = 'time' if subphases == 1 else 'times'
    plural['value'] = 'value' if numberBaseValues == 1 else 'values'
    plural['is'] = 'is' if numberBaseValues == 1 else 'are'

    self.text.append('Incorrect number of filenames in construction.')
    self.text.append('As part of the pipeline, the task \'' + task + '\' has filenames for the argument \'' + argument + \
    ' (' + shortFormArgument + ')\' constructed using instructions from the tool configuration file. The task is not greedy ' + \
    'and has been supplied with multiple input files, so this task is to be run ' + str(subphases) + ' ' + plural['time'] + \
    '. The output file names are being generated based on the values provided to another tool argument, but there ' + plural['is'] + \
    ' ' + str(numberBaseValues) + ' ' + plural['value'] + ' associated with this argument. As a result, the number of output ' + \
    'files created will be different to the number of input files and consequently, the pipeline will not run correctly. ' + \
    'A likely explanation to this problem is that the input file argument with multiple values is not the argument used to ' + \
    'construct the output filenames. Either the construction instructions need to be modified, or the output files need to ' + \
    'be explicitly defined on the command line.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ###########################
  ## Errors with divisions ##
  ###########################

  # If a task splits into multiple divisions, only a single node can be associated with multiple values.
  def multipleDivisionNodes(self, task, argument, nodeIds):
    self.text.append('Error splitting task into multiple divisions.')
    self.text.append('The task \'' + task + '\' is to be split into multiple divisions and consequently run multiple times for ' + \
    'multiple sets of input data. A node associated with the task is marked as the node with multiple values. In this case, the ' + \
    'argument \'' + argument + '\' is the argument that is given multiple values, but this argument is linked to multiple nodes ' + \
    'as listed here:')
    self.text.append('\t')
    for nodeId in nodeIds: self.text.append('\t' + nodeId)
    self.text.append('\t')
    self.text.append('Only a single node is permitted to have multiple values. Please check the pipeline configuration file and ' + \
    'ensure that any task that should be run multiple times for multiple input option values only has a single node with multiple ' + \
    'values')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

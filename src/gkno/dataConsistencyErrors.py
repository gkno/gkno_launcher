#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class consistencyErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '10'

  ##################################################
  ## Errors with the values provided to arguments ##
  ##################################################

  # Multiple values provided to an argument that does not allow it.
  def multipleValues(self, longFormArgument, shortFormArgument, task, isPipeline):
    self.text.append('Multiple values provided when not permitted.')

    # Provide the error if the argument was a top level argument.
    if isPipeline:
      self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was given multiple values on the command line, but this ' + \
      'argument is only permitted to receive a single value. Please check the command line and ensure that this argument was only specified once.')

    # Otherwise, make it clear that tha argument was not a top level argument.
    else:
      self.text.append('The task \'' + task + '\' in the pipeline has been given multiple values for it\'s argument \'' + longFormArgument + ' (' + shortFormArgument + \
      ')\', but this argument is only permitted to receive a single value. This argument does not have a pipeline argument that can be set on the command line, so was' + \
      'either specified for the task specifically, or there is an error in the pipeline definition.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a command line argument is given a value with an incorrect extension.
  def invalidExtensionPipeline(self, longFormArgument, shortFormArgument, value, extensions):
    self.text.append('Invalid extension on argument value.')
    self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was given the value \'' + value + \
    '\', but this has an extension inconsistent with that expected. The extension can be any of the following:')
    self.text.append('\t')
    for extension in extensions: self.text.append('\t' + extension)
    self.text.append('\t')
    self.text.append('Please check that all arguments on the command line (including those in lists) are valid.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If an argument is given a value with an incorrect extension and no pipeline argument exists for this argument.
  def invalidExtension(self, task, longFormArgument, shortFormArgument, value, extensions):
    self.text.append('Invalid extension on argument value.')
    self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' for the task \'' + task + '\' was given ' + \
    'the value \'' + value + '\', but this has an extension inconsistent with that expected. The extension can be any of the following:')
    self.text.append('\t')
    for extension in extensions: self.text.append('\t' + extension)
    self.text.append('\t')
    self.text.append('It is most likely that this value was generated by gkno and was not supplied on the command line (no pipeline command line ' + \
    'argument exists for this value). This is likely a result of a task in the pipeline being linked to another task in an invalid manner. ' + \
    'Please check the pipeline configuration file and ensure that all shared nodes are shared between task arguments that expect the same data ' + \
    'data formats.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##################################################
  ## Errors with arguments that have not been set ##
  ##################################################

  # A required argument has not been set.
  def unsetRequiredArgument(self, longFormArgument, shortFormArgument, description):
    self.text.append('The required command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' is missing.')
    self.text.append('The description of this argument is:')
    self.text.append('\t')
    self.text.append('"' + description + '"')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A required argument has not been set. No pipeline argument exists to set this argument.
  def unsetRequiredNestedArgument(self, task, longFormArgument, shortFormArgument, description, pipeline):
    self.text.append('A required command line argument is missing.')
    self.text.append('The argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' is required by task \'' + task + '\' in order for ' + \
    'execution to proceed, but no value has been provided. There is no top level command line argument that can set this value, so it is highly ' + \
    'recommended that an argument is defined in the pipeline configuration file (' + pipeline + '.json) to allow easier use of this pipeline. ' + \
    'In the absence of a commmand, this value can be set using the following syntax:')
    self.text.append('\t')
    self.text.append('gkno ' + pipeline + ' --' + task + ' [' + longFormArgument + ' value] [options]')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A node for an input file is not present.
  def noInputNode(self, task, tool, argument):
    text = ' (this task is part of a pipeline called by the main pipeline)' if '.' in task else ''
    self.text.append('A node required for the pipeline is missing.')
    self.text.append('The task \'' + task + '\' using tool \'' + tool + '\'' + text + ', requires the argument \'' + argument + '\' to be set. ' + \
    'No node exists in the graph for this argument, which means that there is no pipeline argument to set it\'s value. Please ensure that this ' + \
    'task argument is defined as either a unique or shared node in the pipeline configuration file and include a top level pipeline argument to ' + \
    'set this value.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A node required for constructing filenames is not present.
  def noNodeForConstruction(self, task, tool, argument, requiredArgument):
    print('TEST', task, tool, argument, requiredArgument)
    text = ' (this task is part of a pipeline called by the main pipeline)' if '.' in task else ''
    self.text.append('A node required for constructing a filename is not present.')
    self.text.append('In order to construct values for the argument \'' + argument + '\' in the task with address \'' + task + '\' using tool \'' + \
    tool + '\'' + text + ', the argument \'' + requiredArgument + '\' must be defined, or be constructable. There is no node in the graph for ' + \
    'this argument, so this is not possible. Please modify the pipeline configuration file to provide an argument to set this value, or ensure ' + \
    'that the argument shares a node with another task in the pipeline, allowing the value to be constructed.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # An output file exists with no values and there are no instructions for creating any.
  def noConstructionMethod(self, task, tool, argument):
    self.text.append('No method of constructing an output file.')
    self.text.append('The task \'' + task + '\', using tool \'' + tool + '\' generates an output file using the argument \'' + argument + '\'. This argument has not ' + \
    'been set using a pipeline argument (if available) and no instructions exist in the tool configuration file for constructing the filename. Please ensure that a ' + \
    'value is given for this argument, or update the tool configuration file to allow the filenames to be constructed.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

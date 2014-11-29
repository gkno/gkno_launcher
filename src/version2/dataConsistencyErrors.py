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

    # Admin errors generate an error code of '2'.
    # Command line errors generate an error code of '3'.
    # File handling errors generate an error code of '4'.
    # General configuration file errors generate an error code of '5'.
    # Tool configuration file errors generate an error code of '6'.
    # Pipeline configuration file errors generate an error code of '7'.
    # Errors associated with the graph construction generate an error code of '8'.
    # Data consistency errors generate an error code of '9'.
    self.errorCode = '9'

  # If a command line argument is given a value with an incorrect extension.
  def invalidExtension(self, longFormArgument, value, extensions):
    self.text.append('Invalid extension on argument value.')
    self.text.append('The command line argument \'' + longFormArgument + '\' was given the value \'' + value + '\', but this has an extension ' + \
    'inconsistent with that expected. The extension can be any of the following:')
    self.text.append('\t')
    for extension in extensions: self.text.append('\t' + extension)
    self.text.append('\t')
    self.text.append('Please check that all arguments on the command line (including those in lists) are valid.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A required argument has not been set.
  def unsetRequiredArgument(self, longFormArgument, shortFormArgument, description):
    self.text.append('The required command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' is missing.')
    self.text.append('This argument is described as \'' + description + '\'.')
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

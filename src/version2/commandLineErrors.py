#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class commandLineErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '3'

  # If a tool is added, but the tool is already available.
  def invalidCommandLine(self):
    self.text.append('Invalid command line.')
    self.text.append('The supplied command line is invalid. Please check the syntax and correct any errors. For additional help, see the ' + \
    'documentation, or type gkno --help.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a command line argument is invalid.
  def invalidArgument(self, argument):
    self.text.append('Invalid argument on the command line.')
    self.text.append('The supplied command line contains the argument \'' + argument + '\', but this is not a valid argument. Please use ' + \
    '\'--help\' on the command line to see all of the available arguments and correct the command line.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # Multiple parameter sets are defined.
  def multipleParameterSets(self):
    self.text.append('Multiple parameter set defined')
    self.text.append('The command line argument \'--parameter-set (-ps)\' can be used to define a predefined set of parameters to use. ' + \
    'Multiple parameter sets have been defined on the command line, but it is only permissable to define a single set. Please ensure that only ' + \
    'one parameter set is defined on the command line. If no parameter set exists containing all of the desired parameters, it is possible to ' + \
    'generate a new parameter set by defining all the required parameters on the command line and then using the \'--export-parameter-set (-ep)\' ' + \
    'argument to define a name for the new parmater set.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

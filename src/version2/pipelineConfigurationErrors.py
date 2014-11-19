#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class pipelineErrors:

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
    self.errorCode = '7'

  # If a configuration file contains has repeated definitions of the same long form argument.
  def repeatedLongFormArgument(self, nodeID, longFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. This argument has already been defined in the configuration file. Please ensure that all ' + \
    'arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a configuration file contains has repeated definitions of the same short form argument.
  def repeatedShortFormArgument(self, nodeID, longFormArgument, shortFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'short form argument \'' + shortFormArgument + '\' associated with the long form argument \'' + longFormArgument + '\'. This argument has ' + \
    'already been defined in the configuration file. Please ensure that all arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a long form argument is defined with no short form.
  def noShortFormArgument(self, nodeID, longFormArgument):
    self.text.append('No defined short form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. There is no short form argument associated with this, however. Please ensure that all ' + \
    'nodes in the configuration file defining arguments contain both a short and long form version of the argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a short form argument is defined with no long form.
  def noLongFormArgument(self, nodeID, shortFormArgument):
    self.text.append('No defined long form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'short form argument \'' + shortFormArgument + '\'. There is no long form argument associated with this, however. Please ensure that all ' + \
    'nodes in the configuration file defining arguments contain both a short and long form version of the argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

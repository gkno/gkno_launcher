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

    # Command line errors generate an error code of '2'.
    self.errorCode = '2'

  # If a tool is added, but the tool is already available.
  def invalidCommandLine(self):
    self.text.append('Invalid command line.')
    self.text.append('The supplied command line is invalid. Please check the syntax and correct any errors. For additional help, see the ' + \
    'documentation, or type gkno --help.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

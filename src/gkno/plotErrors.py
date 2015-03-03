#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class plotErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '12'

  # If a plot of the pipeline graph was requested, but no filename was provided.
  def noFilename(self):
    self.text.append('No filename for pipeline graph plot.')
    self.text.append('A plot of the pipeline graph was requested, but no filename was provided. Please ensure that the command line ' + \
    'argument for the graph of choice (full, reduced or both) is accompanied by a filename.')
    self.text.append('\t')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

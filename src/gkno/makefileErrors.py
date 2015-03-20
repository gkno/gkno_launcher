#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class makefileErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '13'

  # The pipeline generates multiple output files with the same name.
  def duplicateOutputFiles(self, duplicates):
    self.text.append('Pipeline produces duplicate output files.')
    self.text.append('Different tasks in the pipeline produce output files that have the same name. This confuses the makefile ' + \
    'used to execute the tasks as multiple rules have the same output. In addition, since multiple tasks write to the same ' + \
    'file, all desired results will not be produced. Either specify output file names on the command line, if possible, or update ' + \
    'the pipeline configuration file to append provide distinguishing text to files.')
    self.text.append('\t')
    self.text.append('The following files were identified as duplicated:')
    for filename in duplicates: self.text.append('\t' + filename)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

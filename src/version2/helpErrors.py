#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors as err

import os
import sys

class helpErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = err.errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '11'

  # The pipeline configuration file contains an invalid category.
  def invalidCategory(self, pipeline, category, categories):
    self.text.append('Invalid category in pipeline configuration file.')
    self.text.append('The configuration file for the pipeline \'' + pipeline + '\' contains an invalid category \'' + category + '\' in the ' + \
    'categories list. The pipeline can be marked as belonging to any of the following categories:')
    self.text.append('\t')
    for category in sorted(categories): self.text.append('\t' + category)
    self.text.append('\t')
    self.text.append('Please ensure that all categories listed in the configuration file are derived from this list.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

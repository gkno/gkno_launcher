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

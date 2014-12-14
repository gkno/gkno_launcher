#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors as errors

import os
import sys

class argumentErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors.errors()

    # The error messages are stored in the following list.
    self.text = []

    # Different segments of gkno produce different error codes. The list of which
    # values correspond to which aspect of the code are held in the adminErrors.

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '9'

  # If arguments are to be imported from a tool, but the tool is not available,
  def invalidImportTool(self, task):
    self.text.append('Unable to import arguments.')
    self.text.append('The pipeline configuration file includes the field \'import arguments\', which identifies a task from which to import ' + \
    'arguments. Note that this task must be the address of a task in the pipeline, and this task could point to a tool or another pipeline. If ' + \
    'the task points to a pipeline, the arguments for that pipeline will be imported, otherwise the arguments from a tool will be imported. If ' + \
    'successful, the arguments from this tool/pipeilne will be available on the command line.')
    self.text.append('\tThe tool identified \'' + task + '\' is not available as part of this pipeline. Please check the configuration file and ' + \
    'replace the tool name with a tool available in the pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

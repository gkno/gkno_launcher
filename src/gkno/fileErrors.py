#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class fileErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '4'

  # The opened file is not a valid json file.
  def notJson(self, filename, info):

    # Determine if this is a tool or a pipeline and strip the path from the name.
    filenameList      = filename.split('/')
    name              = filenameList[-1].rsplit('.json')[0]
    configurationType = 'tool' if filenameList[-2] == 'tools' else 'pipeline'

    # Get additional error messages.
    exc_type, exc_value, exc_traceback = sys.exc_info()

    # Define the error message.
    self.text.append('Invalid configuration file.')
    self.text.append('The ' + configurationType + ' configuration file \'' + name + '\' is not a valid json file. The specific error raised is:')
    self.text.append('\t')
    self.text.append(str(exc_value))
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool is added, but the tool is already available.
  def invalidPipelineName(self, pipelines, pipeline):
    self.text.append('Invalid pipeline.')
    self.text.append('The requested pipeline is not recognised. The command line must have the syntax \'gkno <pipeline>\' where the \'pipeline\' ' + \
    'is the name of a pipeline. The requested pipeline \'' + pipeline + '\' is not an available pipeline. Please check the command ' + \
    'line or request help (\'gkno --help\') to identify the required pipeline.')
    if pipelines:
      self.text.append('\t')
      self.text.append('The following are the closest pipelines, ranked by similarity:')
      for task in pipelines[:5]: self.text.append('\t' + task)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If files required for the pipeline to run are missing, write a warning.
  def missingFiles(self, fileList):
    self.text.append('Missing input files.')
    self.text.append('In order to execute, there are a number of input files that are required. The following list indicates all required files that ' + \
    'are missing. Since files are missing, the generated makefile will not be automatically executed, but will need to be executed manually (make -f' + \
    ' <makefile name>), or gkno can be reexecuted when the required files are present.')
    self.text.append('\t')
    for filename in fileList: self.text.append('\t' + filename)
    self.errors.writeFormattedText(self.text, errorType = 'warning')

  # A list was provided, but does not exist.
  def missingList(self, argument, value):
    self.text.append('Missing list.')
    self.text.append('The argument \'' + argument + '\' was supplied with a file with the extension \'.list\', which implies that the values to be ' + \
    'used for this argument are to be extracted from this file. The file does not exist, however. Please ensure that the file exists, or, if this ' + \
    'is not intended to be a list of values, but a single file, that the extension for the file is not \'.list\'.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

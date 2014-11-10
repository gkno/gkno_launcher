#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class toolErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # Tool configuration file errors generate an error code of '5'.
    self.errorCode = '5'

  # If a tool argument is listed as a stub, it must be accompanied by a list of extensions.
  def noExtensionsForStub(self, name, argument):
    self.text.append('Missing data for argument.')
    self.text.append('The configuration file for tool \'' + name + '\' contains information for the argument \'' + argument + '\'. This ' + \
    'is listed as being a stub, but no extensions are provided. For file stubs, the extensions of all the files that will be created/are ' + \
    'required must be listed.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

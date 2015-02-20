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

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '6'

  # If a tool argument is listed as a stub, it must be accompanied by a list of extensions.
  def noExtensionsForStub(self, name, argument):
    self.text.append('Missing data for argument.')
    self.text.append('The configuration file for tool \'' + name + '\' contains information for the argument \'' + argument + '\'. This ' + \
    'is listed as being a stub, but no extensions are provided. For file stubs, the extensions of all the files that will be created/are ' + \
    'required must be listed.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the value supplied to a tool attribute is invalid.
  def invalidValues(self, name, argument, attribute, value, validValues):
    self.text.append('Invalid value given to attribute.')
    self.text.append('The configuration file for tool \'' + name + '\' contains information for the argument \'' + argument + '\'. The attribute \'' + \
    attribute + '\' for this argument is given the value \'' + value + '\', but this is not a valid value for this attribute. The valid values are:')
    for validValue in validValues: self.text.append('\t' + validValue)
    self.text.append('\t')
    self.text.append('Please modify the the configuration file to only contain valid values for all attributes.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the 'Inputs' or 'Outputs' sections are missing from the arguments.
  def missingArgumentSection(self, name, section):
    self.text.append('Missing arguments section.')
    self.text.append('The configuration file for tool \'' + name + '\' is missing \'' + section + '\' in the arguments section. All tool ' + \
    'configuration files must include sections titled \'Inputs\' and \'Outputs\' (note the capitalisation) in the argument section, even if ' + \
    'no actual arguments are included within these sections. Please ensure that these sections are present.') 
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

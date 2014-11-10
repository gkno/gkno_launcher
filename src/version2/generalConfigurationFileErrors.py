#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class generalConfigurationFileErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # Command line errors generate an error code of '2'.
    self.errorCode = '4'

 # A general entry in the configuration file is invalid.
  def invalidAttribute(self, attribute, allowedAttributes, helpInfo):

    # Get the infomation from the helpInfo.
    name, section, id = helpInfo

    self.text.append('Invalid attribute in configuration file: ' + name)

    # Define the error message if no section or node ID is provided.
    if not section and not id:
      self.text.append('The top level of the configuration file contains the attribute \'' + attribute + '\' which is not valid. The allowed ' + \
      'attributes for this section are as follows:')

    # If a section, but no ID are provided.
    elif section and not id:
      self.text.append('The \'' + section + '\' section of the configuration file contains the attribute \'' + attribute + '\' which is not ' + \
      'valid. The allowed attributes for this section are:')

    # If both the section and ID are provided.
    else:
      self.text.append('The \'' + section + '\' section of the configuration file contains data with the ID \'' + id + '\'. Within this section, ' + \
      'the defined attribute \'' + attribute + '\' is invalid. The valid attributes for this section are:')

    # Create a sorted list of the allowed attributes.
    self.text.append('\t')
    allowed = []
    for attribute in allowedAttributes: allowed.append(attribute)

    # Add the attributes to the text to be written along with the expected type.
    for attribute in sorted(allowed):
      self.text.append(attribute + ':\t' + str(allowedAttributes[attribute][0]) + ', required = ' + str(allowedAttributes[attribute][1]))

    self.text.append('\t')
    self.text.append('Please remove or correct the invalid attribute in the configuration file.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

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

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '5'

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
      self.text.append('The \'' + section + '\' section of the configuration file contains a node with the attribute \'' + attribute + '\' which ' + \
      'is not valid. The allowed attributes for this section are:')

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

  # If a required attribute is missing.
  def missingAttribute(self, attribute, helpInfo):

    # Get the information from the helpInfo.
    name, section, id = helpInfo
    print(name, section, id)
    self.text.append('Missing attribute in the configuration file: ' + name)
    self.text.append('The configuration file section \'' + section + '\' requires a number of different attributes to be set. The section for ' + \
    'id \'' + id + '\' is missing the attribute \'' + attribute + '\'. Please ensure that all required attributes in the configuration file ' + \
    'are defined.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The data type is incorrect.
  def incorrectType(self, helpInfo, attribute, value, dataType):
    name, section, id = helpInfo

    # Get the data types as strings.
    dataType  = str(dataType).rsplit('\'')[1]
    valueType = str(type(value)).rsplit('\'')[1]

    # Write the error.
    self.text.append('Incorrect data type for configuration file attribute.')

    # Define the error message if no section or node ID is provided.
    if not section and not id:
      self.text.append('The top level of the configuration file (' + name + '.json) contains the attribute \'' + attribute + '\'. The data type ' + \
      'of this attribute is expected to be \'' + dataType + '\', but the value provided has the type \'' + valueType + '\'. Please check the ' + \
      'configuration file and ensure that all attributes are correctly defined.')

    # TODO FINISH
    else: print('generalConfigurationFileErrors - incorrectType- NOT HANDLED')

    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A node is missing an ID.
  def missingID(self, name, section, isTool):
    configurationType = 'tool' if isTool else 'pipeline'
    self.text.append('A ' + configurationType + ' configuration file node is missing an ID.')
    self.text.append('The configuration file for ' + configurationType + ' \'' + name + '\' contains a node in the \'' + section + '\' section ' + \
    'that is missing the \'id\' attribute. All nodes in this section must be identified with a unique ID. Please check the configuration file ' + \
    'and ensure that every node in the section has the \'id\' attribute defined.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode) 

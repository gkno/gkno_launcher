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

  ##################################
  ## Errors with top level fields ##
  ##################################

  # If the configuration file type (tool or pipeline) has not been defined.
  def noConfigurationType(self, name):
    self.text.append('Error processing tool configuration file: ' + name + '.json.')
    self.text.append('All gkno configuration files are required to contain the \'configuration type\' field. This can take the value \'tool\' ' + \
    'or \'pipeline\' and is used to ensure that it is possible to distinguish between tool and pipeline configuration files.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the configuration file type is not set to pipeline.
  def invalidConfigurationType(self, name, configurationType):
    self.text.append('Error processing configuration file: ' + name + '.json.')
    self.text.append('All gkno configuration files are required to contain the \'configuration type\' field. The configuration file \'' + name + \
    '.json\' is being processed as a tool, however, the type is listed as \'' + configurationType + '\'. Please ensure that \'' + name + \
    '\' is a tool and not a pipeline, and that the configuration file type is correctly defined within the configuration file (i.e. the ' + \
    'configuration type is set to \'tool\').')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  #######################
  ## Errors with stubs ##
  #######################

  # If a tool argument is listed as a stub, it must be accompanied by a list of extensions.
  def noExtensionsForStub(self, name, argument):
    self.text.append('Missing data for argument.')
    self.text.append('The configuration file for tool \'' + name + '\' contains information for the argument \'' + argument + '\'. This ' + \
    'is listed as being a stub, but no extensions are provided. For file stubs, the extensions of all the files that will be created/are ' + \
    'required must be listed.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ###########################
  ## Errors with arguments ##
  ###########################

  # If the value supplied to a tool attribute is invalid.
  def invalidValues(self, name, argument, attribute, value, validValues):

    # Update the attributes to reflect the values in the configuration files.
    if attribute == 'modifyArgument': attribute = 'modify argument'

    self.text.append('Invalid value given to attribute.')
    self.text.append('The configuration file for tool \'' + name + '\' contains information for the argument \'' + argument + '\'. The attribute ' + \
    '\'' + attribute + '\' for this argument is given the value \'' + value + '\', but this is not a valid value for this attribute. The valid ' + \
    'values are:')
    self.text.append('\t')
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

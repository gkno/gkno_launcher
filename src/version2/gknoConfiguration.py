#!/bin/bash/python

from __future__ import print_function
import fileHandling
import generalConfigurationFileMethods as methods

import json
import os
import sys

# Define a data structure to hold information on each of the gkno arguments.
class gknoArgumentAttributes:
  def __init__(self):

    # A description of the argument.
    self.description = None

    # The data type expected by this argument.
    self.dataType = None

    # The long and short forms of the argument.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # The values associated with the argument.
    self.values = []

# Define a class to process and store information from the gkno configuration file.
class gknoConfiguration:
  def __init__(self, path):

    # Store all of the gkno specific arguments.
    self.arguments = {}

    # Link the short forms to the long forms.
    self.shortForms = {}

    # Open the gkno configuration file.
    data = fileHandling.fileHandling.readConfigurationFile(path + '/tools/gknoConfiguration.json', True)

    # As part of the initialisation, validate the contents of the gkno configuration file.
    self.validate(data['gkno options'])

  #TODO INCLUDE VALIDATION
  # Validate the gkno configuration file.
  def validate(self, data):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['data type']           = (str, True, True, 'dataType')
    allowedAttributes['description']         = (str, False, True, 'description')
    allowedAttributes['long form argument']  = (str, True, True, 'longFormArgument')
    allowedAttributes['short form argument'] = (str, True, True, 'shortFormArgument')
    allowedAttributes['values']              = (list, True, True, 'values')

    # Loop over all of the defined gkno arguments.
    for argument in data:

      # Define a set of information to be used in help messages.
      helpInfo = ('gknoConfiguration', 'gkno options', argument)

      # Check all the supplied attributes.
      attributes = gknoArgumentAttributes()
      success, attributes = methods.checkAttributes(data[argument], allowedAttributes, attributes, True, helpInfo)

      # Check that the argument name is unique.
      #TODO ERROR
      if attributes.longFormArgument in self.arguments: print('gknoConfiguration.validate - 1', attributes.longFormArgument); exit(0)
      if attributes.shortFormArgument in self.shortForms: print('gknoConfiguration.validate - 2', attributes.shortFormArgument); exit(0)

      # Store the attributes for the argument.
      self.arguments[attributes.longFormArgument]   = attributes
      self.shortForms[attributes.shortFormArgument] = attributes.longFormArgument

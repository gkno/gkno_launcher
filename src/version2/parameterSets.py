#!/bin/bash/python

from __future__ import print_function
import generalConfigurationFileMethods as methods

import json
import os
import sys

# Define a structure to hold information on parameter sets.
class parameterSetData:
  def __init__(self):

    # Each parameter set has an id and description.
    self.description = None
    self.id          = None

    # Store all of the arguments and values.
    self.data = []

class parameterSetArguments:
  def __init__(self):

    # The paramter set data should consist of an id, an argument and a list of values.
    self.argument = None
    self.id       = None
    self.values   = []

# Define a class to handle parameter sets.
class parameterSets:
  def __init__(self):

    # Store information on parameter sets.
    self.sets = {}

  # Check the parameter set information
  def checkParameterSets(self, data, allowTermination, name):
    success = True

    # Define the allowed attributes.
    allowedAttributes                = {}
    allowedAttributes['id']          = (str, True, True, 'id')
    allowedAttributes['description'] = (str, True, True, 'description')
    allowedAttributes['data']        = (list, True, False, None)

    # Define the allowed attributes in the data section of the parameter set.
    allowedDataAttributes             = {}
    allowedDataAttributes['argument'] = (str, True, True, 'argument')
    allowedDataAttributes['id']       = (str, True, True, 'id')
    allowedDataAttributes['values']   = (list, True, True, 'values')

    # Loop over all of the defined parameter sets.
    for parameterSet in data:

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(parameterSet, allowTermination): return

      # Check that the node has a valid ID. This is required for help messages.
      id = methods.checkForId(parameterSet, allowTermination)
      if not id: return

      # Define a set of information to be used in help messages.
      helpInfo = (name, 'parameter sets', id)

      # Define a structure to hold the data.
      attributes = parameterSetData()

      # Check the attributes.
      success, attributes = methods.checkAttributes(parameterSet, allowedAttributes, attributes, allowTermination, helpInfo)

      # Loop over all of the data supplied with the parameter set and check the validity.
      for dataSet in parameterSet['data']:

        # Check that the supplied structure is a dictionary.
        if not methods.checkIsDictionary(dataSet, allowTermination): return

        # Define a structure to hold the information for each argument.
        dataAttributes = parameterSetArguments()

        # Check the attributes.
        success, dataAttributes = methods.checkAttributes(dataSet, allowedDataAttributes, dataAttributes, allowTermination, helpInfo)

        # Append this argument to the main parameter set attributes.
        attributes.data.append(dataAttributes)

      # Store the parameter set data.
      #TODO RROR
      if attributes.id in self.sets: print('parameterSets.checkParameterSets - REPEAT', attributes.id); exit(0)
      self.sets[attributes.id] = attributes

    return success

  # Get a parameter set from a configuration file.
  @staticmethod
  def getArguments(parameterSet):
    arguments = {}

    # Loop over all of the defined arguments for this parameter set.
    for dataSet in parameterSet.data:
      argument            = dataSet.argument
      values              = dataSet.values
      arguments[argument] = values

    return arguments

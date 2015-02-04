#!/bin/bash/python

from __future__ import print_function

import fileHandling as fh
import generalConfigurationFileMethods as methods
import parameterSetErrors as er

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

    # The paramter set data should consist of an id and a list of values.
    self.id       = None
    self.values   = []

    # Tool data sets also require an argument.
    self.argument = None

    # Pipeline data sets also require a pipeline node ID.
    self.nodeID = None

# Define a class to handle parameter sets.
class parameterSets:
  def __init__(self):

    # Define the error class.
    self.errors = er.parameterSetErrors()

    # Store information on parameter sets.
    self.sets = {}

  # Check the parameter set information
  def checkParameterSets(self, data, allowTermination, name, isTool):
    success = True

    # Define the allowed attributes.
    allowedAttributes                = {}
    allowedAttributes['id']          = (str, True, True, 'id')
    allowedAttributes['description'] = (str, True, True, 'description')
    allowedAttributes['data']        = (list, True, False, None)

    # Define the allowed attributes in the data section of the parameter set.
    allowedDataAttributes           = {}
    allowedDataAttributes['id']     = (str, True, True, 'id')
    allowedDataAttributes['values'] = (list, True, True, 'values')

    # The parameter set definitions differ slightly between tools and pipelines. For tools, the argument is
    # provided as the means of identifying the node for which the supplied values apply. For pipelines, it is
    # the node within the pipeline that is supplied.
    if isTool: allowedDataAttributes['argument'] = (str, True, True, 'argument')
    else: allowedDataAttributes['node']          = (str, True, True, 'nodeID')

    # Loop over all of the defined parameter sets.
    for parameterSet in data:

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(parameterSet, allowTermination): return

      # Check that the node has a valid ID. This is required for help messages.
      id = methods.checkForId(parameterSet, name, 'parameter sets', allowTermination, isTool)
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

  # Return a parameter sets description.
  def getDescription(self, name):
    try: return self.sets[name].description
    except: return None

  # Export a parameter set.
  def export(self, pipeline, setName, arguments):

    # Define the name of the configuration file that holds the parameter set information.
    filename = str(pipeline + '_parameter-sets.json')
    print('set:', pipeline, filename, setName)

    # Check that the paramter set name is not already defined for the pipeline.
    #TODO

    # Open the configuration file for writing.
    filehandle = fh.fileHandling.openFileForWriting(filename)
    for argument in arguments:
      print(argument, arguments[argument])
    exit(0)

  ######################
  ### Static methods ###
  ######################

  # Get parameter set argument from a tool configuration file.
  @staticmethod
  def SM_getArguments(parameterSet):
    arguments = {}

    # Loop over all of the defined arguments for this parameter set.
    for dataSet in parameterSet.data:
      argument            = dataSet.argument
      values              = dataSet.values
      arguments[argument] = values

    return arguments

  # Get a parameter set from a pipeline configuration file.
  @staticmethod
  def SM_getNodeIDs(parameterSet):
    nodeIDs = {}

    # Loop over all of the defined node IDs for this parameter set.
    for dataSet in parameterSet.data:
      nodeID          = dataSet.nodeID
      values          = dataSet.values
      nodeIDs[nodeID] = values

    return nodeIDs

  # Get an attribute included in the data section of a parameter set.
  @staticmethod
  def SM_getDataAttributeFromNodeID(parameterSet, dataID, attribute):

    # Loop over the data and find the correct ID.
    for dataSet in parameterSet.data:
      if dataSet.nodeID == dataID: return getattr(dataSet, attribute)

    # If the ID wasn't found, return False.
    return False

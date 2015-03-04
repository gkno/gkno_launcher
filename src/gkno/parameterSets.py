#!/bin/bash/python

from __future__ import print_function
from collections import OrderedDict

import fileHandling as fh
import generalConfigurationFileMethods as methods
import parameterSetErrors as er

import json
import os
import shutil
import sys

# Define a structure to hold information on parameter sets.
class parameterSetData:
  def __init__(self):

    # Each parameter set has an id and description.
    self.description = None
    self.id          = None

    # Store all of the arguments and values.
    self.data = []

    # Record if the parameter set is held in the external parameter sets file.
    self.isExternal = False

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
      if not methods.checkIsDictionary(parameterSet, allowTermination): return False

      # Check that the node has a valid ID. This is required for help messages.
      id = methods.checkForId(parameterSet, name, 'parameter sets', allowTermination, isTool)
      if not id: return False

      # Define a set of information to be used in help messages.
      helpInfo = (name, 'parameter sets', id)

      # Define a structure to hold the data.
      attributes = parameterSetData()

      # Check the attributes.
      success, attributes = methods.checkAttributes(parameterSet, allowedAttributes, attributes, allowTermination, helpInfo)

      # Loop over all of the data supplied with the parameter set and check the validity.
      for dataSet in parameterSet['data']:

        # Check that the supplied structure is a dictionary.
        if not methods.checkIsDictionary(dataSet, allowTermination): return False

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
  def export(self, superpipeline, args, setName, arguments):
    pipeline = superpipeline.pipeline

    # Get the configuration file information for the pipeline and the available parameter sets.
    pipelineConfigurationData = superpipeline.pipelineConfigurationData[pipeline]
    sets                      = pipelineConfigurationData.parameterSets.sets

    # Check that the paramter set name is not already defined for the pipeline.
    if setName in sets: self.errors.exportToDefinedSet(pipeline, setName)

    # Define the name of the configuration file that holds the parameter set information.
    filename = str(pipeline + '-parameter-sets.json')

    # Open the configuration file for writing.
    filehandle = fh.fileHandling.openFileForWriting(filename)

    # Add the new parameter set information to the parameterSetAttributes.
    attributes             = parameterSetData()
    attributes.description = 'User specified parameter set.'
    attributes.id          = setName
    attributes.isExternal  = True
    sets[setName]          = attributes

    # Add the arguments and values to the nodes.
    for counter, argument in enumerate(arguments):
      values = arguments[argument]

      # Put all of the values in a list.
      nodeAttributes           = parameterSetArguments()
      nodeAttributes.nodeID    = str(args.arguments[argument].nodeID)
      nodeAttributes.id        = str('node' + str(counter))
      nodeAttributes.values    = values
      attributes.data.append(nodeAttributes)

    # Put all of the parameter set information in a dictionary that can be dumped to a json file.
    jsonParameterSets                  = OrderedDict()
    jsonParameterSets['parameter sets'] = []
    for parameterSet in sets:

      # Only include parameterSets that were marked as external.
      if sets[parameterSet].isExternal:
        parameterSetInformation                = OrderedDict()
        parameterSetInformation['id']          = parameterSet
        parameterSetInformation['description'] = sets[parameterSet].description
        parameterSetInformation['data']        = []

        # Set the nodes.
        for data in sets[parameterSet].data:
          nodeInformation             = OrderedDict()
          nodeInformation['id']       = data.id
          nodeInformation['node']     = data.nodeID
          nodeInformation['values']   = data.values
          parameterSetInformation['data'].append(nodeInformation)

        # Store this parameterSets data.
        jsonParameterSets['parameter sets'].append(parameterSetInformation)

    # Dump all the parameterSets to file.
    json.dump(jsonParameterSets, filehandle, indent = 2)
    filehandle.close()

    # Move the configuration file.
    shutil.copy(filename, pipelineConfigurationData.path)
    os.remove(filename)

    print(file = sys.stdout)
    print('=' * 66, file = sys.stdout)
    print('Configuration file generation complete.', file = sys.stdout)
    print('', file = sys.stdout)
    print('It is recommended that the new configuration is visually inspected', file = sys.stdout)
    print('and tested to ensure expected behaviour.', file = sys.stdout)
    print('=' * 66, file = sys.stdout)
    sys.stdout.flush()
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
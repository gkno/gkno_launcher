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
    self.nodeId = None

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
    else: allowedDataAttributes['node']          = (str, True, True, 'nodeId')

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

  # Remove a parameter set.
  def removeParameterSet(self, graph, superpipeline, setName):
    pipeline = graph.pipeline

    # Get the configuration file information for the pipeline and the available parameter sets.
    pipelineConfigurationData = superpipeline.pipelineConfigurationData[pipeline]
    sets                      = pipelineConfigurationData.parameterSets.sets

    # Only user-generated parameter sets can be removed, so trim the list.
    externalSets = []
    for pSet in sets.keys():
      if sets[pSet].isExternal: externalSets.append(pSet)

    # If the parameter set doesn't exist, it cannot be removed.
    if setName not in sets: self.errors.removeNonSet(setName, externalSets)
    else:

      # If the defined pipeline is not a user-generated parameter set, it cannot be removed.
      if setName not in externalSets: self.errors.removeNonExternalSet(setName, externalSets)

      # Remove the parameter set.
      else:

        # Define the name of the configuration file that holds the parameter set information.
        filename = str(pipeline + '-parameter-sets.json')

        # Open the configuration file for writing.
        filehandle = fh.fileHandling.openFileForWriting(filename)

        # Put all of the parameter set information in a dictionary that can be dumped to a json file.
        jsonParameterSets                  = OrderedDict()
        jsonParameterSets['parameter sets'] = []

        # Keep count of the number of parameter set remaining.
        remainingSets = 0

        # Loop over the external parameter sets.
        for parameterSet in externalSets:

          # Do not include the parameter set to be removed.
          if parameterSet != setName:
            parameterSetInformation                = OrderedDict()
            parameterSetInformation['id']          = parameterSet
            parameterSetInformation['description'] = sets[parameterSet].description
            parameterSetInformation['data']        = []
            remainingSets += 1
    
            # Set the nodes.
            for data in sets[parameterSet].data:
              nodeInformation             = OrderedDict()
              nodeInformation['id']       = data.id
              nodeInformation['node']     = data.nodeId
              nodeInformation['values']   = data.values
              parameterSetInformation['data'].append(nodeInformation)
    
            # Store this parameterSets data.
            jsonParameterSets['parameter sets'].append(parameterSetInformation)
    
        # If there are no parameter sets remaining, delete the parameter sets file.
        if remainingSets == 0:
          filehandle.close()
          os.remove(filename)
          os.remove(pipelineConfigurationData.path + '/' + filename)

        # Dump all the parameterSets to file.
        else:
          json.dump(jsonParameterSets, filehandle, indent = 2)
          filehandle.close()
    
          # Move the configuration file.
          shutil.copyfile(filename, str(pipelineConfigurationData.path + '/' + filename))
          os.remove(filename)

    # Terminate gkno once the parameter set has been removed.
    length = len(setName) + 38
    print('=' * length, file = sys.stdout)
    print('Parameter set \'' + setName + '\' successfully removed', file = sys.stdout)
    print('=' * length, file = sys.stdout)
    sys.stdout.flush()
    exit(0)

  # Return a parameter sets description.
  def getDescription(self, name):
    try: return self.sets[name].description
    except: return None

  # Export a parameter set.
  def export(self, graph, superpipeline, args, arguments):
    pipeline = superpipeline.pipeline

    # Get the parameter set name.
    setName = graph.exportParameterSet

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

    # First, loop over all file nodes and find those with values.
    self.counter      = 1
    observedArguments = []
    for nodeId in graph.getNodes('file'):
      values         = graph.getGraphNodeAttribute(nodeId, 'values')
      if len(values) > 0:

        # Check if this is a stub. If so, check if the stub has already been handled. If not, create
        # the attributes for the parameter set and mark the argument as handled. If so, ignore.
        stubExtension = graph.getGraphNodeAttribute(nodeId, 'stubExtension')
        if stubExtension:
          longFormArgument = graph.getGraphNodeAttribute(nodeId, 'longFormArgument')
          if longFormArgument not in observedArguments:
            observedArguments.append(longFormArgument)
            updatedNodeId = nodeId.rstrip('.' + stubExtension)
            updatedValues = [value.rstrip('.' + stubExtension) for value in values]
            attributes.data.append(self.getNodeAttributes(updatedNodeId, updatedValues))

        # If this is not a stub, handle the attribute.
        else: attributes.data.append(self.getNodeAttributes(nodeId, values))

    # Then loop over all options nodes.
    for nodeId in graph.getNodes('option'):
      values = graph.getGraphNodeAttribute(nodeId, 'values')
      if len(values) > 0: attributes.data.append(self.getNodeAttributes(nodeId, values))

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
          nodeInformation['node']     = data.nodeId
          nodeInformation['values']   = data.values
          parameterSetInformation['data'].append(nodeInformation)

        # Store this parameterSets data.
        jsonParameterSets['parameter sets'].append(parameterSetInformation)

    # Dump all the parameterSets to file.
    json.dump(jsonParameterSets, filehandle, indent = 2)
    filehandle.close()

    # Move the configuration file.
    os.chmod(filename, 0666)
    shutil.copyfile(filename, str(pipelineConfigurationData.path + '/' + filename))
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

  # Given a graph node with values, return node attributes to be added to the parameter set.
  def getNodeAttributes(self, nodeId, values):

    # Put all of the values in a list.
    nodeAttributes           = parameterSetArguments()
    nodeAttributes.nodeId    = str(nodeId)
    nodeAttributes.id        = str('node' + str(self.counter))
    nodeAttributes.values    = values
    self.counter += 1

    return nodeAttributes

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
  def SM_getNodeIds(parameterSet):
    nodeIds = {}

    # Loop over all of the defined node IDs for this parameter set.
    for dataSet in parameterSet.data:
      nodeId          = dataSet.nodeId
      values          = dataSet.values
      nodeIds[nodeId] = values

    return nodeIds

  # Get an attribute included in the data section of a parameter set.
  @staticmethod
  def SM_getDataAttributeFromNodeId(parameterSet, dataID, attribute):

    # Loop over the data and find the correct ID.
    for dataSet in parameterSet.data:
      if dataSet.nodeId == dataID: return getattr(dataSet, attribute)

    # If the ID wasn't found, return False.
    return False

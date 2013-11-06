#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataChecking
from dataChecking import checkDataType

import gknoErrors
from gknoErrors import *

import helpClass
from helpClass import *

import json
import os
import sys

class gknoConfigurationFiles:
  def __init__(self):
    self.jsonFiles                       = {}
    self.jsonFiles['tools']              = {}
    self.jsonFiles['tool instances']     = {}
    self.jsonFiles['pipelines']          = {}
    self.jsonFiles['pipeline instances'] = {}

    # Errors class.
    self.errors = gknoErrors()

    # Define a dictionary to hold information contained in the gkno configuration file.
    self.gknoConfigurationData = {}

    #TODO FILL IN TEXT
    self.delimiter = '_'

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_instances.json' seperately.  These files contain additional instance information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_instances.json'): self.jsonFiles['tool instances'][files] = False
      elif files.endswith('.json'): self.jsonFiles['tools'][files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_instances.json'): self.jsonFiles['pipeline instances'][files] = False
      elif files.endswith('.json'): self.jsonFiles['pipelines'][files] = True

  #TODO SORT THIS OUT
  # Validate the gkno configuration file.
  def validateConfigurationFile(self):
    pass

  # Add the nodes from the gkno configuration file to the graph.  These nodes will not be conected to any
  # other nodes.
  def addGknoSpecificNodes(self, graph, config):

    # Add a task node representing gkno.
    attributes = taskNodeAttributes()
    attributes.description = 'gkno task'
    attributes.tool        = 'gkno'
    attributes.nodeType    = 'gkno'
    graph.add_node('gkno', attributes = attributes)

    for nodeID in self.gknoConfigurationData['gkno options']:

      # Generate a node.
      graph.add_node(nodeID, attributes = optionNodeAttributes())
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'nodeType', 'general')
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'dataType', self.gknoConfigurationData['gkno options'][nodeID]['data type'])
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'description', self.gknoConfigurationData['gkno options'][nodeID]['description'])
      if 'value' in self.gknoConfigurationData['gkno options'][nodeID]:

        # Convert unicode values from the configuration file into strings.
        for counter, value in enumerate(self.gknoConfigurationData['gkno options'][nodeID]['value']):
          if type(value) != bool: self.gknoConfigurationData['gkno options'][nodeID]['value'][counter] = str(value)

        config.nodeMethods.addValuesToGraphNode(graph, nodeID, self.gknoConfigurationData['gkno options'][nodeID]['value'], write = 'replace')
        config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'hasValue', True)
    
      # Join the option node to the gkno task node.
      attributes = edgeAttributes()
      attributes.argument  = self.gknoConfigurationData['gkno options'][nodeID]['argument']
      attributes.shortForm = self.gknoConfigurationData['gkno options'][nodeID]['short form']
      graph.add_edge(nodeID, 'gkno', attributes = attributes)

  # Clear the data structure holding the gkno specific data.
  def eraseConfigurationData(self):
    self.gknoConfigurationData = {}

  # Return the node for a gkno argument contained in the gkno configuration file.
  def getNodeForGknoArgument(self, graph, config, argument):
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].argument: return nodeID

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].shortForm: return nodeID

    return None

  # If a filename is not defined, check to see if there are instructions on how to 
  # construct the filename.
  def constructionInstructions(self, graph, config, task, argument, fileNodeID):
    instructions = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    if instructions == None: return None
    else: return instructions['id']

  # Construct a filename from instructions.
  def constructFilename(self, graph, config, method, task, fileNodeID):
    if method == 'from tool argument':
      self.constructFilenameFromToolArgument(graph, config, task, fileNodeID)

    # TODO ERRORS
    else:
      print('UNKNOWN CONSTRUCTION METHOD: gknoConfig.constructFilename')
      self.errors.terminate()

  # Construct a filename using another tool argument.
  def constructFilenameFromToolArgument(self, graph, config, task, fileNodeID):
    optionNodeID   = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)

    # Check if the filename is a filename stub.
    isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isFilenameStub')
    if isFilenameStub: self.constructFilenameFromToolArgumentStub(graph, config, task, fileNodeID)
    else: self.constructFilenameFromToolArgumentNotStub(graph, config, task, fileNodeID)

  # Construct the filenames for filename stub arguments.
  def constructFilenameFromToolArgumentStub(self, graph, config, task, fileNodeID):
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'argument')
    instructions     = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    baseArgument     = instructions['use argument']
    replaceExtension = instructions['replace extension']

    # Get the ID of the node corresponding to the baseArgument.
    # TODO SORT OUT THE CASE WHERE THERE ARE MULTIPLE VALUES
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument)
    if len(baseNodeIDs) != 1:
      print('Not yet handled constructFilenameFromToolArgumentStub')
      self.errors.terminate()
    else: baseNodeID = baseNodeIDs[0]
    values     = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')

    # Generate the filename for the option node.  Since this is a filename stub, this will not have any
    # extension.
    originalExtension = config.tools.getArgumentData(config.pipeline.tasks[task], baseArgument, 'extension')
    modifiedValues    = self.modifyExtensions(values, originalExtension, '')
    if 'add argument values' in instructions:
      numberOfValues  = len(modifiedValues)

      # The modifiedValues structure is a dictionary.  This contains values for each iteration of the
      # pipeline to be executed.  It must be the case that the modifiedValues dictionary has the same
      # number of iterations as the values structure associated with the node for the argument from
      # which the filenames are to be constructed, or one of the structured must have only one iteration.
      additionalArguments = []
      for taskArgument in instructions['add argument values']:

        # Find the option node that provides information for this argument.
        # TODO HANDLE THE CASE OF MULTIPLE VALUES
        argumentNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, taskArgument)
        if len(argumentNodeIDs) != 1:
          print('not yet handled - constructFilenameFromToolArgumentStub mark2')
          self.errors.terminate()
        else: argumentNodeID = argumentNodeIDs[0]


        argumentNodeValues = config.nodeMethods.getGraphNodeAttribute(graph, argumentNodeID, 'values')
        numberOfNodeValues = len(argumentNodeValues)

        # If both data structures have the same number of values.
        if numberOfValues == numberOfNodeValues:
          for iteration in modifiedValues:

            # Check that there is only a single value in the list for this iteration in 'argumentNodeValues'.
            if len(argumentNodeValues[iteration]) != 1:
              print('CANNOT CONSTRUCT FILENAMES IF THERE IS MORE THAN ONE PARAMETER VALUE.')
              print('constructFilenameFromToolArgumentStub')
              self.errors.terminate()

            else:
              modifiedList = []
              for value in modifiedValues[iteration]: modifiedList.append(value + self.delimiter + argumentNodeValues[iteration][0])
              modifiedValues[iteration] = modifiedList

        else:
          print('NOT YET HANDLED - constructFilenameFromToolArgumentStub')
          self.errors.terminate()

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)

    # Set all of the file nodes with their values.
    fileNodeIDs = config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID)
    extensions  = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'filename extensions')

    # If the number of file nodes is not equal to the number of extensions, there is a problem.
    if len(fileNodeIDs) != len(extensions):
      #TODO SORT ERROR
      print('Number of file nodes != number of extensions - gknoConfigurationFiles.constructFilenameFromToolArgumentStub')
      self.errors.terminate()

    for nodeID in fileNodeIDs:
      fileValues = {}
      extension  = extensions.pop(0)
      for iteration in modifiedValues:
        fileValues[iteration] = []
        for value in modifiedValues[iteration]: fileValues[iteration].append(value + extension)
      config.nodeMethods.replaceGraphNodeValues(graph, nodeID, fileValues)

  # Construct the filenames for non-filename stub arguments.
  def constructFilenameFromToolArgumentNotStub(self, graph, config, task, fileNodeID):
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'argument')
    instructions     = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    baseArgument     = instructions['use argument']
    replaceExtension = instructions['replace extension']

    # Get the ID of the node corresponding to the baseArgument. If there are multiple nodes
    # available, pick one that has a predecessor node itself. TODO SORT THIS OUT
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument)
    if len(baseNodeIDs) == 1: baseNodeID = baseNodeIDs[0]
    elif len(baseNodeIDs) == 0:
      #TODO Sort error
      print('No basenode - constructFilenameFromToolArgumentNotStub')
      self.errors.terminate()
    else: baseNodeID = config.nodeMethods.getNodeIDWithPredecessor(graph, baseNodeIDs, task)

    # Find all predecessor file nodes and then identify the file associated with the baseNodeID.
    # Get the values from this file node.  Some of the values associated with option nodes are
    # for filename stubs, but those attached to file nodes will always be a full file name as
    # required here.
    predecessorFileNodeIDs = config.nodeMethods.getPredecessorFileNodes(graph, task)
    fileNodeExists         = False
    for nodeID in predecessorFileNodeIDs:
      if nodeID.startswith(baseNodeID + '_'):
        values         = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        fileNodeExists = True
        break

    # If no file node was found, terminate.
    if not fileNodeExists:
      #TODO ERROR
      print('constructFilenameFromToolArgumentNotStub')
      self.errors.terminate()

    # If the extension is to be replaced, do that here.
    if replaceExtension:
      originalExtension = config.tools.getArgumentData(config.pipeline.tasks[task], baseArgument, 'extension')
      newExtension      = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'extension')
      modifiedValues    = self.modifyExtensions(values, originalExtension, newExtension)

    else: modifiedValues = values

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

  # Modify the extensions for files.
  def modifyExtensions(self, values, extA, extB):
    modifiedValues = {}

    # The extensions may be a list of allowed extension separated by '|'.  Break the extensions
    # into lists of allowed extensions.
    extAList = extA.split('|')

    # The replacement extension may also be a list of allowed values.  Choose the first value in
    # this list as the extension to use.
    if extB == '': replaceExtension = ''
    else: replaceExtension = '.' + str(extB.split('|')[0])

    # Loop over all values and change the extension.
    for valueID in values:
      newValuesList = []
      for value in values[valueID]:
        for extension in extAList:
          if value.endswith(extension):
            string  = '.' + str(extension)
            newValuesList.append(value.replace(string, replaceExtension))
            break

      # Update the modifiedValues dictionary to reflect the modified extensions.
      modifiedValues[valueID] = newValuesList

    return modifiedValues

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

    # Define a dictionary to hold information contained in the gkno configuration file.
    self.gknoConfigurationData = {}

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

        config.nodeMethods.addValuestoGraphNodeAttribute(graph, nodeID, self.gknoConfigurationData['gkno options'][nodeID]['value'], overwrite = True)
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
    optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    instructions = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    if instructions == None: return None
    else: return instructions['id']

  # Construct a filename from instructions.
  def constructFilename(self, graph, config, method, task, fileNodeID):
    if method == 'from tool argument':
      self.constructFilenameFromToolArgument(graph, config, task, fileNodeID)

    # TODO ERRORS
    else:
      print('UNKNOWN CINSTRUCTION METHOD: gknoConfig.constructFilename')
      self.errors.terminate()

  # Construct a filename using another tool argument.
  def constructFilenameFromToolArgument(self, graph, config, task, fileNodeID):
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'argument')
    instructions     = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    baseArgument     = instructions['use argument']
    replaceExtension = instructions['replace extension']

    # Get the ID of the node corresponding to the baseArgument.
    baseNodeID = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument)
    values     = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')

    # If the extension is to be replaced, do that here.
    if replaceExtension:
      originalExtension = config.tools.getArgumentData(config.pipeline.tasks[task], baseArgument, 'extension')
      newExtension      = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'extension')
      modifiedValues    = self.modifyExtensions(values, originalExtension, newExtension)

    else: modifiedValues = values

    # Reset the node values for the option and the file node.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'values', modifiedValues)
    config.nodeMethods.setGraphNodeAttribute(graph, fileNodeID, 'values', modifiedValues)

  # Modify the extensions for files.
  def modifyExtensions(self, values, extA, extB):
    modifiedValues = {}

    # The extensions may be a list of allowed extension separated by '|'.  Break the extensions
    # into lists of allowed extensions.
    extAList = extA.split('|')

    # The replacement extension may also be a list of allowed values.  Choose the first value in
    # this list as the extension to use.
    replaceExtension = '.' + str(extB.split('|')[0])

    # Loop over all values and change the extension.
    for valueID in values:
      newValuesList = []
      for value in values[valueID]:
        for extension in extAList:
          if value.endswith(extension):
            string   = '.' + str(extension)
            newValuesList.append(value.replace(string, replaceExtension))
            break

      # Update the modifiedValues dictionary to reflect the modified extensions.
      modifiedValues[valueID] = newValuesList

    return modifiedValues

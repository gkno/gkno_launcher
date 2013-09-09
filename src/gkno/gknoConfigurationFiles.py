#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataChecking
from dataChecking import checkDataType

import errors
from errors import *

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
    for nodeID in self.gknoConfigurationData['gkno options']:

      # Determine the node type and generate a node.
      argument = self.gknoConfigurationData['gkno options'][nodeID]['argument']
      nodeType = self.gknoConfigurationData['gkno options'][nodeID]['node type']
      if nodeType == 'file':
        graph.add_node(nodeID, attributes = fileNodeAttributes())
      elif nodeType == 'option':
        graph.add_node(nodeID, attributes = optionNodeAttributes())
        config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'dataType', self.gknoConfigurationData['gkno options'][nodeID]['data type'])

      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'argument', self.gknoConfigurationData['gkno options'][nodeID]['argument'])
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'description', self.gknoConfigurationData['gkno options'][nodeID]['description'])
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'shortForm', self.gknoConfigurationData['gkno options'][nodeID]['short form'])
      if 'value' in self.gknoConfigurationData['gkno options'][nodeID]:
        config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'values', ('1', self.gknoConfigurationData['gkno options'][nodeID]['value']))
        config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'hasValue', True)
    
  # Clear the data structure holding the gkno specific data.
  def eraseConfigurationData(self):
    self.gknoConfigurationData = {}

  # Return the node for a gkno argument contained in the gkno configuration file.
  def getNodeForGknoArgument(self, graph, config, argument):
    for node in graph.nodes(data = False):
      nodeType = config.nodeMethods.getGraphNodeAttribute(graph, node, 'nodeType')
      if nodeType != 'task':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == config.nodeMethods.getGraphNodeAttribute(graph, node, 'argument'): return node

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == config.nodeMethods.getGraphNodeAttribute(graph, node, 'shortForm'): return node

    return None

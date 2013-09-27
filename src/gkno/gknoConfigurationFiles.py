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
    graph.add_node('gkno', attributes = attributes)

    for nodeID in self.gknoConfigurationData['gkno options']:

      # Generate a node.
      graph.add_node(nodeID, attributes = optionNodeAttributes())
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
    for node in graph.nodes(data = False):
      nodeType = config.nodeMethods.getGraphNodeAttribute(graph, node, 'nodeType')
      if nodeType != 'task':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == config.nodeMethods.getGraphNodeAttribute(graph, node, 'argument'): return node

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == config.nodeMethods.getGraphNodeAttribute(graph, node, 'shortForm'): return node

    return None

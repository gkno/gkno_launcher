#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import json
import os
import sys

class nodeAttributes:
  def __init__(self):
    self.description = ''
    self.inputNodes  = {}
    self.nodeType    = ''
    self.outputNodes = []
    self.shortForm   = ''
    self.tool        = ''

class pipelineConfiguration:
  def __init__(self):
    self.configuration   = {}
    self.filename        = ''
    self.jsonError       = ''

  # Open a configuration file and store the contents of the file in the
  # configuration dictionary.
  def readConfiguration(self, filename):
    try: jsonData = open(filename)
    except: return False
    self.filename = filename

    try: self.configuration = json.load(jsonData)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.jsonError = exc_value
      return False

    return True

  #TODO
  # Check that the pipeline configuration file is valid.  If so, put all the information in
  # the pipeline data structures.
  def validateConfigurationData(self, filename):
    return True

  # Transfer all of the information from the configuration file into data structures.
  def addNodesAndEdges(self, graph):

    # Set the pipeline arguments.
    for argument in self.configuration['arguments']:

      # Each new node ID must be unique.  Throw an error if this node ID has been seen before.
      nodeID = self.configuration['arguments'][argument]['ID']
      if graph.has_node(nodeID):
        print('non-unique argument node: ', nodeID)
        exit(1)

      attributes             = nodeAttributes()
      attributes.nodeType    = 'data'
      attributes.description = self.configuration['arguments'][argument]['description']
      attributes.shortForm   = self.configuration['arguments'][argument]['short form']
      graph.add_node(nodeID, attributes = attributes)

    # Loop through all of the tasks and store all the information about the edges.
    for task in self.configuration['tasks']:

      # Each new node ID must be unique.  Throw an error if this node ID has been seen before.
      if graph.has_node(task):
        print('non-unique task node: ', task)
        exit(1)

      # Create the new node and attach the relevant information to it.
      attributes          = nodeAttributes()
      attributes.nodeType = 'task'
      attributes.tool     = self.configuration['tasks'][task]['tool']
      for inputNode in self.configuration['tasks'][task]['input nodes']: 
        attributes.inputNodes[inputNode] = self.configuration['tasks'][task]['input nodes'][inputNode]

        # If the input node is not already in the graph, add it.
        if not graph.has_node(inputNode):
          dataNodeAttributes                   = nodeAttributes()
          dataNodeAttributes.nodeType          = 'data'
          graph.add_node(inputNode, attributes = dataNodeAttributes)

        # Add an edge from the input node to the task.
        graph.add_edge(inputNode, task, argument = attributes.inputNodes[inputNode])

      # Now add output nodes and draw connections.
      for outputNode in self.configuration['tasks'][task]['output nodes']:
        attributes.outputNodes.append(outputNode)

        # If the input node is not already in the graph, add it.
        if not graph.has_node(outputNode):
          dataNodeAttibutes                     = nodeAttributes()
          dataNodeAttibutes.nodeType            = 'data'
          graph.add_node(outputNode, attributes = dataNodeAttibutes)

        # Add an edge from the input node to the task.
        graph.add_edge(task, outputNode, argument = 'dummy')

      graph.add_node(task, attributes = attributes)

    self.configuration = {}

  # Generate the task workflow from the topologically sorted pipeline graph.
  def generateWorkflow(self, graph):
    workflow  = []
    topolSort = nx.topological_sort(graph)
    for node in topolSort:
      if graph.node[node]['attributes'].nodeType == 'task': workflow.append(node)

    return workflow

  # Set all task node attributes.
  def getRequiredTools(self, graph):
    tools = []
    for node in graph.nodes(data = False):

      # Find the tool used by this task.
      if graph.node[node]['attributes'].nodeType == 'task': tools.append(graph.node[node]['attributes'].tool)

    return tools

  # Check that all of the supplied edges (tool arguments) are present in the graph.
  def checkRequiredTaskConnections(self, graph, task, requiredEdges):
    missingEdges = []

    for edge in requiredEdges:
      edgeIsDefined = False

      # Loop over the input and output nodes of this task and check that an edge corresponding to
      # the required edge exists.
      neigbours = nx.all_neighbors(graph, task)
      for node in neigbours:
        isInputNode = True if node in graph.node[task]['attributes'].inputNodes else False
        graphEdge   = graph[node][task]['argument'] if isInputNode else graph[task][node]['argument']
        if graphEdge == edge:
          edgeIsDefined = True
          break

      if not edgeIsDefined: missingEdges.append(edge)

    return missingEdges

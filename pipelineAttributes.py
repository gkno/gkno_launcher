#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import json
import os
import sys

class pipelineArgument:
  def __init__(self):
    self.description = ''
    self.ID          = ''
    self.shortForm   = ''

class taskInformation:
  def __init__(self):
    self.tool          = ''
    self.preTaskNodes  = []
    self.postTaskNodes = []

class pipelineAttributes:
  def __init__(self):
    self.arguments       = {}
    self.configuration   = {}
    self.jsonError       = ''
    self.taskInformation = {}

  # Open a configuration file and store the contents of the file in the
  # configuration dictionary.
  def readConfiguration(self, filename):
    try: jsonData = open(filename)
    except: return False

    try: self.configuration = json.load(jsonData)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.jsonError = exc_value
      return False

    return True

#TODO
# Check that the pipeline configuration file is valid.
  def validate(self, filename):
    return True

  # Transfer all of the information from the configuration file into data structures.
  def setPipelineDataStructures(self):

    # Set the pipeline arguments.
    for argument in self.configuration['arguments']:
      if argument not in self.arguments: self.arguments[argument] = pipelineArgument()
      self.arguments[argument].description = self.configuration['arguments'][argument]['description']
      self.arguments[argument].ID          = self.configuration['arguments'][argument]['ID']
      self.arguments[argument].shortForm   = self.configuration['arguments'][argument]['short form']

    # Loop through all of the tasks and store all the information about the edges.
    for task in self.configuration['tasks']:
      if task not in self.taskInformation: self.taskInformation[task] = taskInformation()
      self.taskInformation[task].tool = self.configuration['tasks'][task]['tool']
      for edge in self.configuration['tasks'][task]['edges']:
        nodeValue = self.configuration['tasks'][task]['edges'][edge]
        if nodeValue == 0: self.taskInformation[task].preTaskNodes.append(edge)
        else: self.taskInformation[task].postTaskNodes.append(edge)

    self.configuration = {}

  # Given a data from the pipeline configuration file, define all of the edges.
  def defineEdges(self, graph):

    # Loop over all of the tasks in the pipeline and define all of the edges,
    for task in self.taskInformation:

      # First, define all of the edges that have the task node as the target, then those that have
      # the task as the source (e.g. outputs).  For each new node, initialise the node attributes
      # with the nodes class and then set the nodes.nodeType to either 'task' or 'data'.
      for edge in self.taskInformation[task].preTaskNodes:
        if not graph.has_node(edge): graph.add_node(edge, nodeType = 'data')
        if not graph.has_node(task.upper()): graph.add_node(task.upper(), nodeType = 'task')
        graph.add_edge(edge, task.upper())
      for edge in self.taskInformation[task].postTaskNodes:
        if not graph.has_node(edge): graph.add_node(edge, nodeType = 'data')
        if not graph.has_node(task.upper()): graph.add_node(task.upper(), nodeType = 'task')
        graph.add_edge(task.upper(), edge)

  # Generate the task workflow from the topologically sorted pipeline graph.
  def generateWorkflow(self, graph):
    workflow  = []
    topolSort = nx.topological_sort(graph)
    for node in topolSort:
      if graph.node[node]['nodeType'] == 'task': workflow.append(node)

    return workflow

  # Set all task node attributes.
  def setTaskNodeAttributes(self, graph, workflow):
    tools = []
    for task in workflow:

      # Find the tool used by this task.
      graph.node[task]['tool'] = self.taskInformation[task.lower()].tool
      tools.append(self.taskInformation[task.lower()].tool)

    return tools

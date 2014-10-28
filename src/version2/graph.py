#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import taskNodes
from taskNodes import *

import json
import os
import sys

# Define a data structure for task nodes.
class taskNodeAttributes:
  def __init__(self):

    # Define the node type.
    self.nodeType = 'task'

    # Define the tool to be used to execute this task.
    self.tool = None

# Define a data structure for file nodes.
class fileNodeAttributes:
  def __init__(self):

    # Define the node type.
    self.nodeType = 'file'

# Define a data structure for option nodes.
class optionNodeAttributes:
  def __init__(self):

    # Define the node type.
    self.nodeType = 'option'

# Define a class to store and manipulate the pipeline graph.
class pipelineGraph:
  def __init__(self):

    # Define the graph.
    self.graph = nx.DiGraph()

    # Create a task nodes class.
    self.taskNodes = taskNodes()

    # Define a task node.
    self.taskNodes = taskNodes()

  # Using a pipeline configuration file, build and connect the defined nodes.
  def buildPipelineTasks(self, tools, pipeline):

    # Define the address for all nodes for this pipeline.
    address = str(pipeline.address) + '.' if pipeline.address != None else ''

    # Loop over all the pipeline tasks and build a node for each task. If the task is
    # a pipeline, ignore it.
    for task in pipeline.pipelineTasks:
      if not pipeline.pipelineTasks[task].isTaskAPipeline: self.addTaskNode(address + str(task), pipeline.pipelineTasks[task].tool)

    # Add unique nodes.
    self.addUniqueNodes(tools, pipeline.uniqueNodeAttributes, pipeline.pipelineTasks, address)

    # Add shared nodes.
    self.addSharedNodes(tools, pipeline.sharedNodeAttributes, pipeline.pipelineTasks, address)

  # Add unique graph nodes to the graph.
  # TODO ADD ATTRIBUTES TO NODE
  def addUniqueNodes(self, tools, attributes, tasks, address):
    for nodeID in attributes:
      nodeAddress = str(address + nodeID)

      # Get the task this node points to and determine if it is a tool or a pipeline.
      task            = attributes[nodeID].task
      tool            = tasks[task].tool
      isTaskAPipeline = tasks[task].isTaskAPipeline

      #TODO If task is a pipeline.
      if isTaskAPipeline: pass
      else:
        longFormArgument = attributes[nodeID].longFormArgument
        isInput          = tools[tool].argumentAttributes[longFormArgument].isInput
        isOutput         = tools[tool].argumentAttributes[longFormArgument].isOutput

        # TODO DEAL WITH ATTRIBUTES
        if isInput:
          self.addFileNode(nodeAddress)
          self.graph.add_edge(nodeAddress, address + task, attributes = {})
        elif isOutput:
          self.addFileNode(nodeAddress)
          self.graph.add_edge(address + task, nodeAddress)
        else:
          self.addOptionNode(nodeAddress)
          self.graph.add_edge(nodeAddress, address + task)

  # Add shared nodes to the graph.
  # TODO ADD ATTRIBUTES
  def addSharedNodes(self, tools, attributes, tasks, address):
    for sharedNodeID in attributes:
      print('TEST', sharedNodeID, address)
      for node in attributes[sharedNodeID].nodes:
        task         = node['task']
        taskArgument = node['task argument']

        # Check if the task is a nested pipeline.
        # TODO INCLUDE METHODS TO GET THESE VALUES
        isTaskAPipeline = False if task in tasks else True
        print('\tTEST', task, taskArgument, isTaskAPipeline)

        if isTaskAPipeline:
          pass

        # If the task is running a tool, build the node and add the required edges.
        else:

          # Check the taskArgument to identify if this node is a file or an option node.
          tool     = tasks[task].tool
          isInput  = tools[tool].argumentAttributes[taskArgument].isInput
          isOutput = tools[tool].argumentAttributes[taskArgument].isOutput
          isFile   = True if (isInput or isOutput) else False
          print('\tTEST', task, taskArgument, isTaskAPipeline, address + sharedNodeID, isInput, isOutput, isFile)

          # If the node is a file node.
          if isFile:
            if address + sharedNodeID not in self.graph: self.addFileNode(address + sharedNodeID)
            if isInput: self.graph.add_edge(address + sharedNodeID, address + task)
            elif isOutput: self.graph.add_edge(address + task, address + sharedNodeID)

          # If the node is an option node.
          else:
            if address + sharedNodeID not in self.graph: self.addOptionNode(address + sharedNodeID)
            self.graph.add_edge(address + sharedNodeID, address + task)

  # Add a task node to the graph.
  #TODO ADD TOOLS CLASS ATTRIBUTES TO TASK NODE.
  def addTaskNode(self, task, tool):
    attributes          = taskNodeAttributes()
    attributes.nodeType = 'task'
    attributes.tool     = tool
    self.graph.add_node(task, attributes = attributes)

  # Add a file node to the graph.
  #TODO ADD TOOLS CLASS ATTRIBUTES TO TASK NODE.
  def addFileNode(self, nodeID):
    attributes          = fileNodeAttributes()
    attributes.nodeType = 'file'
    self.graph.add_node(nodeID, attributes = attributes)

  # Add an option node to the graph.
  #TODO ADD TOOLS CLASS ATTRIBUTES TO TASK NODE.
  def addOptionNode(self, nodeID):
    attributes          = optionNodeAttributes()
    attributes.nodeType = 'option'
    self.graph.add_node(nodeID, attributes = attributes)

  # Generate a topologically sorted graph.
  def generateWorkflow(self):
    workflow = []
    for nodeID in nx.topological_sort(self.graph):
      nodeType = getattr(self.graph.node[nodeID]['attributes'], 'nodeType')
      if nodeType == 'task': workflow.append(nodeID)

    return workflow

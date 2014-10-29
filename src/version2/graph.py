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
      if not pipeline.getTaskAttribute(task, 'pipeline'): self.addTaskNode(address + str(task), pipeline.getTaskAttribute(task, 'tool'))

    # Add unique nodes.
    self.addUniqueNodes(tools, pipeline)

    # Add shared nodes.
    self.addSharedNodes(tools, pipeline)

  # Add unique graph nodes to the graph.
  # TODO ADD ATTRIBUTES TO NODE
  def addUniqueNodes(self, tools, pipeline):
    for nodeID in pipeline.uniqueNodeAttributes:

      # Get the task this node points to and determine if it is a tool or a pipeline.
      pipelineContainingTask = pipeline.getUniqueNodeAttribute(nodeID, 'pipeline')
      task                   = pipeline.getUniqueNodeAttribute(nodeID, 'task')
      taskArgument           = pipeline.getUniqueNodeAttribute(nodeID, 'taskArgument')
      tool                   = pipeline.getTaskAttribute(task, 'tool')

      # Define the pipeline relative address.
      address = str(pipeline.address + '.') if pipeline.address else str('')

      #TODO If task is a pipeline.
      if pipelineContainingTask: print('graph.addUniqueNodes - NOT HANDLED PIPELINE')
      else:
        isInput  = tools[tool].getArgumentAttribute(taskArgument, 'isInput')
        isOutput = tools[tool].getArgumentAttribute(taskArgument, 'isOutput')

        # TODO DEAL WITH ATTRIBUTES
        if isInput:
          self.addFileNode(address + nodeID)
          self.graph.add_edge(address + nodeID, address + task, attributes = {})
        elif isOutput:
          self.addFileNode(address + nodeID)
          self.graph.add_edge(address + task, address + nodeID)
        else:
          self.addOptionNode(address + nodeID)
          self.graph.add_edge(address + nodeID, address + task)

  # Add shared nodes to the graph.
  # TODO ADD ATTRIBUTES
  def addSharedNodes(self, tools, pipeline):
    for sharedNodeID in pipeline.getSharedNodeIDs():
      for node in pipeline.getSharedNodeTasks(sharedNodeID):
        nodeInPipeline = pipeline.getSharedNodeTaskAttribute(node, 'pipeline')
        pipelineNodeID = pipeline.getSharedNodeTaskAttribute(node, 'pipelineNodeID')
        task           = pipeline.getSharedNodeTaskAttribute(node, 'task')
        taskArgument   = pipeline.getSharedNodeTaskAttribute(node, 'taskArgument')

        if nodeInPipeline:
          print('graph.addSharedNodes - HANDLE PIPELINE')

        # If the task is running a tool, build the node and add the required edges.
        else:

          # Check the taskArgument to identify if this node is a file or an option node.
          tool     = pipeline.getTaskAttribute(task, 'tool')
          isInput  = tools[tool].getArgumentAttribute(taskArgument, 'isInput')
          isOutput = tools[tool].getArgumentAttribute(taskArgument, 'isOutput')
          isFile   = True if (isInput or isOutput) else False

          # Define the pipeline relative address.
          address = str(pipeline.address + '.') if pipeline.address else str('')

          # If the node is a file node.
          if isFile:
            if address + sharedNodeID not in self.graph: self.addFileNode(str(address + sharedNodeID))
            if isInput: self.graph.add_edge(str(address + sharedNodeID), str(address + task))
            elif isOutput: self.graph.add_edge(str(address + task), str(address + sharedNodeID))

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

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

  # Using a pipeline configuration file, build and connect the defined nodes.
  def buildPipelineTasks(self, tools, pipeline, superPipeline):

    # Define the address for all nodes for this pipeline.
    address = str(pipeline.address) + '.' if pipeline.address != None else ''

    # Loop over all the pipeline tasks and build a node for each task. If the task is
    # a pipeline, ignore it.
    for task in pipeline.pipelineTasks:
      if not pipeline.getTaskAttribute(task, 'pipeline'): self.addTaskNode(address + str(task), pipeline.getTaskAttribute(task, 'tool'))

    # Add unique nodes.
    self.addUniqueNodes(tools, pipeline)

    # Add shared nodes.
    self.addSharedNodes(tools, pipeline, superPipeline)

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
      if pipelineContainingTask:

        # Generate the address of the task that this points to and check that a node of that
        # name has already been created. This task is a pipeline contained in the pipeline and
        # so must already have been created.
        taskNodeAddress = address + str(pipelineContainingTask) + '.' + str(task)
        #TODO ERROR
        if taskNodeAddress not in self.graph: print('graph.addUniqueNodes - 1'); exit(0)

        # Determine if this is a file or an option.
        

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
  def addSharedNodes(self, tools, pipeline, superPipeline):
    for sharedNodeID in pipeline.getSharedNodeIDs():

      # Determine if this shared node connects to a task or a node in another pipeline.
      containsTaskInAnotherPipeline = pipeline.getSharedNodeAttribute(sharedNodeID, 'containsTaskInAnotherPipeline')
      containsNodeInAnotherPipeline = pipeline.getSharedNodeAttribute(sharedNodeID, 'containsNodeInAnotherPipeline')

      # If all the shared nodes are in this pipeline, create the node and add the edges.
      #if not containsTaskInAnotherPipeline: self.constructLocalSharedNode(tools, pipeline, sharedNodeID)
      if not containsNodeInAnotherPipeline:
        self.constructLocalSharedNode(tools, pipeline, sharedNodeID)

        # If the shared node connects to a task in another pipeline.
        if containsTaskInAnotherPipeline: self.constructEdgesToPipelineTask(tools, pipeline, superPipeline, sharedNodeID)

      # If the shared node contains a node from another pipeline, then this node already exists.
      # Find the existing node and then generate the edges to the tasks in this pipeline.
      elif containsNodeInAnotherPipeline: self.constructEdgesToExistingNode(tools, pipeline, superPipeline, sharedNodeID)

  # Create the shared node and add the edges for the case where all the shared tasks are in this pipeline.
  def constructLocalSharedNode(self, tools, pipeline, sharedNodeID):
    for node in pipeline.getSharedNodeTasks(sharedNodeID):

      # Get the task and the task argument and whether it is external.
      task             = pipeline.getSharedNodeTaskAttribute(node, 'task')
      taskArgument     = pipeline.getSharedNodeTaskAttribute(node, 'taskArgument')
      externalPipeline = pipeline.getSharedNodeTaskAttribute(node, 'pipeline')

      # From this point on, only consider internal tasks. External task links will be added later.
      if not externalPipeline:

        # Check the taskArgument to identify if this node is a file or an option node.
        tool     = pipeline.getTaskAttribute(task, 'tool')
        isInput  = tools[tool].getArgumentAttribute(taskArgument, 'isInput')
        isOutput = tools[tool].getArgumentAttribute(taskArgument, 'isOutput')
    
        # Define the pipeline relative address.
        address = str(pipeline.address + '.') if pipeline.address else str('')
  
        # Add the node and edges.
        self.addNodeAndEdges(sharedNodeID, address, task, isInput, isOutput)

  # Construct edges to an existing node from another pipeline.
  def constructEdgesToExistingNode(self, tools, pipeline, superPipeline, sharedNodeID):

    # Loop over the nodes and determine the existing node.
    nodes = []
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      if pipeline.getSharedNodeTaskAttribute(node, 'pipelineNodeID'): nodes.append(node)

    # If there are multiple nodes in another pipeline, there is an error in the configuration file.
    # TODO LOOK AT THIS AND THE SHARED TASK ROUTINE BELOW. CONSIDER TWO CONTAINED VARIANT CALLING
    # PIPELINES AND YOU WNAT TO JOIN THE INPUT BAM NODE TO AN OUTPUT FROM THE CURRENT PIPELINE.
    # THE CURRENT PIPELINE NODE WOULD BE SHARED WITH NODES FROM TWO PIPELINES. 
    # TODO ERROR
    if len(nodes) != 1: print('constructEdgesToExistingNode - NOT HANDLED MULTIPLE SHARED NODES'); exit(0)
    externalPipeline = pipeline.getSharedNodeTaskAttribute(nodes[0], 'pipeline')
    externalNode     = pipeline.getSharedNodeTaskAttribute(nodes[0], 'pipelineNodeID')

    # Determine the full address of the node.
    address      = str(pipeline.address + '.') if pipeline.address else str('')
    nodeAddress  = str(externalPipeline + '.' + externalNode)

    # Check that the node exists.
    #TODO ERROR
    if address + nodeAddress not in superPipeline.uniqueNodeIDs and nodeAddress not in superPipeline.sharedNodeIDs:
      print('graph.constructEdgesToExistingNode - 2'); exit(0)

    # Loop over the nodes and add edges to the existing node (ignoring the node in the other pipeline).
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      if not pipeline.getSharedNodeTaskAttribute(node, 'pipeline'):
        taskArgument = pipeline.getSharedNodeTaskAttribute(node, 'taskArgument')
        task         = pipeline.getSharedNodeTaskAttribute(node, 'task')

        # Check the taskArgument to identify if this node is a file or an option node.
        tool     = pipeline.getTaskAttribute(task, 'tool')
        isInput  = tools[tool].getArgumentAttribute(taskArgument, 'isInput')
        isOutput = tools[tool].getArgumentAttribute(taskArgument, 'isOutput')

        # Add the node and edges.
        self.addNodeAndEdges(nodeAddress, address, task, isInput, isOutput)

  # If a shared node contains a link to a task in another pipeline, join the tasks in the current
  # pipeline to it.
  def constructEdgesToPipelineTask(self, tools, pipeline, superPipeline, sharedNodeID):

    # Determine the pipeline address and the node address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Loop over the nodes and connect the tasks from external pipelines to the existing node.
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      externalPipeline = pipeline.getSharedNodeTaskAttribute(node, 'pipeline')                     
      if externalPipeline:
        task         = pipeline.getSharedNodeTaskAttribute(node, 'task')                         
        taskArgument = pipeline.getSharedNodeTaskAttribute(node, 'taskArgument')                         
        taskAddress  = str(externalPipeline + '.' + task)

        # Check the taskArgument to identify if this node is a file or an option node.
        tool     = superPipeline.tasks[address + taskAddress]
        isInput  = tools[tool].getArgumentAttribute(taskArgument, 'isInput')
        isOutput = tools[tool].getArgumentAttribute(taskArgument, 'isOutput')

        # Add the node and edges.
        self.addNodeAndEdges(sharedNodeID, address, taskAddress, isInput, isOutput)

  # Add a node if necessary and add edges.
  def addNodeAndEdges(self, nodeID, address, task, isInput, isOutput):
  
    # Determine if this node is for a file or an option.
    isFile = True if (isInput or isOutput) else False

    # If the node is a file node. 
    if isFile:
      if address + nodeID not in self.graph: self.addFileNode(str(address + nodeID))
      if isInput:
        self.graph.add_edge(str(address + nodeID), str(address + task))
      elif isOutput:
        self.graph.add_edge(str(address + task), str(address + nodeID))

    # If the node is an option node.
    else:
      if address + nodeID not in self.graph: self.addOptionNode(address + nodeID)
      self.graph.add_edge(address + nodeID, address + task)

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

  # Return an attribute from a graph node.
  @classmethod
  def getGraphNodeAttribute(cls, graph, nodeID, attribute):
    try: return getattr(graph.node[nodeID]['attributes'], attribute)
    except: return None

  # Return a list of all nodes of the a requested type.
  @classmethod
  def getNodes(cls, graph, nodeType):
    nodeIDs = []
    for nodeID in graph.nodes():
      if cls.getGraphNodeAttribute(graph, nodeID, 'nodeType') == nodeType: nodeIDs.append(nodeID)

    return nodeIDs

#!/bin/bash/python

from __future__ import print_function
from collections import deque
import graphErrors
import networkx as nx
import parameterSets as ps

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

    # Handle errors associated with graph construction.
    self.errors = graphErrors.graphErrors()

    # Define the graph.
    self.graph = nx.DiGraph()

    # Store the workflow.
    self.workflow = []

    # Store parameter set information.
    self.ps = ps.parameterSets()

  # Using a pipeline configuration file, build and connect the defined nodes.
  def buildPipelineTasks(self, pipeline, superPipeline):

    # Define the address for all nodes for this pipeline.
    address = str(pipeline.address) + '.' if pipeline.address != None else ''

    # Loop over all the pipeline tasks and build a node for each task. If the task is
    # a pipeline, ignore it.
    for task in pipeline.pipelineTasks:
      if not pipeline.getTaskAttribute(task, 'pipeline'): self.addTaskNode(address + str(task), pipeline.getTaskAttribute(task, 'tool'))

    # Add unique nodes.
    self.addUniqueNodes(superPipeline, pipeline)

    # Add shared nodes.
    self.addSharedNodes(superPipeline, pipeline)

    # Join tasks and nodes as instructed.
    self.connectNodesToTasks(superPipeline, pipeline)

  # Add unique graph nodes to the graph.
  def addUniqueNodes(self, superPipeline, pipeline):
    for nodeID in pipeline.uniqueNodeAttributes:

      # Define a set of information to be used in help messages.
      information = (pipeline.name, 'unique graph nodes', nodeID)

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

      else:

        # Get the tool and it's attributes associated with this argument.
        longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

        # Determine if this is a file or an option.
        isInput  = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')

        # Determine if this is a filename stub.
        isStub = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
        if isStub: stubExtensions = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')

        # Add the required nodes and edges.
        if isInput and isStub:
          self.addStubNodes(address + nodeID, stubExtensions)
          self.addStubEdges(address + nodeID, address + task, stubExtensions, argumentAttributes, isInput = True)
        elif isInput:
          self.addFileNode(address + nodeID)
          self.addEdge(address + nodeID, address + task, argumentAttributes)
        elif isOutput and isStub:
          self.addStubNodes(address + nodeID, stubExtensions)
          self.addStubEdges(address + task, address + nodeID, stubExtensions, argumentAttributes, isInput = False)
        elif isOutput:
          self.addFileNode(address + nodeID)
          self.addEdge(address + task, address + nodeID, argumentAttributes)
        else:
          self.addOptionNode(address + nodeID)
          self.addEdge(address + nodeID, address + task, argumentAttributes)

  # Add shared nodes to the graph.
  def addSharedNodes(self, superPipeline, pipeline):
    for sharedNodeID in pipeline.getSharedNodeIDs():

      # Determine if this shared node connects to a task or a node in another pipeline.
      containsTaskInAnotherPipeline = pipeline.getSharedNodeAttribute(sharedNodeID, 'containsTaskInAnotherPipeline')
      containsNodeInAnotherPipeline = pipeline.getSharedNodeAttribute(sharedNodeID, 'containsNodeInAnotherPipeline')

      # If all the shared nodes are in this pipeline, create the node and add the edges.
      if not containsNodeInAnotherPipeline:
        self.constructLocalSharedNode(superPipeline, pipeline, sharedNodeID)

        # If the shared node connects to a task in another pipeline.
        if containsTaskInAnotherPipeline: self.constructEdgesToPipelineTask(superPipeline, pipeline, sharedNodeID)

      # If the shared node contains a node from another pipeline, then this node already exists.
      # Find the existing node and then generate the edges to the tasks in this pipeline.
      elif containsNodeInAnotherPipeline: self.constructEdgesToExistingNode(superPipeline, pipeline, sharedNodeID)

  # Create the shared node and add the edges for the case where all the shared tasks are in this pipeline.
  def constructLocalSharedNode(self, superPipeline, pipeline, sharedNodeID):
    for node in pipeline.getSharedNodeTasks(sharedNodeID):

      # Get the task and the task argument and whether it is external.
      task             = pipeline.getNodeTaskAttribute(node, 'task')
      taskArgument     = pipeline.getNodeTaskAttribute(node, 'taskArgument')
      externalPipeline = pipeline.getNodeTaskAttribute(node, 'pipeline')

      # From this point on, only consider internal tasks. External task links will be added later.
      if not externalPipeline:

        # Get the tool for this task.
        tool = pipeline.getTaskAttribute(task, 'tool')

        # Get the tool and it's attributes associated with this argument.
        longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

        # Check the taskArgument to identify if this node is a file or an option node.
        isInput  = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')

        # Determine if this is a filename stub.
        isStub = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
        if isStub: stubExtensions = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')
    
        # Define the pipeline relative address.
        address = str(pipeline.address + '.') if pipeline.address else str('')
  
        # Add the node and edges.
        if isStub: self.addStubNodesAndEdges(sharedNodeID, address, task, isInput, stubExtensions, argumentAttributes)
        else: self.addNodeAndEdges(sharedNodeID, address, task, isInput, isOutput, argumentAttributes)

  # Construct edges to an existing node from another pipeline.
  def constructEdgesToExistingNode(self, superPipeline, pipeline, sharedNodeID):
    externalPipeline = None
    externalNode     = None
    keptNodeIsStub   = False

    # Define the pipeline address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Loop over the nodes and determine the existing node.
    nodes = deque()
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      if pipeline.getNodeTaskAttribute(node, 'pipelineNodeID'):

        # Get the name of the pipeline that is used.
        pipelineName = pipeline.getTaskAttribute(node.pipeline, 'pipeline')

        # If the node points to a unique node in another pipeline, determine whether this node is a stub.
        nodeType = superPipeline.getNodeType(node.pipeline, node.pipelineNodeID)
        if nodeType == 'unique':
          task         = superPipeline.pipelineConfigurationData[node.pipeline].getUniqueNodeAttribute(node.pipelineNodeID, 'task')
          tool         = superPipeline.pipelineConfigurationData[node.pipeline].getTaskAttribute(task, 'tool')
          taskArgument = superPipeline.pipelineConfigurationData[node.pipeline].getUniqueNodeAttribute(node.pipelineNodeID, 'taskArgument')

          # Determine if the task argument is a stub.
          longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)
          isStub                               = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
 
        # If the pipeline node being pointed to is a shared node, this isn't handled. #FIXME
        elif nodeType == 'shared': print('constructEdgesToExistingNode - NOT HANDLED SHARED NODES'); exit(0)

        # If the node type is unknown, terminate.#FIXME
        elif not nodeType: print('constructEdgesToExistingNode - NOT HANDLED NON NODES'); exit(0)

        # If this node points to a stub, mark this as the node to keep in the next step. If there are multiple
        # stub nodes, both nodes require edges to all the files, so which one is kept is arbitrary.
        if isStub:
          externalPipeline = node.pipeline
          externalNode     = node.pipelineNodeID
          nodes.appendleft((node, isStub))
          keptNodeIsStub   = True
        else: nodes.append((node, isStub))

    # If there were no stub nodes, define the first node as the node to keep.
    if not externalPipeline:
      externalPipeline = pipeline.getNodeTaskAttribute(nodes[0][0], 'pipeline')
      externalNode     = pipeline.getNodeTaskAttribute(nodes[0][0], 'pipelineNodeID')

    # If there are multiple nodes in another pipeline, then these need to be merged. An example of this
    # situation could be that two variant calling pipelines have been implemented as pipelines within a
    # pipeline. The input files to both these pipelines were generated when the pipelines were constructed.
    # Only one of these nodes should be kept and the others deleted. The deleted nodes then require edges
    # creating to the node that was kept.

    # Determine the full address of the node being kept..
    nodeAddress  = str(externalPipeline + '.' + externalNode)

    # Pop off the leftmost element. This is the element that is being kept.
    nodes.popleft()

    # Loop over the nodes to be removed.
    while True:
      try: nodeTuple = nodes.popleft()
      except: break

      # Extract the information from the tuple.
      node   = nodeTuple[0]
      isStub = nodeTuple[1]

      # Get the address of the node to delete.
      externalPipeline  = pipeline.getNodeTaskAttribute(node, 'pipeline')
      externalNode      = pipeline.getNodeTaskAttribute(node, 'pipelineNodeID')
      stubExtension     = pipeline.getNodeTaskAttribute(node, 'stubExtension')
      deleteNodeAddress = str(address + externalPipeline + '.' + externalNode)

      # Get the task, tool and argument and argument attributes.
      task         = superPipeline.pipelineConfigurationData[node.pipeline].getUniqueNodeAttribute(node.pipelineNodeID, 'task')
      tool         = superPipeline.pipelineConfigurationData[node.pipeline].getTaskAttribute(task, 'tool')
      taskArgument = superPipeline.pipelineConfigurationData[node.pipeline].getUniqueNodeAttribute(node.pipelineNodeID, 'taskArgument')

      # Determine if the task argument is a stub.
      longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

      # If both the kept node and the node who's edges we are replacing are stubs, join each
      # of the stubs nodes to this node.
      if keptNodeIsStub and isStub: print('NOT HANDLED BOTH STUBS'); exit(0)

      # If the kept node is a stub, but the current node is not, determine which node to connect to
      # and connect.
      elif keptNodeIsStub and not isStub: self.attachNonStubToStub(nodeAddress, deleteNodeAddress, stubExtension, argumentAttributes)

      # If none of the nodes are stubs, connect the nodes together.
      elif not keptNodeIsStub and not isStub: print('NOT HANDLED NON TO NON STUB'); exit(0)

    # Loop over the nodes that point to tasks in this pipeline (e.g. nodes in the shared graph nodes section that
    # do not include a reference to an internal pipeline), and add edges to the node being kept.
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      if not pipeline.getNodeTaskAttribute(node, 'pipeline'):
        taskArgument = pipeline.getNodeTaskAttribute(node, 'taskArgument')
        task         = pipeline.getNodeTaskAttribute(node, 'task')

        # Get the tool associated with this task.
        tool = pipeline.getTaskAttribute(task, 'tool')

        # Get the tool and it's attributes associated with this argument.
        longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

        # Check the taskArgument to identify if this node is a file or an option node.
        isInput  = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')

        # Check if the node is a stub.
        isStub        = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
        stubExtension = pipeline.getNodeTaskAttribute(node, 'stubExtension')
        print('TEST', task, tool, taskArgument, longFormArgument, isInput, isOutput, keptNodeIsStub, isStub)

        # Add the node and edges (accounting for whether the node that was kept is a stub node or not).
        if not keptNodeIsStub and not isStub: self.addNodeAndEdges(nodeAddress, address, task, isInput, isOutput, argumentAttributes)
        elif not keptNodeIsStub and isStub: print('NOT HANDLED STUB TO NON STUB'); exit(0)
        elif keptNodeIsStub and not isStub:
          if not stubExtension: self.errors.missingStubExtensionForSharedNode(task, longFormArgument)
          self.addNodeAndEdges(nodeAddress + '.' + stubExtension, address, task, isInput, isOutput, argumentAttributes)
        elif keptNodeIsStub and isStub: print('NOT HANDLED INTERNAL STUB TO STUB'); exit(0)

  def attachNonStubToStub(self, nodeAddress, deleteNodeAddress, stubExtension, attributes):

    # If no stub extension is supplied, this step cannot be completed.
    if not stubExtension: print('ERROR - attachNonStubToStub - 1'); exit(0)

    # Get all the predecessors and successors and recreate the edges to the node being kept.
    for predecessorID in self.graph.predecessors(deleteNodeAddress): 
      self.addEdge(predecessorID, nodeAddress + '.' + stubExtension, attributes = attributes)
    for successorID in self.graph.successors(deleteNodeAddress):
      self.addEdge(nodeAddress + '.' + stubExtension, successorID, attributes = attributes)

    # Remove the node.
    self.graph.remove_node(deleteNodeAddress)

  # If a shared node contains a link to a task in another pipeline, join the tasks in the current
  # pipeline to it.
  def constructEdgesToPipelineTask(self, superPipeline, pipeline, sharedNodeID):

    # Determine the pipeline address and the node address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Loop over the nodes and connect the tasks from external pipelines to the existing node.
    for node in pipeline.getSharedNodeTasks(sharedNodeID):
      externalPipeline = pipeline.getNodeTaskAttribute(node, 'pipeline')                     
      if externalPipeline:
        task         = pipeline.getNodeTaskAttribute(node, 'task')                         
        taskArgument = pipeline.getNodeTaskAttribute(node, 'taskArgument')                         
        taskAddress  = str(externalPipeline + '.' + task)

        # Get the tool associated with this task.
        tool = superPipeline.tasks[address + taskAddress]

        # Get the tool and it's attributes associated with this argument.
        longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

        # Check the taskArgument to identify if this node is a file or an option node.
        isInput  = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')

        # Add the node and edges.
        self.addNodeAndEdges(sharedNodeID, address, taskAddress, isInput, isOutput, argumentAttributes)

  # Connect nodes and tasks as instructed in the pipeline configuration file.
  def connectNodesToTasks(self, superPipeline, pipeline):

    # Determine the pipeline address and the node address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Loop over all the pipeline connections.
    for nodeID in pipeline.connections:

      # Store the source node IDs.
      sourceNodeIDs = []

      # Determine all the source nodes.
      for source in pipeline.getSources(nodeID):
        externalPipeline = pipeline.getNodeTaskAttribute(source, 'pipeline')
        externalNode     = pipeline.getNodeTaskAttribute(source, 'pipelineNodeID')
        task             = pipeline.getNodeTaskAttribute(source, 'task')
        taskArgument     = pipeline.getNodeTaskAttribute(source, 'taskArgument')

        # Determine the pipeline relative task address.
        taskAddress = str(externalPipeline + '.' + task) if externalPipeline else str(task)

        # If the source node already exists, it is defined with the external node. Store this source
        # node ID.
        if externalNode: sourceNodeIDs.append(str(address + externalPipeline + '.' + externalNode))

        # If the external node isn't specified, the node needs to be created. The source must be a
        # file node (not a task), otherwise this would create a situation with multiple tasks producing
        # the same output file. In creating the node, this must therefore be the output of the defined
        # task. 
        #TODO PUT IN A CHECK THAT IF CREATING NODES, THE ABOVE LOGIC IS VALID.
        else:
          if nodeID in superPipeline.sharedNodeIDs or nodeID in superPipeline.uniqueNodeIDs: print('graph.connectNodesToTasks - 2'); exit(0)

          # Generate the node address (e.g. the output file for a task in the external pipeline).
          nodeAddress = str(externalPipeline + '.' + nodeID) if externalPipeline else str(nodeID)

          # Get the tool associated with this task.
          tool = superPipeline.tasks[address + taskAddress]

          # Get the tool and it's attributes associated with this argument.
          longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

          # Determine if this is a filename stub.
          isStub = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
          if isStub: stubExtensions = superPipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')    

          # Create the file node and connect it to the task for which it is an output.
          self.addNodeAndEdges(nodeAddress, address, taskAddress, False, True, argumentAttributes)

          # Store the node ID for connecting to the target task node.
          sourceNodeIDs.append(str(address + nodeAddress))

      # Loop over the target nodes and join the sources to them.
      for target in pipeline.getTargets(nodeID):
        externalPipeline = pipeline.getNodeTaskAttribute(target, 'pipeline')
        externalNode     = pipeline.getNodeTaskAttribute(target, 'pipelineNodeID')
        task             = pipeline.getNodeTaskAttribute(target, 'task')
        taskArgument     = pipeline.getNodeTaskAttribute(target, 'taskArgument')

        # Get the tool associated with this task.
        tool = superPipeline.tasks[address + taskAddress]

        # Get the tool and it's attributes associated with this argument.
        longFormArgument, argumentAttributes = self.getAttributes(superPipeline, tool, taskArgument)

        # Determine the pipeline relative task address.
        taskAddress = str(externalPipeline + '.' + task) if externalPipeline else str(task)

        # Connect all the source nodes to the target node.
        for sourceNodeID in sourceNodeIDs: self.addEdge(sourceNodeID, taskAddress, argumentAttributes)

  # Add a node if necessary and add edges.
  def addNodeAndEdges(self, nodeID, address, task, isInput, isOutput, attributes):
  
    # Determine if this node is for a file or an option.
    isFile = True if (isInput or isOutput) else False

    # If the node is a file node. 
    if isFile:
      if address + nodeID not in self.graph: self.addFileNode(str(address + nodeID))
      if isInput: self.addEdge(str(address + nodeID), str(address + task), attributes = attributes)
      elif isOutput: self.addEdge(str(address + task), str(address + nodeID), attributes = attributes)

    # If the node is an option node.
    else:
      if address + nodeID not in self.graph: self.addOptionNode(address + nodeID)
      self.addEdge(address + nodeID, address + task, attributes = attributes)

  # Add stub nodes if necessary and then add edges. Stubs are always in reference to a file, so no
  # checks are required for whether this is a file node.
  def addStubNodesAndEdges(self, nodeID, address, task, isInput, extensions, attributes):

    # Loop over all of the extensions associated with this stub.
    for extension in extensions:
      if extension.startswith('_') or extension.startswith('.'): fullAddress = address + nodeID + str(extension)
      else: fullAddress = address + nodeID + '.' + str(extension)

      # Create the node if necessary.
      if fullAddress not in self.graph: self.addFileNode(str(fullAddress))

      # Add the edge from or to the task.
      if isInput: self.addEdge(str(fullAddress), str(address + task), attributes = attributes)
      else: self.addEdge(str(address + task), str(fullAddress), attributes = attributes)

  # Get tool and argument attributes.
  def getAttributes(self, superPipeline, tool, argument):

    # Get the data structure for this argument to add to the created edge.
    toolAttributes     = superPipeline.getToolData(tool)
    longFormArgument   = toolAttributes.getLongFormArgument(argument)
    argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

    return longFormArgument, argumentAttributes

  # If this is a filename stub, a node for each of the files needs to be created. The
  # node ID should be the node ID with the file extension appended.
  def addStubNodes(self, nodeID, extensions):
    for extension in extensions:
      attributes          = fileNodeAttributes()
      attributes.nodeType = 'file'
      self.graph.add_node(nodeID + '.' + str(extension), attributes = attributes)

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

  # Add an edge to the graph.
  def addEdge(self, source, target, attributes):
    self.graph.add_edge(source, target, attributes = attributes)

  # Add edges to the graph for files created from a stub.
  def addStubEdges(self, source, target, extensions, attributes, isInput):
    for extension in extensions:
      modifiedSource = source + '.' + str(extension) if isInput else source
      modifiedTarget = target if isInput else target + '.' + str(extension)
      self.graph.add_edge(modifiedSource, modifiedTarget, attributes = attributes)

  # Generate a topologically sorted graph.
  #TODO
  def generateWorkflow(self):

    # Perform a topological sort of the graph.
    for nodeID in nx.topological_sort(self.graph):
      nodeType = getattr(self.graph.node[nodeID]['attributes'], 'nodeType')
      if nodeType == 'task': self.workflow.append(nodeID)

    # The topological sort does not always generate the corret order. In this routine, check for
    # cases where a task is outputting to the stream. It is possible that after this task, the
    # topological sort could choose from multiple tasks to perform next. This routine exists to
    # ensure that the task following is the one that expects the stream as its input.
    #FIXME
    incomplete = True
    startCount = 0
    while incomplete:
      for counter in range(startCount, len(self.workflow)):
        task = self.workflow[counter]
        if counter == len(self.workflow) - 1: incomplete = False
        else:
          nextTask         = self.workflow[counter + 1]
          #FIXME
          isOutputToStream = False
          #isOutputToStream = self.nodeMethods.getGraphNodeAttribute(graph, task, 'outputStream')

          # If this task outputs to the stream, determine what the next task should be.
          if isOutputToStream:
            for outputNodeID in self.graph.successors(task):
              successorTasks  = []
              for successorTask in self.graph.successors(outputNodeID): successorTasks.append(successorTask)

            # If the next task is not in the list of tasks, modify the workflow to ensure that it is.
            successorIndex = self.workflow.index(successorTasks[0])
            if nextTask not in successorTasks:

              # Store the tasks 
              workflowMiddle = []
              workflowMiddle = self.workflow[counter + 1: successorIndex]

              # Find all the tasks after the successor task. Once tasks have been moved around, these
              # tasks will all be added to the end.
              workflowEnd = []
              workflowEnd = self.workflow[successorIndex + 1:]

              # Reconstruct the workflow.
              updatedWorkflow = []
              for updateCount in range(0, counter + 1): updatedWorkflow.append(workflow[updateCount])
              updatedWorkflow.append(successorTasks[0])
              for updateTask in workflowMiddle: updatedWorkflow.append(updateTask)
              for updateTask in workflowEnd: updatedWorkflow.append(updateTask)

              # Update the workflow.
              self.workflow = updatedWorkflow

              # Reset the startCount. There is no need to loop over the entire workflow on the next
              # pass.
              startCount = counter
              break

    return self.workflow

  # Loop over the workflow adding default parameter set data for all of the tasks.
  def addTaskParameterSets(self, superPipeline, path):

    # Loop over the workflow.
    for task in self.workflow:
      tool = self.getGraphNodeAttribute(self.graph, task, 'tool')

      # Loop over all of the arguments in the default parameter set.
      parameterSet = superPipeline.getToolParameterSet(tool, 'default')
      arguments    = ps.parameterSets.getArguments(parameterSet)
      for argument in arguments:
        values           = arguments[argument]
        toolData         = superPipeline.getToolData(tool)
        longFormArgument = toolData.getLongFormArgument(argument)

        # Check if this edge exists.
	print('\tTEST', task, tool, argument, longFormArgument, values)

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

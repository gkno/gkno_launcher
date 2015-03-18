#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import fileHandling as fh
import graphErrors
import networkx as nx

import constructFilenames as construct
import parameterSets as ps
import parameterSetErrors as pse
import pipelineConfigurationErrors as pce
import stringOperations as stringOps
import superpipeline as sp

import json
import os
import sys

# Define a data structure for holding information on arguments.
class argumentInformation:
  def __init__(self):

    # Define the node ID from which the task was taken.
    self.nodeID = None

    # Define the address of the task and the tool it uses.
    self.taskAddress = None
    self.tool        = None

    # Define the argument (this is in its long form).
    self.argument = None

    # Define whether this argument points to an input or output file.
    self.isInput  = False
    self.isOutput = False

    # Define information relevant to stub arguments.
    self.isStub         = False
    self.stubExtension  = None
    self.stubExtensions = []

    # Define if this argument is greedy.
    self.isGreedy = False

# Define a data structure for task nodes.
class taskNodeAttributes:
  def __init__(self):

    # Define the node type.
    self.nodeType = 'task'

    # Define the tool to be used to execute this task.
    self.tool = None

    # Store information on whether the task is greedy.
    self.isGreedy       = False
    self.greedyArgument = 1

    # Store information on the task divisions.
    self.children   = []
    self.divisions  = 0
    self.divisionID = None
    self.isChild    = False
    self.parent     = None

    # Store the number of subphaes and divisions the task is broken up into.
    self.subphases = 0

    # Record if this node should be included in any graphical output.
    self.includeInReducedPlot = True

    # If this task is marked as accepting a stream as input or output.
    self.isInputStream  = False
    self.isOutputStream = False

# Define a data structure for file/option nodes.
class dataNodeAttributes:
  def __init__(self, nodeType):

    # Define the argument that sets the graph node.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # There are times where multiple arguments can point to the same graph node. For
    # example, if the top level pipeline has an argument pointing to a node with
    # argument --in, but this points to a node in a child pipeline. When the child
    # pipeline is processed, it could have an argument defined, say --out. The highest
    # level argument should be stored in the values above, but all alternatives are
    # stored in the self.alternativeArguments list.
    self.alternativeArguments = []

    # Define the node type.
    self.nodeType = nodeType

    # Record if values for this node are required.
    self.isRequired = False

    # Store values for this node.
    self.values = []

    # Store if the node is an intermediate node (e.g. all files associated with this node
    # will be deleted. In addition, store the task after which the files associated with
    # the node should be deleted.
    self.isIntermediate  = False
    self.deleteAfterTask = None

    # Store information on the task divisions.
    self.children         = []
    self.divisions        = 0
    self.divisionID       = None
    self.isChild          = False
    self.isCreateDivision = False
    self.parent           = None

    # If the files contained in this node are being streamed from one task to the next, the files
    # are actually never created. Mark the node as containing streaming files so that attempts to
    # delete them will not be made, and the files will not be listed as outputs or dependencies.
    self.isStream = False

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
    self.parameterSet = None
    self.ps           = ps.parameterSets()

    # When configuration file nodes (unique and shared nodes) are added to the graph, keep
    # track of the node ID in the graph that the configuration file node is attached to.
    self.configurationFileToGraphNodeID = {}

  # Using a pipeline configuration file, build and connect the defined nodes.
  def buildPipelineTasks(self, pipeline, superpipeline):

    # Define the address for all nodes for this pipeline.
    address = str(pipeline.address) + '.' if pipeline.address != None else ''

    # Loop over all the pipeline tasks and build a node for each task. If the task is
    # a pipeline, ignore it.
    for task in pipeline.pipelineTasks:

      # Define the task address.
      taskAddress = str(address + task)
      if not pipeline.getTaskAttribute(task, 'pipeline'): self.addTaskNode(superpipeline, taskAddress, taskAddress, pipeline.pipelineTasks[task])

    # Add unique nodes.
    self.addUniqueNodes(superpipeline, pipeline)

    # Add shared nodes.
    self.addSharedNodes(superpipeline, pipeline)

    # Join tasks and nodes as instructed.
    self.connectNodesToTasks(superpipeline, pipeline)

  # Add unique graph nodes to the graph.
  def addUniqueNodes(self, superpipeline, pipeline):
    for configurationNodeID in pipeline.uniqueNodeAttributes:

      # Define a set of information to be used in help messages.
      information = (pipeline.name, 'unique graph nodes', configurationNodeID)

      # Define the pipeline relative address.
      address = str(pipeline.address + '.') if pipeline.address else str('')

      # Determine if this node has already been added to the graph. Only proceed with processing
      # this node if it hasn't already been added. If the node has already been processed (for
      # example, a parent pipeline may have included the unique node as a shared node within its
      # configuration file), the graph node ID will appear in the configurationFileToGraphNodeID
      # dictionary.
      graphNodeID = address + configurationNodeID
      if graphNodeID not in self.configurationFileToGraphNodeID:

        # Get the task this node points to and determine if it is a tool or a pipeline.
        task         = pipeline.getUniqueNodeAttribute(configurationNodeID, 'task')
        taskArgument = pipeline.getUniqueNodeAttribute(configurationNodeID, 'taskArgument')
        taskNodeID   = address + task
  
        # Check to see if the task runs a tool or a pipeline.
        tool           = superpipeline.getTool(taskNodeID)
        toolAttributes = superpipeline.getToolData(tool)

        # Get the long form of the argument and the associated attributes for the argument.
        longFormArgument   = toolAttributes.getLongFormArgument(taskArgument)
        argumentAttributes = toolAttributes.getArgumentData(longFormArgument)
  
        # Determine if this is a file or an option.
        isInput  = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')

        # Determine if this argument is greedy.
        argumentAttributes.isGreedy = pipeline.getUniqueNodeAttribute(configurationNodeID, 'isGreedy')
  
        # Determine if this is a filename stub.
        isStub = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
        if isStub: stubExtensions = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')
  
        # If the configuration file node is for a filename stub, add as many nodes to the graph as there are files
        # associated with the stub. Then connect all the nodes to the task.
        if isStub:

          # Loop over all of the stub extensions.
          for i, extension in enumerate(stubExtensions):

            # Define the name of the new file node.
            fileNodeID = str(graphNodeID + '.' + str(extension))

            # Add the file node.
            self.addFileNode(fileNodeID, graphNodeID)

            # Identify the source and target node (depending on whether this is an input or an output)
            # and add the edges to the graph.
            source = fileNodeID if isInput else taskNodeID
            target = taskNodeID if isInput else fileNodeID

            # Store the extension for this particular node.
            stubArgumentAttributes                 = deepcopy(argumentAttributes)
            stubArgumentAttributes.stubExtension   = extension
            stubArgumentAttributes.primaryStubNode = True if i == 0 else False

            # Add the edge to the graph.
            self.graph.add_edge(source, target, attributes = stubArgumentAttributes)

        # If this is an input file (not a stub), add the node and join it to the task.
        elif isInput:
          self.addFileNode(str(graphNodeID), str(graphNodeID))
          self.addEdge(graphNodeID, taskNodeID, argumentAttributes)

        # If this is an output file (not a stub), add the node and join it to the task.
        elif isOutput:
          self.addFileNode(str(graphNodeID), str(graphNodeID))
          self.addEdge(taskNodeID, graphNodeID, argumentAttributes)

        # If this is not a file, then create an option node and join to the task.
        else:
          self.addOptionNode(str(graphNodeID))
          self.addEdge(graphNodeID, taskNodeID, argumentAttributes)

  # Add shared nodes to the graph.
  def addSharedNodes(self, superpipeline, pipeline):
    sharedNodes      = []
    tasksSharingNode = []

    # Define the pipeline relative address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Set the pipeline name. This is just the address above unless this is the top tier pipeline. In this case,
    # the name is defined as pipeline.name.
    pipelineName = pipeline.address if pipeline.address else pipeline.name

    # Loop over all the sets of shared nodes in this pipeline.
    for sharedNodeID in pipeline.getSharedNodeIDs():

      # First check that this node has not already been added to  the graph. Only proceed if it hasn't. If the
      # configuration node has already been processed (e.g. a configuration file node of a pipeline for which
      # this pipeline is a descendant, shared this node), the configuration node ID will have been added to
      # the configurationFileToGraphNodeID dictionary.
      if not pipelineName + '.' + sharedNodeID in self.configurationFileToGraphNodeID:

        # Create a list containing all shared nodes. Each node in the configuration is one of three types: 1) a task
        # and argument defined in this pipeline, 2) a task and argument from an external pipeline, or 3) a node
        # defined in an external pipeline. For 1) and 2), the nodes can be processed immediately, but those in category
        # 3) cannot. Configuration nodes in category 3) are either unique nodes (which can also be processed immediately),
        # or are themselves shared nodes, which may contain links to configuration nodes in pipelines external to that.
        #
        # The process followed here is to march through all the configuration file nodes listed in the current pipeline,
        # and store the task address, argument and any stub extensions of the contained nodes. If the configuration file
        # is itself a shared node, this is added to a separate list. Once the configuration files in this node have been
        # processed, the list of shared nodes are then processed. This will continue until all the shared nodes have been
        # fully explored and all configuration file nodes sharing this graph node have been accounted for. At this point,
        # the tasksSharingNode list will contain information on all of the tasks and the graph node can be created.
        sharedNodes      = [(pipelineName, sharedNodeID)]
        tasksSharingNode = []

      # Keep track of the number of stub arguments in the shared node.
      numberOfStubs          = 0
      numberOfStubExtensions = 0
      numberOfInputFiles     = 0
      numberOfOutputFiles    = 0

      # Loop over the sharedNodes until it is empty.
      while sharedNodes:
        name, sharedNodeID = sharedNodes.pop()

        # Loop over all the tasks sharing this node.
        for taskInformation in superpipeline.pipelineConfigurationData[name].getSharedNodeTasks(sharedNodeID):

          # Get the address of this pipeline.
          pipelineAddress = superpipeline.pipelineConfigurationData[name].address

          # Get the task information
          externalNodeID = taskInformation.externalNodeID
          stubExtension  = taskInformation.stubExtension
          task           = taskInformation.task
          taskAddress    = pipelineAddress + '.' + task if pipelineAddress else task
          taskArgument   = taskInformation.taskArgument

          # Check if this node is listed as greedy.
          isGreedy = taskInformation.isGreedy

          # For tasks pointing to arguments (e.g. types (1) and (2) in the message above), add the information to tasksSharingNode
          # list.
          if not externalNodeID:

            # Get the tool used for the task and determine if the argument is a stub.
            information = self.getArgumentInformation(superpipeline, taskAddress, taskArgument)

            # Add other required information to the argument information data structure.
            information.nodeID        = pipelineAddress + '.' + sharedNodeID if pipelineAddress else sharedNodeID
            information.stubExtension = stubExtension
            information.taskAddress   = taskAddress
            information.isGreedy      = isGreedy

            # Store the information.
            tasksSharingNode.append(information)

            # Update counters on the number of stubs and input/output files.
            if information.stubExtension: numberOfStubExtensions += 1
            numberOfStubs       += information.isStub
            numberOfOutputFiles += information.isOutput
            numberOfInputFiles  += information.isInput

          # If the task points to an external node, determine if this node is a unique node or a shared node.
          else:
            nodeType = superpipeline.getNodeType(taskAddress, externalNodeID)

            # Unique nodes can be added to tasksSharingNode and marked as added to the graph.
            if nodeType == 'unique':
              externalTask         = superpipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeID, 'task')
              externalTaskArgument = superpipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeID, 'taskArgument')
              externalTaskAddress  = taskAddress + '.' + externalTask

              # Get the tool used for the task and determine if the argument is a stub.
              information = self.getArgumentInformation(superpipeline, externalTaskAddress, externalTaskArgument)

              # Add other required information to the argument information data structure.
              information.nodeID        = taskAddress + '.' + externalNodeID
              information.stubExtension = stubExtension
              information.taskAddress   = externalTaskAddress
              information.isGreedy      = isGreedy

              # Store the information.
              tasksSharingNode.append(information)

              # Update counters on the number of stubs and input/output files.
              if information.stubExtension: numberOfStubExtensions += 1
              numberOfStubs       += information.isStub
              numberOfOutputFiles += information.isOutput
              numberOfInputFiles  += information.isInput

            # If this is a shared node in another pipeline, add the node to the sharedNodes list and this will be processed
            # in this loop.
            elif nodeType == 'shared': sharedNodes.append((taskAddress, externalNodeID))

      # Having parsed through all the pipelines and identified all the tasks sharing the node, construct the graph
      # node and link all necessary tasks.
      if tasksSharingNode:

        # Ensure that either all the arguments point to files (inputs or outputs) or that none of them do
        # (options).
        numberOfFiles = numberOfInputFiles + numberOfOutputFiles
        if (numberOfFiles > 0) and (numberOfFiles < len(tasksSharingNode)): print('graph.addSharedNodes - files 1'); exit(0)
        elif numberOfFiles == 0: isFile = False
        else: isFile = True

        # Check that there are no problems with stubs. Firstly, if some, but not all of the arguments
        # sharing a node are stubs, then the subr arguments must have the extension of the file being shared
        # defined. In other words, if 0 < numberOfStubs < number of arguments, then it must be true that
        # numberOfStubs = numberOfStubExtensions.
        if (numberOfStubs > 0) and (numberOfStubs < len(tasksSharingNode)):
          #TODO ERROR
          if numberOfStubs != numberOfStubExtensions: print('graph.addSharedNodes - stubs 1'); exit(0)

          # If all of the stub arguments have the stub extension provided, create all of the required nodes and
          # join the tasks to the required nodes.
          else: self.someStubArguments(superpipeline, address + sharedNodeID, tasksSharingNode)

        # If none of the arguments are stubs, but stub arguments have been provided, there is an error in the
        # configuration file.
        elif (numberOfStubs == 0) and (numberOfStubExtensions > 0): print('graph.addSharedNodes - stub 2'); exit(0)

        # If no stub extensions are defined, either all of the arguments are stubs, or none of them are.
        elif numberOfStubExtensions == 0:

          # If all of the arguments are stubs, create all the necessary nodes and join all the tasks with all of the
          # nodes.
          if numberOfStubs == len(tasksSharingNode): self.allStubArguments(superpipeline, address + sharedNodeID, tasksSharingNode)

          # If none of the arguments are stubs, create the single node and join to all the tasks.
          elif numberOfStubs == 0: self.noStubArguments(superpipeline, address + sharedNodeID, tasksSharingNode, isFile)

        # If the set of tasks is not capture by the above clauses, the situation is not understood.
        else: print('graph.addSharedNodes - UKNOWN SITUATION'); exit(0)

  # Get information on a tool argument and return information on whether the argument is an input, output
  # or a stub.
  def getArgumentInformation(self, superpipeline, task, argument):

    # Generate a data structure for the data.
    information = argumentInformation()

    # Get the tool used for this task and retrieve data on this tool from the super pipeline.
    information.tool = superpipeline.getTool(task)
    toolData         = superpipeline.getToolData(information.tool)

    # Ensure the supplied argument is in the long form and check if the argument is a stub.
    information.argument = toolData.getLongFormArgument(argument)
    information.isStub   = toolData.getArgumentAttribute(information.argument, 'isStub')

    # If this is a stub, get the allowed extensions.
    information.stubExtensions = toolData.getArgumentAttribute(information.argument, 'stubExtensions')

    # Determine if the task node is an input or an output file.
    information.isInput  = toolData.getArgumentAttribute(information.argument, 'isInput')
    information.isOutput = toolData.getArgumentAttribute(information.argument, 'isOutput')

    # Return all information.
    return information

  # If a set of shared configuration file nodes are all stub arguments, ensure that each of the arguments
  # expects the same set of stub extensions, then create all of the nodes and join them to all the tasks.
  def allStubArguments(self, superpipeline, nodeAddress, tasks):
    allowedExtensions = []

    # All of the stub arguments need to share the same set of extensions. Take the first task in the
    # list and create a file node for each of the extensions. Each subsequent task will be checked to 
    # ensure it shares the same extensions before being linked.
    for extension in tasks[0].stubExtensions: allowedExtensions.append(extension)

    # Loop over all the tasks sharing the node.
    for information in tasks:

      # Extract information from the information
      taskAddress = information.taskAddress

      # Get the attributes for the tool.
      toolAttributes = superpipeline.getToolData(information.tool)

      # Get the long form of the argument and the associated attributes for the argument.
      longFormArgument   = toolAttributes.getLongFormArgument(information.argument)
      argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

      # Determine if this argument is greedy.
      isGreedy = information.isGreedy

      # Loop over the stub extensions and create a file node for each extension.
      for extension in information.stubExtensions:

        # Add the extensions to the attributes.
        argumentAttributes.extensions = [str(extension)]
        argumentAttributes.isGreedy   = isGreedy

        # Create th file node.
        self.addFileNode(str(nodeAddress + '.' + extension), str(nodeAddress))

        #TODO ERROR
        if extension not in allowedExtensions: print('graph.allStubArguments'); exit(0)

        # Add the edges.
        source = str(nodeAddress + '.' + extension) if information.isInput else taskAddress
        target = taskAddress if information.isInput else str(nodeAddress + '.' + extension)
        self.addEdge(source, target, argumentAttributes)

      # Link the pipeline configuration file nodes to the graph node.
      self.configurationFileToGraphNodeID[information.nodeID] = [str(nodeAddress + '.' + extension) for extension in information.stubExtensions]

  # If a set of shared configuration file nodes have no stubs, create the node and join to all of the tasks.
  def noStubArguments(self, superpipeline, nodeAddress, tasks, isFile):

    # Loop over the tasks, adding the necessary edges.
    for counter, information in enumerate(tasks):

      # Link the pipeline configuration file nodes to the graph node.
      self.configurationFileToGraphNodeID[information.nodeID] = [nodeAddress]

      # Get the argument attributes associated with this argument and add the edge.
      toolAttributes = superpipeline.getToolData(information.tool)

      # Get the long form of the argument and the associated attributes for the argument.
      longFormArgument   = toolAttributes.getLongFormArgument(information.argument)
      argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

      # Determine if this argument is greedy.
      argumentAttributes.isGreedy = information.isGreedy

      # Add the node to the graph.
      if isFile: self.addFileNode(str(nodeAddress), str(nodeAddress))
      else: self.addOptionNode(str(nodeAddress))

      # Add the edges.
      if information.isOutput: self.addEdge(information.taskAddress, nodeAddress, argumentAttributes)
      else: self.addEdge(nodeAddress, information.taskAddress, argumentAttributes)

  # If a set of shared configuration file nodes include some stubs with defined extensions to be shared, create
  # all the necessary nodes and join the correct nodes to the correct tasks.
  def someStubArguments(self, superpipeline, nodeAddress, tasks):

    # Loop over the tasks to find the stub extension associated with a stub node. All stub nodes sharing
    # this graph node must have the same stub extension.
    for information in tasks:
      if information.isStub:
        usedExtension = information.stubExtension
        break

    # Create the name of the node to create.
    modifiedNodeAddress = str(nodeAddress + '.' + usedExtension)
    self.addFileNode(modifiedNodeAddress, nodeAddress)

    # Loop over the tasks, adding the necessary edges.
    for information in tasks:

      # All of the arguments must be input or output files (since at least one of the arguments is a stub).
      # If an argument is not, there is a problem.
      if not information.isInput and not information.isOutput: print('graph.someStubsArguments'); exit(0)

      # Get the argument attributes associated with this argument and add the edge.
      toolAttributes = superpipeline.getToolData(information.tool)

      # Get the long form of the argument and the associated attributes for the argument.
      longFormArgument   = toolAttributes.getLongFormArgument(information.argument)
      argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

      # Determine if this argument is greedy.
      argumentAttributes.isGreedy = information.isGreedy

      # If the argument is a stub, ensure that the extension matches the stub extension.
      if information.isStub:
        if information.stubExtension != usedExtension: print('graph.someStubsArguments'); exit(0)

        # Initialise the entry in configurationFileToGraphNodeID. The created graph nodes for this configuration
        # file node will be added in the following loop over the extensions.
        self.configurationFileToGraphNodeID[information.nodeID] = []

        # Loop over the extensions associated with the stub, add nodes for the non-linked nodes and connect
        # all the nodes.
        for i, extension in enumerate(information.stubExtensions):

          # Add the extension to the attributes.
          stubArgumentAttributes                 = deepcopy(argumentAttributes)
          stubArgumentAttributes.extensions      = [str(extension)]
          stubArgumentAttributes.stubExtension   = str(extension)
          stubArgumentAttributes.primaryStubNode = True if i == 0 else False

          # Add the nodes associated with the stub that are not being linked to the other tasks,
          if extension != information.stubExtension: self.addFileNode(str(nodeAddress + '.' + extension), str(nodeAddress))

          # Add the edge.
          if information.isInput: self.addEdge(str(nodeAddress + '.' + extension), information.taskAddress, attributes = stubArgumentAttributes)
          elif information.isOutput: self.addEdge(information.taskAddress, str(nodeAddress + '.' + extension), attributes = stubArgumentAttributes)

          # Add the graph node ID to the list produced by this configuration file node.
          self.configurationFileToGraphNodeID[information.nodeID].append(str(nodeAddress + '.' + extension))

      # If this is not a stub, add the edge.
      else:
        if information.isInput: self.addEdge(modifiedNodeAddress, information.taskAddress, attributes = argumentAttributes)
        elif information.isOutput: self.addEdge(information.taskAddress, modifiedNodeAddress, attributes = argumentAttributes)

        # Link the pipeline configuration file nodes to the graph node.
        self.configurationFileToGraphNodeID[information.nodeID] = [modifiedNodeAddress]

  # Connect nodes and tasks as instructed in the pipeline configuration file.
  def connectNodesToTasks(self, superpipeline, pipeline):

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

          # Generate the node address (e.g. the output file for a task in the external pipeline).
          nodeAddress = str(taskAddress + '.' + taskArgument.split('--', 1)[-1])
          if nodeAddress in superpipeline.sharedNodeIDs or nodeAddress in superpipeline.uniqueNodeIDs: print('graph.connectNodesToTasks - 2'); exit(0)

          # Get the tool associated with this task.
          tool           = superpipeline.tasks[address + taskAddress]
          toolAttributes = superpipeline.getToolData(tool)

          # Get the long form of the argument and the associated attributes for the argument.
          longFormArgument   = toolAttributes.getLongFormArgument(taskArgument)
          argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

          # Determine if this is a filename stub.
          isStub = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
          if isStub: stubExtensions = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')    

          # Create the file node and connect it to the task for which it is an output.
          self.addFileNode(address + nodeAddress, address + nodeAddress)
          self.addEdge(address + taskAddress, address + nodeAddress, argumentAttributes)

          # Store the node ID for connecting to the target task node.
          sourceNodeIDs.append(str(address + nodeAddress))

      # Loop over the target nodes and join the sources to them.
      for target in pipeline.getTargets(nodeID):
        externalPipeline = pipeline.getNodeTaskAttribute(target, 'pipeline')
        externalNode     = pipeline.getNodeTaskAttribute(target, 'pipelineNodeID')
        task             = pipeline.getNodeTaskAttribute(target, 'task')
        taskArgument     = pipeline.getNodeTaskAttribute(target, 'taskArgument')

        # Get the tool and it's attributes associated with this argument.
        tool           = superpipeline.tasks[address + taskAddress]
        toolAttributes = superpipeline.getToolData(tool)

        # Get the long form of the argument and the associated attributes for the argument.
        longFormArgument   = toolAttributes.getLongFormArgument(taskArgument)
        argumentAttributes = toolAttributes.getArgumentData(longFormArgument)

        # Determine the pipeline relative task address.
        taskAddress = str(externalPipeline + '.' + task) if externalPipeline else str(task)

        # Connect all the source nodes to the target node.
        for sourceNodeID in sourceNodeIDs: self.graph.add_edge(sourceNodeID, address + taskAddress, attributes = argumentAttributes)

  # Generate a topologically sorted graph.
  #TODO
  def generateWorkflow(self):

    # Perform a topological sort of the graph.
    for nodeID in nx.topological_sort(self.graph):
      nodeType = getattr(self.graph.node[nodeID]['attributes'], 'nodeType')
      if nodeType == 'task': self.workflow.append(nodeID)

    # The topological sort does not always generate the correct order. In this routine, check for
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
          nextTask = self.workflow[counter + 1]

          # If this task outputs to the stream, determine what the next task should be.
          if self.getGraphNodeAttribute(task, 'isOutputStream'):
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
              for updateCount in range(0, counter + 1): updatedWorkflow.append(self.workflow[updateCount])
              updatedWorkflow.append(successorTasks[0])
              for updateTask in workflowMiddle: updatedWorkflow.append(updateTask)
              for updateTask in workflowEnd: updatedWorkflow.append(updateTask)

              # Update the workflow.
              self.workflow = updatedWorkflow

              # Reset the startCount. There is no need to loop over the entire workflow on the next
              # pass.
              startCount = counter
              break

    # Return the workflow.
    return self.workflow

  # Determine which graph nodes are required. A node may be used by multiple tasks and may be optional
  # for some and required by others. For each node, loop over all edges and check if any of the edges
  # are listed as required. If so, the node is required and should be marked as such.
  def markRequiredNodes(self, superpipeline):

    # Loop over all option nodes.
    for nodeID in self.getNodes('option'):

      # Loop over all successor nodes (option nodes cannot have any predecessors) and check if any of
      # the edges indicate that the node is required.
      for successor in self.graph.successors(nodeID):
        if self.getArgumentAttribute(nodeID, successor, 'isRequired'):
          self.setGraphNodeAttribute(nodeID, 'isRequired', True)
          break

    # Now perform the same tasks for file nodes.
    for nodeID in self.getNodes('file'):

      # File nodes can also have predecessors.
      isRequired = False
      for predecessor in self.graph.predecessors(nodeID):
        if self.getArgumentAttribute(predecessor, nodeID, 'isRequired'):
          self.setGraphNodeAttribute(nodeID, 'isRequired', True)
          isRequired = True
          break

      # If the node has already been listed as required, there is no need to check successors.
      if not isRequired:
        for successor in self.graph.successors(nodeID):
          if self.getArgumentAttribute(nodeID, successor, 'isRequired'):
            self.setGraphNodeAttribute(nodeID, 'isRequired', True)
            break

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addTaskParameterSets(self, superpipeline, setName):

    # Loop over the workflow.
    for task in self.workflow:
      tool = self.getGraphNodeAttribute(task, 'tool')

      # Loop over all of the arguments in the default parameter set.
      parameterSet = superpipeline.getToolParameterSet(tool, setName)
      arguments    = ps.parameterSets.SM_getArguments(parameterSet)
      for argument in arguments:
        values           = arguments[argument]
        toolData         = superpipeline.getToolData(tool)
        longFormArgument = toolData.getLongFormArgument(argument)

        # Determine if this argument is an input or output file.
        isInput  = toolData.getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = toolData.getArgumentAttribute(longFormArgument, 'isOutput')

        # Check if this edge exists.
        edges = self.checkIfEdgeExists(task, longFormArgument, not isOutput)

        # Get the attributes for the edge.
        argumentAttributes = toolData.getArgumentData(longFormArgument)

        # If no edges were found, create a new node, add the edges and values.
        if not edges:

          # Create a name for the node. This should be the name of the current task with the argument
          # appended (dashes removed).
          address = str(task) + '.'
          nodeAddress = task + '.' + longFormArgument.split('--', 1)[-1]

          # Create the node.
          if isInput or isOutput: self.addFileNode(nodeAddress, nodeAddress)
          else: self.addOptionNode(nodeAddress)

          # Add the values to the created node.
          self.setGraphNodeAttribute(nodeAddress, 'values', values)

          # Add the edge.
          if isOutput: self.addEdge(str(task), str(nodeAddress), argumentAttributes)
          else: self.addEdge(str(nodeAddress), str(task), argumentAttributes)

        # If a single possible edge was found, populate the relevant node with the values.
        elif len(edges) == 1: self.setGraphNodeAttribute(edges[0], 'values', values)

        # If multiple edges were found, there are multiple nodes associated with this task using the
        # defined argument.
        #FIXME
        else: print('NOT HANDLED PARAMETER SET WITH MULTIPLE EDGES.'); exit(0)

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addPipelineParameterSets(self, superpipeline, setName):
    for tier in reversed(superpipeline.pipelinesByTier.keys()):
      for pipelineName in superpipeline.pipelinesByTier[tier]: self.addParameterSet(superpipeline, pipelineName, setName)

  # Add the values from a pipeline parameter set to the graph.
  def addParameterSet(self, superpipeline, pipelineName, setName):
    parameterSet = superpipeline.getPipelineParameterSet(pipelineName, setName)

    # If the parameter set is not available, there is a problem.
    if not parameterSet: print('addPipelineParameterSets - no set:', setName); exit(0)

    # Loop over the nodes in the parameter set.
    nodeIDs = ps.parameterSets.SM_getNodeIDs(parameterSet)
    for nodeID in nodeIDs:
      values       = nodeIDs[nodeID]
      pipelineData = superpipeline.getPipelineData(pipelineName)
      nodeAddress  = pipelineData.address + '.' + nodeID if pipelineData.address else nodeID

      # Check that the nodeAddress is valid.
      if nodeAddress not in self.configurationFileToGraphNodeID:
        ID = ps.parameterSets.SM_getDataAttributeFromNodeID(parameterSet, nodeID, 'id')
        pse.parameterSetErrors().invalidNodeInPipelineParameterSet(pipelineName, setName, nodeID, ID)

      # Set the values for the graph node.
      for graphNodeID in self.configurationFileToGraphNodeID[nodeAddress]: self.setGraphNodeAttribute(graphNodeID, 'values', values)

  # Loop over all of the nodes for which arguments are defined on the command line and create the nodes
  # that are missing.
  def attachArgumentValuesToNodes(self, superpipeline, args, arguments, nodeList):

    # Loop over all of the set pipeline arguments.
    for argument in arguments:
      values       = arguments[argument]
      graphNodeIDs = args.arguments[argument].graphNodeIDs
      for graphNodeID in graphNodeIDs: self.setGraphNodeAttribute(graphNodeID, 'values', values)

    # Loop over the list of nodes and extract those for which a node requires creating.
    for taskAddress, nodeAddress, tool, argument, values, isCreate in nodeList:

      # Get the tool data.
      toolData = superpipeline.toolConfigurationData[tool]

      # If the node required creating, create it and add the edges.
      if isCreate:

        # Get the attributes associated with the argument. These will be added to the graph edge.
        argumentAttributes = toolData.getArgumentData(argument)

        # Determine if this argument is an input or an output.
        isInput  = toolData.getArgumentAttribute(argument, 'isInput')
        isOutput = toolData.getArgumentAttribute(argument, 'isOutput')

        # Determine if the argument is a stub.
        isStub         = toolData.getArgumentAttribute(argument, 'isStub')
        stubExtensions = toolData.getArgumentAttribute(argument, 'stubExtensions')

        # Define the node attributes.
        if isInput or isOutput: nodeAttributes = dataNodeAttributes('file')
        else: nodeAttributes = dataNodeAttributes('option')

        # Attach the values to the node attributes.
        nodeAttributes.values = values

        # Add the node (or nodes if this is a stub).
        if isStub:
          for extension in stubExtensions:
            modifiedNodeAddress = str(nodeAddress + '.' + extension)
            self.addFileNode(modifiedNodeAddress, nodeAddress)

            # Add the edge.
            if isOutput: self.addEdge(taskAddress, modifiedNodeAddress, argumentAttributes)
            else: self.addEdge(modifiedNodeAddress, taskAddress, argumentAttributes)

        # If this is not a stub, add a single node.
        else:
          self.addFileNode(nodeAddress, nodeAddress)

          # Add the edge.
          if isOutput: self.addEdge(taskAddress, nodeAddress, argumentAttributes)
          else: self.addEdge(nodeAddress, taskAddress, argumentAttributes)

      # If the node already exists, just add the values to the node.
      else: self.setGraphNodeAttribute(nodeAddress, 'values', values)

  # Expand lists of arguments attached to nodes.
  def expandLists(self):
    nodeIDs = []

    # First, check all of the option nods.
    for nodeID in self.getNodes('file'): nodeIDs.append((nodeID, 'file'))
    for nodeID in self.getNodes('option'): nodeIDs.append((nodeID, 'option'))

    # Loop over all the option and file nodes.
    for nodeID, nodeType in nodeIDs:

      # Only look at option nodes or file nodes that are predecessors to a task, but are not simultaneously
      # successors of other tasks.
      isSuccessor = True if self.graph.predecessors(nodeID) else False
      if (nodeType == 'option') or (nodeType == 'file' and not isSuccessor):
        values = self.getGraphNodeAttribute(nodeID, 'values')
  
        # Loop over the values and check if any of them end in '.list'. If so, this is a list of values which should be
        # opened and all the values added to the node.
        modifiedValues = []
        for value in values:
  
          # If this is a list.
          if str(value).endswith('.list'):
  
            # Open the file and terminate if it doesn't exist.
            data = fh.fileHandling.openFileForReading(value)
            #TODO ERROR
            if not data: print('graph.expandLists - FILE DOESN\'T EXIST', value); exit(0)
  
            # Loop over the values in the file, stripping off whitespace.
            for dataValue in [name.strip() for name in data]: modifiedValues.append(dataValue)
  
          # If the value does not end with '.list', add it to the modifiedValues list.
          else: modifiedValues.append(value)
  
        # Replace the values with the modifiedValues.
        self.setGraphNodeAttribute(nodeID, 'values', modifiedValues)

  # Loop over all inputs to each task and determine if any of them are listed as greedy. If so, mark the task
  # as greedy.
  def markGreedyTasks(self, superpipeline):

    # Loop over all the tasks.
    for task in self.workflow:

      # Get the tool associated with the task.
      tool = superpipeline.tasks[task]
  
      # Loop over the input files.
      for fileNodeID in self.getInputFileNodes(task):
  
        # Determine the tool argument that uses the values from this node.
        argument = self.getArgumentAttribute(fileNodeID, task, 'longFormArgument')
  
        # Check the greedy attribute for the task and update if necessary.
        if self.getArgumentAttribute(fileNodeID, task, 'isGreedy'):
          #TODO ERROR
          if not superpipeline.toolConfigurationData[tool].getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - GREEDY'); exit(0)
  
          # Mark the task node to indicate that this task is greedy.
          self.setGraphNodeAttribute(task, 'isGreedy', True)

  # Loop over all of the tasks in the workflow and construct missing filenames where there are instructions to do so. In
  # addition, where multiple options are provided to a task, the task is divided into multiple tasks and handling of input
  # and output files and their relation to other tasks is handled.
  def constructFiles(self, superpipeline):

    # Loop over all of the tasks in the pipeline.
    for task in self.workflow:

      # Store information on the tool used to execute this task.
      tool     = self.getGraphNodeAttribute(task, 'tool')
      toolData = superpipeline.getToolData(tool)

      # Determine if the task is accepting values that are part of a division.
      divisions             = self.isTaskInDivision(task)
      isFirstTaskInDivision = False

      # Check if any of the arguments for this task have been identified as greedy. If so, check
      # that the argument is valid for the tool.
      greedyArgument = self.getGreedyArgument(superpipeline, task)
      if greedyArgument:
        self.setGraphNodeAttribute(task, 'isGreedy', True)
        self.setGraphNodeAttribute(task, 'greedyArgument', greedyArgument)

      # Determine general information about this task.
      consolidate = self.getGraphNodeAttribute(task, 'consolidate')

      # Determine the number of values provided to all arguments for this task.
      values = self.getArgumentValues(task)

      # Loop over all arguments with multiple values and ensure that they are valid.
      for argument in values:

        # If this task is already part of a division, it is not permitted for any option nodes to have multiple
        # values, unless these options are all to be applied to the same command line.
        if values[argument].type == 'option':
          if divisions > 1 and not toolData.getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - graph.constructFiles - division error', task, argument); exit(1)
          else:

            # If this task is split into divisions, set the number of divisions and mark this task as the task that
            # splits into divisions. This task breaks the graph into divisions and subsequent tasks either consolidate
            # the divisions, or act on the divisions already defined.
            # 
            # Note that only a single node can be supplied.
            divisions             = values[argument].noValues
            isFirstTaskInDivision = True
            if len(values[argument].nodeIDs) != 1: print('ERROR - graph.constructFiles - division error 2', values[argument].nodeIDs); exit(1)
            else: divisionNode = values[argument].nodeIDs[0]

      # Set the graph node divisions value. Note that if this task consolidates divisions, then there should only be a
      # single division. All of the outputs from the previous divisions are used in a greedy fashion by this task and so
      # the divisions are ended.
      if consolidate: divisions = 1
      self.setGraphNodeAttribute(task, 'divisions', divisions)

      # Check that all of the input files have their names defined. If not, check to see if instructions exist to 
      # construct the filenames. Note that no account of divisions has been taken yet. Any inputs to the task that
      # have been generated through divisions, must have been the output of a previous task. In this case, the values
      # have already been defined and so the input construction is unnecessary.
      self.checkInputFiles(superpipeline, task)

      # If this task consolidates the divisions, perform the necessary joining of data.
      if consolidate: self.consolidateDivisions(superpipeline, task)

      # If this task has multiple divisions and it isn't greedy (i.e. the task is not being run once using values from 
      # all divisions on the command line), the task node needs to duplicated so that there are as many task nodes as
      # there are divisions.
      elif divisions > 1:
        self.divideTask(superpipeline, task, divisions, divisionNode)

        # If this task breaks into divisions, it's input file nodes are not already broken into divisions. The only
        # required task is to generate the output files.
        if isFirstTaskInDivision:
          self.buildDivisionOutputFiles(superpipeline, task, divisions, divisionNode, greedyArgument)
          self.setGraphNodeAttribute(divisionNode, 'isCreateDivision', True)

        # If a previous task broke the graph into divisions, there already exist multiple file nodes for the input
        # files. The input file nodes need to connect to the correct task node and then the outputs for that task
        # need to be created.
        else: 
          self.connectDivisionInputs(task)
          self.extendDivisionOutputFiles(superpipeline, task)

      # If there are no divisions, no new task nodes need to be constructed, or equivalently, no new output nodes. The
      # existing output nodes need to be checked to ensure that they contain the correct number of values.
      else: self.checkOutputFiles(superpipeline, task, greedyArgument)

  # Loop over all input file nodes and check if any are marked as being a parent node. If so, this node has
  # multiple children, defined as a division. Return the number of divisions.
  def isTaskInDivision(self, task):
    for nodeID in self.getInputFileNodes(task):
      if self.getGraphNodeAttribute(nodeID, 'isParent'): return self.getGraphNodeAttribute(nodeID, 'divisions')

    # If no parent nodes were found, there are no divisions, so return 1.
    return 1

  # Check if a pipeline task has any greedy arguments and, if so, check that it is valid.
  def getGreedyArgument(self, superpipeline, task):
    greedyArgument = self.getGraphNodeAttribute(task, 'greedyArgument')
    if not greedyArgument: return None

    # Check that the argument is a valid argument for the tool.
    tool     = self.getGraphNodeAttribute(task, 'tool')
    toolData = superpipeline.getToolData(tool)

    # Determine the long form version of the greedy argument and check if this allows multiple values.
    longFormArgument = toolData.getLongFormArgument(greedyArgument)
    if not longFormArgument: pce.pipelineErrors().invalidGreedyArgument(superpipeline.pipeline, task, tool, greedyArgument)
    if not toolData.getArgumentAttribute(longFormArgument, 'allowMultipleValues'): pce.pipelineErrors().greedySingleValueArgument(superpipeline.pipeline, task, tool, greedyArgument)

    return longFormArgument

  # For the specified task, loop over all arguments and determine the number of values provided to each.
  def getArgumentValues(self, task):

    # Define a data structure to hold information on the arguments.
    class argumentValues:
      def __init__(self, isInput, noValues, nodeType, nodeID):
        self.isInput  = isInput
        self.nodeIDs  = [nodeID]
        self.noValues = noValues
        self.type     = nodeType

    # Initialise variables.
    nodeIDs = []
    values  = {}

    # Loop over all of the predecessor nodes.
    for nodeID in self.graph.predecessors(task): nodeIDs.append((nodeID, True))
    for nodeID in self.graph.successors(task): nodeIDs.append((nodeID, False))

    # Loop over all nodes attached to the task.
    for nodeID, isInput in nodeIDs:
      argument = self.getArgumentAttribute(nodeID, task, 'longFormArgument') if isInput else self.getArgumentAttribute(task, nodeID, 'longFormArgument')
      nodeType = self.getGraphNodeAttribute(nodeID, 'nodeType')
      noValues = len(self.getGraphNodeAttribute(nodeID, 'values'))

      # If this is the first observation of this argument, store the values.
      if argument not in values: values[argument] = argumentValues(isInput, noValues, nodeType, nodeID)
      else:
        assert nodeType == values[argument].type
        assert isInput == values[argument].isInput
        values[argument].noValues += noValues
        values[argument].nodeIDs.append(nodeID)

    # Only arguments with more than one value are of interest. If the argument has zero or one value, these
    # can be simply applied on the command line without consideration of subphases or divisions.
    remove = []
    inputs = []
    for argument in values:
      if values[argument].noValues < 2: remove.append(argument)
      elif values[argument].isInput and values[argument].type == 'file': inputs.append(argument)
    for argument in remove: del(values[argument])

    # It is not permitted for a single task to have multiple input arguments with multiple values except
    # for the following cases:
    #
    # 1. A
    # FIXME
    if len(inputs) > 1: print('graph.getArgumentValues - MULTIPLE INPUT ARGUMENTS WITH MULTIPLE VALUES _ NEED TO HANDLE'); exit(0)

    # Return the argument information.
    return values

  # If the task is taking as input values from all previous divisions, thus terminating the division, 
  def consolidateDivisions(self, superpipeline, task):
    tool     = self.getGraphNodeAttribute(task, 'tool')
    toolData = superpipeline.getToolData(tool)

    # Loop over the output nodes for the task and find the outputs that need constructing.
    for nodeID in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeID, 'values'):

        # Get instructions for building the output file names.
        instructions = self.getArgumentAttribute(task, nodeID, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkOutputFiles - 1'); exit(1)
  
        # Loop over all predecessor nodes looking for the division parent node.
        for predecessor in self.graph.predecessors(task):
  
          # If this node is a parent node, get the argument and check that the tool accepts multiple values for it.
          if self.getGraphNodeAttribute(predecessor, 'isParent'): 
            argument = self.getArgumentAttribute(predecessor, task, 'longFormArgument')
    
            #TODO ERROR
            if not toolData.getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - graph.consolidateDivisions'); exit(1)
    
            # Construct the filename according to the requested method. Note that the values can be constructed by only considering
            # the parent node since this contains all information about the subphases. The child file nodes contain the same values, but
            # with different text segments describing the division. These text segments are removed, so all child nodes would result in
            # the same set of values. This is as desired, since the output of this task (since it is consolidating all the division information),
            # should be the same number of values as there are subphases.
            if instructions['method'] == 'from tool argument':
          
              # Remove the text that was added to the filename to distinguish between the different divisions.
              values = [value.replace(self.getGraphNodeAttribute(predecessor, 'divisionText'), '') for value in self.getGraphNodeAttribute(predecessor, 'values')]
              self.setGraphNodeAttribute(nodeID, 'values', construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeID, values))

          # Now link all of the outputs from the previous division nodes to this task.
          for child in self.getGraphNodeAttribute(predecessor, 'children'): self.graph.add_edge(child, task, attributes = deepcopy(self.getEdgeAttributes(predecessor, task)))

  # For a task that has multiple divisions, divide the task up so that there exists a task node for each division.
  def divideTask(self, superpipeline, task, divisions, divisionNode):

    # Create the new task nodes.
    children = []
    for i in range(1, divisions):
      taskID = str(task + str(i))

      # Make a copy of the task node attributes and update.
      attributes              = deepcopy(self.getNodeAttributes(task))
      attributes.isChild      = True
      attributes.parent       = task
      attributes.divisions    = divisions
      attributes.divisionID   = i
      attributes.divisionNode = divisionNode
      self.addTaskNode(superpipeline, taskID, task, attributes)

      # Connect all task predecessors to the new node. Succesors will be dealt with later.
      for nodeID in self.graph.predecessors(task): self.addEdge(nodeID, taskID, deepcopy(self.getEdgeAttributes(nodeID, task)))

      # Keep track of the child nodes.
      children.append(taskID)

    # Update the parent node.
    self.setGraphNodeAttribute(task, 'isParent', True)
    self.setGraphNodeAttribute(task, 'children', children)
    self.setGraphNodeAttribute(task, 'divisions', divisions)

  # For tasks whose inputs come from a task that was split into divisions, connect the inputs to the new nodes.
  def connectDivisionInputs(self, task):

    # Populate the list of tasks that need the inputs defining.
    taskNodes = self.getGraphNodeAttribute(task, 'children')

    # Loop over all predecessor nodes and identify the parent file node. This is the original node for the values
    # associated with the division. As parent, this node will have the children identified and it is these that
    # need to be connected to theirr relevant tasks.
    parentNode = None
    children   = []
    for predecessor in self.graph.predecessors(task):
      if self.getGraphNodeAttribute(predecessor, 'isParent'):
        parentNode = predecessor
        fileNodes  = self.getGraphNodeAttribute(parentNode, 'children')
        assert len(taskNodes) == len(fileNodes)
        break

    # Loop over the file nodes and link them to their respective task node. In addition, remove the edge connecting
    # the parent node to the task.
    for fileNode, taskNode in zip(fileNodes, taskNodes):
      attributes = deepcopy(self.getEdgeAttributes(parentNode, task))
      self.graph.add_edge(str(fileNode), str(taskNode), attributes = attributes)
      self.graph.remove_edge(parentNode, taskNode)

  # Loop over all the input files for the task and check how many have been defined. If the number of set files
  # is inconsistent with the number of executions implied by the values given to the task options, terminate.
  def checkInputFiles(self, superpipeline, task):

    # Get the tool associated with the task.
    tool = superpipeline.tasks[task]

    # Loop over the input files.
    for fileNodeID in self.getInputFileNodes(task):

      # Determine the tool argument that uses the values from this node.
      argument = self.getArgumentAttribute(fileNodeID, task, 'longFormArgument')
      values   = self.getGraphNodeAttribute(fileNodeID, 'values')

      # Check the greedy attribute for the task and update if necessary.
      if self.getArgumentAttribute(fileNodeID, task, 'isGreedy'):
        #TODO ERROR
        if not superpipeline.toolConfigurationData[tool].getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - GREEDY'); exit(0)

        # Mark the task node to indicate that this task is greedy.
        self.setGraphNodeAttribute(task, 'isGreedy', True)

      # If there are no set values, check to see if there are instructions on how to construct the filenames. If
      # so, construct the files.
      if len(values) == 0:

        # Determine if the argument has filename construction instructions.
        constructUsingNode = self.getGraphNodeAttribute(fileNodeID, 'constructUsingNode')
        if constructUsingNode:
          baseValues = self.getGraphNodeAttribute(constructUsingNode, 'values')
          self.setGraphNodeAttribute(fileNodeID, 'values', construct.constructInputNode(self.graph, superpipeline, task, argument, fileNodeID, baseValues))

  # Loop over all output file nodes (for tasks with no divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def checkOutputFiles(self, superpipeline, task, greedyArgument):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeID in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeID, 'values'):
        instructions = self.getArgumentAttribute(task, nodeID, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkOutputFiles - 1'); exit(1)

        # Construct the filename according to the requested method.
        if instructions['method'] == 'from tool argument':

          # Get the values from which to construct the filenames. If there are multiple values, but only a single
          # execution, use the first value for constructing the filenames.
          baseValues = self.getBaseValues(superpipeline, instructions, task)

          # If the input argument being used to construct the output filenames is the greedy argument, then this
          # means that there should only be a single output (not an output for each of the input arguments). In
          # this case, reset the base values to be a list that only contains the first value from the input
          # argument.
          if instructions['use argument'] == greedyArgument: baseValues = [baseValues[0]]

          # Construct the output filenames.
          values = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeID, baseValues)

          # Having constructed the output filenames, add them to the node.
          self.setGraphNodeAttribute(nodeID, 'values', values)

        # If the construction method is unknown, terminate.
        # TODO ERROR
        else: print('constructFilenames.constructFilenames - unknown method', instructions.method); exit(0)

  # Loop over all output file nodes (for tasks with divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def buildDivisionOutputFiles(self, superpipeline, task, divisions, divisionNode, greedyArgument):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeID in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeID, 'values'):
        instructions = self.getArgumentAttribute(task, nodeID, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkDivisionOutputFiles - 1'); exit(1)

        # Construct the filename according to the requested method.
        if instructions['method'] == 'from tool argument':

          # Get the values from which to construct the filenames. If there are multiple values, but only a single
          # execution, use the first value for constructing the filenames.
          if greedyArgument: baseValues = [self.getBaseValues(superpipeline, instructions, task)[0]]
          else: baseValues = self.getBaseValues(superpipeline, instructions, task)

          # Get the argument and values associated with the node that has forced the divisions.
          argument       = self.getArgumentAttribute(divisionNode, task, 'longFormArgument')
          divisionValues = self.getGraphNodeAttribute(divisionNode, 'values')
          assert len(divisionValues) == divisions
          self.setGraphNodeAttribute(nodeID, 'divisions', divisions)

          # Loop over the base values (except the first - that will be dealt with at the end when updating the file node
          # that already exists), construct the output filenames, then build and add the node with an edge from the task.
          children = []
          for i in range(1, len(divisionValues)):

            # Define the name of the new node.
            fileNodeID = nodeID + str(i)
            taskNodeID = task + str(i)

            # Construct the filenames for this node. If this is the task that has first split into divisions, the argument
            # and value for the division needs to be built into the filename. If this is a task following on from the task
            # that created the divisions, this is not required.
            values       = construct.addDivisionToValue(self.graph, superpipeline, task, nodeID, instructions, baseValues, argument, divisionValues[i])
            divisionText = str('_' + argument.strip('-') + str(divisionValues[i]))

            # Copy the attributes from the existing node and update the values.
            attributes              = deepcopy(self.getNodeAttributes(nodeID))
            attributes.values       = values
            attributes.divisionID   = i
            attributes.isChild      = True
            attributes.parent       = nodeID
            attributes.divisionText = divisionText

            # Add the node to the list of children.
            children.append(fileNodeID)

            # Add the new file node.
            self.graph.add_node(str(fileNodeID), attributes = attributes)

            # Make a copy of the edge attributes and join the new file node to its task.
            self.graph.add_edge(str(taskNodeID), str(fileNodeID), attributes = deepcopy(self.getEdgeAttributes(task, nodeID)))

          # Now perform the same tasks for the existing node.
          values       = construct.addDivisionToValue(self.graph, superpipeline, task, nodeID, instructions, baseValues, argument, divisionValues[0])
          divisionText = str('_' + argument.strip('-') + str(divisionValues[0]))
          self.setGraphNodeAttribute(nodeID, 'values', values)
          self.setGraphNodeAttribute(nodeID, 'children', children)
          self.setGraphNodeAttribute(nodeID, 'divisionID', 0)
          self.setGraphNodeAttribute(nodeID, 'divisionText', divisionText)
          self.setGraphNodeAttribute(nodeID, 'isParent', True)

        # If the construction method is unknown, terminate.
        # TODO ERROR
        else: print('constructFilenames.constructFilenames - unknown method', instructions.method); exit(0)

  # Loop over all output file nodes (for tasks with divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def extendDivisionOutputFiles(self, superpipeline, task):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeID in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeID, 'values'):
        instructions = self.getArgumentAttribute(task, nodeID, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkDivisionOutputFiles - 1'); exit(1)

        # Construct the filename according to the requested method.
        if instructions['method'] == 'from tool argument':
          divisions  = self.getGraphNodeAttribute(task, 'divisions')

          # Get the argument and values associated with the node that has forced the divisions.
          self.setGraphNodeAttribute(nodeID, 'divisions', divisions)

          # Loop over the children of the task and determine their values.
          children = []
          for i, child in enumerate(self.getGraphNodeAttribute(task, 'children')):
            childValues = self.getBaseValues(superpipeline, instructions, child)
            values      = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeID, childValues)

            # Define the name of the new node.
            fileNodeID = nodeID + str(i + 1)

            # Get the additional text that was added to the filename.
            divisionText = self.getDivisionText(child)

            # Get a copy of the existing file node attributes along with the attributes for the output edge.
            nodeAttributes = deepcopy(self.getNodeAttributes(nodeID))
            edgeAttributes = deepcopy(self.getEdgeAttributes(task, nodeID))

            # Update the node attributes and add the node to the graph.
            nodeAttributes.values       = values
            nodeAttributes.divisionID   = i + 1
            nodeAttributes.isChild      = True
            nodeAttributes.parent       = nodeID
            nodeAttributes.divisionText = divisionText
            self.graph.add_node(str(fileNodeID), attributes = nodeAttributes)
            children.append(fileNodeID)

            # Join the task to the file node.
            self.graph.add_edge(child, fileNodeID, attributes = edgeAttributes)

          # Now perform the same tasks for the existing file node.
          baseValues   = self.getBaseValues(superpipeline, instructions, task)
          values       = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeID, baseValues)
          divisionText = self.getDivisionText(task)
          self.setGraphNodeAttribute(nodeID, 'values', values)
          self.setGraphNodeAttribute(nodeID, 'children', children)
          self.setGraphNodeAttribute(nodeID, 'divisionID', 0)
          self.setGraphNodeAttribute(nodeID, 'divisionText', divisionText)
          self.setGraphNodeAttribute(nodeID, 'isParent', True)

        # If the construction method is unknown, terminate.
        # TODO ERROR
        else: print('constructFilenames.constructFilenames - unknown method', instructions.method); exit(0)

  # Find all of the predecessor nodes to a task that use a given argument and add the values to a list.
  def getBaseValues(self, superpipeline, instructions, task):
    values = []
          
    # Get the input file from which the filenames should be built.
    try: argument = instructions['use argument']
    except: print('ERROR - graph.getBaseValues - 1'); exit(1)
          
    # Get tool information from the superpipline and determine the long form of the argument defined in the
    # instructions.
    tool             = self.getGraphNodeAttribute(task, 'tool')
    longFormArgument = superpipeline.toolConfigurationData[tool].getLongFormArgument(argument)
          
    # Search predecessor nodes.
    for predecessorID in self.getPredecessors(task):
      predecessorArgument = self.getArgumentAttribute(predecessorID, task, 'longFormArgument')
      if predecessorArgument == longFormArgument:
        for value in self.getGraphNodeAttribute(predecessorID, 'values'): values.append(value)

    # Return the values.
    return values

  # Find the text added to the filenames in the divisions.
  def getDivisionText(self, task):

    # Loop over the inputs to the task, looking for the 
    for predecessor in self.graph.predecessors(task):
      text = self.getGraphNodeAttribute(predecessor, 'divisionText')
      if text: return text

    # If no input nodes have the divisionText defined, return False.
    return False

  # Check that tasks listed as streaming can be streamed in te pipeline.
  def checkStreams(self, superpipeline):
    for task in self.workflow:

      # Determine if this task has multiple subphases. This means that it either generates multiple output nodes
      # or it has multiple task calls.
      isGeneratesMultipleNodes = self.getGraphNodeAttribute(task, 'generateMultipleOutputNodes')
      isMultipleTaskCalls      = self.getGraphNodeAttribute(task, 'multipleTaskCalls')

      # Check if the task outputs to a stream.
      if self.getGraphNodeAttribute(task, 'isOutputStream'):

        # Get the tool configuration data.
        tool     = self.getGraphNodeAttribute(task, 'tool')
        toolData = superpipeline.toolConfigurationData[tool]

        # Loop over all of the output nodes for this task and determine the output that can be streamed.
        # There can only be a single streaming output node.
        outputStreamNodeIDs = {}
        for nodeID in self.graph.successors(task):
          streamInstructions = self.getArgumentAttribute(task, nodeID, 'outputStreamInstructions')
          if streamInstructions:
            if nodeID not in outputStreamNodeIDs: outputStreamNodeIDs[nodeID] = []
            outputStreamNodeIDs[nodeID].append(streamInstructions)
            self.setArgumentAttribute(task, nodeID, 'isStream', True)

            # Mark the file node which is being streamed.
            self.setGraphNodeAttribute(nodeID, 'isStream', True)

        # If no arguments were found that can output to a stream, terminate.
        if not outputStreamNodeIDs: pce.pipelineErrors().noOutputStreamArgument(task, tool)

        # Any individual task can only produce a single output stream, however, if this task generates multiple
        # outputs, or is executed multiple times, each of the separate subphases can output to a stream. Check
        # that any tasks with multiple output streams conform to this requirement.
        if len(outputStreamNodeIDs) > 1:
          #TODO ERROR
          if not isGeneratesMultipleNodes and not isMultipleTaskCalls: print('MULTIPLE OUTPUT STREAM - graph.checkStreams - 2'); exit(1)

        # If the nodes stored in streamNodeIDs can be used as streaming nodes, they must also be inputs to
        # other tasks in  the pipeline and the have instructions on how the values should be used when the
        # input is a stream. Check that this is the case.
        inputStreamNodeIDs = {}
        for nodeID in outputStreamNodeIDs:

          # If the node has no successors, it cannot be streamed.
          #TODO ERROR
          if not self.graph.successors(nodeID): print('ERROR - NO TASK TO STREAM TO. graph.checkStreams - 3'); exit(1)

          # Loop over all tasks that are successors to this node and check that one and only one of these
          # tasks is marked as accepting a stream as input.
          for successorTask in self.graph.successors(nodeID):
            isInputStream      = self.getGraphNodeAttribute(successorTask, 'isInputStream')
            streamInstructions = self.getArgumentAttribute(nodeID, successorTask, 'inputStreamInstructions')
            successorTool      = self.getGraphNodeAttribute(successorTask, 'tool')

            # If this task is marked as accepting a stream and the argument has instructions on how to handle a
            # streaming input, store the task and mark the edge as a stream.
            if isInputStream and streamInstructions:

              # Each nodeID can only have a single output node to stream to. If the node ID is already in the
              # inputStreamNodeIDs, this is not the case,
              if nodeID in inputStreamNodeIDs: print('ERROR - Multiple OUPTUT STREAM - graph.checkStreams - 3b'); exit(1)
              inputStreamNodeIDs[nodeID] = successorTask
              self.setArgumentAttribute(nodeID, successorTask, 'isStream', True)

            # If the input is a stream and there are no instructions on how to process the argument, fail.
            if isInputStream and not streamInstructions: pce.pipelineErrors().noStreamInstructions(task, tool, successorTask, successorTool)

        # If there are no nodes accepting a stream, then the pipeline cannot work.
        if not inputStreamNodeIDs: pce.pipelineErrors().noNodeAcceptingStream(task, tool)

        # If there are multiple nodes accepting a stream, this is only allowed if there are multiple subphases and
        # the original task outputting to the stream itself outputs to multiple streams. If there are multiple
        # streams, check that each node ID in the outputStreamNodeIDs has an equivalent in the inputStreamNodeIDs.
        if len(inputStreamNodeIDs) > 1:

          # TODO ERROR
          if len(inputStreamNodeIDs) != len(outputStreamNodeIDs): print('ERROR - DIFFERENT NUMBER OF NODES - graph.checkStreams - 5') ;exit(1)
          for nodeID in inputStreamNodeIDs:
            #TODO ERROR
            if nodeID not in outputStreamNodeIDs: print('ERROR - INCONSISTENT STREAMS - graph.checkStreams - 6'); exit(1)

        # The topological sort of the pipeline could produce a workflow that is inconsistent with the
        # streams. For example, there could be two tasks following the task outputting to a stream and
        # from a topological point of view, neither task is required to come first. The non-uniqueness
        # of the sort could choose either of these tasks to succeed the task outputting to a stream.
        # From the point of view of the pipeline operation, however, it is imperative that the task
        # accepting the stream should follow the task outputting to a stream.
        for nodeID in outputStreamNodeIDs:
          successorTask = inputStreamNodeIDs[nodeID]

          # If there are multiple nodes, this is because there are multiple subphases. There is only a need to check the
          # main node (not all the daughter nodes) since the workflow does not contain the daughter nodes.
          if not self.getGraphNodeAttribute(nodeID, 'isDaughterNode'):
            if self.workflow.index(successorTask) != self.workflow.index(task) + 1: print('ERROR - UPDATE WORKFLOW - graph.checkStreams - 7'); exit(1)

  # Determine after which task intermediate files should be deleted.
  def deleteFiles(self):

    # Loop over all file nodes looking for those marked as intermediate.
    for nodeID in self.getNodes('file'):
      if self.getGraphNodeAttribute(nodeID, 'isIntermediate'):

        # If this node is the daughter of another node (e.g. the task has been split into multiple tasks for
        # each of a set of inputs), the task nodes associated with it will not be in the workflow. If this is
        # the case, strip off the extension (-i) from the end of the nodeID and use the original value for the
        # following method. After determining the task, append the original extension, checking that the
        # resulting task exists. If the task consolidates outputs, the extension is not required.
        if self.getGraphNodeAttribute(nodeID, 'isDaughterNode'):
          splitNodeID = nodeID.rsplit('-', 1)
          useNodeID   = splitNodeID[0]
          extension   = str('-' + splitNodeID[1])
        else: useNodeID = nodeID

        # Get all the task nodes that use this node.
        taskNodeIDs = self.graph.successors(useNodeID)

        # Determine which of these tasks is the latest task in the pipeline.
        index = 0
        for taskNodeID in taskNodeIDs: index = max(index, self.workflow.index(taskNodeID))
        task = self.workflow[index]

        # Append the original extension and check if the task exists.
        if self.getGraphNodeAttribute(nodeID, 'isDaughterNode'): task = str(task + extension) if str(task + extension) in self.graph else task

        # Set the 'deleteAfterTask' value for the node to the task after whose execution the file should
        # be deleted.
        self.setGraphNodeAttribute(nodeID, 'deleteAfterTask', task)

  ########################################
  ##  Methods for modifying the graph.  ##
  ########################################

  # Add a task node to the graph.
  def addTaskNode(self, superpipeline, task, parentTask, attributes):

    # Mark the node for plotting.
    attributes.includeInReducedPlot = superpipeline.tasksInPlot[parentTask]

    # Add the node to the graph.
    self.graph.add_node(task, attributes = attributes)

  # Add a file node to the graph.
  def addFileNode(self, graphNodeID, configurationFileNodeID):
    nodeAttributes = dataNodeAttributes('file')

    # Add the configuration file node address to the attributes.
    nodeAttributes.configurationFileNodeIDs = [configurationFileNodeID]

    # Add the node to the graph, if it does not already exist.
    if graphNodeID not in self.graph: self.graph.add_node(str(graphNodeID), attributes = nodeAttributes)

    # If the node already exists, add the configuration file node ID to the node attributes.
    else:
      linkedConfigurationFileNodeIDs = self.getGraphNodeAttribute(graphNodeID, 'configurationFileNodeIDs')
      if configurationFileNodeID not in linkedConfigurationFileNodeIDs:
        linkedConfigurationFileNodeIDs.append(configurationFileNodeID)
        self.setGraphNodeAttribute(graphNodeID, 'configurationFileNodeIDs', linkedConfigurationFileNodeIDs)

    # Link this configuration node ID with the created graph node ID.
    if configurationFileNodeID not in self.configurationFileToGraphNodeID:
      self.configurationFileToGraphNodeID[configurationFileNodeID] = [graphNodeID]
    else: self.configurationFileToGraphNodeID[configurationFileNodeID].append(graphNodeID)

  # Add an option node to the graph.
  def addOptionNode(self, graphNodeID):
    nodeAttributes = dataNodeAttributes('option')

    # Add the configuration file node address to the attributes.
    nodeAttributes.configurationFileNodeIDs = [graphNodeID]

    # Add the option node to the graph.
    self.graph.add_node(str(graphNodeID), attributes = nodeAttributes)

    # Link this configuration node ID with the created graph node ID.
    self.configurationFileToGraphNodeID[graphNodeID] = [graphNodeID]

  # Add an edge to the graph.
  def addEdge(self, source, target, attributes):
    self.graph.add_edge(source, target, attributes = deepcopy(attributes))

  # Set an attribute for a graph node.
  def setGraphNodeAttribute(self, nodeID, attribute, values):
    try: setattr(self.graph.node[nodeID]['attributes'], attribute, values)
    except: return False

    return True

  # Set an attribute for a graph edge.
  def setArgumentAttribute(self, source, target, attribute, value):
    try: setattr(self.graph[source][target]['attributes'], attribute, value)
    except: return False

    return True

  #######################################
  ##  methods for querying the graph.  ##
  #######################################

  # Return an attribute from a graph node.
  def getGraphNodeAttribute(self, nodeID, attribute):
    try: return getattr(self.graph.node[nodeID]['attributes'], attribute)
    except: return None

  # Get all the attributes for a node.
  def getNodeAttributes(self, nodeID):
    try: return self.graph.node[nodeID]['attributes']
    except: return False

  # Get all the attributes from an edge.
  def getEdgeAttributes(self, source, target):
    try: return self.graph[source][target]['attributes']
    except: return False

  # Get the an argument attribute from graph edge.
  def getArgumentAttribute(self, source, target, attribute):

    # Get the argument attributes from the edge.
    try: return getattr(self.graph[source][target]['attributes'], attribute)
    except: return False

  # Given a task and an argument, determine the node ID connecting the two.
  def getNodeForInputArgument(self, task, argument):
    associatedNodeIDs = []

    # Loop over the input nodes connected to the task and check if this corresponds to the given argument.
    for nodeID in self.graph.predecessors(task):
      if self.getArgumentAttribute(nodeID, task, 'longFormArgument') == argument: associatedNodeIDs.append(nodeID)

    # TODO ERROR
    if len(associatedNodeIDs) != 1: print('ERROR - graph.getNodeForInputArgument'); exit(1)

    # Return the node ID.
    return associatedNodeIDs[0]

  # Check if an edge exists with the requested argument, either coming from or pointing into a given
  # task.
  def checkIfEdgeExists(self, task, argument, isPredecessor):
    edges = []

    # If the argument is an input file or an option, isPredecessor is set to true. In this case, loop over
    # all predecessor nodes and check if any predecessor nodes connect to the task node with an edge with
    # the defined argument. If this is an output file, isPredecessor is false and the successor nodes should
    # be looped over.
    if isPredecessor: nodeIDs = self.graph.predecessors(task)
    else: nodeIDs = self.graph.successors(task)

    # Loop over the nodes.
    for nodeID in nodeIDs:
      if isPredecessor: attributes = self.graph[nodeID][task]['attributes']
      else: attributes = self.graph[task][nodeID]['attributes']

      # Check if this edge has the same argument as requested.
      if attributes.longFormArgument == argument: edges.append(nodeID)

    # Return a list of edges with the requested argument.
    return edges

  # Return a list of all input file nodes.
  def getInputFileNodes(self, task):
    fileNodeIDs = []
    for nodeID in self.graph.predecessors(task):
      if self.getGraphNodeAttribute(nodeID, 'nodeType') == 'file': fileNodeIDs.append(nodeID)

    return fileNodeIDs

  # Return a list of all output file nodes.
  def getOutputFileNodes(self, task):
    fileNodeIDs = []
    for nodeID in self.graph.successors(task):
      if self.getGraphNodeAttribute(nodeID, 'nodeType') == 'file': fileNodeIDs.append(nodeID)

    return fileNodeIDs

  # Return a list of all option nodes.
  def getOptionNodes(self, task):
    optionNodeIDs = []
    for nodeID in self.graph.predecessors(task):
      if self.getGraphNodeAttribute(nodeID, 'nodeType') == 'option': optionNodeIDs.append(nodeID)

    return optionNodeIDs

  # Return a list of all nodes of the requested type.
  def getNodes(self, nodeType):

    # If a single node type is supplied, turn nodeType into a list.
    if not isinstance(nodeType, list): nodeType = [nodeType]

    nodeIDs = []
    for nodeID in self.graph.nodes():
      if nodeType == 'all': nodeIDs.append(nodeID)
      elif self.getGraphNodeAttribute(nodeID, 'nodeType') in nodeType: nodeIDs.append(nodeID)

    return nodeIDs

  # Get all predecessor nodes.
  def getPredecessors(self, nodeID):
    try: return self.graph.predecessors(nodeID)
    except: return False

  # Get all successor nodes.
  def getSuccessors(self, nodeID):
    try: return self.graph.successors(nodeID)
    except: return False

  #####################
  ### Class methods ###
  #####################

  # Return an attribute from a graph node.
  @classmethod
  def CM_getGraphNodeAttribute(cls, graph, nodeID, attribute):
    try: return getattr(graph.node[nodeID]['attributes'], attribute)
    except: return None

  # Return a list of all nodes of the a requested type.
  @classmethod
  def CM_getNodes(cls, graph, nodeType):
    nodeIDs = []
    for nodeID in graph.nodes():
      if cls.CM_getGraphNodeAttribute(graph, nodeID, 'nodeType') == nodeType: nodeIDs.append(nodeID)

    return nodeIDs

  # Get all of the input nodes for a task.
  @classmethod
  def CM_getInputNodes(cls, graph, task):

    # Check that the supplied node (e.g. task), is a task and not another type of node.
    if cls.CM_getGraphNodeAttribute(graph, task, 'nodeType') != 'task': print('ERROR - getInputNodes - 1'); exit(0)

    # Get the predecessor nodes.
    return graph.predecessors(task)

  # Get all of the input file nodes for a task.
  @classmethod
  def CM_getInputFileNodes(cls, graph, task):

    # Check that the supplied node (e.g. task), is a task and not another type of node.
    if cls.CM_getGraphNodeAttribute(graph, task, 'nodeType') != 'task': print('ERROR - getInputNodes - 1'); exit(0)

    # Get the predecessor nodes.
    nodeIDs = []
    for nodeID in graph.predecessors(task):
      if cls.CM_getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'file': nodeIDs.append(nodeID)

    return nodeIDs

  # Get all of the output nodes for a task.
  @classmethod
  def CM_getOutputNodes(cls, graph, task):

    # Check that the supplied node (e.g. task), is a task and not another type of node.
    if cls.CM_getGraphNodeAttribute(graph, task, 'nodeType') != 'task': print('ERROR - getOutputNodes - 1'); exit(0)

    # Get the successor nodes.
    return graph.successors(task)

  # Get the an argument attribute from graph edge.
  @classmethod
  def CM_getArgumentAttribute(cls, graph, source, target, attribute):

    # Get the argument attributes from the edge.
    try: return getattr(graph[source][target]['attributes'], attribute)
    except: return False

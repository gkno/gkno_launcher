#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import fileHandling as fh
import graphErrors
import networkx as nx

import constructFilenames as construct
import parameterSets as ps
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

    # Store information on whether the task is greedy and how many times the task needs to
    # be executed.
    self.isGreedy           = False
    self.numberOfExecutions = 1

    # Store the number of sets of input and output files for the task.
    self.numberOfInputSets  = 1
    self.numberOfOutputSets = 1

    # Keep track of the option nodes for this task that have multiple values.
    self.nodesWithMultipleValues = []

    # Record if this node should be included in any graphical output.
    self.includeInReducedPlot = False

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
    # will be deleted.
    self.isIntermediate = False

    # Some input file nodes have their values generated from another node associated
    # with the task (e.g. index files). For these nodes, keep track of the node from
    # which their values should be constructed.
    self.constructUsingNode = None

    # If a file node is broken out into multiple nodes, the original node has a list of all the
    # nodes created. See information on generating multiple output nodes for more information.
    self.daughterNodes  = []

    # Also store if this node is the daughter of another node.
    self.isDaughterNode = False

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
          for extension in stubExtensions:

            # Define the name of the new file node.
            fileNodeID = str(graphNodeID + '.' + str(extension))

            # Add the file node.
            self.addFileNode(fileNodeID, graphNodeID)

            # Identify the source and target node (depending on whether this is an input or an output)
            # and add the edges to the graph.
            source = fileNodeID if isInput else taskNodeID
            target = taskNodeID if isInput else fileNodeID

            # Add the edge to the graph.
            self.graph.add_edge(source, target, attributes = argumentAttributes)

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
        for extension in information.stubExtensions:

          # Add the extension to the attributes.
          argumentAttributes.extensions = [str(extension)]

          # Add the nodes associated with the stub that are not being linked to the other tasks,
          if extension != information.stubExtension:
            self.addFileNode(str(nodeAddress + '.' + extension), str(nodeAddress))

          # Add the edge.
          if information.isInput: self.addEdge(str(nodeAddress + '.' + extension), information.taskAddress, attributes = argumentAttributes)
          elif information.isOutput: self.addEdge(information.taskAddress, str(nodeAddress + '.' + extension), attributes = argumentAttributes)

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

        # If no edges were found, create a new node, add the edges and values.
        if not edges:

          # Get the attributes for the edge.
          argumentAttributes = toolData.getArgumentData(longFormArgument)

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
        elif len(edges) == 1: print('HELLO', edges)

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
            else: self.addEedge(modifiedNodeAddress, taskAddress, argumentAttributes)

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
            data = fh.fileHandling.openFile(value)
            #TODO ERROR
            if not data: print('graph.expandLists - FILE DOESN\'T EXIST', value); exit(0)
  
            # Loop over the values in the file, stripping off whitespace.
            for dataValue in [name.strip() for name in data]: modifiedValues.append(dataValue)
  
          # If the value does not end with '.list', add it to the modifiedValues list.
          else: modifiedValues.append(value)
  
        # Replace the values with the modifiedValues.
        self.setGraphNodeAttribute(nodeID, 'values', modifiedValues)

  # Check the number of values in each node and determine how many times each task needs to be run. For example,
  # a tool could be fed n input files for a single argument and be run n times or once etc.
  def determineNumberOfTaskExecutions(self, superpipeline):

    # Loop over all tasks in the pipeline.
    for task in self.workflow:

      # If this task needs to be called multiple times for multiple sets of input nodes, create the new task
      # nodes and connect them to the relevant input nodes.
      if self.getGraphNodeAttribute(task, 'multipleTaskCalls'): self.multipleTaskCalls(superpipeline, task)

      # Check all of the options for the task.
      self.checkTaskOptions(task)

      # Check the input files. The number of executions has been set by the number of values supplied to the
      # task options, unless this is still set to one. The task can be greedy with respect to input files, so
      # multiple input files can still equate to a single execution of the task; this is checked now.
      self.checkInputFiles(superpipeline, task)

      # Having determined the number of executions for this task, and constructed any necessary input files,
      # construct the output files. Also determine if the output files are to be deleted. If so, mark the node
      # as temporary and add a random string to the output filenames to ensure that there are not filename
      # conflicts.
      self.checkOutputFiles(superpipeline, task)

  # If this task needs to be called multiple times for multiple sets of input nodes, create the new task
  # nodes and connect them to the relevant input file nodes. Note that this does not create the output
  # nodes from the new tasks nodes and create the filenames. This is performed in the checkOutputFiles
  # section.
  def multipleTaskCalls(self, superpipeline, task):

    # Get the task node attributes to be applied to the created task nodes.
    taskAttributes = self.getNodeAttributes(task)

    # Identify all the input option nodes connected to the task.
    optionNodeIDs = self.getOptionNodes(task)

    # Determine the input node with multiple copies and a list of all other nodes so that
    # all required edges can be set for the new task nodes.
    inputNodeIDs = []
    multinodeID  = None
    for inputNodeID in self.getInputFileNodes(task):
      if self.getGraphNodeAttribute(inputNodeID, 'daughterNodes'): multinodeID = inputNodeID
      else: inputNodeIDs.append(inputNodeID)
    for optionNodeID in self.getOptionNodes(task): inputNodeIDs.append(optionNodeID)

    # If no node was found, throw an error.
    if not multinodeID: print('ERROR - graph.multipleTaskCalls - 1'); exit(1)

    # Record the multinode input in the task attributes.
    self.setGraphNodeAttribute(task, 'multinodeInput', multinodeID)

    # Get the argument attributes associated with the argument linking the multiple input nodes to the
    # multiple tasks (e.g. from the edge that links the originally exsiting node to the original task).
    argumentAttributes = self.getEdgeAttributes(multinodeID, task)

    # Loop over the multiple nodes.
    createdTaskNodeIDs = []
    for i, nodeID in enumerate(self.getGraphNodeAttribute(multinodeID, 'daughterNodes')):

      # Create a new task node.
      daughterTask = str(task + '-' + str(i + 1))
      attributes   = deepcopy(taskAttributes)
      attributes.isDaughterNode = True
      self.addTaskNode(superpipeline, daughterTask, task, attributes)
      createdTaskNodeIDs.append(daughterTask)

      # Attach all the options to the new task node.
      for inputNodeID in inputNodeIDs:
        edgeAttributes = self.getEdgeAttributes(inputNodeID, task)
        self.addEdge(inputNodeID, daughterTask, edgeAttributes)

      # Add the edge between the daughter node and the new task.
      self.addEdge(nodeID, daughterTask, argumentAttributes)

      # Mark the multinode inputs in the new task attributes.
      self.setGraphNodeAttribute(daughterTask, 'multinodeInput', nodeID)

    # Add the daughter nodes to the original task node.
    self.setGraphNodeAttribute(task, 'daughterTasks', createdTaskNodeIDs)

  # Check the supplied options for a task. Options can be supplied with zero or one value without a problem. If
  # more than one value is provided to any option, this implies that the task is to be run multiple times - once
  # for each value. If multiple values are supplied to multiple options, then there must be the same number of
  # values. Each subsequent execution of the task will have all of the options iterated each time, so if option A
  # is given the values A1 and A2, and option B is givem B1 and B2, the first execution will have A1 and B1, and the
  # second execution A2 and B2. If option A was provided the values A1, A2 and A3 and option B only have B1 and B2,
  # it is unclear which combinations to provide. gkno does not attempt to execute all possible combinations of
  # supplied option values.
  def checkTaskOptions(self, task):

    # Keep track of the options with multiple values.
    multivalueOptions = []

    # Record how many times this task is to be executed, based on the supplied option values.
    numberOfExecutions = 1
    for nodeID in self.getOptionNodes(task):

      # Get the values associated with this option.
      values = self.getGraphNodeAttribute(nodeID, 'values')
      if len(values) > 1:

        # If the number of executions, is set at one, reset the number of executions to the number of
        # values supplied to this option.
        if numberOfExecutions == 1: numberOfExecutions = len(values)

        # If the number of executions is already greater than one, the number of values for this option must
        # equal the number of executions.
        # TODO ERROR
        elif len(values) != numberOfExecutions: print('ERROR - graph.checkTaskOptions - 1'); exit(0)

        # Store the node ID.
        multivalueOptions.append(nodeID)

    # Update the task node to reflect the number of executions it needs to undertake.
    self.setGraphNodeAttribute(task, 'numberOfExecutions', numberOfExecutions)

    # Store the options that are multivalued.
    self.setGraphNodeAttribute(task, 'multivalueOptions', multivalueOptions)

  # Loop over all the input files for the task and check how many have been defined. If the number of set files
  # is inconsistent with the number of executions implied by the values given to the task options, terminate.
  def checkInputFiles(self, superpipeline, task):

    # Get the number of executions currently associated with this task.
    numberOfExecutions = self.getGraphNodeAttribute(task, 'numberOfExecutions')

    # Keep track of the number of sets of input files for this task. Note that if the task is greedy, the number of
    # sets of input files is one.
    numberOfInputNodes = 1

    # Get the tool associated with the task.
    tool = superpipeline.tasks[task]

    # Loop over the input files.
    for fileNodeID in self.getInputFileNodes(task):

      # Determine the tool argument that uses the values from this node.
      argument = self.getArgumentAttribute(fileNodeID, task, 'longFormArgument')
      values   = self.getGraphNodeAttribute(fileNodeID, 'values')
      if len(values) > 1:

        # Determine if this task is listed as being greedy. If so, check that the argument associated with these
        # values is permitted to accept multiple values. If so, this task is to be run once using all the values,
        # rather than being run len(values) times.
        if self.getArgumentAttribute(fileNodeID, task, 'isGreedy'):
          #TODO ERROR
          if not superpipeline.toolConfigurationData[tool].getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - GREEDY'); exit(0)

          # Mark the task node to indicate that this task is greedy.
          self.setGraphNodeAttribute(task, 'isGreedy', True)

        # If the number of executions is one and the argument is not greedy, update the number of executions.
        elif numberOfExecutions == 1: numberOfExecutions = len(values)

        # If this task produces multiple output file nodes, this is allowed as the number of executions will
        # correspond to the number of output file nodes produced multiplied by the numberOfExecutions already
        # listed. For example, consider the case where there are two input files and an option is given three
        # values. Since this task is not greedy, each of the input files produce their own output node and the
        # task is executed once per option - so there are 2 x 3 = 6 total executions. This isn't set here,
        # however, since the filenames are constructed for each of the output nodes. For each of the output nodes,
        # there are still just numberOfExecutions calls. The value is modified in the createAdditionalOutputNodes
        # method.
        elif self.getGraphNodeAttribute(task, 'generateMultipleOutputNodes'): pass#numberOfExecutions = len(values) * numberOfExecutions

        # If the number of executions is already greater than one, check that the number of set values is consistent
        # with the number of executions already defined. If the argument is greedy, this is not checked, since the
        # task can be executed multiple times due to the options.
        #TODO ERROR
        elif len(values) != numberOfExecutions: print('ERROR - graph.checkInputFiles - 1', task, values, numberOfExecutions); exit(0)

      # If there are no set values, check to see if there are instructions on how to construct the filenames. If
      # so, construct the files.
      elif len(values) == 0:

        # Determine if the argument has filename construction instructions.
        constructUsingNode = self.getGraphNodeAttribute(fileNodeID, 'constructUsingNode')
        if constructUsingNode:
          baseValues = self.getGraphNodeAttribute(constructUsingNode, 'values')
          self.setGraphNodeAttribute(fileNodeID, 'values', construct.constructInputNode(self.graph, superpipeline, task, argument, fileNodeID, baseValues))

    # Update the task node.
    self.setGraphNodeAttribute(task, 'numberOfExecutions', numberOfExecutions)
    #self.setGraphNodeAttribute(task, 'numberOfInputSets', numberOfInputSets)

  # Loop over all of the output files and construct those that are not present.
  def checkOutputFiles(self, superpipeline, task):

    # Determine task properties.
    isConsolidate       = self.getGraphNodeAttribute(task, 'consolidate')
    isGenerateMultiple  = self.getGraphNodeAttribute(task, 'generateMultipleOutputNodes')
    isMultipleTaskCalls = self.getGraphNodeAttribute(task, 'multipleTaskCalls')

    # Keep track of the number of sets of output files for this task.
    numberOfOutputSets = 1

    # Get the number of executions currently associated with this task.
    numberOfExecutions = self.getGraphNodeAttribute(task, 'numberOfExecutions')

    # Loop over all the output nodes.
    for nodeID in self.getOutputFileNodes(task):

      # Check if this node has values.
      if not self.getGraphNodeAttribute(nodeID, 'values'):
        instructions = self.getArgumentAttribute(task, nodeID, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkOutputFiles - 1'); exit(1)

        # Determine if the values associated with this node are going to be deleted and consequently can be
        # marked as intermediate. Intermediate filenames are prepended with a random string to avoid any
        # any repeated filenames.
        isIntermediate = False
        randomString   = None
        for configurationNodeID in self.getGraphNodeAttribute(nodeID, 'configurationFileNodeIDs'):
          if self.getGraphNodeAttribute(configurationNodeID, 'isIntermediate'):
            isIntermediate = True
            randomString   = stringOps.getRandomString(10)
            break

        # Construct the filename according to the requested method.
        if instructions['method'] == 'from tool argument': 

          # Get the values from which to construct the filenames. If there are multiple values, but only a single
          # execution, use the first value for constructing the filenames.
          baseValues = self.getBaseValues(superpipeline, task, instructions)

          # Check if this task produces multiple output file nodes. If so, determine the number of nodes there should
          # be and create the missing nodes and connect them up in the graph. Also update the number of output sets
          # for the task.
          if isGenerateMultiple:
            self.createAdditionalOutputNodes(superpipeline, instructions, task, nodeID, baseValues)
            numberOfOutputSets = len(baseValues)

          # If multiple task nodes have been created for this task and the outputs from all of these tasks are being
          # consolidated into a single node, perform necessary checks and populate the single output node with all
          # necessary values.
          elif isConsolidate: self.consolidate(superpipeline, instructions, task, nodeID)

          # If multiple task nodes have been created for this task and the output file nodes are not being
          # consolidated into a single node, create the new output nodes, create the filenames and join
          # them up in the graph.
          elif isMultipleTaskCalls: self.createMultipleTaskOutputs(superpipeline, instructions, task, nodeID)

          # If no additional output files are being created, check details, then create filenames.
          else:

            # Given the number of executions, whether the task is greedy and the number of base values, determine
            # how to proceed with constructing the output filenames. Begin with cases where there are multiple
            # executions.
            if numberOfExecutions != 1:
  
              # If there is only a single base value, but there are multiple options, ensure that the options with
              # multiple values are included in the filenames being constructed.
              if len(baseValues) == 1: print('graph.checkOutputFiles - Not handled multiple executions, single file'); exit(0) #TODO REMEMBER NUMBER OF OUTPUT SETS
  
              # If the number of base values is different from the number of executions and the task is not greedy, terminate.
              elif len(baseValues) != numberOfExecutions:
                if not self.getGraphNodeAttribute(task, 'isGreedy'):
                  #TODO ERROR
                  print('ERROR - graph.checkOutputFiles - 2 -', len(baseValues), numberOfExecutions, self.getGraphNodeAttribute(task, 'isGreedy'))
                  exit(1)
  
                # If the task is greedy, the first value from the base values can be used to construct the output
                # filenames, but in order to ensure that the output filenames for each different option value are
                # unique, update the construction instructions to include the option in the filename (if not
                # already included. Also, ensure that there are as many base values as there are executions.
                else: 
                  baseValues = [baseValues[0]] * numberOfExecutions
                  construct.updateArgumentsInInstructions(self.graph, instructions, task)
  
              # If there are multiple executions and there are the same number of base values as there are number
              # of executions, no modification to the base values is required. An output file for each of the base
              # values will be constructed.
  
            # Now consider cases where there is only a single execution of the task.
            else:
  
              # If there are multiple base values, reduce the base values to the first value in the list. This will
              # be used to construct the single output file (since there is only a single execution.)
              if len(baseValues) > 1: baseValues = [baseValues[0]]
  
              # If there is only a single base value. no action is required.
  
            # Now that the values from which to construct the filenames are known, construct the filenames.
            values = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeID, baseValues)
  
            # Having constructed the output filenames, add them to the node.
            self.setGraphNodeAttribute(nodeID, 'values', values)
  
            # Store the number of output file sets.
            numberOfOutputSets = len(values)

        # If the construction method is unknown, terminate.
        else: print('constructFilenames.constructFilenames - unknown method', instructions.method); exit(0)

    # Store the number of output file sets in the graph node.
    self.setGraphNodeAttribute(task, 'numberOfOutputSets', numberOfOutputSets)

  # Check if this task produces multiple output file nodes. If so, determine the number of nodes there should
  # be and create the missing nodes and connect them up in the graph.
  def createAdditionalOutputNodes(self, superpipeline, instructions, task, existingNodeID, baseValues):

    # Additional nodes are created becuase there are multiple input files that are being handled seperately.
    # So, first check that the task isn't listed as greedy.
    # TODO ERROR
    if self.getGraphNodeAttribute(task, 'isGreedy'): print('ERROR - graph.createAdditionalOutputNodes - greedy'); exit(1)

    # Next, check that there are at least two baseValues (e.g. at least two input files that are to be analysed).
    # TODO ERROR
    if len(baseValues) < 2: print('ERROR - graph.createAdditionalOutputNodes - not enough inputs'); exit(1)

    # Finally check that there are at least two executions to be performed. Each of the N input file from the
    # baseValues need to be executed numberOfExecutions times. If this is less than two, there is no need to 
    # generate individual output nodes.
    #TODO ERROR
    if self.getGraphNodeAttribute(task, 'numberOfExecutions') < 2: print('ERROR - graph.createAdditionalOutputNodes - executions'); exit(1)

    # Get the argument for the output node and check that it is valid and points to an output file.
    argument = self.getGraphNodeAttribute(task, 'generateMultipleOutputNodes')
    tool     = superpipeline.tasks[task]

    try: longFormArgument = superpipeline.toolConfigurationData[tool].getLongFormArgument(argument)
    except: print('ERROR - graph.createAdditionalOutputNodes - unknown argument'); exit(1)

    # TODO ERROR
    if not superpipeline.toolConfigurationData[tool].arguments[longFormArgument].isOutput:
      print('ERROR - graph.createAdditionalOutputNodes - not output'); exit(1)

    # Get the attributes associated with the exising output node and the edge connecting to the current
    # task.
    nodeAttributes = deepcopy(self.getNodeAttributes(existingNodeID))
    edgeAttributes = deepcopy(self.getEdgeAttributes(task, existingNodeID))

    # Update the construction instructions to use the option argument values in the filenames.
    construct.updateArgumentsInInstructions(self.graph, instructions, task)

    # Generate the output file names for the existing output node using the first value in the
    # baseValues.
    updatedValues = [baseValues[0]] * self.getGraphNodeAttribute(task, 'numberOfExecutions')
    values        = construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, updatedValues)
    self.setGraphNodeAttribute(existingNodeID, 'values', values)

    # Create new output nodes for each of the input files.
    createdNodeIDs = []
    for i in range(1, len(baseValues)):

      # Generate a new name for the file node.
      nodeID = str(existingNodeID + '-' + str(i))
      createdNodeIDs.append(nodeID)

      # Create the node and edges.
      attributes                = deepcopy(nodeAttributes)
      attributes.isDaughterNode = True
      self.graph.add_node(nodeID, attributes = attributes)
      self.addEdge(task, nodeID, edgeAttributes)

      # Create the filenames for the new node.
      updatedValues = [baseValues[i]] * self.getGraphNodeAttribute(task, 'numberOfExecutions')
      values        = construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, updatedValues)
      self.setGraphNodeAttribute(nodeID, 'values', values)

    # Attach the created node IDs to the existing node, so that all associated output nodes can be easily retrieved.
    self.setGraphNodeAttribute(existingNodeID, 'daughterNodes', createdNodeIDs)

    # Add the ID of the node that has been split into multiple nodes to the task attributes.
    self.setGraphNodeAttribute(task, 'multinodeOutput', existingNodeID)

  # If multiple task nodes have been created for this task and the outputs from all of these tasks are being
  # consolidated into a single node, perform necessary checks and populate the single output node with all
  # necessary values.
  def consolidate(self, superpipeline, instructions, task, existingNodeID):

    # Check that this task is listed as greedy. This must be the case since there are multiple calls to
    # this task. Each call has an individual input node with multiple values. The task must be greedy
    # in order to ensure that there is a single output file for each of the task calls. These output files
    # will be consolidated into the output file node that has already been created for this task.
    #TODO ERROR
    if not self.getGraphNodeAttribute(task, 'isGreedy'): print('ERROR - graph.consolidate - not greedy'); exit(1)

    # Get the multinode input.
    inputNodeID = self.getGraphNodeAttribute(task, 'multinodeInput')
    
    # Get the attributes associated with the edge connecting the current task to the existing output node.
    edgeAttributes = deepcopy(self.getEdgeAttributes(task, existingNodeID))

    # Create the filenames for all of the output files, starting with the existing node.
    baseValues   = [self.getGraphNodeAttribute(inputNodeID, 'values')[0]]
    outputValues = construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, baseValues)

    # Loop over the daughter nodes and create their values.
    for i, nodeID in enumerate(self.getGraphNodeAttribute(inputNodeID, 'daughterNodes')):
      baseValues   = [self.getGraphNodeAttribute(nodeID, 'values')[0]]
      outputValues.extend(construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, baseValues))

      # Join the task to the output file node.
      taskAddress = str(task + '-' + str(i + 1))
      self.addEdge(taskAddress, existingNodeID, edgeAttributes)

    # Add the values to the node.
    self.setGraphNodeAttribute(existingNodeID, 'values', outputValues)

  # If multiple task nodes have been created for this task and the output file nodes are not being
  # consolidated into a single node, create the new output nodes, create the filenames and join
  # them up in the graph.
  def createMultipleTaskOutputs(self, superpipeline, instructions, task, existingNodeID):

    # Get the multinode input.
    inputNodeID = self.getGraphNodeAttribute(task, 'multinodeInput')

    # Get the attributes associated with the exising output node and the edge connecting to the current
    # task.
    nodeAttributes = deepcopy(self.getNodeAttributes(existingNodeID))
    edgeAttributes = deepcopy(self.getEdgeAttributes(task, existingNodeID))

    # Generate the output file names for the existing output node.
    baseValues = self.getGraphNodeAttribute(inputNodeID, 'values')
    values     = construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, baseValues)
    self.setGraphNodeAttribute(existingNodeID, 'values', values)

    # Identify the multinode output in the task attributes.
    self.setGraphNodeAttribute(task, 'multinodeOutput', existingNodeID)

    # Create new output nodes for each of the input nodes, connect them to the relevant nodes and create the
    # filenames.
    createdNodeIDs = []
    for i, nodeID in enumerate(self.getGraphNodeAttribute(inputNodeID, 'daughterNodes')):

      # Create the name of the new output file node.
      fileNodeID  = str(existingNodeID + '-' + str(i + 1))
      taskAddress = str(task + '-' + str(i + 1))
      createdNodeIDs.append(fileNodeID)

      # Create the node and edges.
      attributes                = deepcopy(nodeAttributes)
      attributes.isDaughterNode = True
      self.graph.add_node(fileNodeID, attributes = attributes)
      self.addEdge(taskAddress, fileNodeID, edgeAttributes)

      # Create the filenames for the new node.
      baseValues = self.getGraphNodeAttribute(nodeID, 'values')
      values     = construct.constructFromFilename(self.graph, superpipeline, instructions, task, existingNodeID, baseValues)
      self.setGraphNodeAttribute(fileNodeID, 'values', values)

      # Identify the multinode output in the task attributes.
      self.setGraphNodeAttribute(taskAddress, 'multinodeOutput', nodeID)

    # Attach the created node IDs to the existing node, so that all associated output nodes can be easily retrieved.
    self.setGraphNodeAttribute(existingNodeID, 'daughterNodes', createdNodeIDs)

  # Find all of the predecessor nodes to a task that use a given argument and add the values to a list.
  def getBaseValues(self, superpipeline, task, instructions):
    values = []

    # Get the input file from which the filenames should be built.
    try: argument = instructions['use argument']
    except: print('ERROR - graph.getBaseValues - 1'); exit(1)

    # Get tool information from the superpipline and determine the long form of the argument defined in the
    # instructions.
    tool             = superpipeline.tasks[task]
    longFormArgument = superpipeline.toolConfigurationData[tool].getLongFormArgument(argument)

    # Search predecessor nodes.
    for predecessorID in self.getPredecessors(task):
      predecessorArgument = self.getArgumentAttribute(predecessorID, task, 'longFormArgument')
      if predecessorArgument == longFormArgument:
        for value in self.getGraphNodeAttribute(predecessorID, 'values'): values.append(value)

    # Return the values.
    return values

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

  # Check if an edge exists with the requested argument, either coming from or pointing into a given
  # task.
  def checkIfEdgeExists(self, task, argument, isPredecessor):
    edges = []

    # If the argument is an input file or an option, isPredecessor is set to true. In this case, loop over
    # all precessor nodes and check if any predecessor nodes connect to the task node with an edge with
    # the defined argument. If this is an output file, isPredecessor is false and the successoe nodes should
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

  # Return a list of all nodes of the a requested type.
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

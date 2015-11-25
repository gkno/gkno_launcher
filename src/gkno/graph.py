#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import networkx as nx

import commandLineErrors as cle
import constructFilenames as construct
import constructFilenameErrors as cfe
import fileHandling as fh
import fileErrors as fe
import graphErrors
import parameterSets as ps
import parameterSetErrors as pse
import pipelineConfigurationErrors as pce
import stringOperations as strOps
import superpipeline as sp
import toolConfigurationErrors as tce

import json
import os
import sys

# Define a data structure for holding information on arguments.
class argumentInformation:
  def __init__(self):

    # Define the node ID from which the task was taken.
    self.nodeId = None

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

    # Store the number of subphases and divisions the task is broken up into.
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

    # Store the stub extension associated with the node. If the task takes (or outputs) a stub,
    # multiple file nodes are created, each of which is associated with a particular extension.
    self.stubExtension = None

    # Store if the node is an intermediate node (e.g. all files associated with this node
    # will be deleted. In addition, store the task after which the files associated with
    # the node should be deleted.
    self.isIntermediate  = False
    self.deleteAfterTask = None

    # Store information on the task divisions.
    self.children         = []
    self.divisions        = 0
    self.divisionID       = None
    self.divisionText     = None
    self.isChild          = False
    self.isCreateDivision = False
    self.parent           = None

    # If the files contained in this node are being streamed from one task to the next, the files
    # are actually never created. Mark the node as containing streaming files so that attempts to
    # delete them will not be made, and the files will not be listed as outputs or dependencies.
    self.isStream = False

    # The configuration file can specify a text string that should be applied to filenames for this
    # node (if the filenames are constructed).
    self.addTextToFilename = None

    # If the values associated with the node are commands to be evaluated at run time, then the
    # values will not conform to the required data type (since the command will be a string). If
    # this is the case, the isCommandToEvaluate flag will be set to True so that the checks are 
    # not performed.
    self.isCommandToEvaluate = False

# Define a class to store and manipulate the pipeline graph.
class pipelineGraph:
  def __init__(self, pipeline):

    # Handle errors associated with graph construction.
    self.errors = graphErrors.graphErrors()

    # Store the name of the pipeline.
    self.pipeline = pipeline

    # Define the graph.
    self.graph = nx.DiGraph()

    # Store the workflow.
    self.workflow = []

    # Store parameter set information.
    self.parameterSet = None
    self.ps           = ps.parameterSets()

    # When configuration file nodes (unique and shared nodes) are added to the graph, keep
    # track of the node ID in the graph that the configuration file node is attached to.
    self.configurationFileToGraphNodeId = {}

    # Keep track of whether a parameter set is being exported.
    self.exportParameterSet = False

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

    # If the pipeline imports arguments from a tool, check all of the arguments for that tool for required
    # arguments.
    if pipeline.importArgumentsFromTool:
      pass

  # Add unique graph nodes to the graph.
  def addUniqueNodes(self, superpipeline, pipeline):
    for configurationNodeId in pipeline.uniqueNodeAttributes:

      # Define a set of information to be used in help messages.
      information = (pipeline.name, 'unique graph nodes', configurationNodeId)

      # Define the pipeline relative address.
      address = str(pipeline.address + '.') if pipeline.address else str('')

      # Determine if this node has already been added to the graph. Only proceed with processing
      # this node if it hasn't already been added. If the node has already been processed (for
      # example, a parent pipeline may have included the unique node as a shared node within its
      # configuration file), the graph node ID will appear in the configurationFileToGraphNodeId
      # dictionary.
      graphNodeId = address + configurationNodeId
      if graphNodeId not in self.configurationFileToGraphNodeId:

        # Get the task this node points to and determine if it is a tool or a pipeline.
        task           = pipeline.getUniqueNodeAttribute(configurationNodeId, 'task')
        taskNodeId     = address + task
        taskArgument   = pipeline.getUniqueNodeAttribute(configurationNodeId, 'taskArgument')
        externalNodeId = pipeline.getUniqueNodeAttribute(configurationNodeId, 'nodeId')
  
        # Only create unique nodes that point to an argument. If the configuration file node points to a
        # node in an external pipeline, skip the node. The node will be created when the pipeline being
        # pointed to is parsed and the configuration file node will be associated with this node in the
        # findUniqueNodes method.
        if taskArgument:
          tool           = superpipeline.getTool(taskNodeId)
          toolAttributes = superpipeline.getToolData(tool)
  
          # Get the long form of the argument and the associated attributes for the argument.
          longFormArgument   = toolAttributes.getLongFormArgument(taskArgument)
          argumentAttributes = toolAttributes.getArgumentData(longFormArgument)
    
          # Determine if this is a file or an option.
          isInput  = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isInput')
          isOutput = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isOutput')
    
          # Determine if this is a filename stub.
          isStub = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'isStub')
          if isStub: stubExtensions = superpipeline.toolConfigurationData[tool].getArgumentAttribute(longFormArgument, 'stubExtensions')
    
          # If the configuration file node is for a filename stub, add as many nodes to the graph as there are files
          # associated with the stub. Then connect all the nodes to the task.
          if isStub:
  
            # Loop over all of the stub extensions.
            for i, extension in enumerate(stubExtensions):
  
              # Define the name of the new file node.
              fileNodeId = str(graphNodeId + '.' + str(extension))
  
              # Add the file node and attache the stub extensions to the node.
              self.addFileNode(fileNodeId, graphNodeId)
              self.setGraphNodeAttribute(fileNodeId, 'stubExtension', extension)
  
              # Identify the source and target node (depending on whether this is an input or an output)
              # and add the edges to the graph.
              source = fileNodeId if isInput else taskNodeId
              target = taskNodeId if isInput else fileNodeId
  
              # Store the extension for this particular node.
              stubArgumentAttributes                   = deepcopy(argumentAttributes)
              stubArgumentAttributes.stubExtension     = extension
              stubArgumentAttributes.isPrimaryStubNode = True if i == 0 else False
  
              # Add the edge to the graph.
              self.graph.add_edge(source, target, attributes = stubArgumentAttributes)
  
          # If this is an input file (not a stub), add the node and join it to the task.
          elif isInput:
            self.addFileNode(str(graphNodeId), str(graphNodeId))
            self.addEdge(graphNodeId, taskNodeId, argumentAttributes)
  
          # If this is an output file (not a stub), add the node and join it to the task.
          elif isOutput:
            self.addFileNode(str(graphNodeId), str(graphNodeId))
            self.addEdge(taskNodeId, graphNodeId, argumentAttributes)
  
          # If this is not a file, then create an option node and join to the task.
          else:
            self.addOptionNode(str(graphNodeId))
            self.addEdge(graphNodeId, taskNodeId, argumentAttributes)

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
    for sharedNodeId in pipeline.getSharedNodeIds():
      tasksSharingNode = []

      # First check that this node has not already been added to the graph. Only proceed if it hasn't. If the
      # configuration node has already been processed (e.g. a configuration file node of a pipeline for which
      # this pipeline is a descendant, shared this node), the configuration node ID will have been added to
      # the configurationFileToGraphNodeId dictionary.
      if not pipelineName + '.' + sharedNodeId in self.configurationFileToGraphNodeId:

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
        sharedNodes      = [(pipelineName, sharedNodeId)]
        tasksSharingNode = []

      # Keep track of the number of stub arguments in the shared node.
      numberOfStubs          = 0
      numberOfStubExtensions = 0
      numberOfInputFiles     = 0
      numberOfOutputFiles    = 0

      # Loop over the sharedNodes until it is empty.
      while len(sharedNodes) > 0:
        name, sharedNodeId = sharedNodes.pop()

        # Loop over all the tasks sharing this node.
        for taskInformation in superpipeline.pipelineConfigurationData[name].getSharedNodeTasks(sharedNodeId):

          # Get the address of this pipeline.
          pipelineAddress = superpipeline.pipelineConfigurationData[name].address

          # Get the task information
          externalNodeId = taskInformation.externalNodeId
          stubExtension  = taskInformation.stubExtension
          task           = taskInformation.task
          taskAddress    = pipelineAddress + '.' + task if pipelineAddress else task
          taskArgument   = taskInformation.taskArgument

          # Check if this node is listed as greedy.
          isGreedy = taskInformation.isGreedy

          # For tasks pointing to arguments (e.g. types (1) and (2) in the message above), add the information to tasksSharingNode
          # list.
          if not externalNodeId:

            # Get the tool used for the task and determine if the argument is a stub.
            information = self.getArgumentInformation(superpipeline, taskAddress, taskArgument)

            # Add other required information to the argument information data structure.
            information.nodeId        = pipelineAddress + '.' + sharedNodeId if pipelineAddress else sharedNodeId
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
            nodeType = superpipeline.getNodeType(taskAddress, externalNodeId)

            # Unique nodes can be added to tasksSharingNode and marked as added to the graph.
            if nodeType == 'unique':
              externalTask         = superpipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeId, 'task')
              externalTaskArgument = superpipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeId, 'taskArgument')
              externalTaskAddress  = taskAddress + '.' + externalTask

              # Get the tool used for the task and determine if the argument is a stub.
              information = self.getArgumentInformation(superpipeline, externalTaskAddress, externalTaskArgument)

              # Add other required information to the argument information data structure.
              information.nodeId        = taskAddress + '.' + externalNodeId
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
            elif nodeType == 'shared': sharedNodes.append((taskAddress, externalNodeId))

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
          else: self.someStubArguments(superpipeline, address + sharedNodeId, tasksSharingNode)

        # If none of the arguments are stubs, but stub arguments have been provided, there is an error in the
        # configuration file.
        elif (numberOfStubs == 0) and (numberOfStubExtensions > 0): print('graph.addSharedNodes - stub 2'); exit(0)

        # If no stub extensions are defined, either all of the arguments are stubs, or none of them are.
        elif numberOfStubExtensions == 0:

          # If all of the arguments are stubs, create all the necessary nodes and join all the tasks with all of the
          # nodes.
          if numberOfStubs == len(tasksSharingNode): self.allStubArguments(superpipeline, address + sharedNodeId, tasksSharingNode)

          # If none of the arguments are stubs, create the single node and join to all the tasks.
          elif numberOfStubs == 0: self.noStubArguments(superpipeline, address + sharedNodeId, tasksSharingNode, isFile)

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
      self.configurationFileToGraphNodeId[information.nodeId] = [str(nodeAddress + '.' + extension) for extension in information.stubExtensions]

  # If a set of shared configuration file nodes have no stubs, create the node and join to all of the tasks.
  def noStubArguments(self, superpipeline, nodeAddress, tasks, isFile):

    # Loop over the tasks, adding the necessary edges.
    for counter, information in enumerate(tasks):

      # Link the pipeline configuration file nodes to the graph node.
      self.configurationFileToGraphNodeId[information.nodeId] = [nodeAddress]

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

        # Initialise the entry in configurationFileToGraphNodeId. The created graph nodes for this configuration
        # file node will be added in the following loop over the extensions.
        self.configurationFileToGraphNodeId[information.nodeId] = []

        # Loop over the extensions associated with the stub, add nodes for the non-linked nodes and connect
        # all the nodes.
        for i, extension in enumerate(information.stubExtensions):

          # Add the extension to the attributes.
          stubArgumentAttributes                   = deepcopy(argumentAttributes)
          stubArgumentAttributes.extensions        = [str(extension)]
          stubArgumentAttributes.stubExtension     = str(extension)
          stubArgumentAttributes.isPrimaryStubNode = True if i == 0 else False

          # Add the nodes associated with the stub that are not being linked to the other tasks,
          if extension != information.stubExtension: self.addFileNode(str(nodeAddress + '.' + extension), str(nodeAddress))

          # Add the edge.
          if information.isInput: self.addEdge(str(nodeAddress + '.' + extension), information.taskAddress, attributes = stubArgumentAttributes)
          elif information.isOutput: self.addEdge(information.taskAddress, str(nodeAddress + '.' + extension), attributes = stubArgumentAttributes)

          # Add the graph node ID to the list produced by this configuration file node.
          self.configurationFileToGraphNodeId[information.nodeId].append(str(nodeAddress + '.' + extension))

      # If this is not a stub, add the edge.
      else:
        if information.isInput: self.addEdge(modifiedNodeAddress, information.taskAddress, attributes = argumentAttributes)
        elif information.isOutput: self.addEdge(information.taskAddress, modifiedNodeAddress, attributes = argumentAttributes)

        # Link the pipeline configuration file nodes to the graph node.
        self.configurationFileToGraphNodeId[information.nodeId] = [modifiedNodeAddress]

  # Join nodes together using the 'connect nodes' sections of the configuration files.
  def connectNodes(self, superpipeline):

    # Loop over the pipelines.
    for tier in superpipeline.pipelinesByTier.keys():
      for pipelineName in superpipeline.pipelinesByTier[tier]:
        pipelineData = superpipeline.getPipelineData(pipelineName)

        # Determine the pipeline address and the node address.
        address = str(pipelineData.address + '.') if pipelineData.address else str('')

        # Loop over all the pipeline connections.
        for connection in pipelineData.connections:

          # Define the source and target nodes based on the address of the current pipeline.
          source = address + connection.source
          target = address + connection.target

          # Check that the source and target are both nodes in the graph.
          if source not in self.graph: pce.pipelineErrors().invalidNodeConnection(source, target, 'source')
          if target not in self.graph: pce.pipelineErrors().invalidNodeConnection(source, target, 'target')

          # Either the source or the target must be a task and the other must be a data node. The data node can be found by membership of
          # self.configurationFileToGraphNodeId. This will also define the graph node for the configuration node id. First check if the
          # source is a data node. Set all the necessary parameters according to this.
          if source in self.configurationFileToGraphNodeId:

            # Check that the target is a task.
            if target not in self.graph: self.errors.connectionToInvalidNode(tier, pipelineName, 'target', source, target, self.graph.nodes(data = False))
            targetIsATask = True if self.getGraphNodeAttribute(target, 'nodeType') == 'task' else False

            # Redefine the source to be the node id stored in the graph.
            source        = self.configurationFileToGraphNodeId[source][0]
            sourceIsATask = False

          # Now check if it is the target that is a data node.
          elif target in self.configurationFileToGraphNodeId:

            # Check that the source is a task.
            if source not in self.graph: self.errors.connectionToInvalidNode(tier, pipelineName, 'source', source, target, self.graph.nodes(data = False))
            sourceIsATask = True if self.getGraphNodeAttribute(source, 'nodeType') == 'task' else False

            # Redefine the source to be the node id stored in the graph.
            target        = self.configurationFileToGraphNodeId[target][0]
            targetIsATask = False

          # Throw an error if neither of the source and target connection are tasks.
          # TODO ERROR
          if not sourceIsATask and not targetIsATask: print('ERROR - graph.connectNodes - neither tasks'); exit(1)

          # Determine the tool associated with the task.
          if sourceIsATask: tool = self.getGraphNodeAttribute(source, 'tool')
          elif targetIsATask: tool = self.getGraphNodeAttribute(target, 'tool')

          # Get the data associated with the task and the long form of the supplied argument.
          toolData         = superpipeline.getToolData(tool)
          longFormArgument = toolData.getLongFormArgument(connection.argument)

          # Terminate if the argument is not valid for the tool.
          #TODO ERROR
          if not longFormArgument: print('ERROR - graph.connectNodes - argument'); exit(1)

          # Get the argument attributes.
          attributes = toolData.getArgumentData(longFormArgument)

          # Add the edge to the graph.
          self.graph.add_edge(source, target, attributes = attributes)

  # Associate the configuration node ids for unique nodes that point to nodes in nested pipelines with the
  # created graph nodes.
  def findUniqueNodes(self, superpipeline):
    for tier in superpipeline.pipelinesByTier.keys():
      for pipelineName in superpipeline.pipelinesByTier[tier]:
        pipelineData = superpipeline.pipelineConfigurationData[pipelineName]
        for configurationNodeId in pipelineData.uniqueNodeAttributes:

          # Define the pipeline relative address.
          address = str(pipelineData.address + '.') if pipelineData.address else str('')

          # Get the task this node points to and determine if it is a tool or a pipeline.
          taskAddress    = address + pipelineData.getUniqueNodeAttribute(configurationNodeId, 'task')
          externalNodeId = pipelineData.getUniqueNodeAttribute(configurationNodeId, 'nodeId')
          if externalNodeId:
            externalNodeAddress = taskAddress + '.' + externalNodeId

            # If the configuration node id is already in the configurationFileToGraphNodeId structure, there has
            # been an error.
            #TODO ERROR
            if configurationNodeId in self.configurationFileToGraphNodeId: print('ERROR - findUniqueNodes'); exit(1)

            # The configuration node points to a node in a nested pipeline, so the node must have been constructed.
            # If externalNodeAddress is not in the configurationFileToGraphNodeId structure, there has been an error.
            # TODO ERROR
            if externalNodeAddress not in self.configurationFileToGraphNodeId: print('ERROR - findUniqueNodes'); exit(1)

            # Associate the configuration node with the graph node.
            self.configurationFileToGraphNodeId[configurationNodeId] = [externalNodeAddress]

  # Generate a topologically sorted graph.
  #TODO
  def generateWorkflow(self):

    #TODO SEE IF THIS UPDATED METHOD (CURRENTLY INCOMPLETE) IS BETTER THAN THE EXISTING.
    # Define a structure that holds the predecessor and successor tasks for each task in the pipeline.
    class neighbours:
      def __init__(self, predecessors, successors):
        self.predecessors = predecessors
        self.successors   = successors

    # Store all of the tasks by their tier in the pipeline.
    tasksByTier    = {}
    tasksByTier[1] = {}

    # Determine all of the tasks in the pipeline.
    remainingTasks = {}
    tasks          = []
    for nodeId in nx.topological_sort(self.graph):
      if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'task': tasks.append(nodeId)

    # Loop over all of the tasks in the pipeline and determine which have no predecessors. Store these as the first
    # tier of tasks. For all tasks, keep track of the predecessor and successor tasks for final sorting of the tasks.
    for task in tasks:

      # Get all the predecessor tasks.
      predecessors = []
      for predecessor in self.graph.predecessors(task):
        for predecessorTask in self.graph.predecessors(predecessor):
          if self.getGraphNodeAttribute(predecessorTask, 'nodeType') == 'task' and predecessorTask not in predecessors: predecessors.append(predecessorTask)

      # Get all the successor tasks.
      successors = []
      for successor in self.graph.successors(task):
        for successorTask in self.graph.successors(successor):
          if self.getGraphNodeAttribute(successorTask, 'nodeType') == 'task' and successorTask not in successors: successors.append(successorTask)

      # If the task has no predecessors, store it as a first tier task.
      if not predecessors: tasksByTier[1][task] = neighbours(predecessors, successors)
      else: remainingTasks[task] = neighbours(predecessors, successors)

    # Loop over the the tasks that have predecessors and rank the tasks by tier. Tier 2 tasks are dependent on tier 1 etc.
    tier = 2
    while len(remainingTasks) > 0:
      removeTasks       = []
      tasksByTier[tier] = {}
      for task in remainingTasks:

        # Check all the tasks predecessors and see if any of them appear in the previous tier. If so, and none of the tasks
        # are in the remainingTasks, store this task as a member of the current tier.
        hasTaskInPreviousTier   = False
        hasTaskinRemainingTasks = False
        for predecessor in remainingTasks[task].predecessors:
          if predecessor in tasksByTier[tier - 1].keys(): hasTaskInPreviousTier = True
          elif predecessor in remainingTasks: hasTaskinRemainingTasks = True

        if hasTaskInPreviousTier and not hasTaskinRemainingTasks:
          tasksByTier[tier][task] = remainingTasks[task]
          if task not in removeTasks: removeTasks.append(task)

      # All tasks that have been added to this tier need to be removed from the remaining tasks list.
      for task in removeTasks: del(remainingTasks[task])

      # Increment the tier.
      tier += 1

    # Loop over the first tier tasks until all have been added to the workflow.
    while len(tasksByTier[1]) > 0:

      # Pick a task from the first tier and step through the tiers adding tasks that connect to this task.
      tier         = 1
      task, struct = tasksByTier[tier].popitem()
      self.workflow.append(task)

      # Define the tasks available in the next tier.
      tasks = struct.successors

      # Loop over the tasks in the next tier, searching for tasks dependent on the present task.
      while len(tasks) > 0:
        availableTasks = {}
        for successor in tasks:
          if successor in tasksByTier[tier + 1]:
  
            # Check that all the predecessors to this task are already in the workflow. If not, the task cannot be
            # added to the workflow yet.
            hasPredecessors = True
            for predecessor in tasksByTier[tier + 1][successor].predecessors:
              if predecessor not in self.workflow: hasPredecessors = False
  
            # Only add the task if all predecessors are in the workflow.
            if hasPredecessors:
              noSuccessors = len(tasksByTier[tier + 1][successor].successors)
              if noSuccessors not in availableTasks: availableTasks[noSuccessors] = []
              availableTasks[noSuccessors].append(successor)
    
        # Loop over the tasks from the next tier and add to the workflow. If there are multiple tasks, prioritize
        # based on the minimum number of successors to that task. In particular, of the successor itself has no
        # successors, it should appear first in the workflow.
        tasks = []
        for noSuccessors in sorted(availableTasks):
          for task in availableTasks[noSuccessors]:
            self.workflow.append(task)
  
            # Add the sucecssors to the task added to the workflow to the tasks list. This list will be used to
            # continue extending the workflow into the next tier.
            tasks.extend(tasksByTier[tier + 1].pop(task).successors)
  
        # Increment the tier.
        tier += 1

    # If there are still tasks in reaminingTasks, not all tasks have been added to the workflow. In this case, terminate
    # since the workflow is incomplete.
    if len(remainingTasks) != 0: print('ERROR - graph.generateWorkflow - workflow incomplete'); exit(1)

    # Return the workflow.
    return self.workflow

#    # Perform a topological sort of the graph.
#    tempWorkflow = []
#    for nodeId in nx.topological_sort(self.graph):
#      nodeType = getattr(self.graph.node[nodeId]['attributes'], 'nodeType')
#      if nodeType == 'task': tempWorkflow.append(nodeId)
#
#    # The topological sort is non-unique and so the order is not necessarily the desirable order. A task
#    # can be separated from a set of tasks with which it logically belongs and still be topologically
#    # sorted. Loop over the tasks and try to keep connected tasks together.
#    task = tempWorkflow.pop(0)
#    self.workflow.append(task)
#
#    # Tasks will be removed from the tempWorkflow and placed in the final workflow. Continue working until
#    # all tasks in the pipeline have been moved to the new workflow.
#    while tempWorkflow:
#
#      # Get all of the tasks that are succeed this task by one level. This means any task that takes as input
#      # a task outputted by this task.
#      successorTasks = []
#      for successor in self.graph.successors(task):
#        for successorTask in self.graph.successors(successor):
#          if successorTask not in successorTasks and successorTask in tempWorkflow: successorTasks.append(successorTask)
#
#      # If there is a single task marked as a successor task, but this is not the task that is already indicated
#      # as the next task, check that the task can be moved. This means that the successor task needs to be checked
#      # to ensure that it does not depend on any of the intervening tasks.
#      isDescendant = False
#      if len(successorTasks) == 1:
#        testTasks = []
#        for testTask in tempWorkflow:
#          if testTask != successorTasks[0]: testTasks.append(testTask)
#        for testTask in testTasks:
#          if successorTasks[0] in nx.descendants(self.graph, testTask):
#            isDescendant = True
#            break
# 
#      # If there are multiple successor tasks, loop over the tasks and check if any of these tasks depend on
#      # each other.
#      i = 0
#      while len(successorTasks) > 1:
#        successorTask = successorTasks[i]
#
#        # For this successor task, find all tasks on which it depends.
#        isDependent      = False
#        predecessorTasks = []
#        for predecessor in self.graph.predecessors(successorTask):
#          for predecessorTask in self.graph.predecessors(predecessor): predecessorTasks.append(predecessorTask)
#
#        # Check if any of these tasks on which the successor task depends appear in the list of successor tasks.
#        # If they do, this means that this task cannot be next in the workflow.
#        for predecessorTask in predecessorTasks:
#          if predecessorTask in successorTasks:
#            isDependent = True
#            break
#
#        # If this successor task is dependent on other tasks in the list of successor tasks, move to the next task
#        # in this list.
#        if isDependent: i += 1
#
#        # Otherwise, this task can be added to the workflow and removed from the list of successor tasks and the
#        # tempWorkflow.
#        else:
#          self.workflow.append(successorTask)
#          tempWorkflow.remove(successorTask)
#          successorTasks.remove(successorTask)
#          i = 0
#                
#      # If the successor task has no successors of its own, it can be added to the workflow as the end of a set of
#      # connected tasks. Then the first task in the original topologically sorted list can be added to the workflow
#      # and its successors investigated.
#      if isDescendant or len(successorTasks) != 1:
#        task = tempWorkflow.pop(0)
#        self.workflow.append(task)
#
#      # If there is a only a single successor task, or all but one of the multiple successor tasks have already been
#      # added to the workflow, add this task to the workflow and remove from the tempWorkflow.
#      else:
#        task = successorTasks[0]
#        if task not in self.workflow: self.workflow.append(task)
#        if task in tempWorkflow: tempWorkflow.remove(task)
#
#    # Sanity check.
#    assert len(tempWorkflow) == 0
#
#    # The topological sort does not always generate the correct order. In this routine, check for
#    # cases where a task is outputting to the stream. It is possible that after this task, the
#    # topological sort could choose from multiple tasks to perform next. This routine exists to
#    # ensure that the task following is the one that expects the stream as its input.
#    #FIXME
#    incomplete = True
#    startCount = 0
#    while incomplete:
#      for counter in range(startCount, len(self.workflow)):
#        task = self.workflow[counter]
#        if counter == len(self.workflow) - 1: incomplete = False
#        else:
#          nextTask = self.workflow[counter + 1]
#
#          # If this task outputs to the stream, determine what the next task should be.
#          if self.getGraphNodeAttribute(task, 'isOutputStream'):
#            for outputNodeId in self.graph.successors(task):
#              successorTasks  = []
#              for successorTask in self.graph.successors(outputNodeId): successorTasks.append(successorTask)
#
#            # If the next task is not in the list of tasks, modify the workflow to ensure that it is.
#            successorIndex = self.workflow.index(successorTasks[0])
#            if nextTask not in successorTasks:
#
#              # Store the tasks 
#              workflowMiddle = []
#              workflowMiddle = self.workflow[counter + 1: successorIndex]
#
#              # Find all the tasks after the successor task. Once tasks have been moved around, these
#              # tasks will all be added to the end.
#              workflowEnd = []
#              workflowEnd = self.workflow[successorIndex + 1:]
#
#              # Reconstruct the workflow.
#              updatedWorkflow = []
#              for updateCount in range(0, counter + 1): updatedWorkflow.append(self.workflow[updateCount])
#              updatedWorkflow.append(successorTasks[0])
#              for updateTask in workflowMiddle: updatedWorkflow.append(updateTask)
#              for updateTask in workflowEnd: updatedWorkflow.append(updateTask)
#
#              # Update the workflow.
#              self.workflow = updatedWorkflow
#
#              # Reset the startCount. There is no need to loop over the entire workflow on the next pass.
#              startCount = counter
#              break

    # Return the workflow.
    return self.workflow

  # Determine which graph nodes are required. A node may be used by multiple tasks and may be optional
  # for some and required by others. For each node, loop over all edges and check if any of the edges
  # are listed as required. If so, the node is required and should be marked as such.
  def markRequiredNodes(self, superpipeline):

    # Loop over all option nodes.
    for nodeId in self.getNodes('option'):

      # Loop over all successor nodes (option nodes cannot have any predecessors) and check if any of
      # the edges indicate that the node is required.
      for successor in self.graph.successors(nodeId):
        if self.getArgumentAttribute(nodeId, successor, 'isRequired'):
          self.setGraphNodeAttribute(nodeId, 'isRequired', True)
          break

    # Now perform the same tasks for file nodes.
    for nodeId in self.getNodes('file'):

      # File nodes can also have predecessors.
      isRequired = False
      for predecessor in self.graph.predecessors(nodeId):
        if self.getArgumentAttribute(predecessor, nodeId, 'isRequired'):
          self.setGraphNodeAttribute(nodeId, 'isRequired', True)
          isRequired = True
          break

      # If the node has already been listed as required, there is no need to check successors.
      if not isRequired:
        for successor in self.graph.successors(nodeId):
          if self.getArgumentAttribute(nodeId, successor, 'isRequired'):
            self.setGraphNodeAttribute(nodeId, 'isRequired', True)
            break

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addTaskParameterSets(self, superpipeline, setName, gknoConf):
    gknoArguments = {}

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

        # Check if the argument is a gkno specific argument.
        if not longFormArgument:
          isGknoArgument   = False
          if argument in gknoConf.arguments.keys():
            longFormArgument = argument
            isGknoArgument   = True
          elif argument in gknoConf.shortForms.keys():
            longFormArgument = gknoConf.shortForms[argument]
            isGknoArgument   = True

          # If the argument is a gkno specific arguments, add it to the list of gkno arguments to be
          # returned.
          if isGknoArgument:
            gknoArguments[longFormArgument] = arguments[argument]
            break

          # If the argument supplied in the parameter set is invalid for the specified tool, throw an error.
          pse.parameterSetErrors().invalidArgumentInTool(task, tool, setName, argument)

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
        else:
          print(task, argument, edges)
          print('NOT HANDLED PARAMETER SET WITH MULTIPLE EDGES.'); exit(0)

    # Return any gkno arguments.
    return gknoArguments

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addPipelineParameterSets(self, superpipeline, args, setName, resourcesPath):
    for tier in reversed(superpipeline.pipelinesByTier.keys()):
      for pipelineName in superpipeline.pipelinesByTier[tier]: self.addParameterSet(superpipeline, args, pipelineName, setName, resourcesPath)

  # Add the values from a pipeline parameter set to the graph.
  def addParameterSet(self, superpipeline, args, pipelineName, setName, resourcesPath):
    parameterSet = superpipeline.getPipelineParameterSet(pipelineName, setName)

    # If the parameter set is not available, there is a problem.
    if not parameterSet: pse.parameterSetErrors().invalidParameterSet(setName, superpipeline.getAvailablePipelineParameterSets(pipelineName))

    # Loop over the nodes in the parameter set.
    nodeIds = ps.parameterSets.SM_getNodeIds(parameterSet)
    for nodeId in nodeIds:
      isAddedNode  = False
      values       = nodeIds[nodeId]
      pipelineData = superpipeline.getPipelineData(pipelineName)
      nodeAddress  = pipelineData.address + '.' + nodeId if pipelineData.address else nodeId

      # Check that the nodeAddress is valid.
      if nodeAddress not in self.configurationFileToGraphNodeId:

        # Check if this parameter set node is not a defined pipeline node, but is a valid combination of task and argument.
        # If so, the node can be added to the graph.
        if '.--' in nodeAddress:
          task, argument = nodeAddress.split('.--')
          argument       = str('--' + argument)

          # If this node is invalid, terminate.
          if task not in superpipeline.tasks or argument not in args.arguments.keys():
            Id = ps.parameterSets.SM_getDataAttributeFromNodeId(parameterSet, nodeId, 'id')
            pse.parameterSetErrors().invalidNodeInPipelineParameterSet(pipelineName, setName, nodeId, Id)

          # The task and argument are valid, so a node can be created in the graph with this node address.
          self.addNode(superpipeline, args, task, argument, values)
          isAddedNode  = True

        # If this node is invalid, terminate.
        else:
          Id = ps.parameterSets.SM_getDataAttributeFromNodeId(parameterSet, nodeId, 'id')
          pse.parameterSetErrors().invalidNodeInPipelineParameterSet(pipelineName, setName, nodeId, Id)

      # Check if any of the values begin with $(RESOURCES) or $(PWD). If so. update them.
      updatedValues = []
      for value in values:
        if isinstance(value, str) or isinstance(value, unicode):
          if value.startswith('$(PWD)'): updatedValues.append(str(value.replace('$(PWD)', '.')))
          elif value.startswith('$(RESOURCES)'): updatedValues.append(str(value.replace('$(RESOURCES)', resourcesPath)))
          else: updatedValues.append(str(value))
        else: updatedValues.append(str(value))

      # Set the values for the graph node.
      if not isAddedNode:
        for graphNodeId in self.configurationFileToGraphNodeId[nodeAddress]: self.setGraphNodeAttribute(graphNodeId, 'values', updatedValues)

  # Loop over all of the nodes for which arguments are defined on the command line and create the nodes
  # that are missing.
  def attachArgumentValuesToNodes(self, graph, superpipeline, args, arguments, nodeList):

    # Loop over all of the set pipeline arguments.
    for argument in arguments:
      values       = arguments[argument]
      graphNodeIds = args.arguments[argument].graphNodeIds

      # If there are no graph node Ids, check if the argument is imported from a tool. If so, add this argument
      # to the node list to ensure that a node is created.
      if not graphNodeIds:
        if args.arguments[argument].isImported:
          taskAddress = args.arguments[argument].importedFromTask
          tool        = graph.getGraphNodeAttribute(taskAddress, 'tool')
          nodeAddress = str(taskAddress + '.' + argument)

          # Add to the nodeList.
          nodeList.append((taskAddress, nodeAddress, tool, argument, values, True))

        # If the argument isn't imported, no node will be created and this argument will never make it to the command
        # line. Terminate if this is the case.
        else: print('ERROR - attachArgumentValuesToNodes. No graph nodes created'); exit(1)

      # If nodes are defined, set necessary attributes.
      for graphNodeId in graphNodeIds:

        # Get the stub extension associated with this node. If this is not a stub, then this will be set
        # to None. If a stub extension is defined, add this to the file name.
        stubExtension = self.getGraphNodeAttribute(graphNodeId, 'stubExtension')
        if stubExtension: updatedValues = [str(value + '.' + stubExtension) for value in values]
        else: updatedValues = values
        self.setGraphNodeAttribute(graphNodeId, 'values', updatedValues)

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

        # Add the node (or nodes if this is a stub).
        if isStub:
          for i, extension in enumerate(stubExtensions):

            # If this is the first file, designate it as the primary stub node.
            if i == 0: argumentAttributes.isPrimaryStubNode = True
            else: argumentAttributes.isPrimaryStubNode = False

            # Add the stub extension to the argument attributes.
            argumentAttributes.stubExtension = extension

            modifiedNodeAddress = str(nodeAddress + '.' + extension)
            self.addFileNode(modifiedNodeAddress, nodeAddress)

            # Add the edge.
            if isOutput: self.addEdge(taskAddress, modifiedNodeAddress, argumentAttributes)
            else: self.addEdge(modifiedNodeAddress, taskAddress, argumentAttributes)

            # Add the values to the node.
            self.setGraphNodeAttribute(modifiedNodeAddress, 'values', values)

        # If this is not a stub, add a single node.
        else:
          if isInput or isOutput: self.addFileNode(nodeAddress, nodeAddress)
          else: self.addOptionNode(nodeAddress)

          # Attach the values to the node attributes.
          self.setGraphNodeAttribute(nodeAddress, 'values', values)

          # Add the argument to the arguments data structure.
          shortFormArgument = argumentAttributes.shortFormArgument
          description       = argumentAttributes.description
          args.setAttributes(graph, [nodeAddress], argument, argumentAttributes.shortFormArgument, description)

          # Add the edge.
          if isOutput: self.addEdge(taskAddress, nodeAddress, argumentAttributes)
          else: self.addEdge(nodeAddress, taskAddress, argumentAttributes)

          # Add the values to the node.
          self.setGraphNodeAttribute(nodeAddress, 'values', values)

      # If the node already exists, just add the values to the node.
      else: self.setGraphNodeAttribute(nodeAddress, 'values', values)

  # Expand lists of arguments attached to nodes.
  def expandLists(self):
    nodeIds = []

    # First, check all of the option nods.
    for nodeId in self.getNodes('file'): nodeIds.append((nodeId, 'file'))
    for nodeId in self.getNodes('option'): nodeIds.append((nodeId, 'option'))

    # Loop over all the option and file nodes.
    for nodeId, nodeType in nodeIds:

      # Only look at option nodes or file nodes that are predecessors to a task, but are not simultaneously
      # successors of other tasks.
      isSuccessor = True if self.graph.predecessors(nodeId) else False
      #if (nodeType == 'option') or (nodeType == 'file' and not isSuccessor):
      # FIXME CHECK IF THIS IS ALLOWED
      if True:
        values = self.getGraphNodeAttribute(nodeId, 'values')
  
        # Loop over the values and check if any of them end in '.list'. If so, this is a list of values which should be
        # opened and all the values added to the node.
        modifiedValues = []
        for value in values:
  
          # If this is a list.
          if str(value).endswith('.list'):
  
            # If this is a file, get all successor tasks and check if the expected extension is list for any arguments.
            isListExtension = False
            if nodeType == 'file':
              if isSuccessor:
                for predecessorTask in self.graph.predecessors(nodeId):
                  for extension in self.getArgumentAttribute(predecessorTask, nodeId, 'extensions'):
                    if extension == 'list': isListExtension = True

              # If this is not a successor, check the successors to the task to determine the extensions to the arguments
              # and check if the extension is 'list'.
              else:
                for successorTask in self.graph.successors(nodeId):
                  for extension in self.getArgumentAttribute(nodeId, successorTask, 'extensions'):
                    if extension == 'list': isListExtension = True

            # Open the file and terminate if it doesn't exist, but only if the extension is not list.
            if isListExtension: modifiedValues.append(value)
            else: 
              data = fh.fileHandling.openFileForReading(value)
              if not data:
                try: task     = self.graph.successors(nodeId)[0]
                except: task = 'None'
                argument = self.getArgumentAttribute(nodeId, task, 'longFormArgument')
                fe.fileErrors().missingList(task, value)
    
              # Loop over the values in the file, stripping off whitespace.
              for dataValue in [name.strip() for name in data]: modifiedValues.append(dataValue)
  
          # If the value does not end with '.list', add it to the modifiedValues list.
          else: modifiedValues.append(value)
  
        # Replace the values with the modifiedValues.
        self.setGraphNodeAttribute(nodeId, 'values', modifiedValues)

  # If multiple outputs have been specified, but only single inputs with multiple options, ensure that there are
  # the same number of input files as there output files.
  def propogateInputs(self):
    for task in self.workflow:
      noOutputs      = 0
      noOptions      = 0
      isGreedy       = self.getGraphNodeAttribute(task, 'isGreedy')
      greedyArgument = self.getGraphNodeAttribute(task, 'greedyArgument')

      # Loop over all output nodes and determine the number of output files.
      for nodeId in self.graph.successors(task):
        nodeType = self.getGraphNodeAttribute(nodeId, 'nodeType')
        noValues = len(self.getGraphNodeAttribute(nodeId, 'values'))

        # Find the maximum number of output files.
        if nodeType == 'file': noOutputs = noValues if noValues > noOutputs else noOutputs

      # Loop over all input nodes and determine the max values supplied to any options..
      for nodeId in self.graph.predecessors(task):
        if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'option':
          noValues  = len(self.getGraphNodeAttribute(nodeId, 'values'))
          noOptions = noValues if noValues > noOptions else noOptions

      # If there are the same number of inopur

      # Now loop over all the input files. If there is a single input file and multiple output files, check that there
      # are as many output files as the number of values supplied to options. If this is the case, there need to be as
      # many input files as output files, so propogate the input file to the number of outputs.
      for nodeId in self.graph.predecessors(task):
        if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'file':
          values = self.getGraphNodeAttribute(nodeId, 'values')
          if len(values) == 1 and noOutputs > 1 and (noOutputs == noOptions):

            # Propogate the input file.
            for i in range(1, noOutputs): values.append(values[0])

  # Identify tasks marked as greedy and mark the nodes and edges.
  def setGreedyTasks(self, superpipeline):

    # Loop over all tasks in the pipeline.
    for task in self.workflow:

      # Get any greedy arguments associated with the task and attach the argument to the task node.
      greedyArgument = self.getGreedyArgument(superpipeline, task)
      if greedyArgument:
        self.setGraphNodeAttribute(task, 'greedyArgument', greedyArgument)

        # Loop over the tasks predecessors and find the inputs that correspond to the greedy argument. Set the
        # isGreedy flag to True for these edges.
        for predecessor in self.graph.predecessors(task):
          longFormArgument = self.getArgumentAttribute(predecessor, task, 'longFormArgument')
          if longFormArgument == greedyArgument: self.setArgumentAttribute(predecessor, task, 'isGreedy', True)

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

      # Determine general information about this task.
      consolidate = self.getGraphNodeAttribute(task, 'consolidate')

      # Determine the number of values provided to all arguments for this task.
      values = self.getArgumentValues(task)

      # Get the greedy argument associated with the task.
      greedyArgument = self.getGraphNodeAttribute(task, 'greedyArgument')

      # Loop over the different input files and determine the number of subphases.
      subphases = self.getSubphases(task, values)
      self.setGraphNodeAttribute(task, 'subphases', subphases)

      # Loop over all arguments with multiple values and ensure that they are valid.
      for argument in values:

        # If this task is already part of a division, it is not permitted for any option nodes to have multiple
        # values, unless these options are all to be applied to the same command line.
        if values[argument].type == 'option':

          # If the option can be applied multiple times on the command line, set the number of divisions to 1.
          if toolData.getArgumentAttribute(argument, 'allowMultipleValues'): divisions = 1

          # If there are the same number of option values as there are subphases, there is a value for each
          # subphase and consequently, there is no reason to split the task into divisions.
          elif values[argument].noValues == subphases: divisions = 1

          #TODO ERROR
          elif divisions > 1: print('ERROR - graph.constructFiles - division error', task, argument); exit(1)

          # If this task is split into divisions, set the number of divisions and mark this task as the task that
          # splits into divisions. This task breaks the graph into divisions and subsequent tasks either consolidate
          # the divisions, or act on the divisions already defined.
          # 
          # Note that only a single node can be supplied.
          else:
            divisions             = values[argument].noValues
            isFirstTaskInDivision = True
            if len(values[argument].nodeIds) != 1: cfe.constructFilenameErrors().multipleDivisionNodes(task, argument, values[argument].nodeIds)
            else: divisionNode = values[argument].nodeIds[0]

      # If the task only has a single division, there are no files to consolidate, so set consolidate to False.
      if divisions == 1: consolidate = False

      # Set the graph node divisions value. Note that if this task consolidates divisions, then there should only be a
      # single division. All of the outputs from the previous divisions are used in a greedy fashion by this task and so
      # the divisions are ended.
      if consolidate: divisions = 1
      self.setGraphNodeAttribute(task, 'divisions', divisions)

      # It is possible that the values for option nodes to have instructions on how to construct the values.
      self.checkOptionConstruction(superpipeline, task)

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

  # Determine the number of subphases for a tsak. This is based on the number of values given to an individual non-greedy
  # task.
  def getSubphases(self, task, values):
    subphases = 1
    for argument in values:
      if values[argument].type == 'file' and values[argument].isInput:
        isGreedy = False
        for nodeId in values[argument].nodeIds: isGreedy = self.getArgumentAttribute(nodeId, task, 'isGreedy')

        # Check that the number of subphases is valid.
        if subphases != 1 and subphases != values[argument].noValues: print('ERROR - graph.constructFiles - SUBPHASES', task); exit(1)
        if not isGreedy: subphases = values[argument].noValues

    # Return the number of subphases.
    return subphases

  # Loop over all input file nodes and check if any are marked as being a parent node. If so, this node has
  # multiple children, defined as a division. Return the number of divisions.
  def isTaskInDivision(self, task):
    for nodeId in self.getInputFileNodes(task):
      if self.getGraphNodeAttribute(nodeId, 'isParent'): return self.getGraphNodeAttribute(nodeId, 'divisions')

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
      def __init__(self, isInput, noValues, nodeType, nodeId):
        self.isInput  = isInput
        self.nodeIds  = [nodeId]
        self.noValues = noValues
        self.type     = nodeType

    # Initialise variables.
    nodeIds = []
    values  = {}

    # Loop over all of the predecessor nodes.
    for nodeId in self.graph.predecessors(task): nodeIds.append((nodeId, True))
    for nodeId in self.graph.successors(task): nodeIds.append((nodeId, False))

    # Loop over all nodes attached to the task.
    for nodeId, isInput in nodeIds:

      # If this node belings to a stub, only process the primary stub node. Accounting for all the nodes
      # will result in counting multiple values for the argument, but there was only a single value given
      # on the command line.
      if isInput:
        isStub            = self.getArgumentAttribute(nodeId, task, 'isStub')
        isPrimaryStubNode = self.getArgumentAttribute(nodeId, task, 'isPrimaryStubNode')
      else:
        isStub            = self.getArgumentAttribute(task, nodeId, 'isStub')
        isPrimaryStubNode = self.getArgumentAttribute(task, nodeId, 'isPrimaryStubNode')
      if not isStub or (isStub and isPrimaryStubNode):
        argument = self.getArgumentAttribute(nodeId, task, 'longFormArgument') if isInput else self.getArgumentAttribute(task, nodeId, 'longFormArgument')
        nodeType = self.getGraphNodeAttribute(nodeId, 'nodeType')
        noValues = len(self.getGraphNodeAttribute(nodeId, 'values'))

        # If this is the first observation of this argument, store the values.
        if argument != None:
          if argument not in values: values[argument] = argumentValues(isInput, noValues, nodeType, nodeId)
          else:
            assert nodeType == values[argument].type
            assert isInput == values[argument].isInput
            values[argument].noValues += noValues
            values[argument].nodeIds.append(nodeId)

    # Only arguments with more than one value are of interest. If the argument has zero or one value, these
    # can be simply applied on the command line without consideration of subphases or divisions.
    remove = []
    inputs = []
    for argument in values:
      if values[argument].noValues < 2: remove.append(argument)
      elif values[argument].isInput and values[argument].type == 'file': inputs.append(argument)
    for argument in remove: del(values[argument])

    # It is not permitted for a single task to have multiple input arguments with multiple values except
    # for specific circumstances. Check to ensure that these conditions are met.
    if len(inputs) > 1:

      # All of the arguments with multiple values have the same number of values.
      success  = True
      noValues = 0
      for argument in inputs:
        number  = values[argument].noValues
        isInput = values[argument].isInput
        if number > 1 and number != noValues:
          if noValues == 0: noValues = values[argument].noValues
          else:
           success = False
           break

      # If these cases aren't met, terminate.
      if not success: cle.commandLineErrors().multipleArgumentsWithMultipleValues(task, inputs)

    # Return the argument information.
    return values

  # Check if any of the option values need constructing.
  def checkOptionConstruction(self, superpipeline, task):
    tool     = self.getGraphNodeAttribute(task, 'tool')
    toolData = superpipeline.getToolData(tool)

    # Loop over all of the options.
    for nodeId in self.getOptionNodes(task):

      # Check if the option has values and if not, if it has instructions on how to construct.
      if not self.getGraphNodeAttribute(nodeId, 'values'):
        argument     = self.getArgumentAttribute(nodeId, task, 'longFormArgument')
        instructions = toolData.getArgumentAttribute(argument, 'constructionInstructions')

        # If the option has instructions, determine how to construct the value.
        if instructions:

          # If the instructions use the 'define name' method.
          if instructions['method'] == 'define name':
            values = construct.constructKnownFilename(self.graph, superpipeline, instructions, task, nodeId, argument, not self.exportParameterSet)

  # If the task is taking as input values from all previous divisions, thus terminating the division, 
  def consolidateDivisions(self, superpipeline, task):
    tool     = self.getGraphNodeAttribute(task, 'tool')
    toolData = superpipeline.getToolData(tool)

    # Loop over the output nodes for the task and find the outputs that need constructing.
    for nodeId in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeId, 'values'):

        # Get instructions for building the output file names.
        instructions = self.getArgumentAttribute(task, nodeId, 'constructionInstructions')

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
          
              # Only construct the filenames if the argument associated with this node is the correct argument from the instructions.
              if instructions['use argument'] == argument:

                # Remove the text that was added to the filename to distinguish between the different divisions.
                values = [value.replace(self.getGraphNodeAttribute(predecessor, 'divisionText'), '') for value in self.getGraphNodeAttribute(predecessor, 'values')]
  
                # Check if random text has been added and if this isn't an intermediate file, remove it.
                values = self.checkRandomText(nodeId, predecessor, values)
  
                # Add the values to the node.
                self.setGraphNodeAttribute(nodeId, 'values', construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeId, argument, values))

            # FIXME OTHER METHODS OF CONSTRUCTION
            else: print('ERROR - Haven\'t handled other construction methods - graph.consolidateDivisions'); exit(1)

          # Now link all of the outputs from the previous division nodes to this task.
          for child in self.getGraphNodeAttribute(predecessor, 'children'): self.graph.add_edge(child, task, attributes = deepcopy(self.getEdgeAttributes(predecessor, task)))

  # Check if files have random text to remove.
  def checkRandomText(self, nodeId, predecessor, values):
    isIntermediate = self.getGraphNodeAttribute(nodeId, 'isIntermediate')
    hasRandomString  = self.getGraphNodeAttribute(predecessor, 'hasRandomString')
    randomString     = self.getGraphNodeAttribute(predecessor, 'randomString')
    updatedValues  = deepcopy(values)

    # If this file is itself an intermediate file, retain the text and add its details to the node. If no
    # text has been added, add it here.
    if isIntermediate:
      if hasRandomString:
        self.setGraphNodeAttribute(nodeId, 'hasRandomString', True)
        self.setGraphNodeAttribute(nodeId, 'randomString', randomString)

    # If this is not an intermediate file, remove the text if it exists.
    elif hasRandomString:
      for value in values: updatedValues.append(value.replace(str('_' + randomString), ''))
      self.setGraphNodeAttribute('hasRandomString', False)

    # Return the updated values.
    return updatedValues

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
      for nodeId in self.graph.predecessors(task): self.addEdge(nodeId, taskID, deepcopy(self.getEdgeAttributes(nodeId, task)))

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

    # There are cases where input file names are constructed using other input files to the same task. If this is
    # the case, it is important that the input files are traversed in the correct order. If all input filenames are
    # being constructed, those that have dependencies on other input files must be handled last.
    argumentOrder = construct.determineInputFileOrder(self.graph, superpipeline, task)

    # Loop over the arguments that can be instructed in the order that guarantees all filenames can be build.
    for argument, nodeId, constructionNodeId in argumentOrder:

      # Determine the values set for this node.
      #argument = self.getArgumentAttribute(fileNodeId, task, 'longFormArgument')
      values = self.getGraphNodeAttribute(nodeId, 'values')

      # Check the greedy attribute for the task and update if necessary.
      if self.getArgumentAttribute(nodeId, task, 'isGreedy'):
        #TODO ERROR
        if not superpipeline.toolConfigurationData[tool].getArgumentAttribute(argument, 'allowMultipleValues'): print('ERROR - GREEDY'); exit(0)

        # Mark the task node to indicate that this task is greedy.
        self.setGraphNodeAttribute(task, 'isGreedy', True)

      # If there are no set values, check to see if there are instructions on how to construct the filenames. If
      # so, construct the files.
      if len(values) == 0:

        # Determine if the argument has filename construction instructions.
        #constructUsingNode = self.getGraphNodeAttribute(fileNodeId, 'constructUsingNode')
        #if constructUsingNode:
        updatedValues = construct.constructInputNode(self.graph, superpipeline, task, argument, nodeId, constructionNodeId)
        self.setGraphNodeAttribute(nodeId, 'values', updatedValues)

  # Loop over all output file nodes (for tasks with no divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def checkOutputFiles(self, superpipeline, task, greedyArgument):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeId in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeId, 'values'):
        argument     = self.getArgumentAttribute(task, nodeId, 'longFormArgument')
        instructions = self.getArgumentAttribute(task, nodeId, 'constructionInstructions')

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
          if instructions['use argument'] == greedyArgument and len(baseValues) > 0: baseValues = [baseValues[0]]

          # Check that the number of base values is the same as the number of subphases. If not, throw an error.
          # This can happen where there are multiple subphases because an input file has been given multiple
          # values, but this is not the input file used to generate the output file names.
          #
          # Allow the pipeline to continue if a parameter set is being exported.
          subphases = self.getGraphNodeAttribute(task, 'subphases')
          if len(baseValues) != subphases and not self.isExportParameterSet:

            # If there is a single base value, generate a new set of base values with the same number as there are
            # subphases by introducing an index into the filename.
            if len(baseValues) == 1: baseValues = construct.addIndexToSingleBaseValue(self.graph, superpipeline, task, instructions['use argument'], baseValues, subphases)
        
            # Otherwise, terminate.
            else:
              shortFormArgument = self.getArgumentAttribute(task, nodeId, 'shortFormArgument')
              cfe.constructFilenameErrors().numberBaseValues(task, argument, shortFormArgument, len(baseValues), subphases)

          # Construct the output filenames.
          values = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeId, argument, baseValues)

          # Having constructed the output filenames, add them to the node.
          self.setGraphNodeAttribute(nodeId, 'values', values)

        # If the method is 'define name', construct the values.
        elif instructions['method'] == 'define name':
          values = construct.constructKnownFilename(self.graph, superpipeline, instructions, task, nodeId, argument, not self.exportParameterSet)

        # If the construction method is unknown, terminate.
        else:
          argument = self.getArgumentAttribute(task, nodeId, 'longFormArgument')
          tool     = self.getGraphNodeAttribute(task, 'tool')
          tce.toolErrors().invalidConstructionMethod(task, tool, argument, instructions['method'])

  # Loop over all output file nodes (for tasks with divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def buildDivisionOutputFiles(self, superpipeline, task, divisions, divisionNode, greedyArgument):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeId in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeId, 'values'):
        instructions = self.getArgumentAttribute(task, nodeId, 'constructionInstructions')

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
          divisionValues = self.getDivisionValues(divisionNode)
          assert len(divisionValues) == divisions
          self.setGraphNodeAttribute(nodeId, 'divisions', divisions)

          # Generate a string of random text to add to the filenames. All filenames for a division should share the same
          # piece of random text. The text is appended to intermediate file to ensure no conflicts between tasks. The
          # text is removed from files that are not intermediate, so when consolidation occurs, all files from the same
          # phase/subphase, but different divisions need to have the same text.
          isIntermediate = self.getGraphNodeAttribute(nodeId, 'isIntermediate')
          randomString   = superpipeline.randomString

          # Loop over the base values (except the first - that will be dealt with at the end when updating the file node
          # that already exists), construct the output filenames, then build and add the node with an edge from the task.
          children = []
          for i in range(1, len(divisionValues)):

            # Define the name of the new node.
            fileNodeId = nodeId + str(i)
            taskNodeId = task + str(i)

            # Construct the filenames for this node. If this is the task that has first split into divisions, the argument
            # and value for the division needs to be built into the filename. If this is a task following on from the task
            # that created the divisions, this is not required.
            values       = construct.addDivisionToValue(self.graph, superpipeline, task, nodeId, instructions, baseValues, argument, divisionValues[i])
            divisionText = str('_' + argument.strip('-') + str(divisionValues[i]))

            # Copy the attributes from the existing node and update the values.
            attributes              = deepcopy(self.getNodeAttributes(nodeId))
            attributes.divisionID   = i
            attributes.divisionText = divisionText
            attributes.isChild      = True
            attributes.parent       = nodeId
            attributes.values       = values
            if isIntermediate:
              attributes.hasRandomString = True
              attributes.randomString    = randomString

            # Add the node to the list of children.
            children.append(fileNodeId)

            # Add the new file node.
            self.graph.add_node(str(fileNodeId), attributes = attributes)

            # Make a copy of the edge attributes and join the new file node to its task.
            self.graph.add_edge(str(taskNodeId), str(fileNodeId), attributes = deepcopy(self.getEdgeAttributes(task, nodeId)))

          # Now perform the same tasks for the existing node.
          values       = construct.addDivisionToValue(self.graph, superpipeline, task, nodeId, instructions, baseValues, argument, divisionValues[0])
          divisionText = str('_' + argument.strip('-') + str(divisionValues[0]))
          self.setGraphNodeAttribute(nodeId, 'children', children)
          self.setGraphNodeAttribute(nodeId, 'divisionID', 0)
          self.setGraphNodeAttribute(nodeId, 'divisionText', divisionText)
          self.setGraphNodeAttribute(nodeId, 'isParent', True)
          self.setGraphNodeAttribute(nodeId, 'values', values)

          # Check if random text was added to the values. If so, mark the nodes.
          if isIntermediate:
            self.setGraphNodeAttribute(nodeId, 'hasRandomString', True)
            self.setGraphNodeAttribute(nodeId, 'randomString', randomString)

        # If the construction method is unknown, terminate.
        else:
          argument = self.getArgumentAttribute(task, nodeId, 'longFormArgument')
          tool     = self.getGraphNodeAttribute(task, 'tool')
          tce.toolErrors().invalidConstructionMethod(task, tool, argument, instructions['method'])

  # Update the values supplied to the option argument to ensure that they do not contain any special
  # characters.
  def getDivisionValues(self, nodeId):
    updatedValues = []

    # If the option value contains a special character. If so, replace them with '.'. This will ensure
    # that there aren't conflicts with the makefile.
    for value in self.getGraphNodeAttribute(nodeId, 'values'):
      optionValue = value.replace(':', '.')
      optionValue = optionValue.replace('>', '.')
      optionValue = optionValue.replace('<', '.')
      optionValue = optionValue.replace('|', '.')
      updatedValues.append(optionValue)

    return updatedValues

  # Loop over all output file nodes (for tasks with divisions), checking that all of the filenames are
  # defined. If not, construct them if instructions are provided.
  def extendDivisionOutputFiles(self, superpipeline, task):

    # Loop over the output files nodes and check if filenames have been defined.
    for nodeId in self.graph.successors(task):
      if not self.getGraphNodeAttribute(nodeId, 'values'):
        argument     = self.getArgumentAttribute(task, nodeId, 'longFormArgument')
        instructions = self.getArgumentAttribute(task, nodeId, 'constructionInstructions')

        # If no instructions are provided for constructing the filename, terminate since there is no way that
        # these values can be generated.
        #TODO ERROR
        if not instructions: print('ERROR - graph.checkDivisionOutputFiles - 1'); exit(1)

        # Construct the filename according to the requested method.
        if instructions['method'] == 'from tool argument':
          divisions  = self.getGraphNodeAttribute(task, 'divisions')

          # Get the argument and values associated with the node that has forced the divisions.
          self.setGraphNodeAttribute(nodeId, 'divisions', divisions)

          # Loop over the children of the task and determine their values.
          children = []
          for i, child in enumerate(self.getGraphNodeAttribute(task, 'children')):
            childValues = self.getBaseValues(superpipeline, instructions, child)
            values      = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeId, argument, childValues)

            # Define the name of the new node.
            fileNodeId = nodeId + str(i + 1)

            # Get the additional text that was added to the filename.
            divisionText = self.getDivisionText(child)

            # Get a copy of the existing file node attributes along with the attributes for the output edge.
            nodeAttributes = deepcopy(self.getNodeAttributes(nodeId))
            edgeAttributes = deepcopy(self.getEdgeAttributes(task, nodeId))

            # Update the node attributes and add the node to the graph.
            nodeAttributes.values       = values
            nodeAttributes.divisionID   = i + 1
            nodeAttributes.isChild      = True
            nodeAttributes.parent       = nodeId
            nodeAttributes.divisionText = divisionText
            self.graph.add_node(str(fileNodeId), attributes = nodeAttributes)
            children.append(fileNodeId)

            # Join the task to the file node.
            self.graph.add_edge(child, fileNodeId, attributes = edgeAttributes)

          # Now perform the same tasks for the existing file node.
          baseValues   = self.getBaseValues(superpipeline, instructions, task)
          values       = construct.constructFromFilename(self.graph, superpipeline, instructions, task, nodeId, argument, baseValues)
          divisionText = self.getDivisionText(task)
          self.setGraphNodeAttribute(nodeId, 'values', values)
          self.setGraphNodeAttribute(nodeId, 'children', children)
          self.setGraphNodeAttribute(nodeId, 'divisionID', 0)
          self.setGraphNodeAttribute(nodeId, 'divisionText', divisionText)
          self.setGraphNodeAttribute(nodeId, 'isParent', True)

        # If the construction method is unknown, terminate.
        # TODO ERROR
        else: print('constructFilenames.constructFilenames - unknown method', instructions['method']); exit(0)

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

  # Check if the pipeline should be terminated earlier based on arguments and instructions in the pipeline
  # configuration file.
  def terminatePipeline(self, superpipeline):
    instructions = superpipeline.getPipelineData(superpipeline.pipeline).terminatePipeline
    if instructions:
      isTerminate = False

      # If the instructions require checking if a consolidating task has multiple files to consolidate,
      # check if the conditions are met.
      if instructions.condition == 'no consolidation': isTerminate = self.terminateConsolidate(instructions)

      # If the pipeline is to be terminated, perform the necessary actions.
      if isTerminate:

        # Begin by replacing nodes. For each definition, leave the nodes as is and move the edges to achieve
        # the replacement.
        for nodes in instructions.replaceNodes:

          # Check that a 'to' node and a 'from' node are defined.
          #FIXME ERRORS
          if 'to' not in nodes: print('ERROR - terminate pipeline 1'); exit(1)
          if 'from' not in nodes: print('ERROR - terminate pipeline 2'); exit(1)

          # Ensure that the supplied values are valid.
          if not self.getPredecessors(nodes['to']): pce.pipelineErrors().invalidNodeInTermination(superpipeline.pipeline, nodes['to'], 'to')
          if not self.getPredecessors(nodes['from']): pce.pipelineErrors().invalidNodeInTermination(superpipeline.pipeline, nodes['from'], 'from')

          # Take all edges from the 'to' node and attach them to the 'from' node.
          for predecessor in self.getPredecessors(nodes['to']):
            attributes = deepcopy(self.getEdgeAttributes(predecessor, nodes['to']))
            self.graph.add_edge(predecessor, nodes['from'], attributes = attributes)
            self.graph.remove_edge(predecessor, nodes['to'])

          # Connect the noew node to all the successors of the old node.
          for successor in self.getSuccessors(nodes['to']):
            attributes = deepcopy(self.getEdgeAttributes(nodes['to'], successor))
            self.graph.add_edge(nodes['from'], successor, attributes = attributes)
            self.graph.remove_edge(nodes['to'], successor)

          # Remove the node, now the connections have been remade.
          self.graph.remove_node(nodes['to'])

        # Delete all specified tasks and the successors.
        for task in instructions.deleteTasks:
          self.graph.remove_node(task)

          # Remove the task from the workflow.
          self.workflow.remove(task)

  # Check if a pipeline should terminate based on a consolidating task.
  def terminateConsolidate(self, instructions):
    task = instructions.consolidatingTask
 
    #FIXME ERROR
    if not task: print('ERROR - terminateConsolidate 1'); exit(1)
    if task not in self.workflow: print('ERROR - terminateConsolidate 2'); exit(1)
    if not self.getGraphNodeAttribute(task, 'consolidate'): print('ERROR - terminateConsolidate 3'); exit(1)

    # Check if the consolidating task has any predecessors that are children. If so, the pipeline should not
    # terminate early.
    for predecessor in self.getPredecessors(task):
      if self.getGraphNodeAttribute(predecessor, 'isChild'): return False
    return True

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
        outputStreamNodeIds = {}
        for nodeId in self.graph.successors(task):
          streamInstructions = self.getArgumentAttribute(task, nodeId, 'outputStreamInstructions')
          if streamInstructions:
            if nodeId not in outputStreamNodeIds: outputStreamNodeIds[nodeId] = []
            outputStreamNodeIds[nodeId].append(streamInstructions)
            self.setArgumentAttribute(task, nodeId, 'isStream', True)

            # Mark the file node which is being streamed.
            self.setGraphNodeAttribute(nodeId, 'isStream', True)

        # If no arguments were found that can output to a stream, terminate.
        if not outputStreamNodeIds: pce.pipelineErrors().noOutputStreamArgument(task, tool)

        # Any individual task can only produce a single output stream, however, if this task generates multiple
        # outputs, or is executed multiple times, each of the separate subphases can output to a stream. Check
        # that any tasks with multiple output streams conform to this requirement.
        if len(outputStreamNodeIds) > 1:
          #TODO ERROR
          if not isGeneratesMultipleNodes and not isMultipleTaskCalls: print('MULTIPLE OUTPUT STREAM - graph.checkStreams - 2'); exit(1)

        # If the nodes stored in streamNodeIds can be used as streaming nodes, they must also be inputs to
        # other tasks in  the pipeline and the have instructions on how the values should be used when the
        # input is a stream. Check that this is the case.
        inputStreamNodeIds = {}
        for nodeId in outputStreamNodeIds:

          # If the node has no successors, it cannot be streamed.
          #TODO ERROR
          if not self.graph.successors(nodeId): print('ERROR - NO TASK TO STREAM TO. graph.checkStreams - 3'); exit(1)

          # Loop over all tasks that are successors to this node and check that one and only one of these
          # tasks is marked as accepting a stream as input.
          for successorTask in self.graph.successors(nodeId):
            isInputStream      = self.getGraphNodeAttribute(successorTask, 'isInputStream')
            streamInstructions = self.getArgumentAttribute(nodeId, successorTask, 'inputStreamInstructions')
            successorTool      = self.getGraphNodeAttribute(successorTask, 'tool')

            # If this task is marked as accepting a stream and the argument has instructions on how to handle a
            # streaming input, store the task and mark the edge as a stream.
            if isInputStream and streamInstructions:

              # Each nodeId can only have a single output node to stream to. If the node ID is already in the
              # inputStreamNodeIds, this is not the case,
              if nodeId in inputStreamNodeIds: print('ERROR - Multiple OUPTUT STREAM - graph.checkStreams - 3b'); exit(1)
              inputStreamNodeIds[nodeId] = successorTask
              self.setArgumentAttribute(nodeId, successorTask, 'isStream', True)

            # If the input is a stream and there are no instructions on how to process the argument, fail.
            if isInputStream and not streamInstructions: pce.pipelineErrors().noStreamInstructions(task, tool, successorTask, successorTool)

        # If there are no nodes accepting a stream, then the pipeline cannot work.
        if not inputStreamNodeIds: pce.pipelineErrors().noNodeAcceptingStream(task, tool)

        # If there are multiple nodes accepting a stream, this is only allowed if there are multiple subphases and
        # the original task outputting to the stream itself outputs to multiple streams. If there are multiple
        # streams, check that each node ID in the outputStreamNodeIds has an equivalent in the inputStreamNodeIds.
        if len(inputStreamNodeIds) > 1:

          # TODO ERROR
          if len(inputStreamNodeIds) != len(outputStreamNodeIds): print('ERROR - DIFFERENT NUMBER OF NODES - graph.checkStreams - 5') ;exit(1)
          for nodeId in inputStreamNodeIds:
            #TODO ERROR
            if nodeId not in outputStreamNodeIds: print('ERROR - INCONSISTENT STREAMS - graph.checkStreams - 6'); exit(1)

        # The topological sort of the pipeline could produce a workflow that is inconsistent with the
        # streams. For example, there could be two tasks following the task outputting to a stream and
        # from a topological point of view, neither task is required to come first. The non-uniqueness
        # of the sort could choose either of these tasks to succeed the task outputting to a stream.
        # From the point of view of the pipeline operation, however, it is imperative that the task
        # accepting the stream should follow the task outputting to a stream.
        for nodeId in outputStreamNodeIds:
          successorTask = inputStreamNodeIds[nodeId]

          # If there are multiple nodes, this is because there are multiple subphases. There is only a need to check the
          # main node (not all the daughter nodes) since the workflow does not contain the daughter nodes.
          if not self.getGraphNodeAttribute(nodeId, 'isDaughterNode'):
            if self.workflow.index(successorTask) != self.workflow.index(task) + 1: print('ERROR - UPDATE WORKFLOW - graph.checkStreams - 7'); exit(1)

  # If a task has multiple divisions, ensure that there are the same number of input and output files for the task.
  # It is possible that n input files were specified on the command line, leading to n executions of the task, but
  # m output files were specified. This will lead to problems when constructing the command lines.
  def checkNumberOfOutputs(self):

    # Loop over all tasks in the workflow.
    for task in self.workflow:

      # Determine information about the task.
      greedyArgument = self.getGraphNodeAttribute(task, 'greedyArgument')
      isGreedy       = self.getGraphNodeAttribute(task, 'isGreedy')
      subphases      = self.getGraphNodeAttribute(task, 'subphases')

      # Determine the number of output files.
      for nodeId in self.getOutputFileNodes(task):
        argument = self.getArgumentAttribute(task, nodeId, 'longFormArgument')

        # If there are more or less output files than subphases, throw the relevant error. If the task is
        # greedy, then there should only be a single output file, regardless of the number of inputs.
        outputs = len(self.getGraphNodeAttribute(nodeId, 'values'))

        # Terminate if inconsistencies are found.
        if outputs != subphases and not isGreedy: self.errors.outputsSubphases(task, argument, outputs, subphases)
        if outputs > 1 and isGreedy: self.errors.multipleOutputsForGreedyTask(task, argument, outputs, subphases)

  # Determine after which task intermediate files should be deleted.
  def deleteFiles(self):

    # Loop over all file nodes looking for those marked as intermediate.
    for nodeId in self.getNodes('file'):
      if self.getGraphNodeAttribute(nodeId, 'isIntermediate'):

        # If this node is the child of another node (e.g. the task has been split into multiple tasks for
        # each of a set of inputs), the task nodes associated with it will not be in the workflow. If this is
        # the case, use the parent node id in the following method. After determining the task, append the 
        # original extension, checking that the resulting task exists. If the task consolidates outputs,
        # the extension is not required.
        if self.getGraphNodeAttribute(nodeId, 'isChild'):
          useNodeId = self.getGraphNodeAttribute(nodeId, 'parent')
          extension = nodeId.replace(useNodeId, '')
        else: useNodeId = nodeId

        # Get all the task nodes that use this node.
        taskNodeIds = self.graph.successors(useNodeId)

        # Determine which of these tasks is the latest task in the pipeline.
        index = 0
        for taskNodeId in taskNodeIds:
          if not self.getGraphNodeAttribute(taskNodeId, 'isChild'): index = max(index, self.workflow.index(taskNodeId))
        task = self.workflow[index]

        # Append the original extension and check if the task exists.
        if self.getGraphNodeAttribute(nodeId, 'isChild'): task = str(task + extension) if str(task + extension) in self.graph else task

        # Set the 'deleteAfterTask' value for the node to the task after whose execution the file should
        # be deleted.
        self.setGraphNodeAttribute(nodeId, 'deleteAfterTask', task)

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
  def addFileNode(self, graphNodeId, configurationFileNodeId):
    nodeAttributes = dataNodeAttributes('file')

    # Add the configuration file node address to the attributes.
    nodeAttributes.configurationFileNodeIds = [configurationFileNodeId]

    # Add the node to the graph, if it does not already exist.
    if graphNodeId not in self.graph: self.graph.add_node(str(graphNodeId), attributes = nodeAttributes)

    # If the node already exists, add the configuration file node ID to the node attributes.
    else:
      linkedConfigurationFileNodeIds = self.getGraphNodeAttribute(graphNodeId, 'configurationFileNodeIds')

      #FIXME THIS IS ADDED FOR CONNECTING NODES. CHECK.
      if not linkedConfigurationFileNodeIds: linkedConfigurationFileNodeIds = []
      if configurationFileNodeId not in linkedConfigurationFileNodeIds:
        linkedConfigurationFileNodeIds.append(configurationFileNodeId)
        self.setGraphNodeAttribute(graphNodeId, 'configurationFileNodeIds', linkedConfigurationFileNodeIds)

    # Link this configuration node ID with the created graph node ID.
    if configurationFileNodeId not in self.configurationFileToGraphNodeId:
      self.configurationFileToGraphNodeId[configurationFileNodeId] = [graphNodeId]
    else: self.configurationFileToGraphNodeId[configurationFileNodeId].append(graphNodeId)

  # Add an option node to the graph.
  def addOptionNode(self, graphNodeId):
    nodeAttributes = dataNodeAttributes('option')

    # Add the configuration file node address to the attributes.
    nodeAttributes.configurationFileNodeIds = [graphNodeId]

    # Add the option node to the graph.
    self.graph.add_node(str(graphNodeId), attributes = nodeAttributes)

    # Link this configuration node ID with the created graph node ID.
    self.configurationFileToGraphNodeId[graphNodeId] = [graphNodeId]

  # Given a task and an argument, add a new node to the graph.
  def addNode(self, superpipeline, args, task, argument, values):
    tool   = superpipeline.tasks[task]
    nodeId = str(task + '.' + argument)

    # Get the attributes for the argument.
    toolData           = superpipeline.getToolData(tool)
    argumentAttributes = toolData.getArgumentData(argument)

    # Determine if this is an input file, output file or an option.
    isInput  = argumentAttributes.isInput
    isOutput = argumentAttributes.isOutput
    if isInput or isOutput: nodeAttributes = dataNodeAttributes('file')
    else: nodeAttributes = dataNodeAttributes('option')

    # Add the values to the nodeAttributes.
    nodeAttributes.values = values

    # Add the option node to the graph.
    self.graph.add_node(str(nodeId), attributes = nodeAttributes)

    # Add the necessary edges.
    if isOutput: self.graph.add_edge(task, str(nodeId), attributes = argumentAttributes)
    else: self.graph.add_edge(str(nodeId), task, attributes = argumentAttributes)

  # Add an edge to the graph.
  def addEdge(self, source, target, attributes):
    self.graph.add_edge(source, target, attributes = deepcopy(attributes))

  # Set an attribute for a graph node.
  def setGraphNodeAttribute(self, nodeId, attribute, values):
    try: setattr(self.graph.node[nodeId]['attributes'], attribute, values)
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
  def getGraphNodeAttribute(self, nodeId, attribute):
    try: return getattr(self.graph.node[nodeId]['attributes'], attribute)
    except: return None

  # Get all the attributes for a node.
  def getNodeAttributes(self, nodeId):
    try: return self.graph.node[nodeId]['attributes']
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
    associatedNodeIds = []

    # Loop over the input nodes connected to the task and check if this corresponds to the given argument.
    for nodeId in self.graph.predecessors(task):
      if self.getArgumentAttribute(nodeId, task, 'longFormArgument') == argument: associatedNodeIds.append(nodeId)

    # TODO ERROR
    if len(associatedNodeIds) != 1: print('ERROR - graph.getNodeForInputArgument'); exit(1)

    # Return the node ID.
    return associatedNodeIds[0]

  # Check if an edge exists with the requested argument, either coming from or pointing into a given
  # task.
  def checkIfEdgeExists(self, task, argument, isPredecessor):
    edges = []

    # If the argument is an input file or an option, isPredecessor is set to true. In this case, loop over
    # all predecessor nodes and check if any predecessor nodes connect to the task node with an edge with
    # the defined argument. If this is an output file, isPredecessor is false and the successor nodes should
    # be looped over.
    if isPredecessor: nodeIds = self.graph.predecessors(task)
    else: nodeIds = self.graph.successors(task)

    # Loop over the nodes.
    for nodeId in nodeIds:
      if isPredecessor: attributes = self.graph[nodeId][task]['attributes']
      else: attributes = self.graph[task][nodeId]['attributes']

      # Check if this edge has the same argument as requested.
      if attributes.longFormArgument == argument: edges.append(nodeId)

    # Return a list of edges with the requested argument.
    return edges

  # Return a list of all input file nodes.
  def getInputFileNodes(self, task):
    fileNodeIds = []
    for nodeId in self.graph.predecessors(task):
      if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'file': fileNodeIds.append(nodeId)

    return fileNodeIds

  # Return a list of all output file nodes.
  def getOutputFileNodes(self, task):
    fileNodeIds = []
    for nodeId in self.graph.successors(task):
      if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'file': fileNodeIds.append(nodeId)

    return fileNodeIds

  # Return a list of all option nodes.
  def getOptionNodes(self, task):
    optionNodeIds = []
    for nodeId in self.graph.predecessors(task):
      if self.getGraphNodeAttribute(nodeId, 'nodeType') == 'option': optionNodeIds.append(nodeId)

    return optionNodeIds

  # Return a list of all nodes of the requested type.
  def getNodes(self, nodeType):

    # If a single node type is supplied, turn nodeType into a list.
    if not isinstance(nodeType, list): nodeType = [nodeType]

    nodeIds = []
    for nodeId in self.graph.nodes():
      if nodeType == 'all': nodeIds.append(nodeId)
      elif self.getGraphNodeAttribute(nodeId, 'nodeType') in nodeType: nodeIds.append(nodeId)

    return nodeIds

  # Get all predecessor nodes.
  def getPredecessors(self, nodeId):
    try: return self.graph.predecessors(nodeId)
    except: return False

  # Get all successor nodes.
  def getSuccessors(self, nodeId):
    try: return self.graph.successors(nodeId)
    except: return False

  #####################
  ### Class methods ###
  #####################

  # Return an attribute from a graph node.
  @classmethod
  def CM_getGraphNodeAttribute(cls, graph, nodeId, attribute):
    try: return getattr(graph.node[nodeId]['attributes'], attribute)
    except: return None

  # Set an attribute for a graph node.
  @classmethod
  def CM_setGraphNodeAttribute(cls, graph, nodeId, attribute, values):
    try: setattr(graph.node[nodeId]['attributes'], attribute, values)
    except: return False

    return True

  # Return a list of all nodes of the a requested type.
  @classmethod
  def CM_getNodes(cls, graph, nodeType):
    nodeIds = []
    for nodeId in graph.nodes():
      if cls.CM_getGraphNodeAttribute(graph, nodeId, 'nodeType') == nodeType: nodeIds.append(nodeId)

    return nodeIds

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
    nodeIds = []
    for nodeId in graph.predecessors(task):
      if cls.CM_getGraphNodeAttribute(graph, nodeId, 'nodeType') == 'file': nodeIds.append(nodeId)

    return nodeIds

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

  # Find the node id for an input argument.
  @classmethod
  def CM_getNodeForInputArgument(cls, graph, task, inputArgument):
    for predecessor in graph.predecessors(task):
      argument = cls.CM_getArgumentAttribute(graph, predecessor, task, 'longFormArgument')
      if argument == inputArgument: return predecessor
  
    # If no node with the correct argument was found, return None.
    return None

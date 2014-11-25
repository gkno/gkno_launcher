#!/bin/bash/python

from __future__ import print_function
from collections import deque
import graphErrors
import networkx as nx
import parameterSets as ps

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

# Define a data structure for task nodes.
class taskNodeAttributes:
  def __init__(self):

    # Define the node type.
    self.nodeType = 'task'

    # Define the tool to be used to execute this task.
    self.tool = None

# Define a data structure for file/option nodes.
class dataNodeAttributes:
  def __init__(self, nodeType):

    # Define the node type.
    self.nodeType = nodeType

    # Store values for this node.
    self.values = []

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

      # Define the pipeline relative address.
      address = str(pipeline.address + '.') if pipeline.address else str('')

      # Determine if this node has already been added to the graph. Only proceed with processing
      # this node if it hasn't already been added.
      nodeAddress = address + nodeID
      if nodeAddress not in superPipeline.nodesInGraph:

        # Get the task this node points to and determine if it is a tool or a pipeline.
        task         = pipeline.getUniqueNodeAttribute(nodeID, 'task')
        taskArgument = pipeline.getUniqueNodeAttribute(nodeID, 'taskArgument')
        taskAddress  = address + task
  
        # Check to see if the task runs a tool or a pipeline.
        tool = superPipeline.getTool(taskAddress)
  
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
          self.addStubNodes(nodeAddress, stubExtensions)
          self.addStubEdges(nodeAddress, taskAddress, stubExtensions, argumentAttributes, isInput = True)
        elif isInput:
          nodeAttributes = dataNodeAttributes('file')
          self.graph.add_node(str(nodeAddress), attributes = nodeAttributes)
          self.addEdge(nodeAddress, taskAddress, argumentAttributes)
        elif isOutput and isStub:
          self.addStubNodes(nodeAddress, stubExtensions)
          self.addStubEdges(taskAddress, nodeAddress, stubExtensions, argumentAttributes, isInput = False)
        elif isOutput:
          nodeAttributes = dataNodeAttributes('file')
          self.graph.add_node(str(nodeAddress), attributes = nodeAttributes)
          self.addEdge(taskAddress, nodeAddress, argumentAttributes)
        else:
          nodeAttributes = dataNodeAttributes('option')
          self.graph.add_node(str(nodeAddress), attributes = nodeAttributes)
          self.addEdge(nodeAddress, taskAddress, argumentAttributes)

        # Mark this node as having been added to the graph.
        superPipeline.nodesInGraph.append(nodeAddress)

        # Link this pipeline configuration node with the created graph node.
        superPipeline.configurationNodes[nodeAddress] = nodeAddress

  # Add shared nodes to the graph.
  def addSharedNodes(self, superPipeline, pipeline):
    sharedNodes      = []
    tasksSharingNode = []

    # Define the pipeline relative address.
    address = str(pipeline.address + '.') if pipeline.address else str('')

    # Set the pipeline name. This is just the address above unless this is the top tier pipeline. In this case,
    # the name is defined as pipeline.name.
    pipelineName = pipeline.address if pipeline.address else pipeline.name

    # Loop over all the sets of shared nodes in this pipeline.
    for sharedNodeID in pipeline.getSharedNodeIDs():

      # First check that this node has not already been added to  the graph. Only proceed if it hasn't.
      if not pipelineName + '.' + sharedNodeID in superPipeline.nodesInGraph:

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
        pipelineName, sharedNodeID = sharedNodes.pop()

        # Loop over all the tasks sharing this node.
        for taskInformation in superPipeline.pipelineConfigurationData[pipelineName].getSharedNodeTasks(sharedNodeID):

          # Get the address of this pipeline.
          pipelineAddress = superPipeline.pipelineConfigurationData[pipelineName].address

          # Get the task information
          externalNodeID = taskInformation.externalNodeID
          stubExtension  = taskInformation.stubExtension
          task           = taskInformation.task
          taskAddress    = pipelineAddress + '.' + task if pipelineAddress else task
          taskArgument   = taskInformation.taskArgument

          # For tasks pointing to arguments (e.g. types 1) and 2) in the message above), add the information to tasksSharingNode
          # list.
          if not externalNodeID:

            # Get the tool used for the task and determine if the argument is a stub.
            information = self.getArgumentInformation(superPipeline, taskAddress, taskArgument)

            # Add other required information to the argument information data structure.
            information.nodeID        = pipelineAddress + '.' + sharedNodeID if pipelineAddress else sharedNodeID
            information.stubExtension = stubExtension
            information.taskAddress   = taskAddress

            # Store the information.
            tasksSharingNode.append(information)

            # Update counters on the number of stubs and input/output files.
            if information.stubExtension: numberOfStubExtensions += 1
            numberOfStubs       += information.isStub
            numberOfOutputFiles += information.isOutput
            numberOfInputFiles  += information.isInput

          # If the task points to an external node, determine if this node is a unique node or a shared node.
          else:
            nodeType = superPipeline.getNodeType(taskAddress, externalNodeID)

            # Unique nodes can be added to tasksSharingNode and marked as added to the graph.
            if nodeType == 'unique':
              externalTask         = superPipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeID, 'task')
              externalTaskArgument = superPipeline.pipelineConfigurationData[taskAddress].getUniqueNodeAttribute(externalNodeID, 'taskArgument')
              externalTaskAddress  = taskAddress + '.' + externalTask

              # Get the tool used for the task and determine if the argument is a stub.
              information = self.getArgumentInformation(superPipeline, externalTaskAddress, externalTaskArgument)

              # Add other required information to the argument information data structure.
              information.nodeID        = taskAddress + '.' + externalNodeID
              information.stubExtension = stubExtension
              information.taskAddress   = externalTaskAddress

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

            # Mark this node as having been added to the graph.
            superPipeline.nodesInGraph.append(taskAddress + '.' + externalNodeID)

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
          else: self.someStubArguments(superPipeline, address + sharedNodeID, tasksSharingNode)

        # If none of the arguments are stubs, but stub arguments have been provided, there is an error in the
        # configuration file.
        elif (numberOfStubs == 0) and (numberOfStubExtensions > 0): print('graph.addSharedNodes - stub 2'); exit(0)

        # If no stub extensions are defined, either all of the arguments are stubs, or none of them are.
        elif numberOfStubExtensions == 0:

          # If all of the arguments are stubs, create all the necessary nodes and join all the tasks with all of the
          # nodes.
          if numberOfStubs == len(tasksSharingNode): self.allStubArguments(superPipeline, address + sharedNodeID, tasksSharingNode)

          # If none of the arguments are stubs, create the single node and join to all the tasks.
          elif numberOfStubs == 0: self.noStubArguments(superPipeline, address + sharedNodeID, tasksSharingNode, isFile)

        # If the set of tasks is not capture by the above clauses, the situation is not understood.
        else: print('graph.addSharedNodes - UKNOWN SITUATION'); exit(0)

  # Get information on a tool argument and return information on whether the argument is an input, output
  # or a stub.
  def getArgumentInformation(self, superPipeline, task, argument):

    # Generate a data structure for the data.
    information = argumentInformation()

    # Get the tool used for this task and retrieve data on this tool from the super pipeline.
    information.tool = superPipeline.getTool(task)
    toolData         = superPipeline.getToolData(information.tool)

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
  def allStubArguments(self, superPipeline, nodeAddress, tasks):
    allowedExtensions = []

    # All of the stub arguments need to share the same set of extensions. Take the first task in the
    # list and create a file node for each of the extensions. Each subsequent task will be checked to 
    # ensure it shares the same extensions before being linked.
    information = tasks[0]
    for extension in tasks[0].stubExtensions:
      self.graph.add_node(str(nodeAddress + '.' + extension), attributes = dataNodeAttributes('file'))
      allowedExtensions.append(extension)

    # Loop over all the tasks sharing the node.
    for information in tasks:

      # Link the pipeline configuration file nodes to the graph node.
      superPipeline.configurationNodes[information.nodeID] = str(nodeAddress + '.' + extension)

      # Get the argument attributes associated with this argument and add the edge.
      longFormArgument, attributes = self.getAttributes(superPipeline, information.tool, information.argument)

      for extension in information.stubExtensions:
        #TODO ERROR
        if extension not in allowedExtensions: print('graph.allStubArguments'); exit(0)

        # Add the edges.
        source = str(nodeAddress + '.' + extension) if information.isInput else information.taskAddress
        target = information.taskAddress if information.isInput else str(nodeAddress + '.' + extension)
        self.graph.add_edge(source, target, attributes = attributes)

  # If a set of shared configuration file nodes have no stubs, create the node and join to all of the tasks.
  def noStubArguments(self, superPipeline, nodeAddress, tasks, isFile):

    # Add the new node to the graph.
    if isFile: nodeAttributes = dataNodeAttributes('file')
    else: nodeAttributes = dataNodeAttributes('option')
    self.graph.add_node(str(nodeAddress), attributes = nodeAttributes) 

    # Loop over the tasks, adding the necessary edges.
    for information in tasks:

      # Link the pipeline configuration file nodes to the graph node.
      superPipeline.configurationNodes[information.nodeID] = nodeAddress

      # Get the argument attributes associated with this argument and add the edge.
      longFormArgument, argumentAttributes = self.getAttributes(superPipeline, information.tool, information.argument)
      if information.isOutput: self.addEdge(information.taskAddress, nodeAddress, attributes = argumentAttributes)
      else: self.addEdge(nodeAddress, information.taskAddress, attributes = argumentAttributes)

  # If a set of shared configuration file nodes include some stubs with defined extensions to be shared, create
  # all the necessary nodes and join the correct nodes to the correct tasks.
  def someStubArguments(self, superPipeline, nodeAddress, tasks):

    # Loop over the tasks to find the stub extension associated with a stub node. All stub nodes sharing
    # this graph node must have the same stub extension.
    for information in tasks:
      if information.isStub:
        usedExtension = information.stubExtension
        break

    # Create the node to which all of the tasks link (stub nodes will have additional nodes added as they are
    # encountered).
    modifiedNodeAddress = str(nodeAddress + '.' + usedExtension)
    self.graph.add_node(str(modifiedNodeAddress), attributes = dataNodeAttributes('file'))

    # Loop over the tasks, adding the necessary edges.
    for information in tasks:

      # Link the pipeline configuration file nodes to the graph node.
      superPipeline.configurationNodes[information.nodeID] = modifiedNodeAddress

      # All of the arguments must be input or output files (since at least one of the arguments is a stub).
      # If an argument is not, there is a problem.
      if not information.isInput and not information.isOutput: print('graph.someStubsArguments'); exit(0)

      # Get the argument attributes associated with this argument and add the edge.
      longFormArgument, argumentAttributes = self.getAttributes(superPipeline, information.tool, information.argument)

      # If the argument is a stub, ensure that the extension matches the stub extension.
      if information.isStub:
        if information.stubExtension != usedExtension: print('graph.someStubsArguments'); exit(0)

        # Loop over the extensions associated with the stub, add nodes for the non-linked nodes and connect
        # all the nodes.
        for extension in information.stubExtensions:

          # Add the nodes associated with the stub that are not being linked to the other tasks,
          if extension != information.stubExtension: self.graph.add_node(str(nodeAddress + '.' + extension), attributes = dataNodeAttributes('file'))

          # Add the edge.
          if information.isInput: self.addEdge(str(nodeAddress + '.' + extension), information.taskAddress, attributes = argumentAttributes)
          elif information.isOutput: self.addEdge(information.taskAddress, str(nodeAddress + '.' + extension), attributes = argumentAttributes)

      # If this is not a stub, add the edge.
      else:
        if information.isInput: self.addEdge(modifiedNodeAddress, information.taskAddress, attributes = argumentAttributes)
        elif information.isOutput: self.addEdge(information.taskAddress, modifiedNodeAddress, attributes = argumentAttributes)

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
          if (address + nodeAddress) not in self.graph: self.graph.add_node(address + nodeAddress, attributes = dataNodeAttributes('file'))
          self.graph.add_edge(address + taskAddress, address + nodeAddress, attributes = argumentAttributes)

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
        for sourceNodeID in sourceNodeIDs: self.graph.add_edge(sourceNodeID, address + taskAddress, attributes = argumentAttributes)

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
      nodeAttributes = dataNodeAttributes('file')
      self.graph.add_node(nodeID + '.' + str(extension), attributes = nodeAttributes)

  # Add a task node to the graph.
  #TODO ADD TOOLS CLASS ATTRIBUTES TO TASK NODE.
  def addTaskNode(self, task, tool):
    attributes      = taskNodeAttributes()
    attributes.tool = tool
    self.graph.add_node(task, attributes = attributes)

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

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addTaskParameterSets(self, superPipeline, setName):

    # Loop over the workflow.
    for task in self.workflow:
      tool = self.getGraphNodeAttribute(self.graph, task, 'tool')

      # Loop over all of the arguments in the default parameter set.
      parameterSet = superPipeline.getToolParameterSet(tool, setName)
      arguments    = ps.parameterSets.getArguments(parameterSet)
      for argument in arguments:
        values           = arguments[argument]
        toolData         = superPipeline.getToolData(tool)
        longFormArgument = toolData.getLongFormArgument(argument)

        # Determine if this argument is an input or output file.
        isInput  = toolData.getArgumentAttribute(longFormArgument, 'isInput')
        isOutput = toolData.getArgumentAttribute(longFormArgument, 'isOutput')

        # Check if this edge exists.
        edges = self.checkIfEdgeExists(self.graph, task, longFormArgument, not isOutput)

        # Define the node attributes.
        if isInput or isOutput: nodeAttributes = dataNodeAttributes('file')
        else: nodeAttributes = dataNodeAttributes('option')

        # Attach the values to the node attributes.
        nodeAttributes.values = values

        # If no edges were found, create a new node, add the edges and values.
        if not edges:

          # Get the attributes for the edge.
          argumentAttributes = toolData.getArgumentData(longFormArgument)

          # Create a name for the node. This should be the name of the current task with the argument
          # appended (dashes removed).
          nodeAddress = task + '.' + longFormArgument.split('--', 1)[-1]
          if nodeAddress not in self.graph: self.graph.add_node(nodeAddress, attributes = nodeAttributes)
          if isOutput: self.graph.add_edge(str(task), str(nodeAddress), attributes = argumentAttributes)
          else: self.graph.add_edge(str(nodeAddress), str(task), attributes = argumentAttributes)

        # If a single possible edge was found, populate the relevant node with the values.
        elif len(edges) == 1: print('HELLO', edges)

        # If multiple edges were found, there are multiple nodes associated with this task using the
        # defined argument.
        #FIXME
        else: print('NOT HANDLED PARAMETER SET WITH MULTIPLE EDGES.'); exit(0)

  # Loop over the workflow adding parameter set data for all of the tasks.
  def addPipelineParameterSets(self, superPipeline, setName):
    for tier in reversed(superPipeline.pipelinesByTier.keys()):
      for pipelineName in superPipeline.pipelinesByTier[tier]:
        parameterSet = superPipeline.getPipelineParameterSet(pipelineName, setName)

        # If the parameter set is not available, there is a problem.
        if not parameterSet: print('addPipelineParameterSets - no set:', setName); exit(0)

        # Loop over the nodes in the parameter set.
        nodeIDs = ps.parameterSets.getNodeIDs(parameterSet)
        for nodeID in nodeIDs:
          values       = nodeIDs[nodeID]
          pipelineData = superPipeline.getPipelineData(pipelineName)
          nodeAddress  = pipelineData.address + '.' + nodeID if pipelineData.address else nodeID

          # Set the values for the graph node.
          self.setGraphNodeAttribute(self.graph, superPipeline.configurationNodes[nodeAddress], 'values', values)

  ######################
  ### Static methods ###
  ######################

  # Check if an edge exists with the requested argument, either coming from or pointing into a given
  # task.
  @staticmethod
  def checkIfEdgeExists(graph, task, argument, isPredecessor):
    edges = []

    # If the argument is an input file or an option, isPredecessor is set to true. In this case, loop over
    # all precessor nodes and check if any predecessor nodes connect to the task node with an edge with
    # the defined argument. If this is an output file, isPredecessor is false and the successoe nodes should
    # be looped over.
    if isPredecessor: nodeIDs = graph.predecessors(task)
    else: nodeIDs = graph.successors(task)

    # Loop over the nodes.
    for nodeID in nodeIDs:
      if isPredecessor: attributes = graph[nodeID][task]['attributes']
      else: attributes = graph[task][nodeID]['attributes']

      # Check if this edge has the same argument as requested.
      if attributes.longFormArgument == argument: edges.append(nodeID)

    # Return a list of edges with the requested argument.
    return edges

  #####################
  ### Class methods ###
  #####################

  # Return an attribute from a graph node.
  @classmethod
  def getGraphNodeAttribute(cls, graph, nodeID, attribute):
    try: return getattr(graph.node[nodeID]['attributes'], attribute)
    except: return None

  # Set an attribute for a graph node.
  @classmethod
  def setGraphNodeAttribute(cls, graph, nodeID, attribute, values):
    try: setattr(graph.node[nodeID]['attributes'], attribute, values)
    except: return False

    return True

  # Return a list of all nodes of the a requested type.
  @classmethod
  def getNodes(cls, graph, nodeType):
    nodeIDs = []
    for nodeID in graph.nodes():
      if cls.getGraphNodeAttribute(graph, nodeID, 'nodeType') == nodeType: nodeIDs.append(nodeID)

    return nodeIDs

#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataConsistencyErrors as er
import superpipeline

import json
import os
import sys

# Loop over all of the nodes in a graph and check that the values associated with it
# are of the correct type and have extensions consistent with all of the arguments
# attached to the node.
def checkValues(graph, superpipeline):

  # First, loop over all of the option nodes and check that the data types for all values
  # are valid.
  for nodeId in graph.getNodes(['option', 'file']):
    values   = graph.getGraphNodeAttribute(nodeId, 'values')
    nodeType = graph.getGraphNodeAttribute(nodeId, 'nodeType')

    # Determine if the node values are commands to evaluate at run time. If so, do not perform these checks.
    if not graph.getGraphNodeAttribute(nodeId, 'isCommandToEvaluate'):

      # Get all of the arguments that use this node and check the data types. Start with all predecessors to this node.
      expectedDataType = None
      for predecessorNodeId in graph.getPredecessors(nodeId):
        expectedDataType = checkNode(graph, superpipeline, predecessorNodeId, nodeId, nodeType, expectedDataType, values, isInput = False)

      expectedDataType = None
      for successorNodeId in graph.getSuccessors(nodeId):
        expectedDataType = checkNode(graph, superpipeline, nodeId, successorNodeId, nodeType, expectedDataType, values, isInput = True)

# Check the values for a node.
def checkNode(graph, superpipeline, source, target, nodeType, expectedDataType, values, isInput):
 
  # Define error handling,
  errors = er.consistencyErrors()

  # Get pipeline configuration data.
  data = superpipeline.pipelineConfigurationData[superpipeline.pipeline]

  # Get the required attributes.
  longFormArgument = graph.CM_getArgumentAttribute(graph.graph, source, target, 'longFormArgument')
  dataType         = graph.CM_getArgumentAttribute(graph.graph, source, target, 'dataType')

  # Check if this edge hgas been marked as a link only. This occurs when a nodes values are constructed using values from
  # another node. An edge is included to ensure that the workflow and dependencies are correct, but there will be no
  # argument associated with the edge and the following checks are not required.
  isLinkOnly = graph.CM_getArgumentAttribute(graph.graph, source, target, 'isLinkOnly')
  if not isLinkOnly:

    # If this is the first argument parsed, populate the expectedDataType variable with the data type for this argument.
    if not expectedDataType: expectedDataType = dataType
  
    # If expectedDataType is populated and this data type is different to the expectedDataType, this implies that different
    # arguments using the same values expect different data types. This is clearly impossible, so terminate.
    #TODO ERROR
    elif expectedDataType != dataType: print('dataConsistency.checkNode - 1', dataType, expectedDataType); exit(0)
  
    # Loop over each of the values for this node.
    for value in values:
  
      # Check that the data type is correct.
      #TODO ERROR
      if not isCorrectDataType(value, expectedDataType): print('dataConsistency.checkNode - 2', longFormArgument, value, dataType, type(value)); exit(0)
  
      # If this is a file, check that the extension is valid. Do not perform this check for stubs.
      if nodeType == 'file':
        if not graph.CM_getArgumentAttribute(graph.graph, source, target, 'isStub'):
          extensions = graph.CM_getArgumentAttribute(graph.graph, source, target, 'extensions')
  
          # Not all files have specified extensions. If no extensions are supplied, this check should not be performed.
          if extensions:
            task       = target if isInput else source
            fileNodeId = source if isInput else target
  
            # Fail if there was an error.
            if not checkExtensions(value, extensions):
  
              # Check if a top level pipeline argument exists.
              if longFormArgument in data.longFormArguments.keys():
                shortFormArgument = data.longFormArguments[longFormArgument].shortFormArgument
                errors.invalidExtensionPipeline(longFormArgument, shortFormArgument, value, extensions)
  
              # If no pipeline argument exists for this argument, list the task and argument.
              else:
                shortFormArgument = graph.CM_getArgumentAttribute(graph.graph, source, target, 'shortFormArgument')
                errors.invalidExtension(task, longFormArgument, shortFormArgument, value, extensions)

    # Return the expected data type
    return expectedDataType

# Check a values data type.
def isCorrectDataType(value, dataType):

  # The value can only be none, if this is a flag.
  if not value and value != 0 and dataType != 'flag': return False
  elif not value: return True

  # If the expected data type is an integer.
  if dataType == 'integer':
    try: value = int(value)
    except: return False
    return True

  # If the expected data type is a float.
  elif dataType == 'float':
    try: value = float(value)
    except: return False
    return True

  # If the expected data type is a string.
  elif dataType == 'string':
    try: value = str(value)
    except: return False
    return True

  # If the expected data type is a Boolean.
  elif dataType == 'bool':
    if value == 'true' or value == 'True' or value == 'false' or value == 'False': return True
    return False

  # If the expected data type is a flag.
  elif dataType == 'flag':
    if value == 'set' or value == 'unset': return True
    return False

  # If none of the above conditions were met, the data type is incorrect.
  return False

# Check that the file extension is valid.
def checkExtensions(value, extensions):

  # If the extensions are not known (e.g. are listed as 'no extension') do not perform this check.
  if len(extensions) == 1 and extensions[0] == 'no extension': return True

  # If the value ends with any of the extensions, return True.
  for extension in extensions:
    if value.endswith(extension): return True

  # Otherwise, return False,
  return False

# Loop over all tasks in the pipeline and check that all required values (excepting output files
# which can be constructed) have been defined.
def checkRequiredArguments(graph, superpipeline, args, isTerminate):

  # Define error handling,
  errors    = er.consistencyErrors()
  isSuccess = True

  # Keep track of nodes that can have their values constructed.
  constructableNodes = []

  # Loop over the defined pipeline arguments and check that all arguments listed as required have
  # been set.
  for argument in args.arguments:

    # If the pipeline specifies if this argument is required or not, update the properties of the nodes.
    # If not specified (i.e. isRequired == None), it is left to the tool configuration to determine if
    # the argument is required. This allows the pipeline configuration file to not only specify that an
    # argument is required even if the underlying tool doesn't require the value, the pipeline can also
    # override the tools claim that the argument is required.
    if args.arguments[argument].isRequired == False:
      for nodeId in args.arguments[argument].graphNodeIds: graph.setGraphNodeAttribute(nodeId, 'isRequired', False)
    if args.arguments[argument].isRequired:

      # Loop over the associated graph nodes and see if the values are set.
      for nodeId in args.arguments[argument].graphNodeIds:
        graph.setGraphNodeAttribute(nodeId, 'isRequired', False)

        # Check if this argument was imported from a task in the pipeline. If so, determine if there are
        # any instructions for constructing the filename (if not an option). Only terminate if the argument
        # is for an option, or there are no instructions.
        hasInstructions = False
        if args.arguments[argument].isImported:
          task            = args.arguments[argument].importedFromTask
          tool            = graph.getGraphNodeAttribute(task, 'tool')
          toolData        = superpipeline.getToolData(tool)
          hasInstructions = True if toolData.getArgumentAttribute(argument, 'constructionInstructions') else False

        # If the values haven't been set, terminate. This is a pipeline argument listed as required
        # and so must be set by the user (and not constructed).
        if not graph.getGraphNodeAttribute(nodeId, 'values') and not hasInstructions:
          isSuccess         = False
          shortFormArgument = args.arguments[argument].shortFormArgument
          description       = args.arguments[argument].description
          if isTerminate: errors.unsetRequiredArgument(argument, shortFormArgument, description)

  # Loop over all tasks in the workflow
  for task in graph.workflow:

    # Get the tool for the task.
    tool     = superpipeline.tasks[task]
    toolData = superpipeline.getToolData(tool)

    # Loop over all of the arguments for the tool and check that all required arguments have a node
    # and that the node has values.
    for argument in toolData.arguments:

      # Check if the argument is required.
      if toolData.getArgumentAttribute(argument, 'isRequired'):

        # Record if a node for this node is seen.
        foundNode = False

        # Determine if the argument is for an input file, output file or an option.
        isInput  = toolData.getArgumentAttribute(argument, 'isInput')
        isOutput = toolData.getArgumentAttribute(argument, 'isOutput')

        # If this is an output file with construction instructions, the filenames will be constructed
        # later, so this does not need to be checked. Keep track of the nodes which will be constructed
        # as these could be inputs to other tasks and so the check for existence is also not required
        # for these input files.

        # Start with input files and options.
        if not isOutput:

          # Loop over all input nodes looking for edges that use this argument.
          for nodeId in graph.CM_getInputNodes(graph.graph, task):
            edgeArgument = graph.getArgumentAttribute(nodeId, task, 'longFormArgument')

            # If this node uses the required argument.
            if edgeArgument == argument:
              foundNode = True

              # If this node has already been marked as not required (i.e. the tools requirement has been superceded
              # by instructions in the pipeline configuration file).
              if graph.getGraphNodeAttribute(nodeId, 'isRequired'):
                hasInstructions = False if graph.getArgumentAttribute(nodeId, task, 'constructionInstructions') == None else True
                hasValues       = True if len(graph.getGraphNodeAttribute(nodeId, 'values')) != 0 else False
                if not hasValues and not hasInstructions and nodeId not in constructableNodes:
                  isSuccess = False
  
                  # Check to see if this node can have it's values set with a top level pipeline argument (e.g. can
                  # be set without defining the task on the command line).
                  longFormArgument = graph.getGraphNodeAttribute(nodeId, 'longFormArgument')
                  if longFormArgument and '.' not in longFormArgument:
  
                    # Get the short form of the pipeline argument and the argument description.
                    #shortFormArgument = args.arguments[longFormArgument].shortFormArgument
                    shortFormArgument = graph.getGraphNodeAttribute(nodeId, 'shortFormArgument')
                    description       = graph.getGraphNodeAttribute(nodeId, 'description')
                    if isTerminate: errors.unsetRequiredArgument(longFormArgument, shortFormArgument, description)
  
                  # If this is not a top level argument, provide a different error.
                  # TODO CHECK THIS
                  else: 
  
                    # Get the short form version of the argument as well as the argument description. This is as defined
                    # for the tool, so if this argument can be set using a pipeline argument, these values are incorrect.
                    shortFormArgument = graph.getArgumentAttribute(nodeId, task, 'shortFormArgument')
                    description       = graph.getArgumentAttribute(nodeId, task, 'description')
                    if isTerminate: errors.unsetRequiredNestedArgument(task, argument, shortFormArgument, description, superpipeline.pipeline)

          # If there is no node for this argument, this means that the pipeline configuration file does not contain
          # a unique or shared node for this argument. In addition, the value has not been provided on the command
          # line. This means that no values will get assigned to this argument, so terminate.
          if not foundNode:
            instructions = toolData.getArgumentAttribute(argument, 'constructionInstructions')
            if not instructions: 
              isSuccess = False

              # Check if arguments were imported for this task. If so, check to see if this argument is therefore
              # available on the command line.
              if task == superpipeline.pipelineConfigurationData[superpipeline.pipeline].importArgumentsFromTool:
                if isTerminate: 
                  errors.unsetRequiredArgument(argument, args.arguments[argument].shortFormArgument, args.arguments[argument].description)
              else:
                if isTerminate: errors.noInputNode(task, tool, argument)
 
            # If there are instructions, but no node, construct the node.
            else:
              if instructions['method'] == 'from tool argument':
                argumentToUse = instructions['use argument']

                # Find all nodes for this task using this argument.
                for predecessorNodeId in graph.graph.predecessors(task):
                  if graph.getArgumentAttribute(predecessorNodeId, task, 'longFormArgument') == argumentToUse:
                    nodeAddress = str(predecessorNodeId + '.' + argument)

                    # Add the node and edge.
                    argumentAttributes = toolData.getArgumentData(argument)
                    graph.addFileNode(nodeAddress, nodeAddress)
                    graph.addEdge(nodeAddress, task, argumentAttributes)

                    # Attach the name of the node from which this filename is constructed to the node.
                    graph.setGraphNodeAttribute(nodeAddress, 'constructUsingNode', predecessorNodeId)

              # If there are instructions, but the construction method does not use another argument, create a node.
              else:
                nodeAddress = str(task + '.' + argument)

                # Add the node and edge.
                argumentAttributes = toolData.getArgumentData(argument)
                graph.addFileNode(nodeAddress, nodeAddress)
                graph.addEdge(nodeAddress, task, argumentAttributes)

        # Now consider output files.
        else:
          instructions = toolData.getArgumentAttribute(argument, 'constructionInstructions')

          # Loop over all output nodes looking for edges that use this argument.
          for nodeId in graph.CM_getOutputNodes(graph.graph, task):
            edgeArgument = graph.getArgumentAttribute(task, nodeId, 'longFormArgument')

            # If this node uses the required argument.
            if edgeArgument == argument:
              foundNode = True

              # If construction instructions are provided.
              if instructions:

                # If the construction is to proceed by using an argument from this task, ensure that that
                # argument is either set, or is itelf a successor to another task and so has the chance
                # of being set.
                if instructions['method'] == 'from tool argument':
                  longFormArgument = toolData.getLongFormArgument(instructions['use argument'])
                  foundNode        = False
                  for predecessorNodeId in graph.graph.predecessors(task):
                    edgeArgument = graph.getArgumentAttribute(predecessorNodeId, task, 'longFormArgument')
                    if edgeArgument == longFormArgument:
                      foundNode           = True
                      constructionNodeId = predecessorNodeId

                  # If the node being used to construct the file does not exist, then it cannot be used to 
                  # construct the filename and so some data must be missing.
                  if not foundNode:
                    isSuccess = False
                    if isTerminate:  errors.noNodeForConstruction(task, tool, argument, longFormArgument)

                  # If the node used to construct this filename exists, but it has no values or predecessors,
                  # it also will not be able to be used to construct the argument.
                  #elif not graph.getGraphNodeAttribute(constructionNodeId, 'values'):
                    #if not graph.graph.predecessors(constructionNodeId):
                      # TODO ERROR
                      #print('dataConsistency - checkRequiredArguments - cannot construct output', task, argument); exit(1)

                # Add the node to the list of nodes that have the potential to be constructed.
                if nodeId not in constructableNodes: constructableNodes.append(nodeId)

              # If no instructions are provided check that there are values supplied.
              if not instructions and not graph.getGraphNodeAttribute(nodeId, 'values'):
                isSuccess = False
                if isTerminate: errors.noConstructionMethod(task, tool, argument)

          # If no node exists for this argument, determine the course of action.
          if not foundNode:

            # If there are no instructions for constructing the filename, terminate.
            if not instructions: print('dataConsistency.checkRequiredArguments - no output node', task, argument); exit(1)

            # If there are instructions, but no node, construct the node.
            nodeAddress        = str(task + '.' + argument)
            argumentAttributes = toolData.getArgumentData(argument)

            # Determine if this node is a stub. If so, this is an output that is not shared with any other tasks, so
            # construct as many nodes as required.
            if argumentAttributes.isStub: #graph.constructOutputStubs()
              for i, stubExtension in enumerate(argumentAttributes.stubExtensions):
                modifiedNodeAddress              = str(nodeAddress + '.' + stubExtension)
                stubAttributes                   = deepcopy(argumentAttributes)
                stubAttributes.stubExtension     = stubExtension
                stubAttributes.isPrimaryStubNode = True if i == 0 else False
                graph.addFileNode(modifiedNodeAddress, modifiedNodeAddress)
                graph.addEdge(task, modifiedNodeAddress, stubAttributes)

            # If this is not a stub, add the node and edge.
            else:
              graph.addFileNode(nodeAddress, nodeAddress)
              graph.addEdge(task, nodeAddress, argumentAttributes)

  # Return if the operation was a success.
  return isSuccess

# Purge the graph of nodes with no values.
def purgeEmptyNodes(graph):

  # Loop over all the option nodes in the graph.
  for nodeId in graph.getNodes('option'):

    # Remove empty nodes.
    if not graph.getGraphNodeAttribute(nodeId, 'values'):
      if graph.getGraphNodeAttribute(nodeId, 'isRequired'): print('ERROR - dataConsistency - purgeEmpythNodes'); exit(1)
      graph.graph.remove_node(nodeId)

    # Remove isolated nodes.
    elif not graph.graph.predecessors(nodeId) and not graph.graph.successors(nodeId): graph.graph.remove_node(nodeId)

  # Then loop over all file nodes, removing valueless nodes.
  for nodeId in graph.getNodes('file'):
    if not graph.getGraphNodeAttribute(nodeId, 'values'):
      if graph.getGraphNodeAttribute(nodeId, 'isRequired'): print('ERROR - dataConsistency - purgeEmpythNodes'); exit(1)
      graph.graph.remove_node(nodeId)

    # Remove isolated nodes.
    elif not graph.graph.predecessors(nodeId) and not graph.graph.successors(nodeId): graph.graph.remove_node(nodeId)

# Set the aboslute paths of all the files used in the pipeline.
def setFilePaths(graph, gknoArguments, gkno):
  inputFiles    = []

  # Get the input and output paths as defined by the user.
  definedInputPath  = gkno.getGknoArgument('GKNO-INPUT-PATH', gknoArguments)
  definedOutputPath = gkno.getGknoArgument('GKNO-OUTPUT-PATH', gknoArguments)

  # Get the path of the input and the output directories.
  inputPath  = definedInputPath if definedInputPath else str('$(PWD)')
  outputPath = definedOutputPath if definedOutputPath else str('$(PWD)')

  # If the path is '.', set to $(PWD).
  if inputPath == '.': inputPath = '$(PWD)'
  if outputPath == '.': outputPath = '$(PWD)'

  # Ensure that the input and output paths end with /.
  if not inputPath.endswith('/'): inputPath += '/'
  if not outputPath.endswith('/'): outputPath += '/'

  # Parse all of the file nodes.
  for nodeId in graph.getNodes('file'):

    # Determine if the file is an input or output file. Since the node could be feeding
    # into or from multiple tasks, a file is an input, if and only if, the file nodes
    # associated with the option node have no predecessors.
    isInput = False if graph.graph.predecessors(nodeId) else True
    if isInput:
      source = nodeId
      target = graph.graph.successors(nodeId)[0]
    else:
      source = graph.graph.predecessors(nodeId)[0]
      target = nodeId

    # Determine if this is a stub,
    isStub = graph.getArgumentAttribute(source, target, 'isStub')
    if isStub: stubExtension = graph.getArgumentAttribute(source, target, 'stubExtension')

    # Determine if a file location is set for the argument. If so, add this location to the node.
    fileLocation = graph.getArgumentAttribute(source, target, 'fileLocation')
 
    # Get the values associated with the node.
    updatedValues = []
    for value in graph.getGraphNodeAttribute(nodeId, 'values'):

      # Update the value to include the extension, if this is a stub (if necessary).
      if isStub and not value.endswith(stubExtension):
        modifiedValue = str(value + stubExtension) if '.' in stubExtension else str(value + '.' + stubExtension)
      else: modifiedValue = value

      # Check if the value already has a path. If not, add the input or output path. If the path
      # was defined by the user on the command line, override any path that is already present
      # with that supplied. In addition, store all of the input files. Since these are specifically
      # defined as files that are not created by any task in the pipeline, these files need to exist
      # in order for the pipeline to run.
      if isInput:

        # If a file location is specified with the argument, the value should not have the path altered, but
        # the file location should be stored. This will be used to define where the file should exist in the
        # makefile, but will not appear in the value on the command line.
        if fileLocation:
          graph.setGraphNodeAttribute(nodeId, 'fileLocation', fileLocation)
          updatedValue = str(value)

        # Override the path if necessary.
        elif definedInputPath: updatedValue = str(inputPath + modifiedValue.split('/')[-1])
        else: updatedValue = str(modifiedValue) if '/' in modifiedValue else str(inputPath + modifiedValue)
        updatedValues.append(updatedValue)

        # Add the input files to the list of input files required by the pipeline. These will be checked to ensure
        # that they exist prior to pipeline execution.
        if fileLocation: inputFiles.append(str(fileLocation + updatedValue))
        else: inputFiles.append(updatedValue)
      else:
        if definedOutputPath: updatedValues.append(str(outputPath + modifiedValue.split('/')[-1]))
        else: updatedValues.append(str(modifiedValue) if '/' in modifiedValue else str(outputPath + modifiedValue))

    # Replace the values stored in the node with the values including the absolute path.
    graph.setGraphNodeAttribute(nodeId, 'values', updatedValues)

  # Return the list of all required input files.
  return inputFiles

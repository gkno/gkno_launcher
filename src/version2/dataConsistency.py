#!/bin/bash/python

from __future__ import print_function
import dataConsistencyErrors as er
import superpipeline

import json
import os
import sys

# Loop over all of the nodes in a graph and check that the values associated with it
# are of the correct type and have extensions consistent with all of the arguments
# attached to the node.
def checkValues(graph, superpipeline, args):

  # First, loop over all of the option nodes and check that the data types for all values
  # are valid.
  for nodeID in graph.getNodes(['option', 'file']):
    values   = graph.getGraphNodeAttribute(nodeID, 'values')
    nodeType = graph.getGraphNodeAttribute(nodeID, 'nodeType')

    # Get all of the arguments that use this node and check the data types. Start with all predecessors to this node.
    expectedDataType = None
    for predecessorNodeID in graph.getPredecessors(nodeID):
      expectedDataType = checkNode(graph, args, predecessorNodeID, nodeID, nodeType, expectedDataType, values, isInput = False)
    for successorNodeID in graph.getSuccessors(nodeID):
      expectedDataType = checkNode(graph, args, nodeID, successorNodeID, nodeType, expectedDataType, values, isInput = True)

# Check the values for a node.
def checkNode(graph, args, source, target, nodeType, expectedDataType, values, isInput):
 
  # Define error handling,
  errors = er.consistencyErrors()

  # Get the required attributes.
  longFormArgument = graph.CM_getArgumentAttribute(graph.graph, source, target, 'longFormArgument')
  dataType         = graph.CM_getArgumentAttribute(graph.graph, source, target, 'dataType')

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
          fileNodeID = source if isInput else target

          # Fail if there was an error.
          if not checkExtensions(value, extensions):

            # Check if a top level pipeline argument exists.
            if fileNodeID in args.nodeToArgument:
              pipelineLongFormArgument  = args.nodeToArgument[fileNodeID]
              pipelineShortFormArgument = args.arguments[pipelineLongFormArgument].shortFormArgument
              errors.invalidExtensionPipeline(pipelineLongFormArgument, pipelineShortFormArgument, value, extensions)

            # If no pipeline argument exists for this argument, list the task and argument.
            else:
              shortFormArgument = graph.CM_getArgumentAttribute(graph.graph, source, target, 'shortFormArgument')
              errors.invalidExtension(task, longFormArgument, shortFormArgument, value, extensions)

  # Return the expected data type
  return expectedDataType

# Check a values data type.
def isCorrectDataType(value, dataType):

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
def checkRequiredArguments(graph, superpipeline, args, isFullCheck):

  # Define error handling,
  errors = er.consistencyErrors()

  # Keep track of nodes that can have their values constructed.
  constructableNodes = []

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
          for nodeID in graph.CM_getInputNodes(graph.graph, task):
            edgeArgument = graph.getArgumentAttribute(nodeID, task, 'longFormArgument')

            # If this node uses the required argument.
            if edgeArgument == argument:
              foundNode = True

              # If this node is marked as constructable, no check is required. Only proceed with checks
              # if this node has not been added to the constructableNodes list. 
              if nodeID not in constructableNodes: 
                if not graph.getGraphNodeAttribute(nodeID, 'values'):

                  # Check to see if this node can have it's values set with a top level pipeline argument (e.g. can
                  # be set without defining the task on the command line).
                  longFormArgument = graph.getGraphNodeAttribute(nodeID, 'longFormArgument')
                  if longFormArgument and '.' not in longFormArgument:

                    # Get the short form of the pipeline argument and the argument description.
                    #shortFormArgument = args.arguments[longFormArgument].shortFormArgument
                    shortFormArgument = graph.getGraphNodeAttribute(nodeID, 'shortFormArgument')
                    description       = graph.getGraphNodeAttribute(nodeID, 'description')
                    errors.unsetRequiredArgument(longFormArgument, shortFormArgument, description)

                  # If this is not a top level argument, provide a different error.
                  # TODO CHECK THIS
                  else: 

                    # Get the short form version of the argument as well as the argument description. This is as defined
                    # for the tool, so if this argument can be set using a pipeline argument, these values are incorrect.
                    shortFormArgument = graph.getArgumentAttribute(nodeID, task, 'shortFormArgument')
                    description       = graph.getArgumentAttribute(nodeID, task, 'description')
                    errors.unsetRequiredNestedArgument(task, argument, shortFormArgument, description, superpipeline.pipeline)

          # If there is no node for this argument, this means that the pipeline configuration file does not contain
          # a unique or shared node for this argument. In addition, the value has not been provided on the command
          # line. This means that no values will get assigned to this argument, so terminate.
          if not foundNode:
            instructions = toolData.getArgumentAttribute(argument, 'constructionInstructions')
            if not instructions: errors.noInputNode(task, tool, argument)
 
            # If there are instructions, but no node, construct the node.
            else:
              if instructions['method'] == 'from tool argument':
                argumentToUse = instructions['use argument']

                # Find all nodes for this task using this argument.
                for predecessorNodeID in graph.graph.predecessors(task):
                  if graph.getArgumentAttribute(predecessorNodeID, task, 'longFormArgument') == argumentToUse:
                    nodeAddress = str(predecessorNodeID + '.' + argument)

                    # Add the node and edge.
                    argumentAttributes = toolData.getArgumentData(argument)
                    graph.addFileNode(nodeAddress, nodeAddress)
                    graph.addEdge(nodeAddress, task, argumentAttributes)

                    # Attach the name of the node from which this filename is constructed to the node.
                    graph.setGraphNodeAttribute(nodeAddress, 'constructUsingNode', predecessorNodeID)

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
          for nodeID in graph.CM_getOutputNodes(graph.graph, task):
            edgeArgument = graph.getArgumentAttribute(task, nodeID, 'longFormArgument')

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
                  for predecessorNodeID in graph.graph.predecessors(task):
                    edgeArgument = graph.getArgumentAttribute(predecessorNodeID, task, 'longFormArgument')
                    if edgeArgument == longFormArgument:
                      foundNode           = True
                      constructionNodeID = predecessorNodeID

                  # If the node being used to construct the file does not exist, then it cannot be used to 
                  # construct the filename and so some data must be missing.
                  if not foundNode: errors.noNodeForConstruction(task, tool, argument, longFormArgument)

                  # If the node used to construct this filename exists, but it has no values or predecessors,
                  # it also will not be able to be used to construct the argument.
                  #elif not graph.getGraphNodeAttribute(constructionNodeID, 'values'):
                    #if not graph.graph.predecessors(constructionNodeID):
                      # TODO ERROR
                      #print('dataConsistency - checkRequiredArguments - cannot construct output', task, argument); exit(1)

                # Add the node to the list of nodes that have the potential to be constructed.
                if nodeID not in constructableNodes: constructableNodes.append(nodeID)

              # If no instructions are provided check that there are values supplied.
              # TODO ERROR
              if not instructions and not graph.getGraphNodeAttribute(nodeID, 'values'):
                print('dataConsistency - checkRequiredArguments - output error', task, argument); exit(1)

          # If no node exists for this argument, determine the course of action.
          if not foundNode:

            # If there are no instructions for constructing the filename, terminate.
            if not instructions: print('dataConsistency.checkRequiredArguments - no output node', task, argument); exit(1)

            # If there are instructions, but no node, construct the node.
            nodeAddress        = str(task + '.' + argument)
            argumentAttributes = toolData.getArgumentData(argument)
            graph.addFileNode(nodeAddress, nodeAddress)
            graph.addEdge(task, nodeAddress, argumentAttributes)

# Purge the graph of nodes with no values.
def purgeEmptyNodes(graph):

  # Loop over all the option nodes in the graph.
  for nodeID in graph.getNodes('option'):
    if not graph.getGraphNodeAttribute(nodeID, 'values'): graph.graph.remove_node(nodeID)

  # Then loop over all file nodes, removing valueless nodes.
  for nodeID in graph.getNodes('file'):
    if not graph.getGraphNodeAttribute(nodeID, 'values'): graph.graph.remove_node(nodeID)

# Set the aboslute paths of all the files used in the pipeline.
def setFilePaths(graph, gknoArguments, gknoOptions):
  inputFiles    = []

  # Get the path of the input and the output directories.
  inputPath  = gknoArguments[gknoOptions['GKNO-INPUT-PATH'].longFormArgument][0] if gknoOptions['GKNO-INPUT-PATH'].longFormArgument in gknoArguments else '$(PWD)'
  outputPath = gknoArguments[gknoOptions['GKNO-OUTPUT-PATH'].longFormArgument][0] if gknoOptions['GKNO-OUTPUT-PATH'].longFormArgument in gknoArguments else '$(PWD)'

  # Ensure that the input and output paths end with /.
  if not inputPath.endswith('/'): inputPath += '/'
  if not outputPath.endswith('/'): outputPath += '/'

  # Parse all of the file nodes.
  for nodeID in graph.getNodes('file'):

    # Determine if the file is an input or output file. Since the node could be feeding
    # into or from multiple tasks, a file is an input, if and only if, the file nodes
    # associated with the option node have no predecessors.
    isInput = False if graph.graph.predecessors(nodeID) else True

    # Get the values associated with the node.
    updatedValues = []
    for value in graph.getGraphNodeAttribute(nodeID, 'values'):

      # Check if the value already has a path. If not, add the input or output path. In addition
      # store all of the input files. Since these are specifically defined as files that are not
      # created by any task in the pipeline, these files need to exist in order for the pipeline
      # to run.
      if isInput:
        updatedValue = str(value) if '/' in value else str(inputPath + value)
        updatedValues.append(updatedValue)
        inputFiles.append(updatedValue)
      else: updatedValues.append(str(value) if '/' in value else str(outputPath + value))

    # Replace the values stored in the node with the values including the absolute path.
    graph.setGraphNodeAttribute(nodeID, 'values', updatedValues)

  # Return the list of all required input files.
  return inputFiles

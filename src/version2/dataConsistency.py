#!/bin/bash/python

from __future__ import print_function
import dataConsistencyErrors as er
import superpipeline
import graph as gr

import json
import os
import sys

# Loop over all of the nodes in a graph and check that the values associated with it
# are of the correct type and have extensions consistene with all of the arguments
# attached to the node.
def checkValues(graph, superpipeline):

  # First, loop over all of the option nodes and check that the data types for all values
  # are valid.
  for nodeID in graph.getNodes(['option', 'file']):
    values   = graph.getGraphNodeAttribute(nodeID, 'values')
    nodeType = graph.getGraphNodeAttribute(nodeID, 'nodeType')

    # Get all of the arguments that use this node and check the data types. Start with all predecessors to this node.
    expectedDataType = None
    for predecessorNodeID in graph.getPredecessors(nodeID):
      expectedDataType = checkNode(graph, predecessorNodeID, nodeID, nodeType, expectedDataType, values)
    for successorNodeID in graph.getSuccessors(nodeID):
      expectedDataType = checkNode(graph, nodeID, successorNodeID, nodeType, expectedDataType, values)

# Check the values for a node.
def checkNode(graph, source, target, nodeType, expectedDataType, values):
 
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
          if not checkExtensions(value, extensions): errors.invalidExtension(longFormArgument, value, extensions)

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

  # If the value ends with any of the extensions, return True.
  for extension in extensions:
    if value.endswith(extension): return True

  # Otherwise, return False,
  return False

# Loop over all tasks in the pipeline and check that all required values (excepting output files
# which can be constructed) have been defined.
def checkRequiredArguments(graph, superpipeline):

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
                  if superpipeline.nodeToArgument[nodeID][2]:

                    # Get the short form of the pipeline argument and the argument description.
                    pipeline          = superpipeline.pipelineConfigurationData[superpipeline.pipeline]
                    longFormArgument  = superpipeline.nodeToArgument[nodeID][1]
                    shortFormArgument = pipeline.getArgumentAttribute(longFormArgument, 'shortFormArgument')
                    pipelineNodeID    = pipeline.getArgumentAttribute(longFormArgument, 'nodeID')
                    description       = superpipeline.getNodeAttribute(pipelineNodeID, 'description')
                    errors.unsetRequiredArgument(longFormArgument, shortFormArgument, description)

                  # If this is not a top level argument, provide a different error.
                  else: 

                    # Get the short form version of the argument as well as the argument description. This is as defined
                    # for the tool, so if this argument can be set using a pipeline argument, these values are incorrect.
                    shortFormArgument = graph.getArgumentAttribute(nodeID, task, 'shortFormArgument')
                    description       = graph.getArgumentAttribute(nodeID, task, 'description')
                    errors.unsetRequiredNestedArgument(task, argument, shortFormArgument, description, superpipeline.pipeline)


        # Now consider output files.
        else:
          hasInstructions = toolData.getArgumentAttribute(argument, 'constructionInstructions')

          # Loop over all output nodes looking for edges that use this argument.
          for nodeID in graph.CM_getOutputNodes(graph.graph, task):
            edgeArgument = graph.getArgumentAttribute(task, nodeID, 'longFormArgument')

            # If this node uses the required argument.
            if edgeArgument == argument:
              foundNode = True

              # If construction instructions are provided, just mark this node as constructable.
              if hasInstructions and nodeID not in constructableNodes: constructableNodes.append(nodeID)

              # If no instructions are provided check that there are values supplied.
              # TODO ERROR
              if not hasInstructions and not graph.getGraphNodeAttribute(nodeID, 'values'):
                print('dataConsistency - checkRequiredArguments - output error', argument); exit(1)

          # If no node exists for this argument, determine the course of action.
          if not foundNode:

            # If there are no instructions for constructing the filename, terminate.
            if not hasInstructions: print('dataConsistency.checkRequiredArguments - no output node', task, argument); exit(1)

            # If there are instructions, but no node, construct the node.
            nodeAddress        = str(task + '.' + argument.strip('-'))
            argumentAttributes = toolData.getArgumentData(argument)
            graph.graph.add_node(nodeAddress, attributes = gr.dataNodeAttributes('file'))
            graph.graph.add_edge(task, nodeAddress, attributes = argumentAttributes)

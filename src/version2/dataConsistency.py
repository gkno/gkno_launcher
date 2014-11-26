#!/bin/bash/python

from __future__ import print_function
import dataConsistencyErrors as er
import superpipeline
import graph

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

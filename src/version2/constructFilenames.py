#!/bin/bash/python

from __future__ import print_function
import superpipeline
import graph

import json
import os
import sys

# Loop through the workflow identifying nodes that require filenames to be constructed.
def constructFilenames(graph, superpipeline):
  for task in graph.workflow:

    # Check for unset output files. Any unset input files must also be the ouptut of a 
    # different task, otherwise there is no file from which to construct them. By working
    # through the workflow, the unset output file will always be encountered before the
    # input file, so all files will be correctly set.
    for nodeID in graph.CM_getOutputNodes(graph.graph, task):

      # Get the values associated with the node and if none exist, begin the process for
      # generating a filename.
      if not graph.getGraphNodeAttribute(nodeID, 'values'):

        # Get the tool associated with the task.
        tool = superpipeline.tasks[task]

        # Get the instructions for constructing the filename.
        instructions = graph.getArgumentAttribute(task, nodeID, 'constructionInstructions')
        if instructions['method'] == 'from tool argument': constructFromFilename(graph, superpipeline, instructions, task, tool, nodeID)
        else: print('constructFilenames.constructFilenames - unknown method', instructions.method); exit(0)

# Construct the filename from an input file from the same task.
def constructFromFilename(graph, superpipeline, instructions, task, tool, nodeID):

  # Get the input file from which the filenames should be built.
  try: inputArgument = instructions['use argument']
  except: print('constructFilenames.constructFromFilename - no \'use argument\' field'); exit(1)

  # Get the configuration data for this tool and get the long form version of the argument to 
  # use for building the filenames.
  toolData         = superpipeline.getToolData(tool)
  longFormArgument = toolData.getLongFormArgument(inputArgument)

  # Determine the allowed extensions for the input argument as well as whether this is a stub.
  extensions = toolData.getArgumentAttribute(longFormArgument, 'extensions')
  isStub     = toolData.getArgumentAttribute(longFormArgument, 'isStub')

  # Find all of the predecessor nodes to this task that use this argument and add their values to a
  # list.
  values = []
  for predecessorID in graph.getPredecessors(task):
    predecessorArgument = graph.getArgumentAttribute(predecessorID, task, 'longFormArgument')
    if predecessorArgument == longFormArgument:
      for value in graph.getGraphNodeAttribute(predecessorID, 'values'): values.append(value)

  # Now loop over each of the values and modify them accoriding to the provided instructions.
  modifiedValues = []
  for value in values:
    modifiedValue = value

    # Determine the extension on the input, the create a working version of the new name with the
    # extension removed.
    extension = getExtension(value, extensions)
    if extension: modifiedValue = modifiedValue.replace('.' + str(extension), '')

    # If there are instructions on text to add, add it.
    if 'modify text' in instructions: modifiedValue = modifyText(graph, toolData, instructions, task, modifiedValue)

    # Determine the extension to place on the filename.
    newExtensions = graph.getArgumentAttribute(task, nodeID, 'extensions')
    modifiedValue = furnishExtension(instructions, modifiedValue, extension, newExtensions)

    # Add the updated value to the modifiedValues list.
    modifiedValues.append(modifiedValue)

  # Update the graph node with the new values.
  graph.setGraphNodeAttribute(nodeID, 'values', modifiedValues)

# Determine the extension on a file.
def getExtension(value, extensions):

  # If the extensions list is empty, the input file can have any extension. Determine the extension
  # as everything occurring after the final '.' in the file name. If there is no '.' in the filename
  # assume that the file has no extension.
  if not extensions or extensions[0] == 'no extension':
    try: return value.rsplit('.')[-1]
    except: return None

  # If the extensions list that there is no extension, return none.
  elif len(extensions) == 1 and extensions[0] == 'no extension': return None

  # Finally, if extensions are provided, loop over the extensions and determine the extension that the
  # file has. The file must have one of these extensions otherwise it would have failed previous
  # checks.
  else:
    for extension in extensions:
      if value.endswith(extension): return extension

    # Just for completeness, if the value did not have any of the allowed extensions, fail.
    # TODO ERROR
    print('constructFilenames.getExtension - Unable to identify extension'); exit(1)

# Modify the text in a filename.
def modifyText(graph, toolData, instructions, task, value):

  # Loop over the operations to perform.
  for modify in instructions['modify text']:

    # Check that there is only a single instruction.
    #TODO ERROR
    if len(modify) != 1: print('constructionInstructions.modifyText - multiple instructions'); exit(1)

    # Get the required action.
    action       = modify.keys()[0]
    actionValues = modify[action]

    # Add text.
    if action == 'add text':
      for text in actionValues: value += str(text)

    # If a value from an argument is to be added.
    if action == 'add argument values':
      for argument in actionValues:

        # Check that this is a valid tool argument.
        longFormArgument = toolData.getLongFormArgument(argument)
        #TODO ERROR
        if not longFormArgument: print('constructFilenames.modifyText - invalid argument'); exit(1)

        # Get the node for the linked argument and then find the value.
        taskArgumentValues = []
        for predecessorID in graph.getPredecessors(task):
          if longFormArgument == graph.getArgumentAttribute(predecessorID, task, 'longFormArgument'):
            taskArgumentValues = graph.getGraphNodeAttribute(predecessorID, 'values')
            break

        # If there are multiple values, terminate for now, until a method to decide which value to use
        # is introduced.
        #TODO ERROR
        if len(taskArgumentValues) > 1: print('constructFilenames.modifyText - multiple arguments'); exit(1)
        elif len(taskArgumentValues) == 1: value += str(taskArgumentValues[0])

  # Return the modifed value.
  return value

# Determine the extension to apply to the filename.
def furnishExtension(instructions, value, originalExtension, newExtensions):

  # Determine the new extension to use if required.
  if not newExtensions or newExtensions[0] == 'no extension': newExtension = None
  else: newExtension = newExtensions[0]

  # Get the instructions.
  try: extensionInstructions = instructions['modify extension']
  except: print('constructionInstructions.furnishExtension - no instructions.'); exit(1)

  # If the new extension is to be appended to the old, replace the original extension and then
  # append the new.
  if extensionInstructions == 'append':

    # If no extension exists, fail.
    if not newExtension: print('constructionInstructions - no new extension'); exit(1)
    return str(value + '.' + originalExtension + '.' + newExtension)

  # If the extension is to omitted, just return the value with no extension added.
  elif extensionInstructions == 'omit': return str(value)

  # If the extension is to be replaced, just add the new extension.
  elif extensionInstructions == 'replace':
    if not newExtension: print('constructionInstructions - no new extension'); exit(1)
    return str(value + '.' + newExtension)

  # If the original extension is to be retained, just replace the extension and return.
  elif extensionInstructions == 'retain':
    if not originalExtension: print('constructionInstructions - no new extension'); exit(1)
    return str(value + '.' + originalExtension)

  # Any other action is not recognised.
  #TODO ERROR
  else: print('constructionInstructions.furnishExtension - unknown instruction'); exit(1)

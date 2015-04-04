#!/bin/bash/python

from __future__ import print_function
import graph as gr
import superpipeline
import stringOperations as strOps
import constructFilenameErrors as errors

import json
import os
import sys

# Construct the filenames for an input node.
def constructInputNode(graph, superpipeline, task, argument, nodeId, baseValues):

  #TODO ERROR
  if not baseValues: print('constructFilenames.constructInputNodes - no values'); exit(0)

  # Get the tool used for this value.
  tool     = superpipeline.tasks[task]
  toolData = superpipeline.toolConfigurationData[tool]

  # Get the construction instructions.
  instructions = gr.pipelineGraph.CM_getArgumentAttribute(graph, nodeId, task, 'constructionInstructions')

  # Get the long form of the argument whose values are being used for construction, as well as
  # the extensions associated with the argument.
  useArgument = toolData.getLongFormArgument(instructions['use argument'])
  extensions  = toolData.getArgumentAttribute(useArgument, 'extensions')

  # Loop over the values.
  values = []
  for value in baseValues:
    updatedValue = value

    # Determine the extension on the input, the create a working version of the new name with the
    # extension removed.
    extension = getExtension(value, extensions)
    if extension == False: print('ERROR WITH EXTENSION - constructFilenames'); exit(1)
    if extension: updatedValue = updatedValue.replace('.' + str(extension), '')

    # If there are instructions on text to add, add it.
    if 'modify text' in instructions: updatedValue = modifyText(graph, task, argument, toolData, instructions, updatedValue)

    # Determine the extension to place on the filename.
    newExtensions = gr.pipelineGraph.CM_getArgumentAttribute(graph, nodeId, task, 'extensions')
    updatedValue  = furnishExtension(instructions, updatedValue, extension, newExtensions)

    # Add the updated value to the modifiedValues list.
    values.append(updatedValue)

  # Return the constructed values.
  return values

# Update the construction instructions to include additional argument values. This is triggered because a task is
# being executed multiple times, but each execution uses the same input file - it is an option argument that is
# being changed on each exectution. As a result, the construction instructions as supplied would result in each
# execution of the task generating the same filename. The option that changes is being forced into the output
# filename to ensure that each output filename is unique, and that it is clear how the file was generated.
def updateArgumentsInInstructions(graph, instructions, task):

  # If the instructions do not contain the 'modify text' list, add it. This list provides instructions
  # on text or argument values to add to the filename, so is required to include the options.
  if 'modify text' not in instructions: instructions['modify text'] = []

  # Loop over the modify text section and record which arguments already have their values added to
  # the filename.
  else:
    listedArguments = []
    for modification in instructions['modify text']:
      if 'add argument values' in modification: listedArguments.extend(modification['add argument values'])

  # Loop over the options nodes with multiple values and get their arguments.
  addArguments = []
  for optionNodeID in gr.pipelineGraph.CM_getGraphNodeAttribute(graph, task, 'multivalueOptions'):
    optionArgument = gr.pipelineGraph.CM_getArgumentAttribute(graph, optionNodeID, task, 'longFormArgument')
    if optionArgument not in listedArguments: addArguments.append(str(optionArgument))

  # Define the new instructions block, then add it to the instructions. For each argument, add text including
  # the argument name, then instructions to include the argument value.
  if addArguments:
    for argument in addArguments:

      # Include the text.
      block = {'add text' : [str('-' + argument.strip('-') + '_')]}
      instructions['modify text'].append(block)

      # Then include the value.
      block = {'add argument values' : addArguments}
      instructions['modify text'].append(block)

# Construct the filename from an input file from the same task.
def constructFromFilename(graph, superpipeline, instructions, task, nodeId, argument, baseValues):

  # Define a list of updated values.
  updatedValues = []

  # Get the input file from which the filenames should be built.
  try: inputArgument = instructions['use argument']
  except: print('constructFilenames.constructFromFilename - no \'use argument\' field'); exit(1)

  # Get the configuration data for this tool and get the long form version of the argument to 
  # use for building the filenames.
  tool             = superpipeline.tasks[task]
  toolData         = superpipeline.getToolData(tool)
  longFormArgument = toolData.getLongFormArgument(inputArgument)

  # Determine the allowed extensions for the input argument as well as whether it is a stub.
  extensions   = toolData.getArgumentAttribute(longFormArgument, 'extensions')
  isInputAStub = toolData.getArgumentAttribute(longFormArgument, 'isStub')

  # Determine if this output file is a stub.
  isOutputAStub = toolData.getArgumentAttribute(argument, 'isStub')

  # Get the node corresponding to the input argument and determine if any random text has been added
  # to the filename. If so, get the text.
  inputNodeId   = gr.pipelineGraph.CM_getNodeForInputArgument(graph, task, inputArgument)
  hasRandomString = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, inputNodeId, 'hasRandomString')
  randomString    = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, inputNodeId, 'randomString')

  # Determine if this is an intermediate file.
  isIntermediate = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, nodeId, 'isIntermediate')

  # Now loop over each of the values and modify them accoriding to the provided instructions.
  for counter, value in enumerate(baseValues):

    # If the file being used to construct the output filename already has a path, strip this off.
    updatedValue = value.rsplit('/')[-1]

    # Determine the extension on the input, then create a working version of the new name with the
    # extension removed. This is only necessary if the input file is not a stub. If it is, it will
    # have no extension, so this becomes unnecessary.
    extension = getExtension(updatedValue, extensions)
    if extension: updatedValue = updatedValue.replace('.' + str(extension), '')

    # If there are instructions on text to add, add it.
    if 'modify text' in instructions: updatedValue = modifyText(graph, task, argument, toolData, instructions, counter, updatedValue)

    # Check if there are instructions from the pipeline configuration file to add an extra text field
    # to the filename.
    addText = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, nodeId, 'addTextToFilename')
    if addText: updatedValue += str('_' + addText)

    # If this is an intermediate file and random text has not already been added, add a segment of random text
    # to the filename to ensure that there are no conflicts.
    updatedValue, randomString = handleRandomText(graph, updatedValue, isIntermediate, hasRandomString, randomString, nodeId)

    # Determine the extension to place on the filename. If the file is a stub, do not attach the extension, just store
    # it on the node.
    newExtensions = gr.pipelineGraph.CM_getArgumentAttribute(graph, task, nodeId, 'extensions')
    updatedValue = furnishExtension(instructions, updatedValue, extension, newExtensions)

    # Add the updated value to the modifiedValues list.
    updatedValues.append(updatedValue)

  # Return the values.
  return updatedValues

# Given the base value from which to construct filenames, add the argument with multiple values and
# the specific value for this division to the filename.
def addDivisionToValue(graph, superpipeline, task, nodeId, instructions, baseValues, argument, optionValue, randomString):

  # Get tool information for this task.
  tool     = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, task, 'tool')
  toolData = superpipeline.getToolData(tool)

  # Determine the allowed extensions for the input argument as well as whether this is a stub.
  inputExtensions = toolData.getArgumentAttribute(argument, 'extensions')
  isStub          = toolData.getArgumentAttribute(argument, 'isStub')

  # Determine the extension to place on the filename.
  outputExtensions = gr.pipelineGraph.CM_getArgumentAttribute(graph, task, nodeId, 'extensions')

  # Determine if this is an intermediate file.
  isIntermediate = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, nodeId, 'isIntermediate')

  # FIXME HANDLE STUBS
  if isStub: print('NOT HANDLED STUBS FOR DIVISIONS: constructFilenames.constructDivisions'); exit(1)

  # Loop over all the values associated with the division and add the argument and value to the filename.
  updatedValues = []
  for value in baseValues:

    # If the file being used to construct the output filename already has a path, strip this off.
    updatedValue = value.rsplit('/')[-1]

    # Get the extension on this value and remove it.
    extension = getExtension(updatedValue, inputExtensions)
    if extension == False: print('ERROR WITH EXTENSION - constructFilenames'); exit(1)
    if extension: updatedValue = updatedValue.replace('.' + str(extension), '')
    updatedValue = str(updatedValue + '_' + argument.strip('-') + optionValue)

    # Check if there are instructions from the pipeline configuration file to add an extra text field
    # to the filename.
    addText = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, nodeId, 'addTextToFilename')
    if addText: updatedValue += str('_' + addText)

    # If the file is an intermediate file, add a string of random text (already supplied).
    if isIntermediate: updatedValue += str('_' + randomString)

    # Add the updated value to the list of updated values.
    updatedValues.append(furnishExtension(instructions, updatedValue, extension, outputExtensions))

  # Return the values.
  return updatedValues

# Construct a file of known name.
def constructKnownFilename(graph, superpipeline, instructions, task, nodeId, argument):
  tool     = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, task, 'tool')
  toolData = superpipeline.getToolData(tool)

  # Get the filename to use.
  value = instructions['filename']

  # Determine the number of subphases for this graph. If there are multiple subphases, is is possible
  # that any arguments from the tool whose values are used in the construction can have as many values
  # as there are subphases.
  subphases = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, task, 'subphases')

  # Loop over the number of subphases.
  if 'modify text' in instructions:
    values = [modifyText(graph, task, argument, toolData, instructions, counter, value) for counter in range(0, subphases)]
  else: values = [value] * subphases

  # Check if the 'directory argument' field is set. This will determine if the filename should be
  # prepended with a path defined by a tool argument.
  pathNodeId   = None
  pathArgument = None
  updatedValues = []
  if 'path argument' in instructions:
    pathArgument   = instructions['path argument'] 
    pathNodeId     = gr.pipelineGraph.CM_getNodeForInputArgument(graph, task, pathArgument)
    pathNodeValues = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, pathNodeId, 'values')

    # If there is a single argument for the path node, use this value for all values.
    if len(pathNodeValues) == 1:
      for value in values: updatedValues.append(str(pathNodeValues[0] + '/' + value))

    # If there are multiple path node values, but only a single argument value, the result is a new value for each
    # subphase.
    elif len(values) == 1:
      for value in pathValues: updatedValues.append(str(values[0] + '/' + value))

    # If there are the same number of values as path node values, each path node values applies to a specific subphase.
    elif len(values) == len(pathNodeValues):
      for counter, value in enumerate(values): updatedValues.append(str(pathNodeValues[counter] + '/' + value))

    # Any other combination of values is invalid.
    #TODO ERROR
    else: print('constructFilenames.constructKnownFilename - PATH VALUES.'); exit(1)
  else: updatedValues = values

  # Set the values.
  gr.pipelineGraph.CM_setGraphNodeAttribute(graph, nodeId, 'values', updatedValues)

  # Return the constructed values.
  return updatedValues

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
      if value.endswith(extension): return str(extension)

    # Just for completeness, if the value did not have any of the allowed extensions, return False.
    return False

# Modify the text in a filename.
def modifyText(graph, task, argument, toolData, instructions, counter, value):

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
      for constructionArgument in actionValues:

        # Check that this is a valid tool argument.
        longFormArgument = toolData.getLongFormArgument(constructionArgument)
        tool             = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, task, 'tool')
        if not longFormArgument: errors.constructFilenameErrors().invalidArgument(task, tool, argument, constructionArgument)

        # Get the node for the linked argument and then find the value.
        taskArgumentValues = []
        for predecessorID in graph.predecessors(task):
          if longFormArgument == gr.pipelineGraph.CM_getArgumentAttribute(graph, predecessorID, task, 'longFormArgument'):
            taskArgumentValues = gr.pipelineGraph.CM_getGraphNodeAttribute(graph, predecessorID, 'values')
            break

        # If there are multiple values, terminate for now, until a method to decide which value to use
        # is introduced.
        if len(taskArgumentValues) == 0:
          errors.constructFilenameErrors().noArgumentValuesToBuild(task, argument, constructionArgument)

        elif isinstance(counter, int): value += str(taskArgumentValues[counter])
        #TODO ERROR
        elif len(taskArgumentValues) > 1: print('constructFilenames.modifyText - multiple arguments'); exit(1)
        elif len(taskArgumentValues) == 1: value += str(taskArgumentValues[0])

  # Return the modifed value.
  return value

# Determine the extension to apply to the filename.
def furnishExtension(instructions, value, originalExtension, newExtensions):

  # Determine the new extension to use if required.
  if not newExtensions or newExtensions[0] == 'no extension': newExtension = None
  else: newExtension = str(newExtensions[0])

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

#FIXME MODIFIED TO DO A TASK AT A TIME. CAN BE DELETED?
# Loop over input nodes looking for ones that are connected to other node for construction. Construct
# the values for these nodes.
def constructInputNodes(graph, superpipeline):

  # Loop over all nodes.
  for task in graph.workflow:

    # Get the tool used for this task.
    tool     = superpipeline.tasks[task]
    toolData = superpipeline.toolConfigurationData[tool]

    # Loop over inputs to this task.
    for nodeId in graph.CM_getInputFileNodes(graph.graph, task):

      # If the node has no values and has a link to a node from which filenames can be constructed,
      # contruct the filenames.
      if graph.getGraphNodeAttribute(nodeId, 'constructUsingNode') and not graph.getGraphNodeAttribute(nodeId, 'values'):

        # Get the values from the connected node. If none exist, the filenames cannot be constructed, so
        # terminate.
        connectedValues = graph.getGraphNodeAttribute(graph.getGraphNodeAttribute(nodeId, 'constructUsingNode'), 'values')
        #TODO ERROR
        if not connectedValues: print('constructFilenames.constructInputNodes - no values'); exit(0)

        # Get the construction instructions.
        instructions = graph.getArgumentAttribute(nodeId, task, 'constructionInstructions')

        # Get the long form of the argument whose values are being used for construction, as well as
        # the extensions associated with the argument.
        longFormArgument = toolData.getLongFormArgument(instructions['use argument'])
        extensions       = toolData.getArgumentAttribute(longFormArgument, 'extensions')

        # Loop over the values.
        values = []
        for value in connectedValues:
          modifiedValue = value

          # Determine the extension on the input, the create a working version of the new name with the
          # extension removed.
          extension = getExtension(value, extensions)
          if extension == False: print('ERROR WITH EXTENSION - constructFilenames'); exit(1)
          if extension: modifiedValue = modifiedValue.replace('.' + str(extension), '')

          # If there are instructions on text to add, add it.
          if 'modify text' in instructions: modifiedValue = modifyText(graph, task, argument, toolData, instructions, modifiedValue)

          # Determine the extension to place on the filename.
          newExtensions = graph.getArgumentAttribute(nodeId, task, 'extensions')
          modifiedValue = furnishExtension(instructions, modifiedValue, extension, newExtensions)

          # Add the updated value to the modifiedValues list.
          values.append(modifiedValue)

        # Update the graph node with the new values.
        graph.setGraphNodeAttribute(nodeId, 'values', values)

# If this is an intermediate file and random text has not already been added, add a segment of random text
# to the filename to ensure that there are no conflicts. If this isn't a intermediate file and random text
# has been added, remove it.
def handleRandomText(graph, value, isIntermediate, hasRandomString, randomString, nodeId):

  # Generate a string of random text.
  if not randomString: randomString = strOps.getRandomString(8)

  updatedValue = value
  #if isIntermediate:
  if not hasRandomString: updatedValue = str(value + '_' + randomString)
  gr.pipelineGraph.CM_setGraphNodeAttribute(graph, nodeId, 'hasRandomString', True)
  gr.pipelineGraph.CM_setGraphNodeAttribute(graph, nodeId, 'randomString', randomString)

  # If this is not an intermediate file and random text has been added, remove the text.
  #elif hasRandomString:
  #  updatedValue = value.replace(str('_' + randomString), '')
  #  gr.pipelineGraph.CM_setGraphNodeAttribute(graph, nodeId, 'hasRandomString', False)

  # Return the updated value.
  return updatedValue, randomString

#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import fileHandling as fh
import makefileErrors
import stringOperations as stringOps

import json
import os
import sys

# Define a class to hold information about the command line.
class commandLineInformation():
  def __init__(self, graph, superpipeline, struct, task):

    # Store the task and tool.
    self.task     = task
    self.tool     = graph.getGraphNodeAttribute(task, 'tool')
    self.toolData = superpipeline.toolConfigurationData[self.tool]

    # Store if the task is greedy.
    self.isGreedy = graph.getGraphNodeAttribute(task, 'isGreedy')

    # Determine the number of command lines to be created for the task. This can be determined by finding
    # the phase in which the task resides in the pipeline execution structure, and then determining the
    # number of subphases and divisions within the phase. The total number of command lines is equal to the
    # product of these two values.
    self.phase          = struct.task[task]
    self.noSubphases    = struct.phaseInformation[self.phase].subphases
    self.noDivisions    = struct.phaseInformation[self.phase].divisions
    self.noCommandLines = self.noSubphases * self.noDivisions

    # Get the executable information.
    self.executable = self.toolData.executable
    self.modifier   = self.toolData.modifier
    self.path       = self.toolData.path
    self.precommand = self.toolData.precommand

    # Get the argument delimiter for this tool.
    self.delimiter = self.toolData.delimiter

    # Define and store the path to the executable.
    self.toolID = str('$(' + self.tool.upper() + '-PATH)')

    # Store the command lines for this task.
    self.commands = []

    # Store the dependencies and outputs for each command line.
    self.dependencies = []
    self.outputs      = []

# Define a class to build and manipulate makefiles.
class makefiles:
  def __init__(self):

    # Handle errors associated with makefile construction.
    self.errors = makefileErrors.makefileErrors()

    # Store the paths of all the tools executed in the pipeline.
    self.toolPaths = {}

  # Generate the command lines associated with a task.
  def generateCommandLines(self, graph, superpipeline, struct, task):

    # Generate a data structure for building the command line.
    data = commandLineInformation(graph, superpipeline, struct, task)

    # Store the tools path in the global makefiles dictionary toolPaths.
    if data.tool not in self.toolPaths: self.toolPaths[data.tool] = str(data.toolID + '-PATH)=$(TOOL_BIN)/' + data.path)

    # The output of the method is a list of command lines, one command line for each execution
    # of the task. Each command line is itself a list of the command line executable and arguments.
    # Since each command line starts with the same exeutable command, initialise the output list as
    # numberOfCommandLines individual lists, each of which is the executable command.
    command = str(data.precommand + ' ') if data.precommand else ''
    command += str(data.toolID + '/' + data.executable)
    if data.modifier: command += str(' ' + data.modifier)
    for i in range(0, data.noCommandLines): data.commands.append([command])

    # Initialise the lists of dependencies and outputs to have the same length as the commands.
    for i in range(0, data.noCommandLines):
      data.dependencies.append([])
      data.outputs.append([])

    print()
    print('======NEW TASK======')
    print('task:', data.task)
    print('\ttool:', data.tool)
    print('\tphase:', data.phase)
    print('\tsubphases:', data.noSubphases)
    print('\tdivisions:', data.noDivisions)
    print('\tcommand lines:', data.noCommandLines)

    # Loop over all input files.
    for nodeID in graph.getInputFileNodes(task): self.processFiles(graph, task, data, nodeID, isInput = True)

    # Loop over all the option nodes for this task and get the arguments and values.
    for nodeID in graph.getOptionNodes(task): self.addOption(graph, task, data, nodeID)

    # Loop over all output files.
    for nodeID in graph.getOutputFileNodes(task): self.processFiles(graph, task, data, nodeID, isInput = False)

    print()
    print('command:')
    for command in data.commands: print(command)
    print('dependencies:')
    for dependency in data.dependencies: print(dependency)
    print('outputs:')
    for output in data.outputs: print(output)

  # Process file inputt/outputs.
  def processFiles(self, graph, task, data, nodeID, isInput):

    # Check if the node is a multinode and then handle accordingly.
    multinodeInput  = graph.getGraphNodeAttribute(task, 'multinodeInput')
    multinodeOutput = graph.getGraphNodeAttribute(task, 'multinodeOutput')

    # If this is a daughter node, disregard. All daughter nodes are handled when the parent
    # node is processed.
    if graph.getGraphNodeAttribute(nodeID, 'isDaughterNode'): pass

    # If this is a parent node, process the node and its daughters.
    elif isInput and nodeID == multinodeInput: self.addSubphaseFiles(graph, task, data, nodeID, isInput)
    elif not isInput and nodeID == multinodeOutput: self.addSubphaseFiles(graph, task, data, nodeID, isInput)

    # If this is a single output node.
    else: self.addFiles(graph, task, data, nodeID, isInput)


  # Get all the command arguments for subphase input or output files.
  def addSubphaseFiles(self, graph, task, data, nodeID, isInput):

    # Initialise variables.
    i = 0

    # Get the daughter nodes.
    nodeIDs = [nodeID] + graph.getGraphNodeAttribute(nodeID, 'daughterNodes')

    # Check that the number of node IDs is the same as the number of subphases.
    #TODO ERROR
    if len(nodeIDs) != data.noSubphases: print('ERROR - makefiles.addSubphaseFiles - 1'); exit(1)

    # Get the argument associated with the node.
    if isInput: argument = graph.getArgumentAttribute(nodeIDs[0], task, 'longFormArgument')
    else: argument = graph.getArgumentAttribute(task, nodeIDs[0], 'longFormArgument')

    # TODO ADD METHIDS TO MODIFY ARGUMENTS, E.G. STREAMS ETC.

    # Loop over the input multinodes and add the values to the command line. The order is important here.
    # The values for the first multinode should be applied to all the divisions. If there are N subphases,
    # with M divisions, the first M command lines should be for the input/ouput files associated with the
    # first subphase, with the options in those M command lines being the M different values etc.
    for nodeID in nodeIDs:
      values = graph.getGraphNodeAttribute(nodeID, 'values')

      # Check if this node consolidates the multinodes.
      isConsolidate = True if graph.getGraphNodeAttribute(task, 'consolidate') else False

      # If there are less values than the number of divisions, there is a problem, unless this is a
      # consolidation node. In this case, all of the inputs files are being used in the same command line
      # and the number of command lines is reduced down to the number of subphases, e.g. the number of
      # divisions is reset to one. If this is the case, consolidate the command lines.
      #TODO ERROR
      if len(values) != data.noDivisions and not isConsolidate: print('ERROR - makefiles.getSubphaseCommands - 1'); exit(1)

      # Loop over the values and update the command lines for the task.
      for value in values:

        #TODO ADD METHODS TO MODIFY VALUE. E,G, STREAMS
        data.commands[i].append(str(argument) + str(data.delimiter) + str(value))

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(value))
        else: data.outputs[i].append(str(value))

        # If this is not a consolidation node, increment the counter.
        if not isConsolidate: i += 1

      # If this is a consolidation node, the counter was not incremented for each value, since all the
      # values should be attached to the same command line. However, when moving to the next node (e.g.
      # the next subphase), the counter needs to be incremented.
      if isConsolidate: i += 1

  # Add option values to the command lines.
  def addOption(self, graph, task, data, nodeID):

    # TODO CHECK FOR INFORMATION ON MODIFYING THE ARGUMENT AND THE VALUE.
    # Get the argument and values for the option node.
    argument = graph.getArgumentAttribute(nodeID, task, 'longFormArgument')
    values   = graph.getGraphNodeAttribute(nodeID, 'values')

    # If there is only a single value, apply this to all the command lines.
    if len(values) == 1:
      for i in range(0, data.noCommandLines): data.commands[i].append(str(argument) + str(data.delimiter) + str(values[0]))

    # If there is more than one values, ensure that the number of values is consistent with the
    # pipeline execution structure.
    else:

      # Ensure that there as many values as there are divisions.
      #TODO ERROR
      if len(values) != data.noDivisions: print('ERROR - makefiles.addOption - 1:', nodeID, values, data.noDivisions); exit(1)

      # Loop over the subphases and divisions and update the command lines.
      i = 0
      for j in range(0, data.noSubphases):
        for value in values:
          data.commands[i].append(str(argument) + str(data.delimiter) + str(value))
          i += 1

  # Add input or output files to the command line (this method is only called for nodes that are not multinodes).
  def addFiles(self, graph, task, data, nodeID, isInput):

    # TODO CHECK FOR INFORMATION ON MODIFYING THE ARGUMENT AND THE VALUE.
    # Get the argument and values for the option node.
    if isInput: argument = graph.getArgumentAttribute(nodeID, task, 'longFormArgument')
    else: argument = graph.getArgumentAttribute(task, nodeID, 'longFormArgument')
    values = graph.getGraphNodeAttribute(nodeID, 'values')

    # If there is only a single file, attach to all of the command lines.
    if len(values) == 1:
      for i in range(0, data.noCommandLines):
        data.commands[i].append(str(argument) + str(data.delimiter) + str(values[0]))

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(values[0]))
        else: data.outputs[i].append(str(values[0]))

    # If this is a greedy task, add all the values to each command line.
    elif isInput and data.isGreedy:
      for i in range(0, data.noCommandLines):
        for value in values:
          data.commands[i].append(str(argument) + str(data.delimiter) + str(value))

          # Add the files to the dependencies or outputs for the command line.
          data.dependencies[i].append(str(value))

    # If there are as many files as there are divisions, add the files in the correct order. If there
    # are N divisions, the first file is used for the first subphase and so the first N command lines
    # etc.
    elif len(values) == data.noDivisions:
      for i, value in enumerate(values):
        data.commands[i].append(str(argument) + str(data.delimiter) + str(value))

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(value))
        else: data.outputs[i].append(str(value))

    # If there are a different number of files to subphases, there is a problem.
    #TODO ERROR
    else: print('ERROR - makefileErrors.addFiles'); exit(1)

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

# Define a class to build and manipulate makefiles.
class makefiles:
  def __init__(self):

    # Handle errors associated with makefile construction.
    self.errors = makefileErrors.makefileErrors()

    # Store the paths of all the tools executed in the pipeline.
    self.toolPaths = {}

  # Generate the command lines associated with a task.
  def generateCommandLines(self, graph, superpipeline, task):

    # Determine the number of command lines to be created for the task.
    numberOfCommandLines = graph.getGraphNodeAttribute(task, 'numberOfExecutions')

    # Get the tool used by this task and all the information associated with the tool.
    tool     = superpipeline.tasks[task]
    toolData = superpipeline.toolConfigurationData[tool]

    # Get the executable information.
    executable = toolData.executable
    modifier   = toolData.modifier
    path       = toolData.path
    precommand = toolData.precommand

    # Get the argument delimiter for this tool.
    delimiter = toolData.delimiter

    # Define and store the path to the executable.
    toolID = str('$(' + tool.upper() + '-PATH)')
    if tool not in self.toolPaths: self.toolPaths[tool] = str(toolID + '-PATH)=$(TOOL_BIN)/' + path)

    # The output of the method is a list of command lines, one command line for each execution
    # of the task. Each command line is itself a list of the command line executable and arguments.
    # Since each command line starts with the same exeutable command, initialise the output list as
    # numberOfCommandLines individual lists, each of which is the executable command.
    commands = []
    command  = str(precommand) if precommand else ''
    command += str(toolID + '/' + executable)
    if modifier: command += str(' ' + modifier)
    for i in range(0, numberOfCommandLines): commands.append([command])

    print()
    print('BUILD COMMAND LINES:', task, tool, numberOfCommandLines, delimiter)
    print(commands)
    print()

    # Loop over all the option nodes for this task and get the arguments and values.
    for nodeID in graph.getOptionNodes(task):
      values = self.getOptions(graph, task, nodeID, numberOfCommandLines, delimiter)
      print('\t', nodeID, values)
      for i ,value in enumerate(values): commands[i].append(value)

    print()
    print(commands)

  # Get the argument and values associated with an option node.
  def getOptions(self, graph, task, nodeID, calls, delimiter):

    # Get the option argument and the values.
    argument = graph.getArgumentAttribute(nodeID, task, 'longFormArgument')
    values   = graph.getGraphNodeAttribute(nodeID, 'values')
    
    # Handle situations where only a single value is defined.
    if len(values) == 1:

      # If there is a single task call and a single value, return the value.
      if calls == 1: return [str(argument + delimiter + str(value)) for value in values]

      # If there is a single value, but multiple calls, return the single value for each of the 'calls' task calls.
      elif calls > 1: return [str(argument + delimiter + str(values[0]))] * calls

    # Now handle cases where there is more than a single value.
    else:

      # If the number of values is inconsistent with the number of task calls, throw an error. There
      # can either be a single value which will be used for all task calls, or the same number of
      # values as calls, but nothing else.
      #TODO ERROR
      if len(values) != calls: print('ERROR - makefiles.getOptions - 1'); exit(1)

      # Otherwise return the values.
      else: return [str(argument + delimiter + str(value)) for value in values]

#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import gknoErrors
from gknoErrors import *

import os
import platform
import sys

class argumentLists:
  def __init__(self):

    # Define the errors class.
    self.errors = gknoErrors()

  # Check to see if any of the command line arguments point to lists. If so, unpack them.
  def checkForLists(self, graph, config, gknoConfig, runName, argumentDictionary):
    isPipeline            = config.isPipeline
    argumentsToAdd        = []
    hasInternalLoop       = False
    hasMultipleRuns       = False
    tasksWithDefinedLoops = []
    valuesToRemove        = []
    for argument in argumentDictionary:

      # Do not consider gkno specific arguments.
      if gknoConfig.getNodeForGknoArgument(graph, config, argument) == None:

        # Loop over all of the values supplied to the argument.
        for filename in argumentDictionary[argument]:

          # Any list must have the extension '.list'. Check if this is the case.
          if filename.endswith('.list'):

            # Get the task, tool and tool argument for this pipeline argument.
            if isPipeline:

              # Get the task to which this argument points and the argument within that task to which
              # this pipeline argument points.
              # TODO Consider all nodes, not just the first in the list.
              try: task, toolArgument = config.pipeline.commonNodes[config.pipeline.pipelineArguments[argument].configNodeID][0] 
    
              # If the above failed, the argument is not an argument for the pipeline, but it may be the name of a task in 
              # the pipeline, so leave it for future consideration.
              except: continue
              tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')

            else:
              task         = runName
              tool         = runName
              toolArgument = argument

            # Check that this argument allows a list to be provided and if so, record if this list adds 
            # all the contents to the list of values for the argument (as opposed to creating multiple
            # executions of the command).
            isRepeat = config.tools.getArgumentAttribute(tool, toolArgument, 'isRepeatedArgumentList')
            isList   = config.tools.getArgumentAttribute(tool, toolArgument, 'isArgumentList')


            # Parse the list and modify the value in argumentDictionary from the list to the files
            # in the list. First check that the file exists.
            values = []
            try: data = open(filename)
            except: self.errors.missingFileCommandLine(graph, config, argument, filename)
            for value in [name.strip() for name in data]: values.append(value)
            if not values: self.errors.emptyArgumentList(argument, filename)

            # If the values contained in the list should be added to this argument, add them to the 
            # argumentsToAdd list. These will be transferred to the argumentDictionary after the loop 
            # over it is complete. If this is a pipeline, find the pipeline argument that is used for
            # this argument.
            if isRepeat: argumentsToAdd.append((toolArgument, values))

            # If the argument is given a list of values, but the argument is not repeatable, then
            # multiple iterations of the tool need to be run.
            else:

              # If another list has already been defined, terminate. gkno is unable to accept multiple different
              # definitions of internal loops/multiple runs.
              #TODO MODIFY HELP MESSAGE
              if task in tasksWithDefinedLoops: self.errors.multipleArgumentListsDefined(argument, argument)
              tasksWithDefinedLoops.append(task)

              if argument in gknoConfig.loopData.argumentValues: print('ERROR - commandLine - unpackLists'); self.errors.terminate()
              gknoConfig.loopData.argumentValues[argument] = {}

              # Determine if a single makefile or multiple makefiles are requested.
              if '--multiple-makefiles' in argumentDictionary: hasMultipleRuns = True
              else: hasInternalLoop = True

              # Store the tasks that have arguments set with multiple data sets.
              if isPipeline:
                for linkedTask, dummy in config.pipeline.commonNodes[config.pipeline.pipelineArguments[argument].configNodeID]:
                  if linkedTask not in gknoConfig.loopData.tasksWithMultipleValuesSet:
                    gknoConfig.loopData.tasksWithMultipleValuesSet.append(linkedTask)

              # If gkno is run in tool mode.
              else:
                if task not in gknoConfig.loopData.tasksWithMultipleValuesSet: gknoConfig.loopData.tasksWithMultipleValuesSet.append(task)
  
              for iteration, value in enumerate(values):
                gknoConfig.loopData.argumentValues[argument][iteration + 1] = [value]
                gknoConfig.loopData.fromArgumentList                        = True

            # Mark the value defining the list so that it can be removed from the argumentDictionary.
            valuesToRemove.append((argument, filename))

    # Remove any lists from the argumentDictionary structure.
    for argument, value in valuesToRemove: argumentDictionary[argument].remove(value)

    # Add any required arguments to the argument list.
    for argument, values in argumentsToAdd:
      if argument not in argumentDictionary: argumentDictionary[argument] = []
      for value in values: argumentDictionary[argument].append(value)

    return hasMultipleRuns, hasInternalLoop

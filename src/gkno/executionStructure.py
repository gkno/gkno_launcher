#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import json
import os
import sys

# Define a class to store information about a pipeline phase.
class pipelinePhase():
  def __init__(self):

    # Store a list of tasks associated with each phase.
    self.tasks = []

    # Record how many subphases are present in the phase.
    self.numberSubphases = 1

    # Record the number of divisions present in the phase/subphase.
    self.numberDivisions = 1

# Define the executionStructure class.
class executionStructure():
  def __init__(self):

    # Store the number of phases into which the pipeline is divided.
    self.numberOfPhases = 0

    # Generate a structure to hold information about each phase.
    self.phaseInformation = {}

    # Record which phase each task is in.
    self.task = {}

  # Determine the structure of the pipeline execution.
  def determineExecutionStructure(self, graph):

    # Record the number of subphases and divisions seen in the previous task.
    previousTaskNumberSubphases = 0
    previousTaskNumberDivisions = 0
  
    # Loop over all the tasks in the workflow.
    for task in graph.workflow:
  
      # Get basic information about this task.
      isConsolidate   = graph.getGraphNodeAttribute(task, 'consolidate')
      isGreedy        = graph.getGraphNodeAttribute(task, 'isGreedy')
      numberDivisions = graph.getGraphNodeAttribute(task, 'divisions')

      # Determine the number of input and output files going to this task.
      numberInputs = 1
      if not isGreedy:
        for predecessor in graph.getInputFileNodes(task):
          numberValues = len(graph.getGraphNodeAttribute(predecessor, 'values'))
          if numberValues > numberInputs: numberInputs = numberValues

      # Determine the number of input and output files going to this task.
      numberOutputs = 1
      for successor in graph.graph.successors(task):
        numberValues = len(graph.getGraphNodeAttribute(successor, 'values'))
        if numberValues > numberOutputs: numberOutputs = numberValues

      # Determine the number of subphases. If the task is not greedy, then there will be an output file for
      # each subphase, so the number of output files determines the number of subphases.
      if isGreedy: numberSubphases = 1
      else: numberSubphases = numberOutputs
      # Calculate the total number of task executions. This is dependent on a number of factors. First
      # consider cases where the node is greedy. If there are multiple input nodes, all the values within
      # each node will be used in a single task execution. Thus the number of executions is equal to the
      # number of input nodes. If there is only a single input file node, there is only a single execution
      # of the task, since all values are used in a single greedy execution. Thus, either way, the total
      # number of executions is equal to the number of input nodes.
      #if isGreedy: totalExecutions = numberInputNodes

#      # If the task isn't greedy, the total number of executions is the maximum of the number of input 
#      # and output nodes, multiplied by the number of executions.
#      else: totalExecutions = max(numberInputNodes, numberOutputNodes) * divisions
#
#      # Determine the number of subphases. This is simply the maximum of the number of input or output
#      # multinodes. A phase contains a set of tasks that need to be run sequentially. If there are
#      # multiple values associated with the nodes for the task, there can be multiple jobs in a phase
#      # that can be run in parallel. Subphases result from the case where tasks can produce multiple
#      # output nodes, each of which has multiple values associated with it. In this case, within the
#      # phase there are subphases and each subphase is itself divided up into divisions. The divisions
#      # are dictated by the number of options provided to the task.
#      subphases = max(numberInputNodes, numberOutputNodes)
#
#      # If this task has one division and the previous task has multiple, reset the number of divisions
#      # for this task, to the same number as the previous unless this task is greedy. If this task is
#      # greedy, there should only be one division and a new phase will be generated.
#      divisionsInPreviousTask = self.phaseInformation[self.numberOfPhases].divisions if self.numberOfPhases in self.phaseInformation else 1
#      if (divisions == 1) and (divisionsInPreviousTask != 1) and not isGreedy: divisions = divisionsInPreviousTask
#
      # If this is the first task in the pipeline, start a new phase and define the number of subphases
      # and divisions in the phase and append the task to the phase.
      #if i == 0: self.defineNewPhase(numberSubphases, numberDivisions)

      # If this is the first task in the pipeline, or the task is greedy or is consolidating files from
      # multiple divisions, a new phase is required.
      if isGreedy or isConsolidate or self.numberOfPhases == 0:
        self.defineNewPhase(numberSubphases, numberDivisions)
        previousTaskNumberDivisions = numberDivisions
        previousTaskNumberSubphases = numberSubphases

      # Add the task to the current phase and also record the reverse, the phase that the task is in.
      self.phaseInformation[self.numberOfPhases].tasks.append(task)
      self.task[task] = self.numberOfPhases

  # Define a new phase in the pipeline structure.
  def defineNewPhase(self, numberSubphases, numberDivisions):

    # Increment the number of phases in the pipeline.
    self.numberOfPhases += 1

    # Create a new task list for the phase and the number of subphases in the phase.
    self.phaseInformation[self.numberOfPhases] = pipelinePhase()
    self.phaseInformation[self.numberOfPhases].numberSubphases = numberSubphases
    self.phaseInformation[self.numberOfPhases].numberDivisions = numberDivisions

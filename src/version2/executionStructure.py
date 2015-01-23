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
    self.subphases = None

    # Record the number of divisions present in the phase/subphase.
    self.divisions = None

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
  
    # Loop over all the tasks in the workflow.
    for i, task in enumerate(graph.workflow):
  
      # Get the maximum number of values for a single option provided to the task.
      divisions = graph.getGraphNodeAttribute(task, 'divisions')

      # Get execution information about this task. Specifically, the number of input and output
      # multinodes and the number of times the task is executed for each set of nodes.
      #subphases = graph.getGraphNodeAttribute(task, 'subphases')
      isGreedy  = graph.getGraphNodeAttribute(task, 'isGreedy')
  
      # Multinode inputs.
      multinodeInput      = graph.getGraphNodeAttribute(task, 'multinodeInput')
      daughterInputNodes  = graph.getGraphNodeAttribute(multinodeInput, 'daughterNodes')
      numberInputNodes    = len(daughterInputNodes) + 1 if daughterInputNodes else 1

      # Multinode inputs.
      multinodeOutput     = graph.getGraphNodeAttribute(task, 'multinodeOutput')
      daughterOutputNodes = graph.getGraphNodeAttribute(multinodeOutput, 'daughterNodes')
      numberOutputNodes   = len(daughterOutputNodes) + 1 if daughterOutputNodes else 1
 
      # Calculate the total number of task executions. This is dependent on a number of factors. First
      # consider cases where the node is greedy. If there are multiple input nodes, all the values within
      # each node will be used in a single task execution. Thus the number of executions is equal to the
      # number of input nodes. If there is only a single input file node, there is only a single execution
      # of the task, since all values are used in a single greedy execution. Thus, either way, the total
      # number of executions is equal to the number of input nodes.
      if isGreedy: totalExecutions = numberInputNodes

      # If the task isn't greedy, the total number of executions is the maximum of the number of input 
      # and output nodes, multiplied by the number of executions.
      else: totalExecutions = max(numberInputNodes, numberOutputNodes) * divisions#executionsPerNode

      # Determine the number of subphases. This is simply the maximum of the number of input or output
      # multinodes. A phase contains a set of tasks that need to be run sequentially. If there are
      # multiple values associated with the nodes for the task, there can be multiple jobs in a phase
      # that can be run in parallel. Subphases result from the case where tasks can produce multiple
      # output nodes, each of which has multiple values associated with it. In this case, within the
      # phase there are subphases and each subphase is itself divided up into divisions. The divisions
      # are dictated by the number of options provided to the task.
      subphases = max(numberInputNodes, numberOutputNodes)

      # If this task has one division and the previous task has multiple, reset the number of divisions
      # for this task, to the same number as the previous unless this task is greedy. If this task is
      # greedy, there should only be one division and a new phase will be generated.
      divisionsInPreviousTask = self.phaseInformation[self.numberOfPhases].divisions if self.numberOfPhases in self.phaseInformation else 1
      if (divisions == 1) and (divisionsInPreviousTask != 1) and not isGreedy: divisions = divisionsInPreviousTask

      # If this is the first task in the pipeline, start a new phase and define the number of subphases
      # and divisions in the phase and append the task to the phase.
      if i == 0: self.defineNewPhase(subphases, divisions)

      # If this isn't the first task, check if the number of subphases and divisions for this task are
      # equal to those of the previous task. If so, this task is part of the same phase.
      elif (subphases != self.phaseInformation[self.numberOfPhases].subphases) or (divisions != divisionsInPreviousTask):
        self.defineNewPhase(subphases, divisions)

      # Add the task to the current phase and also record the reverse, the phase that the task is in.
      self.phaseInformation[self.numberOfPhases].tasks.append(task)
      self.task[task] = self.numberOfPhases

  # Define a new phase in the pipeline structure.
  def defineNewPhase(self, subphases, divisions):

    # Increment the number of phases in the pipeline.
    self.numberOfPhases += 1

    # Create a new task list for the phase and the number of subphases in the phase.
    self.phaseInformation[self.numberOfPhases] = pipelinePhase()
    self.phaseInformation[self.numberOfPhases].subphases = subphases
    self.phaseInformation[self.numberOfPhases].divisions = divisions

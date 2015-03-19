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

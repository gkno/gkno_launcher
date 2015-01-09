#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import os
import platform
import sys

class executionStructure:
  def __init__(self):

    # Define information on the makefile structure. This is information on the number of phases 
    # and how many makefile each phase has.
    self.makefilesInPhase  = {}
    self.makefileNames     = {}
    self.numberOfPhases    = 1
    self.tasksInPhase      = {}

    # Record the number of input and output data sets for each phase.
    self.numberOfPhaseInputs  = {}
    self.numberOfPhaseOutputs = {}

  # Define the structure of the pipeline. This structure will be used to define the makefile structure.
  # This involved identifying which tasks can be run in parallel and how many data sets each task has. 
  # This results in breaking the pipeline into phases which need to be executed sequentially, with 
  # iterations within each phase that can be run in parallel.
  def determineStructure(self, graph):
    firstTask         = True
    self.currentPhase = 1
    for task in graph.workflow:

      # Determine the number of iterations of input and output files.
      numberOfInputDataSets  = graph.getGraphNodeAttribute(task, 'numberOfInputSets')
      numberOfOutputDataSets = graph.getGraphNodeAttribute(task, 'numberOfOutputSets')
      print(task, numberOfInputDataSets, numberOfOutputDataSets)

      # Check if any of the arguments have multiple iterations of data.
#      numberOfInputArgumentIterations = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getPredecessorOptionNodes(graph, task))

      # If there are multiple sets of input arguments, check the number of input and output files. If there
      # are only single sets of input and output data, the number of input and output data sets are equal to
      # the number of input argument iterations.
#      if numberOfInputArgumentIterations != 1:
#        if numberOfInputDataSets == 1 and numberOfOutputDataSets == 1:
#          numberOfInputDataSets  = numberOfInputArgumentIterations
#          numberOfOutputDataSets = numberOfInputArgumentIterations

      # If this is the first task in the workflow, determine how many makefiles are required
      # for this task. This is the number of input or output data sets. Set the current makefiles
      # to these.
      if firstTask:
        self.numberOfFilesinPhase            = max(numberOfInputDataSets, numberOfOutputDataSets)
        self.makefilesInPhase[1]             = self.numberOfFilesinPhase
        self.tasksInPhase[self.currentPhase] = []
        firstTask                            = False

        # Since this is the first task in the phase, record the number of input and output data sets. If
        # there are more tasks in this phase, the number of output data sets will be overwritten.
        self.numberOfPhaseInputs[self.currentPhase]  = numberOfInputDataSets
        self.numberOfPhaseOutputs[self.currentPhase] = numberOfOutputDataSets
      else:

        # If there are more input data sets than output data sets, this must be the start of a 
        # new phase.
        if numberOfInputDataSets > numberOfOutputDataSets:

          # If the number of input data sets is not equal to the number of files in the current phase,
          # an error has occured.
          if numberOfInputDataSets != self.numberOfFilesinPhase:
            #TODO ERROR
            print('makefileData.determineMakefileStructure')
            print('Number of input data sets is different to the number of files in the phase.')
            print(numberOfInputDataSets, self.numberOfFilesinPhase)
            exit(1)
 
          # If the number of output data sets is smaller than the number of input data sets, there
          # must be a single output data set only. This essentially means that the task is taking the
          # outputs from multiple tasks and using them all to run. If this is the case, there must
          # be a single output data set.
          if numberOfOutputDataSets != 1:
            #TODO ERROR
            print('makefileData.determineMakefileStructure')
            print('A greedy task is accepting multiple inputs, but has more than one output data set.')
            exit(1)

          # Create a new phase.
          self.createNewPhase(1, 1)

        # If the number of input data sets is equal to the number of output data sets, whether this
        # is the start of a new phase or not depends on the number of data sets output by the previous
        # phase.
        else:

          # If the number of input data sets differs from the number of output data sets from the
          # last task, this is the start of a new phase.
#          if numberOfInputArgumentIterations != self.numberOfFilesinPhase: self.createNewPhase(numberOfInputArgumentIterations, numberOfOutputDataSets)
#          elif (numberOfInputDataSets != self.numberOfFilesinPhase) and (numberOfInputDataSets != numberOfInputArgumentIterations):
#            self.createNewPhase(numberOfInputArgumentIterations, numberOfOutputDataSets)
          if numberOfInputDataSets != self.numberOfFilesinPhase: self.createNewPhase(numberOfInputDataSets, numberOfOutputDataSets)
          else: self.numberOfPhaseOutputs[self.currentPhase] = numberOfOutputDataSets

#        # Add this task to the makefile structure.
#        if self.numberOfFilesinPhase != 1: config.nodeMethods.setGraphNodeAttribute(graph, task, 'hasMultipleIterations', True)

      # Append this task to the list of tasks in this phase.
      self.tasksInPhase[self.currentPhase].append(task)

    # Since the topological sort is non-unique, it is possible that the workflow is such that there are
    # phases that can be consolidated with previous phases, reducing the number of phases in the pipeline.
    # Check to see if this is the case.
    self.consolidatePhases(graph, config)

  # Create a new phase in the makefile structure.
  def createNewPhase(self, numberOfInputDataSets, numberOfOutputDataSets):
    self.currentPhase += 1
    self.tasksInPhase[self.currentPhase]     = []
    self.numberOfPhases                      = self.currentPhase
    self.makefilesInPhase[self.currentPhase] = numberOfInputDataSets
    self.numberOfFilesinPhase                = numberOfInputDataSets

    # As the start of a new phase, record the number if input and output data sets for this phase.
    # Again, the number of output data sets will be overwritten if there are other tasks in this
    # phase.
    self.numberOfPhaseInputs[self.currentPhase]  = numberOfInputDataSets
    self.numberOfPhaseOutputs[self.currentPhase] = numberOfOutputDataSets

#
#  # Get the number of data sets for a node.
#  def getNumberOfDataSets(self, graph, config, task, nodeIDs):
#    finalNumber = 0
#
#    for nodeID in nodeIDs:
#      optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
#      numberOfDataSets = len(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))
#      try: argument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
#      except: argument = config.edgeMethods.getEdgeAttribute(graph, task, optionNodeID, 'longFormArgument')
#
#      # Check to see if this particular argument is greedy.
#      isGreedy = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isGreedy')
#      if isGreedy: numberOfDataSets = 1
#      if numberOfDataSets > finalNumber: finalNumber = numberOfDataSets
#
#    return finalNumber
#
#  # Check to see if the structure can be reduced to fewer phases.
#  def consolidatePhases(self, graph, config):
#
#    # Loop over the phases and index the phases by the number of makefiles.
#    makefileNumbers = {}
#    for phaseID in self.makefilesInPhase:
#      if self.makefilesInPhase[phaseID] not in makefileNumbers: makefileNumbers[self.makefilesInPhase[phaseID]] = []
#      makefileNumbers[self.makefilesInPhase[phaseID]].append(phaseID)
#
#    # Start from the final phase and see if the tasks can be moved to an earlier phase. If a phase is
#    # moved, break out of the loop, delete the moved phase and start again.
#    continueSearch = True
#    while continueSearch:
#      for phaseID in reversed(self.makefilesInPhase.keys()):
#        phaseHasBeenMoved = False
#
#        # If this is the second phase, it cannot be moved to the first, so there is no possibility of
#        # any more phases being moved, so teminate the search.
#        if phaseID <= 2:
#          continueSearch = False
#          break
#  
#        # Check if there are any phases prior to this phase with the same number of makefiles.
#        for otherPhaseID in makefileNumbers[self.makefilesInPhase[phaseID]]:
#          canBeMoved = True
#  
#          # Don't consider this phase and only consider phases prior to one phase before. The previous
#          # phase was separated from this phase for a reason.
#          if otherPhaseID != phaseID and otherPhaseID < (phaseID - 1):
#  
#            # Check if any of the tasks in the phase depend on files generated by tasks in the phases
#            # in between the otherPhaseID and this one. First compile a list of all file nodes
#            # produced in the preceding phases.
#            for counter in range(otherPhaseID + 1, phaseID):
#              createdFileNodeIDs = []
#              for task in self.tasksInPhase[counter]:
#                for fileNodeID in config.nodeMethods.getSuccessorFileNodes(graph, task): createdFileNodeIDs.append(fileNodeID)
#  
#            # Check if any task in this phase depends on any of these files.
#            for task in self.tasksInPhase[phaseID]:
#              for fileNodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
#                if fileNodeID in createdFileNodeIDs:
#                  canBeMoved = False
#                  break
#              if not canBeMoved: break
#  
#          # If this otherPhaseID does not point to a phase that the current phase could potentially be
#          # moved to, mark it as so.
#          else: canBeMoved = False
#  
#          # If this phase can be moved, move the tasks to the end of the identified phase.
#          if canBeMoved:
#            for task in self.tasksInPhase[phaseID]: self.tasksInPhase[otherPhaseID].append(task)
#            phaseHasBeenMoved = True
#            break
#  
#        # If a phase has been moved, break out of the loop over the phases, remove the moved phase and restart
#        # the loop.
#        if phaseHasBeenMoved: break
#  
#      # Renumber the phase ID of subsesquent phases.
#      if phaseHasBeenMoved:
#        for ID in range(phaseID + 1, self.numberOfPhases + 1, 1):
#          self.tasksInPhase[ID - 1]     = deepcopy(self.tasksInPhase[ID])
#          self.makefilesInPhase[ID - 1] = deepcopy(self.makefilesInPhase[ID])
#    
#        # Remove the moved phase.
#        del(self.tasksInPhase[self.numberOfPhases])
#        del(self.makefilesInPhase[self.numberOfPhases])
#        self.numberOfPhases -= 1
#
#  # Set the names of the makefiles to be created.  If this is a single run, a single name
#  # is required, otherwise, there will be a list of names for each of the created makefiles.
#  def setMakefilenames(self, text):
#
#    # If there is only a single phase, there is no need for phase information in the makefile
#    # name.
#    if self.numberOfPhases == 1:
#      self.makefileNames[1] = []
#      if self.makefilesInPhase[1] == 1: self.makefileNames[1].append(text + '.make')
#      else:
#        for count in range(1, self.makefilesInPhase[1] + 1): self.makefileNames[1].append(text + '_' + str(count) + '.make')
#
#    # If there are phases, include the phase in the name of the makefiles.
#    else:
#      for phaseID in range(1, self.numberOfPhases + 1):
#        self.makefileNames[phaseID] = []
#        if self.makefilesInPhase[phaseID] == 1: self.makefileNames[phaseID].append(text + '_phase_' + str(phaseID) + '.make')
#        else:
#          for count in range(1, self.makefilesInPhase[phaseID] + 1):
#            self.makefileNames[phaseID].append(text + '_phase_' + str(phaseID) + '_' + str(count) + '.make')

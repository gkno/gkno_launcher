#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import configurationClass.configurationClass
from configurationClass.configurationClass import *

import gknoErrors
from gknoErrors import *

import json
import os
import sys

class dataConsistency:
  def __init__(self):

    # Errors class.
    self.errors = gknoErrors()

  # Check that there are as many output files as there are input data sets.
  def checkNumberOfOutputFiles(self, graph, config):

    # Loop over all tasks in the pipeline.
    for task in config.pipeline.workflow:

      # Loop over all input files and options and determine the maximum number of data sets.
      noInputDataSets  = 0
      for nodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
        noInputDataSets = max(noInputDataSets, len(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')))
      for nodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
        noInputDataSets = max(noInputDataSets, len(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')))

      # Output data sets.
      noOutputDataSets = 0
      for nodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        noOutputDataSets = max(noOutputDataSets, len(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')))

      # If the number of output sets is less than the number of input data sets, modify the number of output files,
      # but the number of output files is greater than 1, terminate. It isn't clear how to reconcile the input and
      # output data.
      if (noInputDataSets != noOutputDataSets) and (noOutputDataSets != 1):
        #TODO ERROR
        print('ERROR - dataConsistency.checkNumberOfOutputFiles')
        self.error.terminate()

      # Loop over the output files.
      for fileNodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        values = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')
        if len(values) == 1:
          optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
          extensions   = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowedExtensions')
          self.updateOutputFiles(graph, config, optionNodeID, values, extensions, noInputDataSets)
          self.updateOutputFiles(graph, config, fileNodeID, values, extensions, noInputDataSets)

  # Update the output nodes to have the correct number of iterations.
  def updateOutputFiles(self, graph, config, nodeID, values, extensions, noInputDataSets):

    # For each file in the list of values, determine the extension.
    usedExtensions = []
    for value in values[1]:
      foundExtension = False
      for extension in extensions:
        if value.endswith(extension):
          usedExtensions.append(str(extension))
          foundExtension = True
          break

      # If the file has an unknown extension, terminate.
      if not foundExtension:
        # TODO ERROR
        print('ERROR - dataConsistency.checkNumberOfOutputFiles 2')
        self.errors.terminate()

    # Generate a new dictionary containing the number of iterations in the input data sets, with integers
    # appended to the names.
    modifiedValues = {}
    for counter in range(1, noInputDataSets + 1, 1):
      newSet = []
      for valueCounter, (value, extension) in enumerate(zip(values[1], usedExtensions)):
        newSet.append(value.rsplit(extension)[0] + '_' + str(counter) + extension)
      modifiedValues[counter] = newSet

    # Replace the node values.
    config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'values', modifiedValues)

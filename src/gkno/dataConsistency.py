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
        print('ERROR - dataConsistency.checkNumberOfOutputFiles', noInputDataSets, noOutputDataSets)
        self.errors.terminate()

      # Loop over the output files to see if amendments are required.
      if noInputDataSets != noOutputDataSets:

        # If the task is not greedy, the output files need to be modified. If it is, find all option nodes with
        # multiple iterations of values. If any of these nodes are not greedy, then the output files still
        # need to be modified (see comment below).
        if config.nodeMethods.getGraphNodeAttribute(graph, task, 'isGreedy'):
          requiresMultipleOutputs = False
          for optionNodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
            isGreedy     = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isGreedy')
            noIterations = len(config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values'))
            if not isGreedy and noIterations > 1:
              requiresMultipleOutputs = True
              break
        else: requiresMultipleOutputs = True

        for fileNodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
          optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
          values       = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')

          # Determine if this is a greedy task. If so, and there is only a single input with multiple iterations,
          # do not modify the output files. If the task is greedy, but there are several option nodes with 
          # multiple inputs, still modify the outputs. A task can take in, for example, multiple bam files and
          # is considered greedy, so they are pulled into a single execution. However, multiple regions may also
          # be required, which would require multiple executions (hence multiple output files).

          if len(values) == 1 and requiresMultipleOutputs:
            isFilenameStub = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFilenameStub')

            # If this is a filename stub, supply the extensions expected for this file.
            if isFilenameStub:
              self.updateOutputStub(graph, config, optionNodeID, fileNodeID, noInputDataSets)
            else:
              extensions = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowedExtensions')
              self.updateOutputFiles(graph, config, optionNodeID, values, extensions, noInputDataSets)
              self.updateOutputFiles(graph, config, fileNodeID, values, extensions, noInputDataSets)
            config.nodeMethods.setGraphNodeAttribute(graph, task, 'numberOfDataSets', noInputDataSets)

  # Update the output nodes to have the correct number of iterations.
  def updateOutputFiles(self, graph, config, nodeID, values, extensions, noInputDataSets):

    # For each file in the list of values, determine the extension.
    usedExtensions = []
    for value in values[1]:
      foundExtension = False

      # If the extensions are not set (e.g. is 'no extension'), do not search for the extension.
      if extensions == [u'no extension'] or extensions == ['no extension']:
        foundExtension = True
        usedExtensions.append(value.rsplit('.')[1])

      # If there is defined extensions, search for the correct one.
      else:
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

  # Update the output nodes to have the correct number of iterations.
  def updateOutputStub(self, graph, config, optionNodeID, fileNodeID, noInputDataSets):

    # Get the extension for the file node.
    extension = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'allowedExtensions')[0]

    # Parse each iteration in the option node and modify the values. It is possible that the same
    # option node can be sent here multiple times. If the values have already been modified, do not
    # modify again.
    isOptionNodeModified = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isValuesModified')
    if not isOptionNodeModified:
      config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isValuesModified', True)
      modifiedOptionValues = {}
      optionNodeValues     = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
      for counter in range(1, noInputDataSets + 1, 1):
        newOptionSet = []
        for value in optionNodeValues[1]: newOptionSet.append(value + '_' + str(counter))
        modifiedOptionValues[counter] = newOptionSet

      # Replace the node values.
      config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'values', modifiedOptionValues)

    # Now handle the file node.
    modifiedFileValues   = {}
    fileNodeValues       = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')
    for counter in range(1, noInputDataSets + 1, 1):
      newFileSet = []

      # The extension needs to be removed when dealing with the file node values.
      for value in fileNodeValues[1]:
        if not value.endswith(extension):
          print('ERROR: dataConsistency.updateOutputStub'); exit(0)

        newFileSet.append(value.rsplit(extension)[0] + '_' + str(counter) + extension)
      modifiedFileValues[counter] = newFileSet

    # Replace the node values.
    config.nodeMethods.setGraphNodeAttribute(graph, fileNodeID, 'values', modifiedFileValues)

  # Parse all of the requested nodes and check to see if the included values have the correct extensions.
  def checkExtensions(self, graph, config):

    # Loop over all the nodes of the requested type.
    for task in config.pipeline.workflow:
      print('\tTEST', task)
      self.checkFileExtensions(graph, config, config.nodeMethods.getPredecessorFileNodes(graph, task))
      self.checkFileExtensions(graph, config, config.nodeMethods.getSuccessorFileNodes(graph, task))

  # Parse the files and check the extensions.
  def checkFileExtensions(self, graph, config, nodeIDs):
    for nodeID in nodeIDs:
      values     = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
      extensions = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions')

      for iteration in values:
        isMatchedExtension = False
        for value in values[iteration]:
          for extension in extensions:
            if value.endswith(str(extension)):
              isMatchedExtension = True
              break

        # If the value did not match any of the allowed extensions, terminate.
        #if not isMatchedExtension:

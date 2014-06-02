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

# Define a data structure for holding information about multiple runs/internal loops.
class loops:
  def __init__(self):

    # Define a list of arguments. The order is important since the values in the loop file are
    # in the same order as the arguments.
    self.arguments = []

    # Define the number of data sets in the file.
    self.numberOfDataSets = 0

    # Define the number of arguments with values in the file.
    self.numberOfSetArguments = 0

    # Define a dictionary that will hold the values.
    self.values = {}

    # Define if the loop data comes from an argument list (as opposed to having --multiple-runs
    # or --internal-loop defined).
    self.fromArgumentList = False

    # If the argument in the multiple run file pointed to a list argument, store the argument.
    self.listArguments = []

  # Check if multiple runs or internal loops have been requested. If so, check that only one file
  # has been provided.
  def hasLoop(self, graph, config, resourcePath, isPipeline, name, hasMultipleRuns, hasInternalLoop):
    loopDefined = hasMultipleRuns or hasInternalLoop

    # Check if an argument list has already defined a multiple-run/internal-loop.
    multipleRuns = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-MULTIPLE-RUNS', 'values')
    internalLoop = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-LOOP', 'values')

    # Either multiple runs or internal loops are allowed, but not both.
    if multipleRuns and internalLoop: self.errors.internalLoopAndMultipleRuns()

    # If multiple runs or internal loops are requested, but an argument list has already been defined,
    # another set of values cannot be supplied.
    if (multipleRuns or internalLoop) and loopDefined: self.errors.multipleRunsDisabled()

    # If no multiple runs or internal loops are requested, return.
    if not multipleRuns and not internalLoop: return hasMultipleRuns, hasInternalLoop

    # If a file is provided, check the format.
    hasMultipleRuns = False
    hasInternalLoop = False
    if multipleRuns:
      files           = multipleRuns[1]
      hasMultipleRuns = True
    elif internalLoop:
      files = internalLoop[1]
      hasInternalLoop = True

    # There can only be a single file specified
    if len(files) != 1: self.errors.multipleMultipleRunsOrInternalLoops(hasMultipleRuns)

    # Validate the file and import the information into a data structure.
    filename = files[0].replace('$(RESOURCES)/', resourcePath) if files[0].startswith('$(RESOURCES)') else files[0]
    data = config.fileOperations.readConfigurationFile(filename)
    self.validateMultipleRunsFiles(graph, config, filename, hasMultipleRuns, data, isPipeline, name)

    return hasMultipleRuns, hasInternalLoop

  # Validate the contents of a multiple run or internal loop file.
  def validateMultipleRunsFiles(self, graph, config, filename, hasMultipleRuns, data, isPipeline, name):
    allowedAttributes              = {}
    allowedAttributes['arguments'] = (list, True)
    allowedAttributes['values']    = (list, True)

    # Keep track of the observed required values.
    observedAttributes = {}

    # Loop over all of the attributes in the configuration file.
    for attribute in data:

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if attribute not in allowedAttributes:
        self.errors.invalidAttributeInMultipleRunsFile(filename, hasMultipleRuns, attribute, allowedAttributes)

      # Mark this values as having been observed,
      observedAttributes[attribute] = True

      # Check that the value given to the attribute is of the correct type. If the value is unicode,
      # convert to a string first.
      value = str(data[attribute]) if isinstance(data[attribute], unicode) else data[attribute]
      if allowedAttributes[attribute][0] != type(value):
        self.errors.incorrectTypeInMultipleRunsFile(filename, hasMultipleRuns, attribute, value, allowedAttributes[attribute][0])

    # Having parsed all of the general attributes attributes, check that all those that are required
    # are present.
    for attribute in allowedAttributes:
      if allowedAttributes[attribute][1] and attribute not in observedAttributes:
        self.errors.missingAttributeInMultipleRunsFile(filename, hasMultipleRuns, attribute, allowedAttributes)

    # Check that all supplied arguments are valid.
    if isPipeline: self.checkMultipleRunsArgumentsPipeline(graph, config, data, filename)
    else: self.checkMultipleRunsArgumentsTool(graph, config, data, name, filename)

    # Now loop over all the data sets and store the argument values.
    self.processValues(graph, config, data, filename, hasMultipleRuns)

  # Check that all arguments in the multiple runs/internal loop file are valid for the current
  # pipeline.
  def checkMultipleRunsArgumentsPipeline(self, graph, config, data, filename):
    self.numberOfSetArguments = len(data['arguments'])
    for argument in data['arguments']:

      # Check if the argument is a gkno specific argument.
      gknoNodeID = self.getNodeForGknoArgument(graph, config, argument)
      if gknoNodeID: self.arguments.append(argument)
      else:

        # Check that this is a valid argument.
        pipelineLongFormArgument, pipelineShortFormArgument = config.pipeline.getLongFormArgument(graph, argument)
        if pipelineLongFormArgument not in config.pipeline.pipelineArguments: self.errors.unknownPipelineArgumentMultipleRun(argument, filename)

        # Check if the argument is a list that points to another argument. Begin by getting the tool
        # argument, to which this points, then determine if the tool argument is a list pointing to
        # a different tool argument. If so, determine if there is a pipeline argument pointing to this
        # tool argument.
        task, toolArgument = config.pipeline.pipelineToTaskArgument[pipelineLongFormArgument][0]
        tool               = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
        if config.tools.getArgumentAttribute(tool, toolArgument, 'listArgument'):
          try: linkedPipelineArgument = config.pipeline.taskArgument[task][config.tools.getArgumentAttribute(tool, toolArgument, 'listArgument')]
          except: print('ERROR - gknoConfigurationFiles.checkMultipleRunsArgumentsTool'); self.errors.terminate(); #TODO ERROR
          self.arguments.append(linkedPipelineArgument)
          self.listArguments.append(linkedPipelineArgument)

        # If the argument doesn't point to a list, store the argument in the data structure.
        else: self.arguments.append(pipelineLongFormArgument)

  # Check that all arguments in the multiple runs/internal loop file are valid for the current
  # pipeline.
  def checkMultipleRunsArgumentsTool(self, graph, config, data, tool, filename):
    self.numberOfSetArguments = len(data['arguments'])
    for argument in data['arguments']:

      # Check if the argument is a gkno specific argument.
      gknoNodeID = self.getNodeForGknoArgument(graph, config, argument)
      if gknoNodeID: self.arguments.append(argument)
      else:
        longFormArgument = config.tools.getLongFormArgument(tool, argument, allowTermination = False)
        if not longFormArgument: self.errors.unknownArgumentMultipleRun(argument, filename)

        # Check if the argument points to a list.
        if config.tools.getArgumentAttribute(tool, longFormArgument, 'listArgument'):
          self.arguments.append(config.tools.getArgumentAttribute(tool, longFormArgument, 'listArgument'))
          self.listArguments.append(config.tools.getArgumentAttribute(tool, longFormArgument, 'listArgument'))
        else: self.arguments.append(config.tools.getLongFormArgument(tool, argument))

  # Process the argument values in the multiple run/internal loop file.
  def processValues(self, graph, config, data, filename, hasMultipleRuns):

    # Record the number of data sets.
    self.numberOfDataSets = len(data['values'])
    for iteration, dataSet in enumerate(data['values']):

      # Check that the data set is a list containing the same number of entries as there are
      # arguments in the 'arguments' section of the file.
      if not isinstance(dataSet, list): self.errors.incorrectTypeForDataSet(filename, hasMultipleRuns)
      if len(dataSet) != self.numberOfSetArguments: self.errors.incorrectNumberOfValues(filename, hasMultipleRuns)

      # Store the values.
      self.values[iteration + 1] = []
      for argument, value in zip(self.arguments, dataSet):

        # If this argument points to a list, open the file and add all the contained values to
        # the data structure.
        if argument in self.listArguments:
          values = []

          # Attempt to open the list defined in the multiple run file.
          try: listData = open(value)
          except: self.errors.missingFileCommandLine(graph, config, argument, value)

          # Loop over all the values and add them to the data structure.
          values = []
          for dataValue in [name.strip() for name in listData]: values.append(dataValue)
          if not values: self.errors.emptyArgumentList(argument, value)
          self.values[iteration + 1].append(values)

        else: self.values[iteration + 1].append([str(value)])

  # Assign loop values to the graph.
  def addLoopValuesToGraph(self, graph, config, isPipeline, runName):

    # Loop over each of the data sets and add to the correct iteration in the correct node.
    for iteration in range(1, self.numberOfDataSets + 1):
      for argument in self.arguments:
        values = self.values[iteration]

        # Find the node for this argument. First check if it is a gkno argument (rather than a
        # tool or pipeline argument).
        nodeID = self.getNodeForGknoArgument(graph, config, argument)

        # If the loop data was defined from an argument list (i.e. not from a file associated with the
        # --multiple-runs or --internal-loop commands, get the nodeID associated with the argument. If
        # this is the case, there is only a single argument associated with the data (a multiple-runs
        # command, for example, can specify values for multiple different arguments).
        if self.fromArgumentList:
          if not isPipeline: nodeID = config.nodeMethods.getNodeForTaskArgument(graph, runName, argument, 'option')[0]

        # Check if the argument is a non-list argument for the tool/pipeline.
        if not nodeID:
          if isPipeline: nodeID = config.pipeline.pipelineArguments[argument].ID
          else:
            nodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, runName, argument, 'option')

            # If the node doesn't exist, the argument which the multiple argument points has not been
            # created.
            if not nodeIDs:
              attributes = config.nodeMethods.buildNodeFromToolConfiguration(config.tools, runName, argument)
              nodeID     = config.nodeMethods.buildOptionNode(graph, config.tools, runName, runName, argument, attributes)
            else: nodeID = nodeIDs[0]

        # If this nodeID is not in the graph, an error has occured. Likely this node has been
        # deleted in the merge process.
        if nodeID not in graph.nodes(): self.errors.nodeNotInGraph(graph, config, nodeID, 'gknoConfigurationFiles.addLoopValuesToGraph')

        if values:
          if iteration == 1: config.nodeMethods.addValuesToGraphNode(graph, nodeID, values, write = 'replace')
          else: config.nodeMethods.addValuesToGraphNode(graph, nodeID, values, write = 'iteration', iteration = str(iteration))

  # TODO REPEATED IN GKNOCONFIG. SORT OUT CLASSES AND CONSOLIDATE.
  # Return the node for a gkno argument contained in the gkno configuration file.
  def getNodeForGknoArgument(self, graph, config, argument):
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].longFormArgument: return nodeID

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].shortFormArgument: return nodeID

    return None

#!/bin/bash/python

from __future__ import print_function

import argumentErrors as err

import json
import os
import sys

# Define a data structure to hold information relevant to each argument.
class argumentInformation:
  def __init__(self):

    # The argument description.
    self.description = 'No description'

    # Store the short form version of the argument.
    self.shortFormArgument = None

    # The node ID of the graph node that the argument points to.
    self.graphNodeID = None

# Define a class for handling all arguments and their relationship with the graph.
class arguments:
  def __init__(self):

    # Define error handling for file errors.
    self.errors = err.argumentErrors()

    # Store information for each argument.
    self.arguments = {}

    # A dictionary to long graph node IDs with an argument that can set it's value.
    self.nodeToArgument = {}

  # Add arguments from pipeline configuration data to the object.
  def addPipelineArguments(self, data):

    # Loop over the arguments.
    for argument in data:

      # Create a data structure for the argument.
      self.arguments[argument] = self.addArgument(data[argument])

  # Add an argument to the required data strcutures.
  def addArgument(self, argumentToAdd):
    
    information = argumentInformation()

    # Store the argument description and the short form.
    information.description       = argumentToAdd.description
    information.shortFormArgument = argumentToAdd.shortFormArgument

    return information

  # Now that the graph is built, parse all of the arguments in the pipelines and associate them with
  # the graph nodes and vice versa.
  def assignNodesToArguments(self, superpipeline):

    # Loop over all tiers of the superpipeline (except the top level as this has already been handled),
    # and add the arguments by path.
    for tier in range(1, len(superpipeline.pipelinesByTier) + 1):

      # Loop over the pipelines.
      for pipeline in superpipeline.pipelinesByTier[tier]:

        # Get the pipeline configuration data.
        pipelineData = superpipeline.pipelineConfigurationData[pipeline]
        for argument in pipelineData.longFormArguments:

          # Get the pipeline address.
          address = pipelineData.address

          # Get the node that this argument is associated with and the graph node associated with
          # the configuration node.
          configurationNodeID = pipelineData.longFormArguments[argument].nodeID
          nodeAddress         = address + '.' + configurationNodeID if address else configurationNodeID
          graphNodeID         = superpipeline.configurationNodes[nodeAddress]

          # If this is not the top level pipeline, the argument requires the pipeline address. Define
          # the argument name for use in the data structures.
          argumentAddress = str(address + '.' + argument) if address else str(argument)

          # Link the graph node ID with the argument.
          if graphNodeID not in self.nodeToArgument: self.nodeToArgument[str(graphNodeID)] = argumentAddress

          # If this is not the top level pipeline, add the argument to the list of available arguments.
          if tier != 1:
            self.arguments[str(argumentAddress)] = argumentInformation()
            self.arguments[str(argumentAddress)].description       = pipelineData.longFormArguments[argument].description
            self.arguments[str(argumentAddress)].shortFormArgument = pipelineData.longFormArguments[argument].shortFormArgument

          # Link the argument with the graph node ID to which it points.
          self.arguments[str(argumentAddress)].graphNodeID = str(graphNodeID)

  # If the main pipeline lists a tool whose arguments should be imported, check that the listed tool is
  # valid, that none of the arguments conflict with the pipeline and then add the arguments to the
  # allowed arguments.
  def importArguments(self, superpipeline):

    # Get the name of the tool.
    task = superpipeline.pipelineConfigurationData[superpipeline.pipeline].importArgumentsFromTool
    if not task: return

    # Check if the named task is a pipeline, a tool or invalid and respond appropriately.
    if task in superpipeline.tasks: self.importToolArguments(task, superpipeline)
    elif task in superpipeline.tiersByPipeline: self.importPipelineArguments(task, superpipeline)

    # The supplied task is invalid.
    else: self.errors.invalidImportTool(task)

  # Import arguments from a tool in the pipeline.
  def importToolArguments(self, tool, superpipeline):
    pass

  # Import arguments from a pipeline contained within the pipeline.
  def importPipelineArguments(self, pipeline, superpipeline):
    pass

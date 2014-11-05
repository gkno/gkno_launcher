#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import version2.pipelineConfiguration as pipelineConfiguration

import json
import os
import sys

# Define a class to store task attribtues.
class superPipelineClass:
  def __init__(self, pipeline):

    # The number of tiers in the super pipeline.
    self.numberOfTiers = 1

    # Store all of the pipeline configuration files comprising the superpipeline in a
    # dictionary, indexed by the tier. The first tier contains the top level configuration
    # file (e.g. the one defined on the command line).
    self.configurationData    = {}
    self.configurationData[1] = []

    # Store all the tasks in the superpipeline along with the tools,
    self.tools = []
    self.tasks = {}

    # Store the unique and shared node IDs in all the pipeline.
    self.uniqueNodeIDs = []
    self.sharedNodeIDs = []

  # Starting from the defined pipeline, process and validate the configuration file contents,
  # then dig down through all the nested pipelines and validate their configuration files.
  def getNestedPipelineData(self, path, filename):

    # Get the top level pipeline configuration file data.
    pipeline = pipelineConfiguration.pipelineConfiguration()
    pipeline.getConfigurationData(filename)
    self.configurationData[1].append(pipeline)

    # Now dig into the nested pipeline and build up the super pipeline structure.
    tier = 2
    checkForNestedPipelines = True
    while checkForNestedPipelines:
      tierHasNestedPipeline = False
      for currentPipeline in self.configurationData[tier - 1]:
  
        # If the pipeline contains a pipeline as a task, process the configuration file for that
        # pipeline and add to the pipelines in the current tier.
        if currentPipeline.hasPipelineAsTask:
          tierHasNestedPipeline = True
          for taskPointingToNestedPipeline, nestedPipeline in currentPipeline.requiredPipelines:
            filename = path + str(nestedPipeline) + '.json'
            pipeline = pipelineConfiguration.pipelineConfiguration()
            pipeline.getConfigurationData(filename)
  
            # If this is the first pipeline in this tier, generate the entry in the dictionary.
            if tier not in self.configurationData: self.configurationData[tier] = []
  
            # Construct the address of the task.
            pipeline.address = '' if currentPipeline.address == None else str(currentPipeline.address) + '.'
            pipeline.address += str(taskPointingToNestedPipeline)
            self.configurationData[tier].append(pipeline)
  
        # Increment the tier. If no pipelines in the just processed tier had a nested pipeline, the
        # loop can end.
        tier += 1
        if not tierHasNestedPipeline: checkForNestedPipelines = False

  # Get all of the tools from each pipeline in the super pipeline and store them.
  def getTools(self):
    for tier in self.configurationData.keys():
      for pipeline in self.configurationData[tier]:

        # Loop over all of the pipeline tasks.
        for task in pipeline.getAllTasks():

          # Get the pipeline relative address of the task.
          taskAddress = str(pipeline.address + '.' + task) if pipeline.address else str(task)

          # Get the tool for the task.
          tool = pipeline.getTaskAttribute(task, 'tool')

          # If this tool is not yet in the tools list, include it.
          if tool not in self.tools: self.tools.append(tool)

          # Store the task with its tool.
          self.tasks[taskAddress] = tool

        # Store the unique and shared node IDs for each pipeline.
        self.uniqueNodeIDs += [str(pipeline.address + '.' + nodeID) if pipeline.address else str(nodeID) for nodeID in pipeline.getUniqueNodeIDs()]
        self.sharedNodeIDs += [str(pipeline.address + '.' + nodeID) if pipeline.address else str(nodeID) for nodeID in pipeline.getSharedNodeIDs()]

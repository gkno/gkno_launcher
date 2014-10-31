#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import json
import os
import sys

# Define a class to store task attribtues.
class superPipelineClass:
  def __init__(self):

    # The number of tiers in the super pipeline.
    self.numberOfTiers = 1

    # Store all the tasks in the superpipeline along with the tools,
    self.tools = []
    self.tasks = {}

    # Store the unique and shared node IDs in all the pipeline.
    self.uniqueNodeIDs = []
    self.sharedNodeIDs = []

  # Get all of the tools from each pipeline in the super pipeline and store them.
  def getTools(self, pipelineConfigurationData):
    for tier in pipelineConfigurationData.keys():
      for pipeline in pipelineConfigurationData[tier]:

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

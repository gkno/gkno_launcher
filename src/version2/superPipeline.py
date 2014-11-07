#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import version2.pipelineConfiguration as pipelineConfiguration
import version2.toolConfiguration as toolConfiguration

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

    # Store information on all the constituent tools.
    self.toolConfigurationData = {}

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
  def setTools(self):
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

  # Check that all references to tasks in the pipeline configuration file are valid. The task may
  # be a task in a contained pipeline and not within the pipeline being checked. The allTasks
  # list contains all of the tasks in all of the pipelines.
  def checkContainedTasks(self):

    # Loop over all the tiers in the super pipeline.
    for tier in self.configurationData.keys():
      for pipelineObject in self.configurationData[tier]:

        # Check the tasks that any unique nodes point to.
        for nodeID in pipelineObject.uniqueNodeAttributes.keys():
    
          # Get the name of the pipeline (if exists) and the task that this node points to.
          pipeline = pipelineObject.getUniqueNodeAttribute(nodeID, 'pipeline')
          task     = pipelineObject.getUniqueNodeAttribute(nodeID, 'task')
    
          # This pipeline may itself be called by an enveloping pipeline. If so, any tasks
          # will require prepending with the address of this pipeline.
          if pipeline: task = pipeline + '.' + task
          if pipelineObject.address: task = pipelineObject.address + '.' + task
    
          # If the task is not listed as one of the pipeline tasks. terminate.
          #TODO ERROR
          if task not in self.tasks: print('superPipeline.checkContainedTasks - 1', task); exit(0)
    
        # Check the tasks that shared nodes point to.
        for sharedNodeID in pipelineObject.sharedNodeAttributes.keys():
          for node in pipelineObject.sharedNodeAttributes[sharedNodeID].sharedNodeTasks:
            task           = pipelineObject.getNodeTaskAttribute(node, 'task')
            taskArgument   = pipelineObject.getNodeTaskAttribute(node, 'taskArgument')
            pipeline       = pipelineObject.getNodeTaskAttribute(node, 'pipeline')
            pipelineNodeID = pipelineObject.getNodeTaskAttribute(node, 'pipelineNodeID')
    
            # If the shared node is a defined node in another pipeline, ensure that no task or
            # argument are supplied. If they are terminate, as there is more information than
            # required, which suggests an error in the configuration file construction. The pipeline
            # in which the node resides is required.
            if pipelineNodeID:
              #TODO ERROR
              if task or taskArgument: print('superPipeline.checkContainedTasks - 2'); exit(0)
              if not pipeline: print('superPipeline.checkContainedTasks - 3'); exit(0)
              pipelineNodeID = pipeline + '.' + pipelineNodeID
              if pipelineObject.address: pipelineNodeID = pipelineObject.address + '.' + pipelineNodeID
    
              # If the task is not listed as one of the pipeline tasks. terminate.
              #TODO ERROR
              if pipelineNodeID not in self.uniqueNodeIDs and pipelineNodeID not in self.sharedNodeIDs:
                print('superPipeline.checkContainedTasks - 4'); exit(0)
    
            # If the shared node is a task in another pipeline, check that the task exists.
            elif pipeline:
              task = pipeline + '.' + task
              if pipelineObject.address: task = pipelineObject.address + '.' + task
              #TODO ERROR
              if task not in self.tasks: print('superPipeline.checkContainedTasks - 5'); exit(0)
    
            # Finally, if the shared node points to a task from this pipeline.
            else:
              if pipelineObject.address: task = pipelineObject.address + '.' + task
              #TODO ERROR
              if task not in self.tasks: print('superPipeline.checkContainedTasks - 6'); exit(0)

  # Add tool configuration data to the super pipeline.
  def addTool(self, tool, toolData):
    self.toolConfigurationData[tool] = toolData

  # Return all the tools used in the superpipeline.
  def getTools(self):
    return self.tools

  # Return data for a specified tool.
  def getToolData(self, tool):
    return self.toolConfigurationData[tool]

  # Get a parameter set for a tool.
  def getToolParameterSet(self, tool, parameterSet):
    try: return self.toolConfigurationData[tool].parameterSets.sets[parameterSet]
    except: return None

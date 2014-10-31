#!/usr/bin/python

from __future__ import print_function

from copy import deepcopy
import os.path
import getpass
import subprocess
import sys

import networkx as nx

import version2.graph
from version2.graph import *

import version2.plotGraph
from version2.plotGraph import *

import version2.toolConfiguration
from version2.toolConfiguration import *

import version2.pipelineConfiguration
from version2.pipelineConfiguration import *

import version2.superPipeline
from version2.superPipeline import *

__author__ = "Alistair Ward"
__version__ = "2.0.0"
__date__ = "October 2014"

def main():
  print('TESTING VERSION 2')

   # Define the source path of all the gkno machinery.
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]

  # TODO REMOVE
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/version2.py')]

  configurationFilesPath         = sourcePath + '/config_files/'
  gknoConfigurationFilePath      = sourcePath + '/config_files/'
  pipelineConfigurationFilesPath = sourcePath + '/config_files/pipes/'
  toolConfigurationFilesPath     = sourcePath + '/config_files/tools/'
  resourcesPath                  = sourcePath + '/resources/'
  toolsPath                      = sourcePath + '/tools/'

  # TODO REMOVE
  pipelineConfigurationFilesPath = sourcePath + '/development/'
  filename = pipelineConfigurationFilesPath + 'biggest.json'

  pipelineConfigurationData    = {}
  pipelineConfigurationData[1] = []

  # Get the pipeline configuration file data.
  pipeline = pipelineConfiguration()
  pipeline.getConfigurationData(filename)
  pipelineConfigurationData[1].append(pipeline)

  # Generate a super pipeline class that holds information about the full collection of all nested
  # pipeline.
  superPipeline = superPipelineClass()

  tier = 2
  checkForNestedPipelines = True
  while checkForNestedPipelines:
    tierHasNestedPipeline = False
    for currentPipeline in pipelineConfigurationData[tier - 1]:

      # If the pipeline contains a pipeline as a task, process the configuration file for that
      # pipeline and add to the pipelines in the current tier.
      if currentPipeline.hasPipelineAsTask:
        tierHasNestedPipeline = True
        for taskPointingToNestedPipeline, nestedPipeline in currentPipeline.requiredPipelines:
          filename = pipelineConfigurationFilesPath + str(nestedPipeline) + '.json'
          pipeline = pipelineConfiguration()
          pipeline.getConfigurationData(filename)

          # If this is the first pipeline in this tier, generate the entry in the dictionary.
          if tier not in pipelineConfigurationData: pipelineConfigurationData[tier] = []

          # Construct the address of the task.
          pipeline.address = '' if currentPipeline.address == None else str(currentPipeline.address) + '.'
          pipeline.address += str(taskPointingToNestedPipeline)
          pipelineConfigurationData[tier].append(pipeline)

      # Increment the tier. If no pipelines in the just processed tier had a nested pipeline, the
      # loop can end.
      tier += 1
      if not tierHasNestedPipeline: checkForNestedPipelines = False

  # Generate a list of all tasks, tools, unique and shared node IDs from all pipelines.
  superPipeline.getTools(pipelineConfigurationData)

  # Now that all the tasks are known, check that each pipeline only contains valid tasks. If a 
  # task in the pipeline addresses a node in a contained pipeline, knowledge of all pipelines is
  # required to perform this check.
  for tier in pipelineConfigurationData.keys():
    for pipeline in pipelineConfigurationData[tier]: pipeline.checkContainedTasks(superPipeline)
  
  # Loop over the list of required tools, open and process their configuration files and store.
  toolConfigurationData = {}
  for toolName in superPipeline.tools:
    filename = toolConfigurationFilesPath + str(toolName) + '.json'
    tool     = toolConfiguration()
    tool.getConfigurationData(filename)
    toolConfigurationData[toolName] = tool

  # Define the graph object that will contain the pipeline graph and necessary operations and methods
  # to build and modify it.
  graph = pipelineGraph()

  # Loop backwards over the tiers of nested pipelines and build them into the graph.
  for tier in reversed(pipelineConfigurationData.keys()):
    for pipeline in pipelineConfigurationData[tier]: graph.buildPipelineTasks(toolConfigurationData, pipeline, superPipeline)

  plot = plotGraph()
  plot.plot(graph.graph.copy(), 'test.dot')
  #workflow = graph.generateWorkflow()

if __name__ == "__main__":
  main()

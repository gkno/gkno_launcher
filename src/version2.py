#!/usr/bin/python

from __future__ import print_function

from copy import deepcopy
import os.path
import getpass
import subprocess
import sys

import networkx as nx

import version2.adminUtils
from version2.adminUtils import *

import version2.commandLine
from version2.commandLine import *

import version2.fileOperations

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

  # Define a class for processing the command line.
  command = commandLine()

   # Define the source path of all the gkno machinery.
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]

  # TODO REMOVE
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/version2.py')]

  configurationFilesPath         = sourcePath + '/config_files/'
  pipelineConfigurationFilesPath = sourcePath + '/config_files/pipes/'
  toolConfigurationFilesPath     = sourcePath + '/config_files/tools/'

  # TODO REMOVE
  pipelineConfigurationFilesPath = sourcePath + '/development/'

  resourcesPath                  = sourcePath + '/resources/'
  toolsPath                      = sourcePath + '/tools/'

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = adminUtils(sourcePath)

  # Determine if gkno is being run in admin mode and then determine the mode.
  isAdminMode, adminMode = command.isAdmin(admin.allModes)
  mode                   = command.determineMode(isAdminMode)

  # If not being run in pipeline mode, determine the name of the pipeline being run. Note that
  # for the code, a tool is considered a pipeline with a single task, so the terminology
  # 'pipeline' is used throughout for both cases.
  if not isAdminMode: pipeline = command.determinePipeline()

  # Get the path to the pipeline and configuration file.
  filename = pipelineConfigurationFilesPath + pipeline + '.json'

  # Check that the pipeline configuration file exists. If not, see if this is running a tool.
  isTool = False
  isFile = fileOperations.checkIfFileExists(filename)
  if not isFile:
    filename = toolConfigurationFilesPath + pipeline + '.json'
    isFile   = fileOperations.checkIfFileExists(filename)
    isTool   = True
  
  #TODO RROR
  if not isFile: print('NO CONFIG'); sys.exit(0)

  # Generate a super pipeline class that holds information about the full collection of all nested
  # pipeline.
  superPipeline = superPipelineClass(filename)

  # If the pipeline is really a single tool, set up the super pipeline.
  # TODO HANDLE TOOLS
  if isTool: print('NOT HANDLED TOOLS'); exit(0)

  # Dig down into the pipeline configuration files, validate the contents of the configuration files
  # and build the super pipeline tiered structure.
  superPipeline.getNestedPipelineData(pipelineConfigurationFilesPath, filename)

  # Generate a list of all tasks, tools, unique and shared node IDs from all pipelines.
  superPipeline.getTools()

  # Now that all the tasks are known, check that each pipeline only contains valid tasks. If a 
  # task in the pipeline addresses a node in a contained pipeline, knowledge of all pipelines is
  # required to perform this check.
  for tier in superPipeline.configurationData.keys():
    for pipeline in superPipeline.configurationData[tier]: pipeline.checkContainedTasks(superPipeline)
  
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
  for tier in reversed(superPipeline.configurationData.keys()):
    for pipeline in superPipeline.configurationData[tier]: graph.buildPipelineTasks(toolConfigurationData, pipeline, superPipeline)

  plot = plotGraph()
  plot.plot(graph.graph.copy(), 'test.dot')

  #workflow = graph.generateWorkflow()

if __name__ == "__main__":
  main()

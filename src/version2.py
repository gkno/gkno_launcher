#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
import subprocess
import sys

import version2.adminUtils
from version2.adminUtils import *

import version2.commandLine
from version2.commandLine import *

import version2.fileHandling
import version2.gknoConfiguration as gknoConfiguration

import version2.graph
from version2.graph import *

import version2.plotGraph
from version2.plotGraph import *

import version2.toolConfiguration

import version2.pipelineConfiguration
from version2.pipelineConfiguration import *

import version2.superpipeline
from version2.superpipeline import *

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
  configurationFilesPath         = sourcePath + '/development/'
  pipelineConfigurationFilesPath = sourcePath + '/development/pipelines/'
  toolConfigurationFilesPath     = sourcePath + '/development/tools/'

  resourcesPath                  = sourcePath + '/resources/'
  toolsPath                      = sourcePath + '/tools/'

  # Define a class for handling files. In the initialisation, determine the names of all available
  # tools and pipelines.
  files = fileHandling.fileHandling(toolConfigurationFilesPath, pipelineConfigurationFilesPath)

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = adminUtils(sourcePath)

  # Determine if gkno is being run in admin mode and then determine the mode.
  isAdminMode, adminMode = command.isAdmin(admin.allModes)
  mode                   = command.determineMode(isAdminMode)

  # If not being run in admin mode, determine the name of the pipeline being run. Note that
  # for the code, a tool is considered a pipeline with a single task, so the terminology
  # 'pipeline' is used throughout for both cases.
  if not isAdminMode: pipeline = command.determinePipeline()

  # Get the path to the pipeline and configuration file.
  filename, isTool = files.checkPipeline(toolConfigurationFilesPath, pipelineConfigurationFilesPath, pipeline)

  # Initialise the gkno specific configuration file.
  gc = gknoConfiguration.gknoConfiguration(configurationFilesPath)

  # Generate a super pipeline class that holds information about the full collection of all nested
  # pipeline.
  superpipeline = superpipelineClass(filename)

  # If the pipeline is really a single tool, set up the super pipeline.
  # TODO HANDLE TOOLS
  if isTool: print('NOT HANDLED TOOLS'); exit(0)

  # Dig down into the pipeline configuration files, validate the contents of the configuration files
  # and build the super pipeline tiered structure.
  superpipeline.getNestedPipelineData(pipelineConfigurationFilesPath, filename)
  executedPipeline = superpipeline.pipelinesByTier[1][0]

  # Generate a list of all tasks, tools, unique and shared node IDs from all pipelines.
  superpipeline.setTools()

  # Now that all the tasks are known, check that each pipeline only contains valid tasks. If a 
  # task in the pipeline addresses a node in a contained pipeline, knowledge of all pipelines is
  # required to perform this check.
  superpipeline.checkContainedTasks()
  
  # Loop over the list of required tools, open and process their configuration files and store.
  for tool in superpipeline.getTools():
    toolData = toolConfiguration.toolConfiguration()
    toolData.getConfigurationData(tool, toolConfigurationFilesPath + str(tool) + '.json')
    superpipeline.addTool(tool, toolData)

  # Define the graph object that will contain the pipeline graph and necessary operations and methods
  # to build and modify it.
  graph = pipelineGraph()

  # Collate a list of all arguments associated with each pipeline, gkno arguments or pipeline tasks.
  superpipeline.getArguments(executedPipeline)

  # Process the command line arguments.
  command.processArguments(superpipeline, gc.arguments, gc.shortForms)

  # Loop over the tiers of nested pipelines and build them into the graph.
  for tier in superpipeline.pipelinesByTier.keys():
    for pipelineName in superpipeline.pipelinesByTier[tier]:
      graph.buildPipelineTasks(superpipeline.pipelineConfigurationData[pipelineName], superpipeline)

  # Generate the workflow.
  workflow = graph.generateWorkflow()

  # Step through the workflow and determine the default parameter sets for all of the tasks. Populate
  # the nodes with these task level default parameter sets, creating nodes where necessary.
  graph.addTaskParameterSets(superpipeline, 'default')

  # Now add the default parameter set for the pipelines.
  graph.addPipelineParameterSets(superpipeline, 'default')

  # Determine the requested parameter set and add the parameters to the graph.
  parameterSet = command.getParameterSetName(command.gknoArguments)
  if parameterSet: graph.addParameterSet(superpipeline, executedPipeline, parameterSet)

  plot = plotGraph()
  plot.plot(graph.graph.copy(), 'test.dot')

if __name__ == "__main__":
  main()

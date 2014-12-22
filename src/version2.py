#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
import subprocess
import sys

import version2.adminUtils as au
import version2.arguments as ag
import version2.commandLine as cl
import version2.constructFilenames as construct
import version2.dataConsistency as dc
import version2.fileHandling as fh
import version2.gknoConfiguration as gc
import version2.graph as gr
import version2.helpInformation as hp
import version2.plotGraph as pg
import version2.toolConfiguration as tc
import version2.pipelineConfiguration as pc
import version2.superpipeline as sp

__author__ = "Alistair Ward"
__version__ = "2.0.0"
__date__ = "October 2014"

def main():

  # Define a class for processing the command line.
  command = cl.commandLine()

  # Define a help class.
  gknoHelp = hp.helpInformation(os.getenv('GKNOCOMMITID'), __date__, __version__)

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
  files = fh.fileHandling(toolConfigurationFilesPath, pipelineConfigurationFilesPath)

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = au.adminUtils(sourcePath)

  # Initialise the gkno specific configuration file.
  gknoConfiguration = gc.gknoConfiguration(configurationFilesPath)

  # Determine if gkno is being run in admin mode and then determine the mode.
  isAdminMode, adminMode = command.isAdmin(admin.allModes)
  mode                   = command.determineMode(isAdminMode, gknoConfiguration)

  # If not being run in admin mode, determine the name of the pipeline being run. Note that
  # for the code, a tool is considered a pipeline with a single task, so the terminology
  # 'pipeline' is used throughout for both cases.
  if not isAdminMode: pipeline = command.determinePipeline()

  # Otherwise, handle the admin functions.
  else: print('NOT HANDLED ADMIN'); exit(0)

  # If the pipeline name has not been supplied, general help must be required.
  if not pipeline: gknoHelp.generalHelp(mode, command.category, admin, pipelineConfigurationFilesPath)

  # Get the path to the pipeline and configuration file.
  filename = files.checkPipeline(toolConfigurationFilesPath, pipelineConfigurationFilesPath, pipeline)

  # Generate a super pipeline class that holds information about the full collection of all nested
  # pipeline.
  superpipeline = sp.superpipelineClass(filename)

  # Dig down into the pipeline configuration files, validate the contents of the configuration files
  # and build the super pipeline tiered structure.
  superpipeline.getNestedPipelineData(pipelineConfigurationFilesPath, filename)

  # Check that no pipeline arguments conflict with gkno arguments.
  superpipeline.checkForArgumentConflicts(gknoConfiguration.arguments, gknoConfiguration.shortForms)

  # If help categories were requested, or a list of all available pipelines, print them here.
  if mode == 'categories' or mode == 'list-all': gknoHelp.generalHelp(mode, command.category, admin, pipelineConfigurationFilesPath)

  # Generate a list of all tasks, tools, unique and shared node IDs from all pipelines.
  superpipeline.setTools()

  # Now that all the tasks are known, check that each pipeline only contains valid tasks. If a 
  # task in the pipeline addresses a node in a contained pipeline, knowledge of all pipelines is
  # required to perform this check.
  superpipeline.checkContainedTasks()
  
  # Loop over the list of required tools, open and process their configuration files and store.
  for tool in superpipeline.getTools():
    toolData = tc.toolConfiguration()
    toolData.getConfigurationData(tool, toolConfigurationFilesPath + str(tool) + '.json')
    superpipeline.addTool(tool, toolData)

  # Define the graph object that will contain the pipeline graph and necessary operations and methods
  # to build and modify it.
  graph = gr.pipelineGraph()

  # Loop over the tiers of nested pipelines and build them into the graph.
  for tier in superpipeline.pipelinesByTier.keys():
    for pipelineName in superpipeline.pipelinesByTier[tier]:
      graph.buildPipelineTasks(superpipeline.pipelineConfigurationData[pipelineName], superpipeline)

  # Create an arguments object. This will be populated with all of the arguments available for this
  # pipeline along with associated functions. Add all of the top level pipeline arguments to this
  # object.
  args = ag.arguments()
  args.addPipelineArguments(superpipeline.pipelineConfigurationData[superpipeline.pipeline].longFormArguments)

  # Now that the graph is built, parse all of the arguments in the pipelines and associate them with the
  # graph nodes and vice versa.
  args.assignNodesToArguments(graph, superpipeline)

  # If the main pipeline lists a tool whose arguments should be imported, check that the listed tool is
  # valid, that none of the arguments conflict with the pipeline and then add the arguments to the
  # allowed arguments.
  args.importArguments(graph, superpipeline)

  # Generate the workflow.
  workflow = graph.generateWorkflow()

  # If help was requested, print out the relevent help information.
  # TODO ADMIN HELP
  if mode == 'help' or mode == 'gkno help':

    # Write out help on gkno specific (e.g. not associated with a specific pipeline) arguments.
    if mode == 'gkno help': gknoHelp.gknoArgumentHelp(gknoConfiguration.arguments)

    # Otherwise, write out help for the pipeline being run.
    else: gknoHelp.pipelineHelp(superpipeline, graph, args.arguments)
  
  # Process the command line arguments.
  command.processArguments(superpipeline, gknoConfiguration.arguments, gknoConfiguration.shortForms)

  # Step through the workflow and determine the default parameter sets for all of the tasks. Populate
  # the nodes with these task level default parameter sets, creating nodes where necessary.
  graph.addTaskParameterSets(superpipeline, 'default')

  # Now add the default parameter set for the pipelines.
  graph.addPipelineParameterSets(superpipeline, 'default')

  # Determine the requested parameter set and add the parameters to the graph.
  parameterSet = command.getParameterSetName(command.gknoArguments)
  if parameterSet: graph.addParameterSet(superpipeline, superpipeline.pipeline, parameterSet)

  # Parse the command line arguments and associate the supplied command line argument values with the graph node.
  command.parseTasksAsArguments(superpipeline)
  associatedNodes = command.associateArgumentsWithGraphNodes(graph.graph, superpipeline)

  # Create nodes for all of the defined arguments for which a node does not already exist and add the
  # argument values to the node.
  graph.attachArgumentValuesToNodes(superpipeline, args, command.pipelineArguments, associatedNodes)

  # Loop over all nodes and expand lists of arguments. This is only valid for arguments that are either options,
  # or inputs to a task that are not simulateously outputs of another task.
  graph.expandLists()

  # Check that all of the values associated with all of the nodes are of the correct type (e.g. integer, flag etc)
  # and also that any files also have the correct extension.
  dc.checkValues(graph, superpipeline, args)

  # Loop over all of the nodes in the graph and ensure that all required arguments have been set. Any output files
  # for which construction instructions are provided can be omitted from this check. This will ensure that all required
  # input files are set, ensuring that filename construction can proceed. The check will be performed again after
  # filenames have been constructed, without the omission of constructed files.
  dc.checkRequiredArguments(graph, superpipeline, args, isFullCheck = False)

  # With the graph built, all arguments attached and checked, the final task prior to converting the graph to
  # an executable is to construct filenames that have not been provided.
  construct.constructFilenames(graph, superpipeline)

  # Construct input files.
  construct.constructInputNodes(graph, superpipeline)

  # Having constructed all of the output file names (which may then be linked to other tasks as outputs), rerun the
  # check of the values to ensure that the data types and the ssociated extensions are valid. This will provide a
  # check of whether tools can be linked as described in the configuration file. In the previous check, not all of the
  # filenames were present (but the check ensured that the values provided on the command line were valid). If a task
  # outputs a file with and extension 'ext1' and the file is then passed to a file that requires files with the
  # extension 'ext2', the pipeline is invalid. The output filename has been constructed as file.ext1 and so the following
  # routine will flag the file as invalid as input to the next task.
  dc.checkValues(graph, superpipeline, args)
  dc.checkRequiredArguments(graph, superpipeline, args, isFullCheck = True)

  #for task in graph.workflow:
  #  print(task)
  #  print('\tINPUTS')
  #  for nodeID in graph.getPredecessors(task): print('\t\t', nodeID, graph.getArgumentAttribute(nodeID, task, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))
  #  print('\tOUTPUTS')
  #  for nodeID in graph.getSuccessors(task): print('\t\t', nodeID, graph.getArgumentAttribute(task, nodeID, 'longFormArgument'), graph.getGraphNodeAttribute(nodeID, 'values'))

  # At this point, all values must be set. If anything is missing, the pipeline is incomplete or data hasn't been
  # provided. If this is the case, terminate.
  #dc.finalCheck(graph, superpipeline)


  plot = pg.plotGraph()
  plot.plot(superpipeline, graph, 'full.dot', isReduced = False)
  plot.plot(superpipeline, graph, 'reduced.dot', isReduced = True)

if __name__ == "__main__":
  main()

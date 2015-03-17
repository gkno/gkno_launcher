#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
import subprocess
import sys

import gkno.adminUtils as au
import gkno.adminErrors as adminErrors
import gkno.arguments as ag
import gkno.commandLine as cl
import gkno.constructFilenames as construct
import gkno.dataConsistency as dc
import gkno.debug as debug
import gkno.executionStructure as es
import gkno.fileHandling as fh
import gkno.gknoConfiguration as gc
import gkno.graph as gr
import gkno.helpInformation as hp
import gkno.makefiles as mk
import gkno.plotGraph as pg
import gkno.parameterSets as ps
import gkno.pipelineConfiguration as pc
import gkno.superpipeline as sp
import gkno.toolConfiguration as tc
import gkno.web as w
import gkno.writeToScreen as write

__author__ = "Alistair Ward"
__version__ = "2.0.0"
__date__ = "January 2015"

def main():

  # Define a class for processing the command line.
  command = cl.commandLine()

  # Define a help class.
  gknoHelp = hp.helpInformation(os.getenv('GKNOCOMMITID'), __date__, __version__)

  # Define a plotting class for drawing the graph.
  plot = pg.plotGraph()

  #Define an object to hold information for creating web content.
  web = w.webContent()

  # Define the source paths of all the gkno machinery.
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]
  configurationFilesPath         = sourcePath + '/config_files'
  pipelineConfigurationFilesPath = sourcePath + '/config_files/pipes'
  toolConfigurationFilesPath     = sourcePath + '/config_files/tools'
  resourcesPath                  = sourcePath + '/resources'
  toolsPath                      = sourcePath + '/tools'

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = au.adminUtils(sourcePath)

  # Initialise the gkno specific configuration file.
  gknoConfiguration = gc.gknoConfiguration(configurationFilesPath)

  # Determine if gkno is being run in admin mode and then determine the mode.
  admin.isRequested, admin.mode = command.isAdmin(admin.allModes)
  mode                          = command.determineMode(admin.isRequested, gknoConfiguration)

  # Print gkno title and version to the screen.
  write.printHeader(__version__, __date__, os.getenv('GKNOCOMMITID'))

  # Check to see if the configuration files are to be found in a directory other than the default.
  path = command.getConfigurationFilePath(gknoConfiguration.options)
  userConfigurationPath = path if path else None

  # Define a class for handling files. In the initialisation, determine the names of all available
  # tools and pipelines.
  files = fh.fileHandling(toolConfigurationFilesPath, pipelineConfigurationFilesPath, userConfigurationPath)

  # If not being run in admin mode, determine the name of the pipeline being run. Note that
  # for the code, a tool is considered a pipeline with a single task, so the terminology
  # 'pipeline' is used throughout for both cases.
  if not admin.isRequested: pipeline = command.determinePipeline()

  # Otherwise, handle the admin functions.
  else:
    if admin.run(sys.argv):

      # Check that all of the tools were successfully built. If not, post a warning about which tools cannot
      # be used.
      if admin.allBuilt: exit(0)
      else: adminErrors.adminErrors().failedToolBuilds(admin.builtTools)
    else: adminErrors.adminErrors().errors.terminate(adminErrors.adminErrors().errorCode)

  # If the pipeline name has not been supplied, general help must be required.
  if not pipeline and mode != 'web': gknoHelp.generalHelp(mode, command.category, admin, pipelineConfigurationFilesPath)

  # If json files for the web page were requested, set the pipelinesList to all pipelines and loop over
  # them all, generating the required information. Otherwise, set the list to the pipeline to be run.
  pipelinesList = files.pipelines if mode == 'web' else [pipeline]
  for pipeline in pipelinesList:
  
    # Get the path to the pipeline and configuration file.
    filename = files.checkPipeline(toolConfigurationFilesPath, pipelineConfigurationFilesPath, userConfigurationPath, pipeline)

    # Generate a super pipeline class that holds information about the full collection of all nested
    # pipeline.
    superpipeline = sp.superpipelineClass(filename)

    # Dig down into the pipeline configuration files, validate the contents of the configuration files
    # and build the super pipeline tiered structure.
    superpipeline.getNestedPipelineData(files, pipelineConfigurationFilesPath, userConfigurationPath, filename)
  
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
    superpipeline.addTools(files, toolConfigurationFilesPath, userConfigurationPath)
  
    # Loop over all of the pipeline configuration files and check that all nodes that define a tool
    # argument have valid arguments for the tool.
    superpipeline.checkArgumentsInPipeline()

    # Create an arguments object. This will be populated with all of the arguments available for this
    # pipeline along with associated functions. Add all of the top level pipeline arguments to this
    # object.
    args = ag.arguments()
    args.addPipelineArguments(superpipeline.pipelineConfigurationData[superpipeline.pipeline].longFormArguments)

    # Define the graph object that will contain the pipeline graph and necessary operations and methods
    # to build and modify it.
    graph = gr.pipelineGraph()

    # Loop over the tiers of nested pipelines and build them into the graph.
    for tier in superpipeline.pipelinesByTier.keys():
      for pipelineName in superpipeline.pipelinesByTier[tier]:
        graph.buildPipelineTasks(superpipeline.pipelineConfigurationData[pipelineName], superpipeline)

    # Determine which graph nodes are required. A node may be used by multiple tasks and may be optional
    # for some and required by others. For each node, loop over all edges and check if any of the edges
    # are listed as required. If so, the node is required and should be marked as such.
    graph.markRequiredNodes(superpipeline)

    # If the main pipeline lists a tool whose arguments should be imported, check that the listed tool is
    # valid, that none of the arguments conflict with the pipeline and then add the arguments to the
    # allowed arguments.
    args.importArguments(graph, superpipeline)

    # Now that the graph is built, parse all of the arguments in the pipelines and associate them with the
    # graph nodes and vice versa.
    args.assignNodesToArguments(graph, superpipeline)

    # If web page json files are being created, update the list of categories and the pipeline information.
    if mode == 'web':
      web.updateCategories(superpipeline.pipelineConfigurationData[superpipeline.pipeline])
      web.updatePipelineInformation(superpipeline.pipelineConfigurationData[superpipeline.pipeline], args.arguments)

  # Write out web content and terminate.
  if mode == 'web': web.writeContent()

  # Generate the workflow.
  workflow = graph.generateWorkflow()

  # Process the command line arguments.
  command.processArguments(superpipeline, args, gknoConfiguration)

  # Step through the workflow and determine the default parameter sets for all of the tasks. Populate
  # the nodes with these task level default parameter sets, creating nodes where necessary.
  graph.addTaskParameterSets(superpipeline, 'default')

  # Now add the default parameter set for the pipelines.
  graph.addPipelineParameterSets(superpipeline, 'default')

  # Determine the requested parameter set and add the parameters to the graph.
  parSet             = ps.parameterSets()
  graph.parameterSet = command.getParameterSetName(command.gknoArguments, gknoConfiguration)
  if graph.parameterSet: graph.addParameterSet(superpipeline, superpipeline.pipeline, graph.parameterSet)

  # If help was requested, print out the relevent help information.
  # TODO ADMIN HELP
  if mode == 'help' or mode == 'gkno help':

    # Write out help on gkno specific (e.g. not associated with a specific pipeline) arguments.
    if mode == 'gkno help': gknoHelp.gknoArgumentHelp(gknoConfiguration.arguments)

    # Otherwise, write out help for the pipeline being run.
    else: gknoHelp.pipelineHelp(superpipeline, graph, args.arguments)  

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
  dc.checkValues(graph, superpipeline)

  # Determine if a parameter set is being exported. If so, there is no need to check that all required
  # arguments are set, since the pipeline is not being executed.
  isExportSet = gknoConfiguration.getGknoArgument('GKNO-EXPORT-PARAMETER-SET', command.gknoArguments)

  # Loop over all of the nodes in the graph and ensure that all required arguments have been set. Any output files
  # for which construction instructions are provided can be omitted from this check. This will ensure that all required
  # input files are set, ensuring that filename construction can proceed. The check will be performed again after
  # filenames have been constructed, without the omission of constructed files.
  if not isExportSet: dc.checkRequiredArguments(graph, superpipeline, args, isFullCheck = False)

  # Determine which files are marked for deletion.
  superpipeline.determineFilesToDelete(graph)

  # Mark any tasks that have greedy arguments as greedy.
  graph.markGreedyTasks(superpipeline)

  # Determine whether or not to output a visual representation of the pipeline graph.
  plot.isPlotRequired(command.gknoArguments, gknoConfiguration)
  if plot.isFullPlot: plot.plot(superpipeline, graph, plot.fullPlotFilename, isReduced = False)
  if plot.isReducedPlot: plot.plot(superpipeline, graph, plot.reducedPlotFilename, isReduced = True)

  # TODO
  graph.constructFiles(superpipeline)
  debug.debug().allTasks(graph)
  exit(0)

  # Check the number of values in each node and determine how many times each task needs to be run. For example,
  # a tool could be fed 'n' input files for a single argument and be run 'n' times or once etc. In addition check
  # the arguments that have been supplied to each task. In particular, check the number of values given to all
  # arguments and determine whether tasks need to be defined as generating multiple output nodes, having multiple
  # task calls or consolidating nodes.
  graph.determineNumberOfTaskExecutions(superpipeline)

  # Print the workflow to screen.
  write.workflow(superpipeline, workflow)

  # Having constructed all of the output file names (which may then be linked to other tasks as outputs), rerun the
  # check of the values to ensure that the data types and the ssociated extensions are valid. This will provide a
  # check of whether tools can be linked as described in the configuration file. In the previous check, not all of the
  # filenames were present (but the check ensured that the values provided on the command line were valid). If a task
  # outputs a file with and extension 'ext1' and the file is then passed to a file that requires files with the
  # extension 'ext2', the pipeline is invalid. The output filename has been constructed as file.ext1 and so the following
  # routine will flag the file as invalid as input to the next task.
  dc.checkValues(graph, superpipeline)

  # If the user has requested that a parameter set is to be exported, export the parameter set and terminate.
  if isExportSet: parSet.export(superpipeline, args, isExportSet[0], command.pipelineArguments)

  # Check that all files exist. At this point, all filenames have been constructed, so anything that is required, but
  # is not set will have no opportunity to be set, so gkno should terminate.
  #FIXME ENSURE THAT AL FILES ARE CHECKED - THE CAN BE CONSTRUCTED CHECK SHOULD BE REMOVED.
  dc.checkRequiredArguments(graph, superpipeline, args, isFullCheck = True)

  # Having reached this point, all of the required values have been checked, are present and have the correct data
  # type. In the construction of the graph, a number of non-required nodes could have been created and, since they
  # are not required, they could be unpopoulated. March through the graph and purge any nodes that have no values.
  dc.purgeEmptyNodes(graph)

  # Check if any tasks have been listed as outputting to a stream. If so, check that the task can output to a
  # stream and the task it feeds into can accept a stream. If everything is ok, update the graph to reflect
  # the streaming nodes.
  graph.checkStreams(superpipeline)

  # For all files marked as intermediate, determine the latest task in the pipeline that uses them. Ensure that
  # the data structures inside 'struct' only associate the files to delete with this latest task.
  graph.deleteFiles()
  
  # Set the absolute paths of all the files used in the pipeline.
  requiredInputFiles = dc.setFilePaths(graph, command.gknoArguments, gknoConfiguration)

  # Determine the execution structure of the pipeline.
  struct = es.executionStructure()
  struct.determineExecutionStructure(graph)

  # Generate a makefiles object and then build all the command lines for the tasks as well as creating a list of each
  # tasks dependencies and output.
  make = mk.makefiles()
  make.generateCommandLines(graph, superpipeline, struct)

  # Create the makefiles. This could either be a single makefile, or a set of multiple makefiles.
  make.generateMakefiles(struct, superpipeline.pipeline, gknoConfiguration.options, command.gknoArguments)

  # Open all the makefiles for writing.
  make.openFiles(graph, struct, os.getenv('GKNOCOMMITID'), __date__, __version__, superpipeline.pipeline, sourcePath, toolsPath, resourcesPath)

  # Add the command lines to the makefiles.
  make.addCommandLines(graph, struct)

  # Close all of the open makefiles.
  make.closeFiles()

  # Check that all of the dependent files exist (excluding dependencies that are created by tasks in the pipeline).
  success = files.checkFileExistence(requiredInputFiles, resourcesPath, toolsPath)

  # Execute the generated script unless the user has explicitly asked for it not to be run, or if multiple makefiles
  # have been generated.
  if gknoConfiguration.options['GKNO-DO-NOT-EXECUTE'].longFormArgument not in command.gknoArguments and not make.isMultipleMakefiles and success:
    makefileName = make.makefileNames[1][1][1]

    # Get the number of parallel jobs to be requested.
    jobsArgument = gknoConfiguration.options['GKNO-JOBS'].longFormArgument
    numberJobs   = command.gknoArguments[jobsArgument][0] if jobsArgument in command.gknoArguments else 1

    # Generate the execution command.
    execute = 'make -j ' + str(numberJobs) + ' --file ' + makefileName
    success = subprocess.call(execute.split())

if __name__ == "__main__":
  main()

#!/usr/bin/python

from __future__ import print_function

from copy import deepcopy
import os.path
import getpass
import subprocess
import sys

import networkx as nx

import gkno.adminUtils
from gkno.adminUtils import *

import gkno.commandLine
from gkno.commandLine import *

import configurationClass.configurationClass
from configurationClass.configurationClass import *

import gkno.gknoErrors
from gkno.gknoErrors import *

import gkno.exportInstance
from gkno.exportInstance import *

import gkno.files
from gkno.files import *

import gkno.gknoConfigurationFiles
from gkno.gknoConfigurationFiles import *

import gkno.helpClass
from gkno.helpClass import *

import gkno.makefileData
from gkno.makefileData import *

import gkno.tracking
from gkno.tracking import *

import gkno.writeToScreen
from gkno.writeToScreen import *

__author__ = "Alistair Ward"
__version__ = "0.100"
__date__ = "July 2013"

def main():

  # Initialise variables:
  phoneHomeID = ''

  # Define the errors class.
  errors = gknoErrors()

  # Define the source path of all the gkno machinery.
  sourcePath = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = adminUtils(sourcePath)

  # Define a configurationClass object.  This is part of the configurationClass library.  Also
  # define an object that handles finding configuration files for gkno (e.g. gkno specific
  # configuration file operations.
  config     = configurationMethods()
  gknoConfig = gknoConfigurationFiles()

  # Create a graph object.  This is a directed graph consisting of nodes representing the tasks
  # in the pipeline as well as data being fed into the nodes.  All relevant tool information
  # will be attached to the task nodes and information about the data is attached to the data
  # nodes.  The edges between the nodes define the command line argument for the data and tool.
  pipelineGraph = nx.DiGraph()

  # Define a command line options, get the first command line argument
  # and proceed as required.
  commands = commandLine()

  # Generate a class for handling instances.
  #TODO REMOVE
  #ins = instances()

  # Generate a class for storing details for use in the makefile.
  make = makefileData()

  # Define a help class.  This provides usage information for the user. Also define an object used
  # for writing to screen.
  gknoHelp = helpClass()
  write    = writeToScreen()

  # Get information on the mode being run. The pipelineName is the name of the pipeline
  # or the tool if being run in tool mode.
  admin.isRequested, admin.mode = commands.isAdminMode(admin.allModes)
  isPipeline                    = commands.setMode(admin.isRequested)
  runName                       = commands.getPipelineName(isPipeline)

  # Read in information from the gkno specific configuration file.
  gknoConfig.gknoConfigurationData = config.fileOperations.readConfigurationFile(sourcePath + '/config_files/gknoConfiguration.json')
  #TODO SORT OUT VALIDATION OF GKNO CONFIGURATION FILE>
  gknoConfig.validateConfigurationFile()
  gknoConfig.addGknoSpecificNodes(pipelineGraph, config, isPipeline)
  gknoConfig.eraseConfigurationData()

  # Check to see if gkno is being run in verbose mode or not.
  isVerbose = commands.checkVerbose(pipelineGraph, config, admin)

  # Each of the tools available to gkno should have a config file to describe its operation,
  #  purpose etc.  These are contained in config_files/tools.  Find all of the config files
  # and create a hash table with all available tools.
  # FIXME REMOVE TEMP
  gknoConfig.getJsonFiles(sourcePath + '/config_files/temp/')

  # Check if the pipeline/tool name is valid.
  if commands.mode != 'admin': gknoConfig.checkPipelineName(gknoHelp, isPipeline, runName)

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line. If help has been requested, print out the required
  # help.
  gknoHelp.checkForHelp(isPipeline, runName, admin, commands.mode)
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp: gknoHelp.printUsage(pipelineGraph, config, gknoConfig, admin, sourcePath, runName)

  # Print gkno title and version to the screen.
  write.printHeader(__version__, __date__)

  # No admin mode requested. Prepare to setup our tool or pipeline run.
  if not admin.isRequested:

    # Make sure we've actually been "built" before doing any real processing.
    # Skip this requirement if we're only going to be printing a help message later.
    if not gknoHelp.printHelp and not admin.isBuilt():
      errors.gknoNotBuilt()
      errors.terminate()

    # If a pipeline is being run, check that configuration files exist for the selected
    # pipeline.  This should be in directory config_files and have the name <$ARGV[1]>.json.
    # If the file exists, parse the json file.
    if isPipeline:
      phoneHomeID               = 'pipes/' + runName
      #FIXME REMOVE TEMP
      pipelineFile              = sourcePath + '/config_files/temp/pipes/' + runName + '.json'
      pipelineConfigurationData = config.fileOperations.readConfigurationFile(pipelineFile)

      # TODO VALIDATION MODULE IS INCOMPLETE.  CONFIGURATIONCLASS NEEDS TO BE
      # MODIFIED TO INCLUDE THIS.
      instances = config.pipeline.processConfigurationData(pipelineConfigurationData, pipelineFile)

    # If gkno is being run in tool mode, set the phoneHomeID.
    else: phoneHomeID = 'tools/' + runName

  # Define the list to hole the pipeline workflow.
  workflow = []

  # Process all of the tool configuration files that are used.
  if commands.mode == 'pipeline':

    # Find all of the tasks to be used in the pipeline.
    tasks = config.pipeline.getTasks()
    for task in tasks:
      tool = tasks[task]

      # FIXME TEMPORARY LOCATION OF CONFIG FILES.  REMOVE TEMP WHEN COMPLETE.
      toolFile              = sourcePath + '/config_files/temp/tools/' + tool + '.json'
      toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

      # TODO TOOL CONFIGURATION FILE VALIDATION HAS NOT YET BEEN HANDLED IN THE
      # CONFIGURATIONCLASS.
      # Ensure that the tool configuration file is well constructed and put all of the data
      # in data structures.  Each tool in each configuration file gets its own data structure.
      config.tools.processConfigurationData(tool, toolConfigurationData)

    # For each task in the pipeline, build an individual graph consisting of a task node, input
    # option nodes (all input and output file arguments are treated as option nodes) and finally
    # all input and output files are given file nodes.  Nodes are merged later to generate the
    # final pipeline.
    config.buildTaskGraph(pipelineGraph, tasks)

    # Add the pipeline arguments to the nodeIDs dictionary.
    config.nodeMethods.getPipelineArgumentNodes(pipelineGraph, config.pipeline, config.tools)
  
    # Now that every task in the pipeline has an individual graph built, use the information
    # in the pipeline configuration file to merge nodes and build the final pipeline graph.
    config.mergeNodes(pipelineGraph)
  
    # Generate the workflow using a topological sort of the pipeline graph.
    workflow = config.generateWorkflow(pipelineGraph)
  
    # Loop over all of the nodes and determine which require a value.  Also check to see if there
    # are missing edges.  For example, if a tool has an argument that is required, but is not included
    # in the pipeline configuration file (as a pipeline argument or via connections), the graph cannot
    # be completely defined.
    config.nodeMethods.setRequiredNodes(pipelineGraph, config.tools)

    # If help was requested on this specific pipeline, the information now exists to generate
    # the help information.
    if gknoHelp.specificPipelineHelp: gknoHelp.specificPipelineUsage(pipelineGraph, config, gknoConfig, runName, workflow, sourcePath)

  # If being run in the tool mode.
  elif commands.mode == 'tool':
    # FIXME TEMPORARY LOCATION OF CONFIG FILES.  REMOVE TEMP WHEN COMPLETE.
    toolFile              = sourcePath + '/config_files/temp/tools/' + runName + '.json'
    toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

    # TODO TOOL CONFIGURATION FILE VALIDATION HAS NOT YET BEEN HANDLED IN THE
    # CONFIGURATIONCLASS.
    # Ensure that the tool configuration file is well constructed and put all of the data
    # in data structures.  Each tool in each configuration file gets its own data structure.
    instances = config.tools.processConfigurationData(runName, toolConfigurationData)

    # Define the tasks structure. Since a single tool is being run, this is simply the name
    # of the tool. Set the tasks structure in the pipeline configuration object as well.
    tasks                 = {}
    tasks[runName]        = runName
    config.pipeline.tasks = tasks
    workflow.append(runName)
    config.buildTaskGraph(pipelineGraph, tasks)

  # Parse the command line and put all of the arguments into a list.
  if isVerbose: write.writeReadingCommandLineArguments()
  commands.getCommandLineArguments(pipelineGraph, config, gknoConfig, runName, isPipeline, isVerbose)
  if isVerbose: write.writeDone()

  # If help was requested or there were problems (e.g. the tool name or pipeline
  # name did not exist), print out the required usage information.
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp:
    gknoHelp.printUsage(pipelineGraph, config, workflow, admin, __version__, __date__, sourcePath, runName)

  # Populate the tl.arguments structure with the arguments with defaults from the tool configuration files.
  # The x.arguments structures for each of the classes used in gkno has the same format (a dictionary whose
  # keys are the names of tools: each tool is itself a dictionary of command line arguments, the value being
  # a list of associated parameters/files etc).  The command line in the makefile is then constructed from 
  # the x.arguments structures in a strict hierarchy.  tl.arguments contains the defaults found in the
  # configuration file.  These are overwritten (if conflicts occur) by the values in ins.arguments (i.e.
  # arguments drawn from the specified instance). Next, the cl.arguments are the commands defined on the
  # command line by the user and then finally, mr.arguments pulls information from the given multiple runs
  # file if one exists.

  # If admin mode requested, then run it & terminate script.
  # No need to bother with running tools or pipes.
  if admin.isRequested:
    success = admin.run(sys.argv)
    if success: exit(0)
    else: errors.terminate()
  
  # Print information about the pipeline to screen.
  if isPipeline and isVerbose: write.writePipelineWorkflow(pipelineGraph, config, workflow, gknoHelp)

  # Check if an instance was requested by the user.  If so, get the data and add the values to the data nodes.
  if isVerbose: write.writeCheckingInstanceInformation()
  instanceName = commands.getInstanceName()
  if isPipeline:
    #TODO REMOVE temp
    path               = sourcePath + '/config_files/temp/pipes/'
    availableInstances = gknoConfig.jsonFiles['pipeline instances']
  else:
    #TODO REMOVE temp
    path               = sourcePath + '/config_files/temp/tools/'
    availableInstances = gknoConfig.jsonFiles['tool instances']
  #TODO CHECK IF HELPCLASS FUNCTIONS ALREADY GET WHAT IS NEEDED.
  instanceData = config.getInstanceData(path, runName, instanceName, instances, availableInstances)
  # TODO Validate instance data. Check that tool instances have the argument field.
  config.attachInstanceArgumentsToNodes(pipelineGraph, instanceData)
  if isVerbose: write.writeDone()

  # Attach the values of the pipeline arguments to the relevant nodes.
  #TODO USE attachToolArgumentsToNodes in attachPipelineArgumentsToNodes when dealing with tasks.
  if isVerbose: write.writeAssignPipelineArgumentsToNodes()
  if isPipeline: commands.attachPipelineArgumentsToNodes(pipelineGraph, config, gknoConfig)
  else: commands.attachToolArgumentsToNodes(pipelineGraph, config, gknoConfig)
  if isVerbose: write.writeDone()

  # Check if multiple runs or internal loops have been requested.
  hasMultipleRuns, hasInternalLoop = gknoConfig.hasLoop(pipelineGraph, config)
  if hasMultipleRuns or hasInternalLoop:
    if isVerbose: write.writeAssignLoopArguments(hasMultipleRuns)
    gknoConfig.addLoopValuesToGraph(pipelineGraph, config)
    if isVerbose: write.writeDone()
   
  # Check that all files have a path set.
  gknoConfig.setFilePaths(pipelineGraph, config)

  # Now that the command line argument has been parsed, all of the values supplied have been added to the
  # option nodes.  All of the file nodes can take their values from their corresponding option nodes.
  #for fileNodeID in config.nodeMethods.getNodes(pipelineGraph, 'file'):
  #  print(fileNodeID, config.nodeMethods.getGraphNodeAttribute(pipelineGraph, fileNodeID, 'values'))
  commands.mirrorFileNodeValues(pipelineGraph, config, workflow)
  #print('AFTER')
  #for fileNodeID in config.nodeMethods.getNodes(pipelineGraph, 'file'):
  #  print(fileNodeID, config.nodeMethods.getGraphNodeAttribute(pipelineGraph, fileNodeID, 'values'))
  #exit(0)

  # TODO DEAL WITH INSTANCE EXPORTS
  # If the --export-config has been set, then the user is attempting to create a
  # new configuration file based on the selected pipeline.  This can only be
  # selected for a pipeline and if multiple runs are NOT being performed.
  #if '--export-instance' in cl.uniqueArguments:
    #if mr.hasMultipleRuns:
    #  er.exportInstanceForMultipleRuns(verbose)
    #  er.terminate()

    # Define the json export object, initialise and then check that the given filename is unique.
    #make.arguments = deepcopy(make.coreArguments)
    #make.prepareForInternalLoop(iLoop.tasks, iLoop.arguments, iLoop.numberOfIterations)
    #ei = exportInstance()
    #if pl.isPipeline: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, pl.instances, verbose)
    #else: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, tl.instances[tl.tool], verbose)
    #ei.getData(gknoHelp, tl.argumentInformation, tl.shortForms, pl.isPipeline, pl.workflow, pl.taskToTool, pl.argumentInformation, pl.arguments, pl.toolsOutputtingToStream, pl.toolArgumentLinks, pl.linkage, make.arguments, verbose)
    #if pl.isPipeline: ei.writeNewConfigurationFile(sourcePath, 'pipes', ins.externalInstances, pl.instances, cl.linkedArguments)
    #else: ei.writeNewConfigurationFile(sourcePath, 'tools', ins.externalInstances, tl.instances[tl.tool], cl.linkedArguments)

    # After the configuration file has been exported, terminate the script.  No
    # Makefile is generated and nothing is executed.
    #exit(0)

  # If flags are linked in a pipeline configuration file, but none of them were set on the command line,
  # the nodes will have no values. This will cause problems when generating the makefiles. Search all
  # option nodes looking for flags and set any unset nodes to 'unset'.
  config.searchForUnsetFlags(pipelineGraph)

  # Construct all filenames.  Some output files from a single tool or a pipeline do not need to be
  # defined by the user.  If there is a required input or output file and it does not have its value set, 
  # determine how to construct the filename and populate the node with the value.
  gknoConfig.constructFilenames(pipelineGraph, config, workflow)

  # Prior to filling in missing filenames, check that all of the supplied data is consistent with
  # expectations.  This includes ensuring that the inputted data types are correct (for example, if
  # an argument expects an integer, check that the values are integers), filename extensions are valid
  # and that multiple values aren't given to arguments that are only allowed a single value.
  gknoConfig.checkData(pipelineGraph, config)

  # Find the maximum number of datasets for each task.
  config.getNumberOfDataSets(pipelineGraph, workflow)

  # If there are multiple runs, multiple make files are created, using only the values for individual
  # iterations.
  make.determineMakefileStructure(pipelineGraph, config, workflow, hasMultipleRuns)
  makeFilename = make.getFilename(runName)

  # Set the output path foe use in the makefile generation.
  make.getOutputPath(pipelineGraph, config)

  for phaseID in make.makefileNames:
    for iteration, makefileName in enumerate(make.makefileNames[phaseID]):

      # If multiple runs are being performed, the iteration needs to be sent to the various following
      # routines in order to pick the files necessary for the particular makefile. Otherwise, all
      # iterations of data should be used in the makefile (there is either only one iteration or
      # internal loops are required in which case, all of the iterations are used in the same file).
      # Set the 'key' to the iteration or 'all' depending on the run type.
      if hasMultipleRuns: key = iteration + 1
      else: key = 'all'

      # Open the makefile.
      makefileHandle = make.openMakefile(makefileName)

      # Write header information to all of the makefiles.
      make.writeHeaderInformation(sourcePath, runName, makefileName, makefileHandle, phaseID, key)

      # Write out the executable paths for all of the tools being used in the makefile.
      make.writeExecutablePaths(makefileHandle, make.tasksInPhase[phaseID], config.pipeline.tasks, config.tools)

      # Detemine which files are dependencies, outputs and intermediate files. Begin by marking all
      # intermediate file nodes. If a file node has both a predecessor and a successor, it is an
      # intermediate file. Mark the file node as such unless the pipeline configuration file specifically
      # states that the file should be kept.
      graphDependencies  = config.determineGraphDependencies(pipelineGraph, make.tasksInPhase[phaseID], key = key)
      graphOutputs       = config.determineGraphOutputs(pipelineGraph, make.tasksInPhase[phaseID], key = key)
      graphIntermediates = config.determineGraphIntermediateFiles(pipelineGraph, make.tasksInPhase[phaseID], key = key)

      # Write the intermediate files to the makefile.
      make.writeIntermediateFiles(makefileHandle, graphIntermediates)

      # Write the pipeline outputs to the makefile.
      make.writeOutputFiles(makefileHandle, graphOutputs)

      # Determine the task in which each intermediate file is last used. This will allow the files to
      # be deleted as early as possible in the pipeline.
      deleteList = config.setWhenToDeleteFiles(pipelineGraph, graphIntermediates, workflow)

      # Write out the information for running each task.
      make.writeTasks(pipelineGraph, config, makefileName, makefileHandle, make.tasksInPhase[phaseID], key)

      # Close the makefile in preparation for execution.
      make.closeMakefile(makefileHandle)

      # Check that all of the input files exist.
      gknoConfig.checkFilesExist(pipelineGraph, config, graphDependencies)

  # If there are files required for the makefiles to run and theu don't exist, write a warning to the
  # screen and ensure that the makefiles aren't executed.
  gknoConfig.writeMissingFiles(pipelineGraph, config)

  # Check that all of the executable files exist.
  # checkExecutables()

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DNL', 'values')[1][0] == 'unset':
    if isVerbose: write.writeTracking(phoneHomeID)
    phoneHome(sourcePath, phoneHomeID)
    if isVerbose: write.writeDone()
  write.writeBlankLine()

  # Execute the generated script unless the execute flag has been unset.
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-EXECUTE', 'values')[1][0]:
    for phaseID in make.makefileNames:
      for iteration, makefileName in enumerate(make.makefileNames[phaseID]):

        # Check if the '--number-jobs' option is set.  If so, request this number of jobs.
        numberOfJobs = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-JOBS', 'values')[1][0]
        execute      = 'make -j ' + str(numberOfJobs) + ' --file ' + makefileName
        if isVerbose: write.writeExecuting(execute)
        success = subprocess.call(execute.split())
        if isVerbose: write.writeComplete(success)
  exit(0)




  # FIXME REMOVE OLD METHODS
  # Now that all of the information has been gathered and stored, start a loop over the remainder of 
  # the gkno subroutines.  Each iteration (there is only a single iteration in the absence of the
  # multiple runs command), the arguments for that run are set up and the makefile generated and
  # executed (unless, no execution was requested).
  #while True:

    # Define the name of the Makefile.  If there are multiple runs, append an intefer
    # ID to the end of the name.  This will be incremented for each subsequent Makefile.
    #make.getFilename(mr.hasMultipleRuns, pl.pipelineName)
    #make.arguments = deepcopy(make.coreArguments)
    #if mr.hasMultipleRuns:
    #  mr.getArguments()
    #  make.getMultipleArguments(tl.argumentInformation, pl.workflow, pl.taskToTool, mr.arguments)

    #make.arguments = checkInputLists(tl.argumentInformation, pl.workflow, pl.taskToTool, make.arguments, verbose) # dataChecking.py
    #make.prepareForInternalLoop(iLoop.tasks, iLoop.arguments, iLoop.numberOfIterations)

    # Some of the variables use the value MAKEFILE_ID in their names.  This is often used in
    # the names of temporary files etc and is intended to ensure that if multiple scripts are
    # generated, these values are all different in each script.  If there are parameters in the
    # internal loop that use this value, then they need to be modified to include the iteration
    # number to ensure that the values are still unique.
    #if iLoop.usingInternalLoop: checkMakefileID(make.arguments, iLoop.tasks, iLoop.numberOfIterations)

    # Loop over each of the tools in turn and set all of the parameters.  Each
    # task in turn may depend on parameters/outputs of previous tasks and so
    # handling in each task in the order it appears in the pipeline is necessary.
    #for task in pl.workflow:
    #  tool = pl.taskToTool[task]

      # Check all of the options for each tool and determine if the values are
      # linked to any other tool.  If so, set the values as necessary.
    #  if pl.isPipeline:
    #    pl.toolLinkage(task, tool, tl.argumentInformation[tool], make.arguments, iLoop.usingInternalLoop, iLoop.tasks, iLoop.numberOfIterations, verbose)

        # If the tool is listed as only outputting to a stream, check if it appears within or
        # at the end of piped tasks.  If it appears at the end and an output file has been
        # specified (or instructtions on how to construct it have been included), set the output.
    #    if tool in tl.toolsDemandingOutputStream: checkStreamedOutput(task, tool, tl.argumentInformation, pl.taskToTool, pl.constructFilenames, pl.toolsOutputtingToStream, make.arguments, verbose)

        # Check all input and output files.  If there are instructions on how to construct
        # filenames, construct them.
    #    constructFilenames(task, tool, make.arguments, tl.argumentInformation, pl.constructFilenames, pl.toolArgumentLinks, pl.taskToTool, verbose)

      # Check that all required files and parameters have been set.
    #  checkParameters(gknoHelp, task, tool, tl.argumentInformation, make.arguments, pl.isPipeline, pl.workflow, pl.argumentInformation, pl.toolsOutputtingToStream, pl.toolArgumentLinks, pl.linkage, True, verbose)

      # For all files, check that a path has been given.  If a path is set, leave the file
      # as is.  If no path has been set, check if the file is an input or output
      # file and use the --input-path and --output-path values
      # respectively.
    #  setPaths(task, tool, tl.argumentInformation, tl.shortForms, pl.argumentInformation, pl.arguments, pl.toolArgumentLinks, make.arguments, verbose)

    # Determine each tools dependencies for building the makefile.
    #make.dependencies, make.outputs = determineDependencies(tl.argumentInformation, tl.generatedFiles, pl.workflow, pl.taskToTool, pl.toolsOutputtingToStream, make.arguments)
  
    # There may be files that are required by the tool to run (e.g. files to
    # appear in the dependency list) that are not listed in the input arguments.
    # Those listed with arguments have already been included in the dependency
    # string for each tool in checkParameters, now check for others.
    #
    # Similarly, each tool produces output files.  These are listed in the
    # Makefile in order to ensure that tools are only run if their outputs
    # don't already exist.
    #determineAdditionalFiles(tl.additionalFiles, pl.workflow, pl.taskToTool, pl.additionalFileDependencies, make.arguments, make.dependencies, make.outputs, verbose)
  
    # If there are any explicit dependencies included in the pipeline configuration file, 
    # include them.
    #if pl.isPipeline:
    #  if len(pl.additionalFileDependencies) != 0: includeAdditionalFileDependencies(pl.additionalFileDependencies, make.dependencies)

    # In the course of executing the pipeline, some of the intermediate files
    # generated along the way should be deleted.  The pipeline configuration
    # file segment 'delete files' identifies which files should be deleted and
    # when in the pipeline they can be removed.
    #make.deleteFiles = determineFilesToDelete(make.arguments, pl.deleteFiles, iLoop.tasks, iLoop.numberOfIterations, verbose)
  
    # The list of files to be produced by the script is all of the files created
    # by each individual task in the pipeline.  However, if some of the files
    # are deleted along the way, the final list of files should not include these
    # deleted files.
  
    # The pipeline allows for tools to be outputted to the stream rather than to
    # an output file.  This allows tools to be joined together by pipes rather
    # than forcing the generation of all intermediate files.  The tasks that
    # output to the stream are listed in the pipeline configuration file, so check
    # if there are any and if so, check that the tools allow outputting to the
    # stream.
    #make.hasPipes, make.addedInformation = determinePiping(make.arguments, tl.argumentInformation, tl.toolsDemandingInputStream, tl.toolsDemandingOutputStream, pl.workflow, pl.taskToTool, pl.toolsOutputtingToStream, verbose)
  
    # The basic order of the Makefile is to start with the final tool and write
    # out the rules to build the final output file.  If the prerequisites for this
    # task do not exist, then make will search for the rule to make the files.  The
    # Makefile proceeds in this manner all the way to the first task.  If any of the
    # tasks are piped together, then these need to be output in order, not reverse
    # order.
    #make.taskBlocks = determineToolWriteOrder(pl.workflow, pl.toolsOutputtingToStream, make.hasPipes)
  
    # Determine the outputs and dependencies for each block of tasks.
    #make.taskBlockOutputs, make.taskBlockDependencies = getTaskBlockOutputsAndDependencies(make.taskBlocks, make.outputs, make.dependencies, iLoop.tasks, iLoop.numberOfIterations)
    #determineFinalOutputs(make.deleteFiles, make.outputs)

    # Generate scripts to run the selected pipeline.
    #make.openMakefile(sourcePath, pl.isPipeline)
    #make.setIntermediateFiles(pl.workflow, pl.taskToTool)
    #make.writeAllOutputs()

    # Loop over all of the task blocks in the pipeline.
    #for tasks, outputs, dependencies in zip(reversed(make.taskBlocks), reversed(make.taskBlockOutputs), reversed(make.taskBlockDependencies)):

      # For this taskBlock, determine if the tasks are included in an internal loop.  If
      # so, loop over the internal loop parameter sets, generating a command for each of
      # them.
      #for counter in range(0, len(outputs)):
        #make.writeInitialInformation(pl.taskToTool, tasks, counter)
        #make.getExecutablePath(sourcePath, tl.paths, pl.taskToTool, tasks, counter)
        #make.writeOutputsToMakefile(outputs[counter])
        #make.writeDependenciesToMakefile(dependencies[counter])
        #make.checkStdout(tasks, pl.arguments['--task-stdout'], mr.hasMultipleRuns)
        #make.generateCommand(tl.argumentInformation, tl.argumentDelimiters, tl.precommands, tl.executables, tl.modifiers, tl.argumentOrder, pl.taskToTool, pl.linkage, pl.arguments['--timing'], tasks, verbose, counter)
        #make.addFileDeletion(tasks, counter)
        #make.handleAdditionalOutputs(outputs[counter], dependencies[counter])
      #print(file = make.makeFilehandle)
    #make.closeMakefile()

    # Having completed the makefile for one set of parameters, reset the tl.toolArguments
    # structure to the original values before running the pipeline again.
    #make.arguments        = make.coreArguments
    #make.addedInformation = {}

    # Terminate the loop when all the required Makefiles have been produced.
    #if make.id == mr.numberDataSets: break

  # Check that all of the executable files exist.
  #checkExecutables(sourcePath, tl.paths, tl.executables, pl.workflow, pl.taskToTool, verbose)

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  #if pl.arguments['--do-not-log-usage'] == 'unset':
  #  if verbose: writeTracking(phoneHomeID)
  #  phoneHome(sourcePath, phoneHomeID)
  #  if verbose: writeDone()
  #writeBlankLine()

  # Execute the generated script unless the execute flag has been unset.
  #success = 0
  #if pl.arguments['--execute']:
  #  for makefile in make.filenames:
  #    if verbose: writeExecuting(makefile)

      # Check if the '--number-jobs' option is set.  If so, request this number of jobs.
  #    if pl.arguments['--number-jobs'] != '': execute = 'make -j ' + str(pl.arguments['--number-jobs'])
  #    else: execute = 'make'
  #    execute += ' --file ' + makefile
  #    print('Executing command:', execute, '\n')
  #    success = subprocess.call(execute.split())
  #    if verbose: writeComplete(success)

  # If the makefile was succesfully run, finish gkno with the exit condition of 0.
  # If the makefile failed to run, finish with the exit condition 3.  A failure
  # prior to execution of the makefile uses the exit condition 2.
  if success == 0: exit(0)
  else: exit(3)

if __name__ == "__main__":
  main()

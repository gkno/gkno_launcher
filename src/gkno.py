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
__version__ = "0.116"
__date__ = "January 2014"

def main():

  # Initialise variables:
  phoneHomeID       = ''
  generateMakefiles = True
  hasIsolatedNode   = False

  # Define the errors class.
  errors = gknoErrors()

  # Define the source path of all the gkno machinery.
  sourcePath                     = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno.py')]
  configurationFilesPath         = sourcePath + '/config_files/'
  gknoConfigurationFilePath      = sourcePath + '/config_files/'
  pipelineConfigurationFilesPath = sourcePath + '/config_files/pipes/'
  toolConfigurationFilesPath     = sourcePath + '/config_files/tools/'
  toolsPath                      = sourcePath + '/tools/'

  # Get the latest commitID for gkno (the environment variable was set up in the shell script).
  gknoCommitID = os.getenv('GKNOCOMMITID')

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

  # Define a class for outputting graphics.
  draw = drawGraph()

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
  gknoConfig.gknoConfigurationData = config.fileOperations.readConfigurationFile(gknoConfigurationFilePath + '/gknoConfiguration.json')
  gknoConfig.validateConfigurationFile()
  gknoConfig.addGknoSpecificNodes(pipelineGraph, config, isPipeline)
  gknoConfig.eraseConfigurationData()

  # Check to see if gkno is being run in verbose mode or not.
  isVerbose = commands.checkVerbose(pipelineGraph, config, admin)

  # Each of the tools available to gkno should have a config file to describe its operation,
  # purpose etc.  These are contained in config_files/tools.  Find all of the config files
  # and create a hash table with all available tools.
  gknoConfig.getJsonFiles(configurationFilesPath)

  # Check if the pipeline/tool name is valid.
  if commands.mode != 'admin': gknoConfig.checkPipelineName(gknoHelp, isPipeline, runName)

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line. If help has been requested, print out the required
  # help.
  gknoHelp.checkForHelp(isPipeline, runName, admin, commands.mode)
  instanceName = commands.getInstanceName(pipelineGraph, config, isPipeline)
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp:
    gknoHelp.printUsage(pipelineGraph, config, gknoConfig, admin, toolConfigurationFilesPath, pipelineConfigurationFilesPath, runName, instanceName)

  # Print gkno title and version to the screen.
  write.printHeader(__version__, __date__, gknoCommitID)

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
      filename                  = pipelineConfigurationFilesPath + runName + '.json'
      pipelineConfigurationData = config.fileOperations.readConfigurationFile(filename)
      config.pipeline.processConfigurationData(pipelineConfigurationData, runName, gknoConfig.jsonFiles['tools'])
      config.instances.checkInstances(runName, pipelineConfigurationData['instances'], isPipeline, isExternal = False)
      config.instances.checkExternalInstances(config.fileOperations, filename, runName, gknoConfig.jsonFiles['tools'], isPipeline)
      del(pipelineConfigurationData)

    # If gkno is being run in tool mode, set the phoneHomeID.
    else: phoneHomeID = 'tools/' + runName

  # Process all of the tool configuration files that are used.
  if commands.mode == 'pipeline':

    # Find all of the tasks to be used in the pipeline.
    for task in config.pipeline.taskAttributes:
      tool                  = config.pipeline.taskAttributes[task].tool
      toolFile              = toolConfigurationFilesPath + tool + '.json'
      toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

      # Ensure that the tool configuration file is well constructed and put all of the data
      # in data structures.  Each tool in each configuration file gets its own data structure.
      config.tools.processConfigurationData(tool, toolConfigurationData)
      del(toolConfigurationData)

    # Check that any argument in a pipeline configuration file node taht defines a filename stub
    # is linked to other stub arguments, or that the desired extension is included in the node.
    config.pipeline.checkCommonNodes(config.tools)

    # For each task in the pipeline, build an individual graph consisting of a task node, input
    # option nodes (all input and output file arguments are treated as option nodes) and finally
    # all input and output files are given file nodes.  Nodes are merged later to generate the
    # final pipeline.
    config.buildTaskGraph(pipelineGraph, config.pipeline.taskAttributes.keys())

    # Attach additional information from the pipeline configuration file to the nodes.
    config.assignPipelineAttributes(pipelineGraph, config.pipeline.taskAttributes.keys())

    # Add the pipeline arguments to the nodeIDs dictionary.
    config.nodeMethods.getPipelineArgumentNodes(pipelineGraph, config)
  
    # Now that every task in the pipeline has an individual graph built, use the information
    # in the pipeline configuration file to merge nodes and build the final pipeline graph.
    config.mergeNodes(pipelineGraph)
  
    # Generate the workflow using a topological sort of the pipeline graph.
    config.pipeline.workflow = config.generateWorkflow(pipelineGraph)

    # Check to see if any tasks in the pipeline are isolated, i.e. they share no files with any other task
    # in the pipeline.
    hasIsolatedNode, isolatedNodes = config.checkForIsolatedNodes(pipelineGraph)

    # Loop over all of the nodes and determine which require a value.  Also check to see if there
    # are missing edges.  For example, if a tool has an argument that is required, but is not included
    # in the pipeline configuration file (as a pipeline argument or via connections), the graph cannot
    # be completely defined.
    config.nodeMethods.setRequiredNodes(pipelineGraph, config.tools)

    # If help was requested on this specific pipeline, the information now exists to generate
    # the help information.
    if gknoHelp.specificPipelineHelp:
      gknoHelp.specificPipelineUsage(pipelineGraph, config, gknoConfig, runName, toolConfigurationFilesPath, instanceName)

  # If being run in the tool mode.
  elif commands.mode == 'tool':
    toolFile              = toolConfigurationFilesPath + runName + '.json'
    toolConfigurationData = config.fileOperations.readConfigurationFile(toolFile)

    # Ensure that the tool configuration file is well constructed and put all of the data
    # in data structures.  Each tool in each configuration file gets its own data structure.
    config.tools.processConfigurationData(runName, toolConfigurationData)
    config.instances.checkInstances(runName, toolConfigurationData['instances'], isPipeline, isExternal = False)
    config.instances.checkExternalInstances(config.fileOperations, toolFile, runName, gknoConfig.jsonFiles['tools'], isPipeline)
    del(toolConfigurationData)

    # Define the tasks structure. Since a single tool is being run, this is simply the name
    # of the tool. Set the tasks structure in the pipeline configuration object as well.
    config.pipeline.definePipelineAttributesForTool(runName)
    config.buildTaskGraph(pipelineGraph, config.pipeline.taskAttributes.keys())

  # Parse the command line and put all of the arguments into a list.
  write.writeReadingCommandLineArguments()
  commands.getCommandLineArguments(pipelineGraph, config, gknoConfig, runName, isPipeline)
  write.writeDone()

  # If help was requested or there were problems (e.g. the tool name or pipeline
  # name did not exist), print out the required usage information.
  if gknoHelp.printHelp and not gknoHelp.specificPipelineHelp:
    gknoHelp.printUsage(pipelineGraph, config, gknoConfig, admin, sourcePath, runName)

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
  if isPipeline: write.writePipelineWorkflow(pipelineGraph, config, gknoHelp)

  # Check if an instance was requested by the user.  If so, get the data and add the values to the data nodes.
  write.writeCheckingInstanceInformation()

  # Check to see if the requested instance is available.
  config.instances.checkRequestedInstance(configurationFilesPath, runName, instanceName, gknoConfig.jsonFiles, isPipeline)

  # Check to see if any of the instance arguments are gkno specific arguments.
  gknoConfig.attachInstanceArgumentsToNodes(config, pipelineGraph, runName, instanceName)

  # Now handle the rest of the instance arguments.
  if isPipeline: config.attachPipelineInstanceArgumentsToNodes(pipelineGraph, runName, instanceName)
  else: config.attachToolInstanceArgumentsToNodes(pipelineGraph, runName, instanceName)
  write.writeDone()

  # Attach the values of the pipeline arguments to the relevant nodes.
  write.writeAssignPipelineArgumentsToNodes()
  if isPipeline: commands.attachPipelineArgumentsToNodes(pipelineGraph, config, gknoConfig)
  else: commands.attachToolArgumentsToNodes(pipelineGraph, config, gknoConfig)
  write.writeDone()

  # Check if multiple runs or internal loops have been requested.
  hasMultipleRuns, hasInternalLoop = gknoConfig.hasLoop(pipelineGraph, config)
  if hasMultipleRuns or hasInternalLoop:
    write.writeAssignLoopArguments(hasMultipleRuns)
    gknoConfig.addLoopValuesToGraph(pipelineGraph, config)
    write.writeDone()

  # Now that the command line argument has been parsed, all of the values supplied have been added to the
  # option nodes.  All of the file nodes can take their values from their corresponding option nodes.
  commands.mirrorFileNodeValues(pipelineGraph, config)

  # Not all of the following operation need to be performed if an instance is being exported. Since exporting
  # an instance just requires that the supplied values are valid, but not that all values are supplied (since
  # gkno will not be executed).
  isExportInstance = True if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-EXPORT-INSTANCE', 'values') else False
  if not isExportInstance:

    # Construct all filenames.  Some output files from a single tool or a pipeline do not need to be
    # defined by the user.  If there is a required input or output file and it does not have its value set, 
    # determine how to construct the filename and populate the node with the value.
    gknoConfig.constructFilenames(pipelineGraph, config, isPipeline)

    # Check that all required files and values have been set. All files and parameters that are listed as
    # required by the infividual tools should already have been checked, but if the pipeline has some
    # additional requirements, these may not yet have been checked.
    config.checkRequiredFiles(pipelineGraph)

    # If flags are linked in a pipeline configuration file, but none of them were set on the command line,
    # the nodes will have no values. This will cause problems when generating the makefiles. Search all
    # option nodes looking for flags and set any unset nodes to 'unset'.
    config.searchForUnsetFlags(pipelineGraph)

  # Check that all files have a path set.
  gknoConfig.setFilePaths(pipelineGraph, config)

  # Prior to filling in missing filenames, check that all of the supplied data is consistent with
  # expectations.  This includes ensuring that the inputted data types are correct (for example, if
  # an argument expects an integer, check that the values are integers), filename extensions are valid
  # and that multiple values aren't given to arguments that are only allowed a single value.
  gknoConfig.checkData(pipelineGraph, config, not isExportInstance)

  # Check that all of the supplied values for the gkno specific nodes are valid.
  gknoConfig.checkNodeValues(pipelineGraph, config)

  # If the --export-config has been set, then the user is attempting to create a
  # new configuration file based on the selected tool/pipeline.  This can only be
  # if multiple runs are NOT being performed.
  if isExportInstance:
    if hasMultipleRuns: config.errors.exportInstanceForMultipleRuns()
    if isPipeline: config.exportInstance(pipelineGraph, pipelineConfigurationFilesPath, runName, isPipeline)
    else: config.exportInstance(pipelineGraph, toolConfigurationFilesPath, runName, isPipeline) 
    config.nodeMethods.addValuesToGraphNode(pipelineGraph, 'GKNO-EXECUTE', [False], write = 'replace')
    generateMakefiles = False

  # Find the maximum number of datasets for each task.
  config.getNumberOfDataSets(pipelineGraph)

  # Identify file nodes that are streaming.
  config.identifyStreamingNodes(pipelineGraph)

  if generateMakefiles:
    # If there are multiple runs, multiple make files are created, using only the values for individual
    # iterations.
    make.determineMakefileStructure(pipelineGraph, config, hasMultipleRuns)
    makeFilename = make.getFilename(runName)
  
    # Set the output path for use in the makefile generation.
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
        make.writeHeaderInformation(sourcePath, runName, makefileName, makefileHandle, phaseID, key, __version__, __date__, gknoCommitID)
  
        # Write out the executable paths for all of the tools being used in the makefile.
        make.writeExecutablePaths(pipelineGraph, config, makefileHandle, make.tasksInPhase[phaseID])
  
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
        deleteList = config.setWhenToDeleteFiles(pipelineGraph, graphIntermediates)
  
        # Search through the tasks in the workflow and check for tasks outputting to a stream. Generate a
        # list of tasks for generating the makefiles. Each entry in the list should be a list of all tasks
        # that are piped together (in a pipeline with no streaming, this list will just be the workflow).
        taskList = make.determineStreamingTaskList(pipelineGraph, config, make.tasksInPhase[phaseID])
  
        # Write out the information for running each task.
        make.writeTasks(pipelineGraph, config, makefileName, makefileHandle, taskList, deleteList, key)
  
        # Close the makefile in preparation for execution.
        make.closeMakefile(makefileHandle)
  
        # Check that all of the input files exist.
        gknoConfig.checkFilesExist(pipelineGraph, config, graphDependencies, sourcePath)
  
    # If there are files required for the makefiles to run and theu don't exist, write a warning to the
    # screen and ensure that the makefiles aren't executed.
    gknoConfig.writeMissingFiles(pipelineGraph, config)
  
    # Check that all of the executable files exist.
    gknoConfig.checkExecutables(config, pipelineGraph, toolsPath)

  # If the pipeline contains any isolated nodes, print a warning to screen.
  if hasIsolatedNode:
    errors.isolatedNodes(pipelineGraph, config, isolatedNodes)

    # Force the uset to acknowledge that the warning was read,
    doNotExecute   = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DO-NOT-EXECUTE', 'values')[1][0]
    noHardWarnings = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-NO-HARD-WARNINGS', 'values')[1][0]
    if doNotExecute == 'unset' and noHardWarnings == 'unset': raw_input('Press Enter to continue...')

  # Check if a plotting the pipeline was requested. If so, check that a name for the output file was given and
  # draw the pipeline.
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DRAW-PIPELINE', 'values'): gknoConfig.drawPipeline(pipelineGraph, config, draw)

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DNL', 'values')[1][0] == 'unset':
    write.writeTracking(phoneHomeID)
    phoneHome(sourcePath, phoneHomeID)
    write.writeDone()
  write.writeBlankLine()

  # Execute the generated script unless the execute flag has been unset.
  success = 0
  if config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-DO-NOT-EXECUTE', 'values')[1][0] == 'unset':
    for phaseID in make.makefileNames:
      for iteration, makefileName in enumerate(make.makefileNames[phaseID]):

        # Check if the '--number-jobs' option is set.  If so, request this number of jobs.
        numberOfJobs = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, 'GKNO-JOBS', 'values')[1][0]
        execute      = 'make -j ' + str(numberOfJobs) + ' --file ' + makefileName
        write.writeExecuting(execute)
        success = subprocess.call(execute.split())
        write.writeComplete(success)

  # If the makefile was succesfully run, finish gkno with the exit condition of 0.
  # If the makefile failed to run, finish with the exit condition 3.  A failure
  # prior to execution of the makefile uses the exit condition 2.
  if success == 0: exit(0)
  else: exit(3)

if __name__ == "__main__":
  main()

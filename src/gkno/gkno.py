#!/usr/bin/python

from __future__ import print_function

from copy import deepcopy
import os.path
import getpass
import subprocess
import sys

# Add the configuration class directory to the search path for modules.
sys.path.insert(0,'src/configurationClass/src')

import networkx as nx

import adminUtils
from adminUtils import *

import commandLine
from commandLine import *

import gknoErrors
from gknoErrors import *

import exportInstance
from exportInstance import *

import files
from files import *

import gknoConfigurationFiles
from gknoConfigurationFiles import *

import helpClass
from helpClass import *

import instances
from instances import *

import internalLoop
from internalLoop import *

import makefileData
from makefileData import *

import multipleRuns
from multipleRuns import *

import pipelineAttributes
from pipelineAttributes import *

import toolAttributes
from toolAttributes import *

import tracking
from tracking import *

import writeToScreen
from writeToScreen import *

__author__ = "Alistair Ward"
__version__ = "0.100"
__date__ = "July 2013"

def main():

  # Define the errors class.
  error = gknoErrors()

  # Define the source path of all the gkno machinery.
  sourcePath = os.path.abspath(sys.argv[0])[0:os.path.abspath(sys.argv[0]).rfind('/src/gkno/gkno.py')]

  # Define an admin utilities object. This handles all of the build/update steps
  # along with 'resource' management.
  admin = adminUtils(sourcePath)

  # Define a pipeline configuration object.  This is part of the configurationClass library.  Also
  # define an object that handles finding configuration files for gkno (e.g. gkno specific
  # configuration file operations.
  pipe = pipelineConfiguration()
  conf = gknoConfigurationFiles()

  # Create a graph object.  This is a directed graph consisting of nodes representing the tasks
  # in the pipeline as well as data being fed into the nodes.  All relevant tool information
  # will be attached to the task nodes and information about the data is attached to the data
  # nodes.  The edges between the nodes define the command line argument for the data and tool.
  pipelineGraph = nx.DiGraph()

  # Each task in the pipeline (if a single tool is being run, the graph consists of a single
  # task node, but is still represented by a graph) is represented by a node.  The task is
  # then associated with a tool.  Each unique tool in the pipeline has a configuration file
  # associated with it and the information for each tool is store in the toolObjects structure.
  # Each tool configuration will have its own data structure in this object.
  toolData = toolConfiguration()

  # FIXME REMOVE. REPLACED WITH TOOLOBJECTS
  # Define a tools object.  This stores all information specific to individual
  # tools.
  #tl = tools()

  # Define a command line options, get the first command line argument
  # and proceed as required.
  commands = commandLine()

  # FIXME REMOVE. REPLACED WITH PIPE
  # Define a pipeline object.  Even if a single tool is all that is required,
  # some of the routines in the pipelines.py are still used.  A single tool
  # is essentially treated as a pipeline with a single element.
  #pl = pipeline()

  # FIXME. REMOVE AND REMOVE FILES.PY.  HANDLED IN THE CONFIGURATIONCLASS
  # Generate a class for handling files.
  #io = files()

  # Generate a class for handling instances.
  ins = instances()

  # Generate a class for handling internal loops.
  iLoop = internalLoop()

  # Generate a class for storing details for use in the makefile.
  make = makefileData()

  # Define a help class.  This provides usage information for the user.
  gknoHelp = helpClass()

  # Check if help has been requested.  If so, print out usage information for
  # the tool or pipeline as requested.
  isModeSet    = commands.isModeSet()
  isPipeline   = False
  isTool       = False
  pipelineName = ''
  toolName     = ''
  if not isModeSet:
    gknoHelp.generalHelp = True
    gknoHelp.printHelp   = True
    isPipeline           = False
  else:

    # Check if gkno is running in pipeline mode and if so, that a pipeline name is given.
    # Also check if the pipeline to be run is the run-test pipeline from the 'Getting started
    # with gkno' tutorial.  This doesn't require the pipeline to be explicitly defined with
    # the pipe identifier on the command line.
    isPipeline, hasName, pipelineName = commands.isPipelineMode()
    pipe.pipelineName                 = pipelineName
    if isPipeline:
      if not hasName:
        gknoHelp.pipelineHelp = True
        gknoHelp.printHelp    = True

    # Check if an admin function was requested.
    else:
      admin.isRequested = commands.isAdminMode(admin.allModes)
      if admin.isRequested: admin.mode = sys.argv[1]

      # If this isn't a pipeline or a request for admin functions, then it must be a tool.
      else:
        isTool   = True
        toolName = sys.argv[1]

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  verbose = commands.checkForHelp(gknoHelp, isPipeline, pipelineName, admin)

  # Print gkno title and version to the screen.
  gknoHelp.printHeader(__version__, __date__)

  # No admin mode requested. Prepare to setup our tool or pipeline run.
  if not admin.isRequested:

    # Make sure we've actually been "built" before doing any real processing.
    # Skip this requirement if we're only going to be printing a help message later.
    if not gknoHelp.printHelp and not admin.isBuilt():
      error.gknoNotBuilt()
      error.terminate()

    # Each of the tools available to gkno should have a config file to
    # describe its operation, purpose etc.  These are contained in
    # config_files/tools.  Find all of the config files and create a hash
    # table with all available tools.
    toolFiles, pipelineFiles = conf.getJsonFiles(sourcePath + '/config_files/')

    # FIXME THESE NEED TO BE ADDED TO THE GRAPH AS NODES.
    # Add some necessary commands to the pipeline arguments structure.
    #pl.addPipelineSpecificOptions()

    # FIXME DEAL WITH CONFIG FILES WITH CONFIGURATIONCLASS.  REMOVE THIS.
    # Check that the config files are valid.
    if gknoHelp.printHelp: verbose = False
    #if verbose: beginToolConfigurationFileCheck()
    #for toolFile in io.jsonToolFiles:
    #  if verbose: writeToolConfigurationFile(toolFile)
    #  toolData = io.getJsonData(sourcePath + '/config_files/tools/' + toolFile, True)
    #  tl.checkToolConfigurationFile(toolData, toolFile, verbose)
    #  tl.setupShortFormArguments()
    #  pl.taskToTool[tl.tool] = tl.tool
    #  toolData = '' # Clear the data structure as it is no longer necessary
    #  if verbose: writeDone()
    #if verbose: writeBlankLine()

    # If a pipeline is being run, check that configuration files
    # exist for the selected pipeline.  This should be in directory
    # config_files and have the name <$ARGV[1]>.json.  If the file
    # exists, parse the json file.
    phoneHomeID = ''
    if isPipeline:
      phoneHomeID    = 'pipes/' + pipelineName
      pipelineFile   = sourcePath + '/config_files/pipes/' + pipelineName + '.json'
      pipelineExists, jsonError, jsonErrorText = pipe.readConfigurationFile(pipelineFile)

      # Terminate if the pipeline file does not exits.
      if not pipelineExists:
        error.missingFile(True, pipelineFile)
        error.terminate()

      # Terminate if there are errors in the json file.
      if jsonError:
        error.jsonOpenError(True, jsonErrorText, pipelineFile)
        error.terminate()
  
      #FIXME REMOVE LINE
      #success      = pl.checkPipelineExists(gknoHelp, io.jsonPipelineFiles)

      # TODO VALIDATION MODULE IS INCOMPLETE.  CONFIGURATIONCLASS NEEDS TO BE
      # MODIFIED TO INCLUDE THIS.
      success = pipe.validateConfigurationData(pipelineFile)
       
      #iLoop.tasks     = pl.checkConfigurationFile(gknoHelp, pipelineData, io.jsonPipelineFiles, tl.availableTools, tl.argumentInformation, verbose)
      #pipelineData    = '' # Clear the data structure as it is no longer necessary.
      #pl.setArgumentLinks()
      #if verbose: writeDone()

    # If gkno is being run in tool mode, the pl object still exists and is used.
    # Set the pl.information structure up to reflect a pipeline containing a
    # single tool.
    else:
      pipelineName = toolName
      #phoneHomeID  = pl.setupIndividualTool(toolName, not gknoHelp.printHelp)

    # TODO DEAL WITH INDIVIDUAL TOOL.
    # If a single tool is being run, check that it is a valid tool.
    #if not pl.isPipeline: tl.checkTool(gknoHelp)

  # Process all of the tool configuration files.
  for tool in toolFiles:
    toolFile                                   = sourcePath + '/config_files/tools/' + tool
    toolExists, jsonError, jsonErrorText, data = toolData.readConfigurationFile(toolFile)

    # TODO TOOL CONFIGURATION FILE VALIDATION HAS NOT YET BEEN HANDLED IN THE
    # CONFIGURATIONCLASS.
    # Ensure that the tool configuration file is well constructed and put all of the data
    # in data structures.  Each tool in each configuration file gets its own data structure.
    toolData.processConfigurationFile(data, toolFile)

    # Terminate if the file cannot be found.
    if not toolExists:
      error.missingFile(True, toolFile)
      error.terminate()

    # Terminate if there is something wrong with the configuration file.
    if jsonError:
      error.jsonOpenError(True, jsonErrorText, toolFile)
      error.terminate()

  # TODO Deal with individual tool operation.
  if isTool:
    print('Not yet handled individual tool')
    exit(0)

  if isPipeline or isTool:

    # Construct the pipeline graph using the information contained in the pipeline configuration
    # file.
    pipe.addNodesAndEdges(pipelineGraph, toolData)
    pipe.eraseConfigurationData()

    # Populate the nodes with necessary information.  Return a list of all of the tools used by the
    # pipelines.
    requiredTools = pipe.getRequiredTools(pipelineGraph)

    # Generate the workflow using a topological sort of the pipeline graph.
    workflow = pipe.generateWorkflow(pipelineGraph)

    # Loop over all of the nodes and determine which require a value.  Also check to see if there
    # are missing edges.  For example, if a tool has an argument that is required, but is not included
    # in the pipeline configuration file (as a pipeline argument or via connections), the graph cannot
    # be completely defined.
    pipe.setRequiredNodes(pipelineGraph, toolData)
    pipe.setTaskNodes(pipelineGraph, toolData)
    missingEdges = pipe.checkRequiredTaskConnections(pipelineGraph, toolData)
    if len(missingEdges) != 0:
      print('missing required edges for task:', missingEdges)
      #error.terminate()
    exit(0)

  # For help messages the helpClass needs a list of all available tools and all available pipelines.  These
  # lists are generated here.
  gknoHelp.setAvailableToolsAndPipelines(toolData.attributes.keys(), pipelineFiles)

  # TODO DEAL WITH INSTANCES
  # Check for an additional instance file associated with this tool/pipeline and add the information
  # to the relevant data structure.
  #if pl.isPipeline:
  #  instanceData = ins.checkInstanceFile(sourcePath, 'pipes', pl.pipelineName, io.jsonPipelineInstances)
  #  if len(instanceData) != 0: ins.checkInstanceInformation(instanceData, pl.instances, pl.pipelineName + '_instances.json')
  #else:
  #  instanceData = ins.checkInstanceFile(sourcePath, 'tools', tl.tool, io.jsonToolInstances)
  #  if len(instanceData) != 0: ins.checkInstanceInformation(instanceData, tl.instances[tl.tool], tl.tool + '_instances.json')

  # Parse the command line and put all of the arguments into a list.
  if verbose: gettingCommandLineArguments()
  commands.getCommandLineArguments(pipelineGraph, toolName, isPipeline)
  if verbose:
    writeDone()
    writeBlankLine()

  # If help was requested or there were problems (e.g. the tool name or pipeline
  # name did not exist), print out the required usage information.
  #if gknoHelp.printHelp: gknoHelp.printUsage(io, tl, pl, admin, __version__, __date__, sourcePath)
  if gknoHelp.printHelp: gknoHelp.printUsage(pipelineGraph, pipe, workflow, toolData, admin, __version__, __date__, sourcePath)

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
    else: er.terminate()
  
  # Print information about the pipeline to screen.
  if isPipeline and verbose: writePipelineWorkflow(pipelineGraph, workflow, gknoHelp)

  # Set up an array to contain the names of the Makefiles created.
  make.initialiseNames()

  # Parse the command line and populate the cl.arguments structure with all of the arguments set
  # by the user.
  if verbose: writeAssignPipelineArgumentsToTasks()
  #cl.assignArgumentsToTasks(tl.tool, tl.shortForms, pl.isPipeline, pl.arguments, pl.argumentInformation, pl.shortForms, pl.workflow, verbose)
  commands.assignArgumentsToTasks()#tl.tool, tl.shortForms, pl.isPipeline, pl.arguments, pl.argumentInformation, pl.shortForms, pl.workflow, verbose)
  exit(0)
  if verbose:
    writeDone()
    writeParseCommandLineArguments()
  cl.parseCommandLine(tl.tool, tl.argumentInformation, tl.shortForms, pl.isPipeline, pl.workflow, pl.argumentInformation, pl.shortForms, pl.taskToTool, verbose)
  if verbose: writeDone()

  # Check if an instance was selected.  If so, read the specific instance parameters.
  if verbose: writeCheckingInstanceInformation()
  ins.getInstanceName(cl.uniqueArguments, cl.argumentList, verbose)

  if pl.isPipeline:
    ins.getInstanceArguments(sourcePath + '/config_files/pipes/', pl.pipelineName, pl.instances, verbose)
    ins.convertPipeArgumentsToToolArguments(pl.argumentInformation, pl.shortForms, pl.arguments, verbose)
  else:
    ins.getInstanceArguments(sourcePath + '/config_files/tools/', tl.tool, tl.instances[tl.tool], verbose)
    ins.setToolArguments(tl.tool, verbose)
  ins.checkInstanceArguments(pl.taskToTool, tl.argumentInformation, tl.shortForms, verbose)
  if verbose: writeDone()

  # If this is a pipeline and internal loops are permitted, check if the user has requested use of
  # the internal loop.  If so, check that the supplied file exists and read in the information.  First,
  # check if an internal loop was specified on the command line, but the pipeline does not have any
  # internal loop information in the configuration file.
  if pl.arguments['--internal-loop'] != ''  and not pl.hasInternalLoop:
    er.internalLoopRequestedButUndefined(verbose, pl.pipelineName, pl.arguments['--internal-loop'])
    er.terminate()
  if pl.isPipeline and pl.hasInternalLoop:
    iLoop.checkLoopFile(sourcePath + '/resources', pl.arguments)
    if iLoop.usingInternalLoop: iLoop.checkInformation(pl.argumentInformation, pl.shortForms, verbose)
    else: iLoop.numberOfIterations = 1
  else: iLoop.numberOfIterations = 1

  # If the pipeline is going to be run multiple times for a different set of input
  # files, the '--multiple-runs (-mr)' argument can be set.  If this is set, the
  # whole pipeline needs to be looped over with each iteration built from the new
  # input files.  Check to see if this value is set.  If the --multiple-runs argument
  # was set in the instance, this will be stored in the pl.arguments, so also check
  # this value.
  mr = multipleRuns()
  mr.checkForMultipleRuns(cl.uniqueArguments, cl.argumentList, pl.arguments['--multiple-runs'], sourcePath + '/resources', verbose)
  if verbose: writeCheckingMultipleRunsInformation()
  if mr.hasMultipleRuns:
    mr.getInformation(verbose)
    if pl.isPipeline: mr.checkInformation(tl.tool, pl.argumentInformation, pl.shortForms, verbose)
    else: mr.checkInformation(tl.tool, tl.argumentInformation[tl.tool], tl.shortForms[tl.tool], verbose)
  if verbose: writeDone()

  # Generate the make.arguments structure.  This is built from the arguments collected from the
  # configuration files, the command line, instances and the multiple runs file where applicable.
  # The order of precedence is:
  #
  # 1. Configuration file defaults,
  # 2. Instance information,
  # 3. Command line information,
  # 4. Multiple runs file (these are added later).
  #
  # So, parameters appearing in (4) overwrite those in (3) which overwrote those from (2) etc where
  # conflicts occur.
  if pl.isPipeline: tl.getDefaults(pl.workflow, pl.taskToTool, tl.argumentInformation, tl.shortForms, verbose)
  else: tl.getDefaults(pl.workflow, pl.taskToTool, tl.argumentInformation, tl.shortForms, verbose)
  make.getCoreArguments(tl.argumentInformation, pl.workflow, pl.taskToTool, tl.arguments, ins.arguments, cl.arguments)

  # Some of the tools included in gkno can have multiple input files set on the
  # command line.  When many files are to be included, it can be more convenient
  # to allow a file including a list of files to be included.  Check if any of the
  # tools have input lists specified and if so, add these to the actual command line
  # argument list that should be used.
  make.coreArguments = checkInputLists(tl.argumentInformation, pl.workflow, pl.taskToTool, make.coreArguments, verbose) # dataChecking.py

  # Ensure that all of the required arguments are present (even if their value is blank) in the coreArguments.
  # These should be filled in later using linkage information, otherwise gkno will terminate.
  make.setAllRequiredArguments(pl.workflow, pl.taskToTool, tl.argumentInformation)

  # If the --export-config has been set, then the user is attempting to create a
  # new configuration file based on the selected pipeline.  This can only be
  # selected for a pipeline and if multiple runs are NOT being performed.
  if '--export-instance' in cl.uniqueArguments:
    if mr.hasMultipleRuns:
      er.exportInstanceForMultipleRuns(verbose)
      er.terminate()

    # Define the json export object, initialise and then check that the given filename is unique.
    make.arguments = deepcopy(make.coreArguments)
    make.prepareForInternalLoop(iLoop.tasks, iLoop.arguments, iLoop.numberOfIterations)
    ei = exportInstance()
    if pl.isPipeline: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, pl.instances, verbose)
    else: ei.checkInstanceFile(cl.argumentList, pl.pipelineName, tl.instances[tl.tool], verbose)
    ei.getData(gknoHelp, tl.argumentInformation, tl.shortForms, pl.isPipeline, pl.workflow, pl.taskToTool, pl.argumentInformation, pl.arguments, pl.toolsOutputtingToStream, pl.toolArgumentLinks, pl.linkage, make.arguments, verbose)
    if pl.isPipeline: ei.writeNewConfigurationFile(sourcePath, 'pipes', ins.externalInstances, pl.instances, cl.linkedArguments)
    else: ei.writeNewConfigurationFile(sourcePath, 'tools', ins.externalInstances, tl.instances[tl.tool], cl.linkedArguments)

    # After the configuration file has been exported, terminate the script.  No
    # Makefile is generated and nothing is executed.
    exit(0)

  # Now that all of the information has been gathered and stored, start a loop over the remainder of 
  # the gkno subroutines.  Each iteration (there is only a single iteration in the absence of the
  # multiple runs command), the arguments for that run are set up and the makefile generated and
  # executed (unless, no execution was requested).
  while True:

    # Define the name of the Makefile.  If there are multiple runs, append an intefer
    # ID to the end of the name.  This will be incremented for each subsequent Makefile.
    make.getFilename(mr.hasMultipleRuns, pl.pipelineName)
    make.arguments = deepcopy(make.coreArguments)
    if mr.hasMultipleRuns:
      mr.getArguments()
      make.getMultipleArguments(tl.argumentInformation, pl.workflow, pl.taskToTool, mr.arguments)

    make.arguments = checkInputLists(tl.argumentInformation, pl.workflow, pl.taskToTool, make.arguments, verbose) # dataChecking.py
    make.prepareForInternalLoop(iLoop.tasks, iLoop.arguments, iLoop.numberOfIterations)

    # Some of the variables use the value MAKEFILE_ID in their names.  This is often used in
    # the names of temporary files etc and is intended to ensure that if multiple scripts are
    # generated, these values are all different in each script.  If there are parameters in the
    # internal loop that use this value, then they need to be modified to include the iteration
    # number to ensure that the values are still unique.
    if iLoop.usingInternalLoop: checkMakefileID(make.arguments, iLoop.tasks, iLoop.numberOfIterations)

    # Loop over each of the tools in turn and set all of the parameters.  Each
    # task in turn may depend on parameters/outputs of previous tasks and so
    # handling in each task in the order it appears in the pipeline is necessary.
    for task in pl.workflow:
      tool = pl.taskToTool[task]

      # Check all of the options for each tool and determine if the values are
      # linked to any other tool.  If so, set the values as necessary.
      if pl.isPipeline:
        pl.toolLinkage(task, tool, tl.argumentInformation[tool], make.arguments, iLoop.usingInternalLoop, iLoop.tasks, iLoop.numberOfIterations, verbose)

        # If the tool is listed as only outputting to a stream, check if it appears within or
        # at the end of piped tasks.  If it appears at the end and an output file has been
        # specified (or instructtions on how to construct it have been included), set the output.
        if tool in tl.toolsDemandingOutputStream: checkStreamedOutput(task, tool, tl.argumentInformation, pl.taskToTool, pl.constructFilenames, pl.toolsOutputtingToStream, make.arguments, verbose)

        # Check all input and output files.  If there are instructions on how to construct
        # filenames, construct them.
        constructFilenames(task, tool, make.arguments, tl.argumentInformation, pl.constructFilenames, pl.toolArgumentLinks, pl.taskToTool, verbose)

      # Check that all required files and parameters have been set.
      checkParameters(gknoHelp, task, tool, tl.argumentInformation, make.arguments, pl.isPipeline, pl.workflow, pl.argumentInformation, pl.toolsOutputtingToStream, pl.toolArgumentLinks, pl.linkage, True, verbose)

      # For all files, check that a path has been given.  If a path is set, leave the file
      # as is.  If no path has been set, check if the file is an input or output
      # file and use the --input-path and --output-path values
      # respectively.
      setPaths(task, tool, tl.argumentInformation, tl.shortForms, pl.argumentInformation, pl.arguments, pl.toolArgumentLinks, make.arguments, verbose)

    # Determine each tools dependencies for building the makefile.
    make.dependencies, make.outputs = determineDependencies(tl.argumentInformation, tl.generatedFiles, pl.workflow, pl.taskToTool, pl.toolsOutputtingToStream, make.arguments)
  
    # There may be files that are required by the tool to run (e.g. files to
    # appear in the dependency list) that are not listed in the input arguments.
    # Those listed with arguments have already been included in the dependency
    # string for each tool in checkParameters, now check for others.
    #
    # Similarly, each tool produces output files.  These are listed in the
    # Makefile in order to ensure that tools are only run if their outputs
    # don't already exist.
    determineAdditionalFiles(tl.additionalFiles, pl.workflow, pl.taskToTool, pl.additionalFileDependencies, make.arguments, make.dependencies, make.outputs, verbose)
  
    # If there are any explicit dependencies included in the pipeline configuration file, 
    # include them.
    #if pl.isPipeline:
    #  if len(pl.additionalFileDependencies) != 0: includeAdditionalFileDependencies(pl.additionalFileDependencies, make.dependencies)

    # In the course of executing the pipeline, some of the intermediate files
    # generated along the way should be deleted.  The pipeline configuration
    # file segment 'delete files' identifies which files should be deleted and
    # when in the pipeline they can be removed.
    make.deleteFiles = determineFilesToDelete(make.arguments, pl.deleteFiles, iLoop.tasks, iLoop.numberOfIterations, verbose)
  
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
    make.hasPipes, make.addedInformation = determinePiping(make.arguments, tl.argumentInformation, tl.toolsDemandingInputStream, tl.toolsDemandingOutputStream, pl.workflow, pl.taskToTool, pl.toolsOutputtingToStream, verbose)
  
    # The basic order of the Makefile is to start with the final tool and write
    # out the rules to build the final output file.  If the prerequisites for this
    # task do not exist, then make will search for the rule to make the files.  The
    # Makefile proceeds in this manner all the way to the first task.  If any of the
    # tasks are piped together, then these need to be output in order, not reverse
    # order.
    make.taskBlocks = determineToolWriteOrder(pl.workflow, pl.toolsOutputtingToStream, make.hasPipes)
  
    # Determine the outputs and dependencies for each block of tasks.
    make.taskBlockOutputs, make.taskBlockDependencies = getTaskBlockOutputsAndDependencies(make.taskBlocks, make.outputs, make.dependencies, iLoop.tasks, iLoop.numberOfIterations)
    determineFinalOutputs(make.deleteFiles, make.outputs)

    # Generate scripts to run the selected pipeline.
    make.openMakefile(sourcePath, pl.isPipeline)
    make.setIntermediateFiles(pl.workflow, pl.taskToTool)
    make.writeAllOutputs()

    # Loop over all of the task blocks in the pipeline.
    for tasks, outputs, dependencies in zip(reversed(make.taskBlocks), reversed(make.taskBlockOutputs), reversed(make.taskBlockDependencies)):

      # For this taskBlock, determine if the tasks are included in an internal loop.  If
      # so, loop over the internal loop parameter sets, generating a command for each of
      # them.
      for counter in range(0, len(outputs)):
        make.writeInitialInformation(pl.taskToTool, tasks, counter)
        make.getExecutablePath(sourcePath, tl.paths, pl.taskToTool, tasks, counter)
        make.writeOutputsToMakefile(outputs[counter])
        make.writeDependenciesToMakefile(dependencies[counter])
        make.checkStdout(tasks, pl.arguments['--task-stdout'], mr.hasMultipleRuns)
        make.generateCommand(tl.argumentInformation, tl.argumentDelimiters, tl.precommands, tl.executables, tl.modifiers, tl.argumentOrder, pl.taskToTool, pl.linkage, pl.arguments['--timing'], tasks, verbose, counter)
        make.addFileDeletion(tasks, counter)
        make.handleAdditionalOutputs(outputs[counter], dependencies[counter])
      print(file = make.makeFilehandle)
    make.closeMakefile()

    # Having completed the makefile for one set of parameters, reset the tl.toolArguments
    # structure to the original values before running the pipeline again.
    make.arguments        = make.coreArguments
    make.addedInformation = {}

    # Terminate the loop when all the required Makefiles have been produced.
    if make.id == mr.numberDataSets: break

  # Check that all of the executable files exist.
  checkExecutables(sourcePath, tl.paths, tl.executables, pl.workflow, pl.taskToTool, verbose)

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  if pl.arguments['--do-not-log-usage'] == 'unset':
    if verbose: writeTracking(phoneHomeID)
    phoneHome(sourcePath, phoneHomeID)
    if verbose: writeDone()
  writeBlankLine()

  # Execute the generated script unless the execute flag has been unset.
  success = 0
  if pl.arguments['--execute']:
    for makefile in make.filenames:
      if verbose: writeExecuting(makefile)

      # Check if the '--number-jobs' option is set.  If so, request this number of jobs.
      if pl.arguments['--number-jobs'] != '': execute = 'make -j ' + str(pl.arguments['--number-jobs'])
      else: execute = 'make'
      execute += ' --file ' + makefile
      print('Executing command:', execute, '\n')
      success = subprocess.call(execute.split())
      if verbose: writeComplete(success)

  # If the makefile was succesfully run, finish gkno with the exit condition of 0.
  # If the makefile failed to run, finish with the exit condition 3.  A failure
  # prior to execution of the makefile uses the exit condition 2.
  if success == 0: exit(0)
  else: exit(3)

if __name__ == "__main__":
  main()

#!/usr/bin/python

from __future__ import print_function

import os.path
import getpass
import subprocess
import sys

import gkno.executables as exe
import gkno.adminUtils as au
import gkno.adminErrors as adminErrors
import gkno.arguments as ag
import gkno.commandLine as cl
import gkno.constructFilenames as construct
import gkno.dataConsistency as dc
import gkno.debug as debug
import gkno.executionStructure as es
import gkno.evaluateCommands as ec
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
import gkno.tracking as tracking
import gkno.web as w
import gkno.writeToScreen as write

__author__ = "Alistair Ward"
__version__ = "2.48.4"
__date__ = "November 2015"

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

  # Define the commit id of the this version of gkno.
  commitId = os.getenv('GKNOCOMMITID')

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

  # List the gkno arguments if requested.
  #if mode == "gkno help": gknoHelp.gknoArgumentHelp()

  # Check to see if the configuration files are to be found in a directory other than the default.
  path                  = command.getConfigurationFilePath(gknoConfiguration.options)
  userConfigurationPath = path if path else None

  # Define a class for handling files. In the initialisation, determine the names of all available
  # tools and pipelines.
  files = fh.fileHandling(toolConfigurationFilesPath, pipelineConfigurationFilesPath, userConfigurationPath)

  # Define a cloass for handling arguments whose values are a command to evaluate.
  evalCom = ec.evaluateCommands()

  # If not being run in admin mode, determine the name of the pipeline being run. Note that
  # for the code, a tool is considered a pipeline with a single task, so the terminology
  # 'pipeline' is used throughout for both cases.
  if not admin.isRequested:

    # Check that gkno has been built before proceeding.
    if not admin.isBuilt(): adminErrors.adminErrors().gknoNotBuilt()
    pipeline = command.determinePipeline()

  # Otherwise, handle the admin functions.
  else:
    if admin.run(sys.argv):

      # Check that all of the tools were successfully built. If not, post a warning about which tools cannot
      # be used.
      if admin.allBuilt: exit(0)
      else: adminErrors.adminErrors().failedToolBuilds(admin.builtTools)
    else: adminErrors.adminErrors().errors.terminate(adminErrors.adminErrors().errorCode)

  # Display gkno arguments if requested.
  if mode == 'gkno help': gknoHelp.gknoArgumentHelp(gknoConfiguration.arguments)

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
    graph = gr.pipelineGraph(superpipeline.pipeline)

    # Loop over the tiers of nested pipelines and build them into the graph.
    for tier in superpipeline.pipelinesByTier.keys():
      for pipelineName in superpipeline.pipelinesByTier[tier]:
        graph.buildPipelineTasks(superpipeline.pipelineConfigurationData[pipelineName], superpipeline)

    # Associate configuration file unique node ids with graph node ids for unique nodes pointing to nodes
    # in nested pipelines.
    graph.findUniqueNodes(superpipeline)

    # Parse the configuration files identifying nodes that are to be connected.
    graph.connectNodes(superpipeline)

    # If any pipeline configuration nodes are given commands to evaluate, check the validity of the instructions
    # and implement them.
    evalCom.checkCommands(graph, superpipeline)

    # Determine which graph nodes are required. A node may be used by multiple tasks and may be optional
    # for some and required by others. For each node, loop over all edges and check if any of the edges
    # are listed as required. If so, the node is required and should be marked as such.
    graph.markRequiredNodes(superpipeline)

    # If the main pipeline lists a tool whose arguments should be imported, check that the listed tool is
    # valid, that none of the arguments conflict with the pipeline and then add the arguments to the
    # allowed arguments.
    args.importArguments(graph, superpipeline)

    # Now that arguments have been imported from tools, check that there are no problems.
    args.checkArguments(superpipeline)

    # Now that the graph is built, parse all of the arguments in the pipelines and associate them with the
    # graph nodes and vice versa.
    args.assignNodesToArguments(graph, superpipeline)

    # If web page json files are being created, update the list of categories and the pipeline information. Also
    # generate a reduced plot of the pipeline.
    if mode == 'web' and not superpipeline.getPipelineData(superpipeline.pipeline).isDevelopment:
      web.updateCategories(superpipeline.pipelineConfigurationData[superpipeline.pipeline])
      web.updatePipelineInformation(superpipeline.pipelineConfigurationData[superpipeline.pipeline], args.arguments)

      # Generate the workflow for the pipeline.
      workflow = graph.generateWorkflow()

      # Check for required arguments. This check will create required nodes that are unset, but not terminate gkno,
      # since we are just trying to create pipeline plots.
      dc.checkRequiredArguments(graph, superpipeline, args, isTerminate = False)

      # Generate the plot.
      plot.plot(superpipeline, graph, str(superpipeline.pipeline), isReduced = True)

  # Get information about individual tools, write out web content and terminate.
  if mode == 'web':
    web.updateTools(files, toolConfigurationFilesPath)
    web.getGknoArguments(gknoConfiguration.arguments)
    web.writeContent(os.getenv('GKNOCOMMITID'), __version__, __date__)

    print('All web content successfully generated.')
    exit(0)

  # Generate the workflow.
  workflow = graph.generateWorkflow()

  # Process the command line arguments.
  command.processArguments(superpipeline, args, gknoConfiguration)

  # If the pipeline is being rerun, determine the random string to use, if possible.
  if gknoConfiguration.getGknoArgument('GKNO-RERUN', command.gknoArguments):
    randomString = files.getRandomString(pipeline)
    if not randomString: command.errors.cannotRerunPipeline(pipeline)
    else: superpipeline.randomString = randomString

  # Check if a parameter set is to be removed.
  removeParameterSet = gknoConfiguration.getGknoArgument('GKNO-REMOVE-PARAMETER-SET', command.gknoArguments)

  # Determine if a parameter set is being exported. If so, there is no need to check that all required
  # arguments are set, since the pipeline is not being executed.
  graph.exportParameterSet = gknoConfiguration.getGknoArgument('GKNO-EXPORT-PARAMETER-SET', command.gknoArguments)

  # Determine the requested parameter set and add the parameters to the graph.
  parSet             = ps.parameterSets()
  graph.parameterSet = command.getParameterSetName(command.gknoArguments, gknoConfiguration)
  if removeParameterSet: parSet.removeParameterSet(graph, superpipeline, removeParameterSet)

  # Step through the workflow and determine the default parameter sets for all of the tasks. Populate
  # the nodes with these task level default parameter sets, creating nodes where necessary.
  command.addGknoArguments(graph.addTaskParameterSets(superpipeline, 'default', gknoConfiguration))

  # Now add the default parameter set for the pipelines.
  graph.addPipelineParameterSets(superpipeline, args, 'default', resourcesPath)

  if graph.parameterSet and graph.parameterSet != 'none' and graph.parameterSet != 'None': 
    graph.addParameterSet(superpipeline, args, superpipeline.pipeline, graph.parameterSet, resourcesPath)

  # If help was requested, print out the relevent help information.
  # TODO ADMIN HELP
  if mode == 'help': gknoHelp.pipelineHelp(superpipeline, graph, args.arguments, False)

  # Write out help on gkno specific (e.g. not associated with a specific pipeline) arguments.
  elif mode == 'gkno help': gknoHelp.pipelineHelp(superpipeline, graph, args.arguments, gknoConfiguration.arguments)

  # Parse the command line arguments and associate the supplied command line argument values with the graph node.
  command.parseTasksAsArguments(superpipeline)
  associatedNodes = command.associateArgumentsWithGraphNodes(graph.graph, superpipeline)

  # Create nodes for all of the defined arguments for which a node does not already exist and add the
  # argument values to the node.
  graph.attachArgumentValuesToNodes(graph, superpipeline, args, command.pipelineArguments, associatedNodes)

  # Loop over all nodes and expand lists of arguments. This is only valid for arguments that are either options,
  # or inputs to a task that are not simulateously outputs of another task.
  graph.expandLists()

  # Check that all of the values associated with all of the nodes are of the correct type (e.g. integer, flag etc)
  # and also that any files also have the correct extension.
  dc.checkValues(graph, superpipeline)

  # Determine whether or not to output a visual representation of the pipeline graph.
  plot.isPlotRequired(command.gknoArguments, gknoConfiguration)
  if plot.isFullPlot: plot.plot(superpipeline, graph, plot.fullPlotFilename, isReduced = False)
  if plot.isReducedPlot: plot.plot(superpipeline, graph, plot.reducedPlotFilename, isReduced = True)

  # If multiple values have been supplied to linked arguments, determine if they should be reordered.
  if not gknoConfiguration.getGknoArgument('GKNO-DO-NOT-REORDER', command.gknoArguments): command.linkedArguments(graph, superpipeline, args)

  # Loop over all of the nodes in the graph and ensure that all required arguments have been set. Any output files
  # for which construction instructions are provided can be omitted from this check. This will ensure that all required
  # input files are set, ensuring that filename construction can proceed. The check will be performed again after
  # filenames have been constructed, without the omission of constructed files.
  if not graph.exportParameterSet: dc.checkRequiredArguments(graph, superpipeline, args, isTerminate = True)

  # Check for greedy tasks in the pipeline and mark the relevant nodes and edges.
  graph.setGreedyTasks(superpipeline)

  # If multiple outputs have been specified, but only single inputs with multiple options, ensure that there are
  # the same number of input files as there output files.
  graph.propogateInputs()

  # If the user has requested that a parameter set is to be exported, export the parameter set and terminate.
  if graph.exportParameterSet: parSet.export(graph, superpipeline, args, command.pipelineArguments)

  # Loop over the tasks in the pipeline and construct filenames for arguments that require them, but weren't given
  # any on the command line. In addition, if multiple options are given to a task, this routine will generate new
  # nodes for the task and files and link them together as necessary.
  graph.constructFiles(superpipeline)

  # Check that all of the streams are correctly marked in the superpipeline. This checks to see if a task is
  # marked as accepting a stream, but the task is itelf a pipeline, for example. In this case, the first task
  # in the nested pipeline needs to be marked as accepting a stream.
  superpipeline.checkStreams(graph)

  # Determine which files are marked for deletion.
  superpipeline.determineFilesToDelete(graph)

  # Print the workflow to screen.
  write.workflow(superpipeline, workflow)

  # If any input values have been reordered, warn the user.
  write.reordered(graph, command.reorderedLists)

  # Having constructed all of the output file names (which may then be linked to other tasks as outputs), rerun the
  # check of the values to ensure that the data types and the ssociated extensions are valid. This will provide a
  # check of whether tools can be linked as described in the configuration file. In the previous check, not all of the
  # filenames were present (but the check ensured that the values provided on the command line were valid). If a task
  # outputs a file with and extension 'ext1' and the file is then passed to a file that requires files with the
  # extension 'ext2', the pipeline is invalid. The output filename has been constructed as file.ext1 and so the following
  # routine will flag the file as invalid as input to the next task.
  dc.checkValues(graph, superpipeline)

  # If the pipeline has instructions to terminate based on input conditions, modify the pipeline.
  graph.terminatePipeline(superpipeline)

  # Having reached this point, all of the required values have been checked, are present and have the correct data
  # type. In the construction of the graph, a number of non-required nodes could have been created and, since they
  # are not required, they could be unpopoulated. March through the graph and purge any nodes that have no values or
  # are isolated.
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

  # If a task has multiple divisions, ensure that there are the same number of input and output files for the task.
  # It is possible that n input files were specified on the command line, leading to n executions of the task, but
  # m output files were specified. This will lead to problems when constructing the command lines.
  graph.checkNumberOfOutputs()

  # For values that are commands to be executed at runtime, include any values from other graph nodes as necessary.
  evalCom.addValues(graph)

  # Generate a makefiles object and then build all the command lines for the tasks as well as creating a list of each
  # tasks dependencies and output.
  make = mk.makefiles()
  make.generateCommandLines(graph, superpipeline, struct)

  # Determine if multiple makefiles have been requested and whether to add a unique id to the makefiles.
  make.isMultipleMakefiles, make.makefileId = command.checkMakefiles(gknoConfiguration.options)

  # Update the intermediate files.
  make.updateIntermediates(struct)

  # Open the required makefiles. This is either a single makefile that will run all tasks, or a set of makefiles broken
  # up by the phase, subphase and division
  make.openMakefiles(superpipeline.pipeline, superpipeline.randomString, struct)

  # Add the header text to the file(s).
  make.addHeader(commitId, __date__, __version__, superpipeline.pipeline, sourcePath, toolsPath, resourcesPath)

  # Include the paths of all the required executables.
  make.addUniqueExecutables(graph, struct)

  # Add phony information.
  make.addPhony()

  # Get the intermediate and output files for the whole pipeline.
  outputs = make.getAllOutputs(struct, superpipeline.randomString)

  # Remove the 'ok' file used to indicated successful execution.
  make.removeOk()

  # Add the command lines to the makefiles.
  for phase in struct.phaseInformation:
    for subphase in range(1, struct.phaseInformation[phase].numberSubphases + 1):
      for division in range(1, struct.phaseInformation[phase].numberDivisions + 1):
        make.addCommandLines(graph, struct, phase, subphase, division)

  # Write final information to the makefile, then close the file.
  make.completeFile(outputs)

  # Close the makefiles.
  make.closeFiles()

  # Check that all of the dependent files exist (excluding dependencies that are created by tasks in the pipeline).
  success = files.checkFileExistence(requiredInputFiles, resourcesPath, toolsPath)

  # Having established the mode of operation and checked that the command lines are
  # valid etc., ping the website to log use of gkno.
  if not gknoConfiguration.getGknoArgument('GKNO-DNL', command.gknoArguments): tracking.phoneHome(sourcePath, pipeline)

  # Prior to execution of the makefile, ensure that all required executables exist. This first requires parsing the
  # user settings file.
  admin.exportUserSettings()
  exe.executables().checkExecutables(toolsPath, superpipeline, admin.userSettings['compiled tools'])

  # Execute the generated script unless the user has explicitly asked for it not to be run, or if multiple makefiles
  # have been generated.
  if gknoConfiguration.options['GKNO-DO-NOT-EXECUTE'].longFormArgument not in command.gknoArguments and not make.isMultipleMakefiles and success:

    # Get the number of parallel jobs to be requested.
    jobsArgument = gknoConfiguration.options['GKNO-JOBS'].longFormArgument
    numberJobs   = command.gknoArguments[jobsArgument][0] if jobsArgument in command.gknoArguments else 1

    # Generate the execution command.
    execute = 'make -k -j ' + str(numberJobs) + ' --file ' + make.singleFilename
    success = subprocess.call(execute.split())

if __name__ == "__main__":
  main()

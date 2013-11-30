#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import gknoErrors
from gknoErrors import *

import os
import sys

class makefileData:
  def __init__(self):
    self.addedInformation       = {}
    self.arguments              = {}
    self.coreArguments          = {}
    self.dependencies           = {}
    self.errors                 = gknoErrors()
    self.finalArguments         = {}
    self.hasPipes               = False
    self.intermediateFiles      = []
    self.outputs                = {}
    self.outputPath             = ''
    self.phonyTargetID          = 1
    self.phonyTargets           = []
    self.taskBlocks             = []
    self.taskBlocksOutputs      = []
    self.taskBlocksDependencies = []

    # Define information on the makefile structure. This is information on the number of phases 
    # and how many makefile each phase has.
    self.makefilesInPhase  = {}
    self.makefileNames     = {}
    self.makefileStructure = {}
    self.numberOfPhases    = 1
    self.tasksInPhase      = {}

    # Store the paths of all executable files.
    self.executablePaths = {}

  def determineMakefileStructure(self, graph, config, workflow, hasMultipleRuns):

    # If the pipeline is not being run with multiple runs, there is a single makefile generated,
    # so all tasks are added to the same phase and have one file in that phase.
    if not hasMultipleRuns:
      for task in workflow: self.makefileStructure[task] = (1, 1)
      self.makefilesInPhase[1] = 1
      self.tasksInPhase[1]     = workflow

    # If the pipeline is being in multiple runs mode, determine the structure.
    else:
      firstTask    = True
      currentPhase = 1
      for task in workflow:
  
        # Determine the number of iterations of input and output files.
        numberOfInputDataSets  = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getPredecessorFileNodes(graph, task))
        numberOfOutputDataSets = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getSuccessorFileNodes(graph, task))
  
        if numberOfInputDataSets != numberOfOutputDataSets:
          #TODO ERROR
          print('NUMBER OF INPUT DATA SETS IS DIFFERENT TO NUMBER OF OUTPUT DATASETS - determineMakefileStructure')
          self.error.terminate()
  
        # If this is the first task in the workflow, determine how many makefiles are required
        # for this task. This is the number of input or output data sets. Set the current makefiles
        # to these.
        if firstTask:
          numberOfFilesinPhase            = numberOfInputDataSets
          self.makefileStructure[task]    = (currentPhase, numberOfFilesinPhase)
          self.makefilesInPhase[1]        = numberOfInputDataSets
          self.tasksInPhase[currentPhase] = []
          firstTask                       = False
        else:
          if numberOfInputDataSets != numberOfFilesinPhase:
            currentPhase += 1
            self.tasksInPhase[currentPhase]     = []
            self.numberOfPhases                 = currentPhase
            self.makefilesInPhase[currentPhase] = numberOfInputDataSets
            numberOfFilesinPhase                = numberOfInputDataSets
          self.makefileStructure[task]    = (currentPhase, numberOfFilesinPhase)
        self.tasksInPhase[currentPhase].append(task)

  # Get the number of data sets for a node.
  def getNumberOfDataSets(self, graph, config, task, nodeIDs):
    finalNumber = 0

    for nodeID in nodeIDs:
      optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
      numberOfDataSets = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'numberOfDataSets')

      # Check to see if this particular argument is greedy.
      isGreedy = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isGreedy')
      if isGreedy: numberOfDataSets = 1
      if numberOfDataSets > finalNumber: finalNumber = numberOfDataSets

    return finalNumber

  # Set the names of the makefiles to be created.  If this is a single run, a single name
  # is required, otherwise, there will be a list of names for each of the created makefiles.
  def getFilename(self, text):
 
    # If there is only a single phase, there is no need for phase information in the makefile
    # name.
    if self.numberOfPhases == 1:
      self.makefileNames[1] = []
      if self.makefilesInPhase[1] == 1: self.makefileNames[1].append(text + '.make')
      else:
        for count in self.makefilesInPhase[1]: self.makefileNames[1].append(text + '_' + str(count) + '.make')

    # If there are phases, include the phase in the name of the makefiles.
    else:
      text = text + '_phase_'
      for phaseID in range(1, self.numberOfPhases + 1):
        self.makefileNames[phaseID] = []
        if self.makefilesInPhase[phaseID] == 1: self.makefileNames[phaseID].append(text + str(phaseID) + '.make')
        else:
          for count in range(1, self.makefilesInPhase[phaseID] + 1):
            self.makefileNames[phaseID].append(text + str(phaseID) + '_' + str(count) + '.make')

  # Get the output path for use with generating the makefiles.
  def getOutputPath(self, graph, config):

    # The output path is stored with the gkno specific nodes. Since the valiues are treated as all other
    # arguments, the value itself is the first (and only) value in the list associated with the first (and
    # only iteration).
    outputPath = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-OUTPUT-PATH', 'values')
    if not outputPath: self.outputPath = '$(PWD)'
    else:
      self.outputPath = outputPath[1][0]

      # If the chosen output path is not the current directory, check to see if the directory exists.
      if not os.path.isdir(self.outputPath):
        self.errors.missingOutputDirectory(graph, config, self.outputPath)
        config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-EXECUTE', [False], write = 'replace')

  # Open the makefile and write the initial information to the file.
  def openMakefile(self, makefileName):
    makefileHandle = open(makefileName, 'w')
    makefileName   = os.path.abspath(makefileName)

    return makefileHandle

  # Write initial information to the makefiles.
  def writeHeaderInformation(self, sourcePath, pipelineName, makefileName, fileHandle, phaseID, iteration):
    print('### gkno Makefile', file = fileHandle)
    print('### Running pipeline:', pipelineName, file = fileHandle)

    # Write phase information if there is more than one phase in the pipeline.
    if self.numberOfPhases != 1: print('### Phase ', str(phaseID), ' of ', str(self.numberOfPhases), sep = '', file = fileHandle)

    # If this phase has multiple data sets, write out which set this is.
    if self.makefilesInPhase[phaseID] > 1: print('### Data set ', str(iteration), ' of ', self.makefilesInPhase[phaseID], sep = '', file = fileHandle)

    print(file = fileHandle)
    print('### Paths to tools and resources.', file = fileHandle)
    print('GKNO_PATH=', sourcePath, "/src/gkno", sep = '', file = fileHandle)
    print('TOOL_BIN=', sourcePath, "/tools", sep = '', file = fileHandle)
    print('RESOURCES=', sourcePath + '/resources', sep = '', file = fileHandle)
    print('MAKEFILE_ID=', makefileName.split('/')[-1].split('.')[0], sep = '', file = fileHandle)
    print(file = fileHandle)
    print('### Standard output and errors files.', file = fileHandle)
    print('STDOUT=', self.outputPath, '/', pipelineName, '.stdout', sep = '', file = fileHandle)
    print('STDERR=', self.outputPath, '/', pipelineName, '.stderr', sep = '', file = fileHandle)
    print(file = fileHandle)

  # Write out all of the intermediate files.
  def writeIntermediateFiles(self, fileHandle, intermediates):
    print('.DELETE_ON_ERROR:', file = fileHandle)
    print('.PHONY: all', file = fileHandle)
    print('.INTERMEDIATE:', end = ' ', file = fileHandle)
    if intermediates:
      for nodeID, intermediateFile in intermediates:
        print(intermediateFile, end = ' ', file = fileHandle)
    print(file = fileHandle)
    print(file = fileHandle)

  # Write out all of the output files.
  def writeOutputFiles(self, fileHandle, outputs):
    print('all:', end = ' ', file = fileHandle)
    if outputs:
      for nodeID, outputFile in outputs:
        print(outputFile, end = ' ', file = fileHandle)
    print(file = fileHandle)
    print(file = fileHandle)

  # Write out all of the executable paths that are used in the makefile.
  def writeExecutablePaths(self, fileHandle, taskList, tasks, tools):
    print('### Executable paths.', file = fileHandle)
    for task in taskList:
      tool                       = tasks[task]
      pathVariable               = (tool.replace(" ", "_")  + '_PATH').upper()
      self.executablePaths[tool] = tools.getConfigurationData(tool, 'path')

      # Some tools (e.g. UNIX commands) have no path and shouldn't be given an executable.
      if self.executablePaths[tool] != 'no path':
        print(pathVariable, "=$(TOOL_BIN)/", self.executablePaths[tool], sep = "" , file = fileHandle)
    print(file = fileHandle)

  # Loop over all of the tasks in the workflow and write out all of the information for
  # executing each task.
  def writeTasks(self, graph, config, makefileName, fileHandle, taskList, deleteList, iteration):
    for task in taskList:

      # Define the minimum and maximum iteration values. If a single iteration is being performed,
      # this will be the same, but if there is an internal loop, all the iterations need to be
      # written to the same file.
      if iteration == 'all':
        minIteration = 1
        maxIteration = config.nodeMethods.getGraphNodeAttribute(graph, task, 'numberOfDataSets')
      else:
        minIteration = iteration
        maxIteration = iteration
      for counter in range(minIteration, maxIteration + 1):
        taskOutputs      = config.getTaskOutputs(graph, task, iteration = counter)
        taskDependencies = config.getTaskDependencies(graph, task, iteration = counter)
        print('### Command line information for ', task, ' (', config.pipeline.tasks[task], ').', sep = '', file = fileHandle)
  
        # Due to the vagaries of the makefile operation, if there are multiple outputs, it is
        # not acceptable to just list all of the outputs at the start of the rule. In reality,
        # to ensure proper operation, a single output is listed and then an additional rule is
        # included after the task to check for the existence of the remaining outputs.
        primaryOutput = taskOutputs.pop(0)
        print(primaryOutput, end = ': ', file = fileHandle)
  
        # Write out the task dependencies separated by spaces.
        for i in range(0, len(taskDependencies)): print(taskDependencies[i], end = ' ', file = fileHandle)
        print(file = fileHandle)
  
        # Include a line that will echo which task is being run.
        print('\t@echo -e "Executing task: ', task, '...\c"', sep = '', file = fileHandle)
  
        # Write the executable command.
        stdoutUsed = self.writeCommand(graph, config, fileHandle, task, counter)

        # Write output and errors to the stdout and stderr files.
        self.writeStdouts(stdoutUsed, fileHandle)

        # Write that the task complete successfully.
        self.writeComplete(fileHandle)
  
        # If there are additional output files from this task, include an additional rule in the
        # makefile to check on their existence.
        if len(taskOutputs) != 0: self.writeRuleForAdditionalOutputs(makefileName, fileHandle, taskOutputs, primaryOutput, taskDependencies)

  # Write an additional rule in the makefile to check for outputs from a task. Only a single
  # output is included in the rule for the additional task.
  def writeRuleForAdditionalOutputs(self, makefileName, fileHandle, outputs, primaryOutput, dependencies):
    lastOutput = outputs.pop(0)
    print(file = fileHandle)
    print('### Rule for checking that all outputs of previous task exist.', file = fileHandle)
    for counter in range(0, len(outputs)): print(outputs[counter], end = ' ', file = fileHandle)
    print(lastOutput, end = ': ', file = fileHandle)
    for filename in dependencies: print(filename, end = ' ', file = fileHandle)
    print(file = fileHandle)
    print('\t@if test -f $@; then \\', file = fileHandle)
    print('\t  touch $@; \\', file = fileHandle)
    print('\telse \\', file = fileHandle)
    print('\t  rm -f ', primaryOutput, "; \\", sep = '', file = fileHandle)
    print('\t  $(MAKE) -f ', makefileName, ' ', primaryOutput, '; \\', sep = '', file = fileHandle)
    print('\tfi', file = fileHandle)
    print(file = fileHandle)

  # Write the command line for the current task.
  def writeCommand(self, graph, config, fileHandle, task, iteration):
    stdoutUsed = False

    # Define some tool attributes. These are extracted from the task node.
    #tool     = config.pipeline.tasks[task]
    tool       = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    precommand = config.nodeMethods.getGraphNodeAttribute(graph, task, 'precommand')
    modifier   = config.nodeMethods.getGraphNodeAttribute(graph, task, 'modifier')

    # Add the precommand if one exists.
    print('\t@', end = '', file = fileHandle)
    if precommand: print(precommand, end = ' ', file = fileHandle)

    if self.executablePaths[tool] != 'no path': print('$(', (tool + '_path').upper(), ')/', sep = '', end = '', file = fileHandle)

    print(config.nodeMethods.getGraphNodeAttribute(graph, task, 'executable'), end = ' ', file = fileHandle)

    # Add the command modifier if one exists.
    if modifier: print(modifier, end = ' ', file = fileHandle)

    print('\\', sep = '', file = fileHandle)
    arguments = self.getCommandLineInformation(graph, config, task)

    # Check if the argument need to be written in any particular order. If not, generate the
    # order randomly. It is possible that there are arguments with no value. This is because
    # the argument order will contain all of the argument for the tool, but they might not all
    # be set. Remove any of these argument from the argumentOrder structure.
    argumentOrder = self.defineArgumentOrder(config, tool, arguments)

    # Write the arguments to the makefile.
    for argument in argumentOrder:
      for nodeID, values in arguments[argument]:

        # Determine if this argument is a flag or a file.
        isFlag = True if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'dataType') == 'flag' else False
        isFile = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'isFile')

        # If the iteration does not exist, use the value from the first iteration.
        if iteration in values: valueList = values[iteration]
        elif iteration != 1: valueList = values[1]
        else:
          #TODO ERROR
          print('error in make.writeCommand', task, argument)
          self.errors.terminate()

        # The argument in the tool configuration file is not necessarily the same command that
        # the tool itself expects. This is because gkno attempts to standardise the command line
        # arguments across the tools. The argument to be used is also attached to the edge, so
        # get and use this value,
        commandLineArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'commandLineArgument')
        if not commandLineArgument: commandLineArgument = argument

        # Some arguments are included with the tools in order to help track the files, but do not
        # actually get written to the command line. For example, bamtools-index requires an input
        # bam file, but the output index file is created based on the name of the input file and
        # is not specified by the user. Check to see if this is the case.
        includeArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'includeOnCommandLine')

        # If the option refers to a file, then check, whether the option is a filename stub. Since the same
        # option can point to multiple tasks and the option can be a filename stub for one task, but a file
        # for another, determine this using the edge describing the individual argument. If the option is a
        # filename stub, use the values attached to the option node. If it isn't, find the associated file
        # node and use the values from there.
        if isFile:
          if not config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'isFilenameStub'):
            for fileNodeID in config.nodeMethods.getAssociatedFileNodeIDs(graph, nodeID):

              # Check that this file node points into or from the current task. Since this option may have been
              # associated with a filename stub, not all of the associated files are necessarily required by
              # this task.
              if config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isInput'):
                isAssociated = config.edgeMethods.checkIfEdgeExists(graph, fileNodeID, task)

                # Check that the iteration exists in the values of associated file nodes.
                if isAssociated:
                  try: valueList = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')[iteration]
                  except:
                    # TODO ERROR
                    print('Iteration not associated with file node values - make.writeCommand')
                    self.errors.terminate()

        for value in valueList:
          if includeArgument:

            # Determine the argument delimiter for this tool.
            delimiter = config.nodeMethods.getGraphNodeAttribute(graph, task, 'delimiter')
                    
            # Check if the argument is an output that writes to standard out.
            if config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'stdout':
              print('\t>> ', value, ' \\', sep = '', file = fileHandle)
              stdoutUsed = True

            # If the argument should be hidden, only write the value.
            elif config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'hide':
              print('\t', value, ' \\', sep = '', file = fileHandle)

            # If the argument and value should be hidden, don't write anything.
            elif config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'omit':
              pass

            # Check if the argument is a flag.
            elif not isFlag: print('\t', commandLineArgument, delimiter, value, ' \\', sep = '', file = fileHandle)

            # If the argument is a flag, check that the value is 'set' and if so, just write the argument.
            else:
              if value == 'set': print('\t', commandLineArgument, ' \\', sep = '', file = fileHandle)

    return stdoutUsed

  # Write outputs and errors to the stdout and stderr files.
  def writeStdouts(self, stdoutUsed, fileHandle):
    if not stdoutUsed: print('\t>> $(STDOUT) \\', file = fileHandle)
    print('\t2>> $(STDERR)', file = fileHandle)

  # Indicate that the task ran successfully.
  def writeComplete(self, fileHandle):

    # Write out that the task completed successfully.
    print('\t@echo -e "completed successfully."', sep = '', file = fileHandle)
    print(file = fileHandle)

  # Close the Makefile.
  def closeMakefile(self, fileHandle):
    fileHandle.close()

  # Define the order in which to write out the command line arguments.
  def defineArgumentOrder(self, config, tool, arguments):
    argumentOrder = config.tools.getToolAttribute(tool, 'argumentOrder')
    if not argumentOrder:
      for argument in arguments: argumentOrder.append(argument)

    # Check for arguments in argumentOrder that are not present in arguments and consequently
    # have no value.
    modifiedArgumentOrder = [ argument for argument in argumentOrder if argument in arguments ]

    return modifiedArgumentOrder

  # Parse all of the option nodes for a task and build up a data structure containing all
  # of the arguments and values.
  def getCommandLineInformation(self, graph, config, task):
    arguments = {}
    for nodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
      argument = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'argument')
      values   = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
      if argument not in arguments: arguments[argument] = []
      arguments[argument].append((nodeID, values))

    return arguments









  # Parse through the arguments in the different data structures to build up the list of
  # arguments to be applied.  Each set of arguments overwrites previous arguments in the
  # hierarchy (tool, instance and finally command line arguments).  This set of values
  # only needs to be generated once.  If multiple runs are being performed, they will use
  # this structure as the basis and add the new values from the multiple runs files.  If 
  # the particular command line argument allows multiple values, the values in each 
  # structure are appended.
  def getCoreArguments(self, information, workflow, taskToTool, toolArguments, instanceArguments, commandLineArguments):
    self.coreArguments = {}

    for task in workflow:
      tool = taskToTool[task]
      if task in toolArguments: self.getArguments(task, tool, information[tool], toolArguments, self.coreArguments)
      if task in instanceArguments: self.getArguments(task, tool, information[tool], instanceArguments, self.coreArguments)
      if task in commandLineArguments: self.getArguments(task, tool, information[tool], commandLineArguments, self.coreArguments)

  # If multiple runs have been requested, modify the arguments to include those from the
  # multiple runs file.
  def getMultipleArguments(self, information, workflow, taskToTool, multipleRunsArguments):
    for task in workflow:
      tool = taskToTool[task]
      if task in multipleRunsArguments:
        self.getArguments(task, tool, information[tool], multipleRunsArguments, self.arguments)

  # Parse the data structure for a particular task.
  def getArguments(self, task, tool, information, arguments, toModify):
    if task not in toModify: toModify[task] = {}
    for argument in arguments[task]:
      if argument not in toModify[task]: toModify[task][argument] = []

      # Check if the argument allows multiple entries.
      if 'allow multiple definitions' in information[argument]:
        for value in arguments[task][argument]: toModify[task][argument].append(value)
      else:
        toModify[task][argument] = arguments[task][argument]

  # Now that all of the default have been added to the tool commands, parse through all of the
  # arguments for each tool in the pipeline and check that the required fields are present.  If
  # they are already set, leave them alone, otherwise, set them to blank.  As linkage between
  # tools is checked, the unset values should be filled in.  If not, gkno will ultimately terminate.
  def setAllRequiredArguments(self, workflow, taskToTool, argumentInformation):
    for task in workflow:
      tool = taskToTool[task]
      for argument in argumentInformation[tool]:
        if argumentInformation[tool][argument]['required']:
          if argument not in self.coreArguments[task]:
            self.coreArguments[task][argument] = []

  # Build up the command lines in the makefile.
  def setIntermediateFiles(self, workflow, taskToTool):

    # Having established all the dependencies and the output files for each
    # tool, write out the commands for the Makefile.
    #
    # If any files are deleted during execution of the pipeline, mark them as
    # intermediate files.  This will ensure that if the Makefile is rerun, the
    # intermediate files will not be recreated.
    if len(self.deleteFiles) != 0:
      print('.INTERMEDIATE:', end = '', file = self.makeFilehandle)
      for task in self.deleteFiles:
        for counter, iteration in enumerate(self.deleteFiles[task]):
          for fileToDelete in self.deleteFiles[task][counter]:
            print(fileToDelete, end = ' ', file = self.makeFilehandle)

            # Put all of the intermediate files in a list.  This will be used to
            # ensure that the intermediate files are not included in the list of
            # output files.
            self.intermediateFiles.append(fileToDelete)

      print(file = self.makeFilehandle)

  # Write out all of the output files generated.
  def writeAllOutputs(self):
    print(file = self.makeFilehandle)
    print('all:', end = ' ', file = self.makeFilehandle)

    # Include all phony targets.
    for phonyTarget in self.phonyTargets: print(phonyTarget, end = ' ', file = self.makeFilehandle)

    allOutputs = []
    for outputBlock in reversed(self.taskBlockOutputs):
      for inputLoopIteration in outputBlock:
        for output in inputLoopIteration:
          allOutputs.append(output)

    for task in self.outputs:
      for inputLoopIteration in self.outputs[task]:
        for output in inputLoopIteration:
          if output in allOutputs and output not in self.intermediateFiles: print(output, end = ' ', file = self.makeFilehandle)

    print(file = self.makeFilehandle)
    print(file = self.makeFilehandle)

  # Set the name of the stdout and stderr and output the name of the task to the
  # file.
  # If there are multiple runs of the pipeline, the stdout and stderr from each of
  # the commands in the makefile will be written out to files of the form
  # <task>_<ID>.stdout, where ID is an integer
  def checkStdout(self, taskBlock, stdout, hasMultipleRuns):
    self.outputID = ''
    self.redirect = ''
    if stdout:
      if hasMultipleRuns: self.outputID = str(taskBlock[-1]) + '_' + str(self.id)
      else: self.outputID = str(taskBlock[-1])
      self.redirect = '>>'
    else:
      if hasMultipleRuns: self.outputID = str(self.filename.split('.')[0]) + '_' + str(self.id)
      else: self.outputID = str(self.filename.split('.')[0])
      self.redirect = '>>'

  # The arguments structure needs to be modified, so that each task has a list of arguments.  If
  # there is an internal loop, each task can have multiple sets of parameters to define multiple
  # runs of a task within the same Makefile.  This structure will allow each iteration of the task
  # to be held in the same place.  For tasks outside of the loop, the list should only contain one
  # set of parameters.
  def prepareForInternalLoop(self, iTasks, iArguments, numberOfIterations):
    arguments = {}
    for task in self.arguments:
      arguments[task] = []
      if task not in iTasks:
        arguments[task].append(self.arguments[task])
      else:
        if numberOfIterations == 0: arguments[task].append(deepcopy(self.arguments[task]))
        else:
          for counter in range(0, numberOfIterations): arguments[task].append(deepcopy(self.arguments[task]))

        # Now that the arguments structure has all of the parameters from the internal arguments, include
        # all of the arguments from the internal loop file.
        if task in iArguments:
          for argument in iArguments[task]:
            for counter, iteration in enumerate(iArguments[task][argument]):
              arguments[task][counter][argument] = deepcopy(iArguments[task][argument][iteration])

    # Now set the self.arguments structure to the newly created finalArguments structure.
    self.arguments = deepcopy(arguments)

  # Loop over each of the tasks in the task block and generate the command line.
  def generateCommand(self, argumentInformation, delimiters, precommands, executables, modifiers, argumentOrder, taskToTool, linkage, timing, taskBlock, verbose, internalLoopCounter):
    er                 = errors()
    useStdout          = False
    lineStart          = "\t"
    firstCommand       = True
    numberOfIterations = len(self.arguments[taskBlock[0]])
    for task, path in zip(taskBlock, self.pathList):
      if firstCommand:
        if len(taskBlock) == 1:
          print("\t@echo -e \"Executing task: ", taskBlock[-1], sep = '', end = '', file = self.makeFilehandle)
          if numberOfIterations > 1: print(' (Iteration: ', internalLoopCounter + 1, ')...\\c"', sep = '', file = self.makeFilehandle)
          else: print('...\\c"', sep = '', file = self.makeFilehandle)
        else:
          print("\t@echo -e \"Executing piped tasks (", taskBlock[0], ' --> ', taskBlock[-1], ')...\\c"', sep = '', file = self.makeFilehandle)
      tool      = taskToTool[task]
      delimiter = delimiters[tool] if tool in delimiters else ' '

      # Print out the command line.
      print(lineStart, end = '', file = self.makeFilehandle)

      # If this is a single command, or the first command in a set of piped commands, 
      # start the line with the '@' character.  This will stop make 'echoing' the command
      # to the screen.
      if firstCommand: 
        if timing == 'set':
          print('@echo -e \'Running task: ', task ,'\' ', self.redirect, ' ', self.outputID, '.stderr', sep = '', file = self.makeFilehandle)
          print(lineStart, end = '', file = self.makeFilehandle)
          print('@(time ', end = '', file = self.makeFilehandle)
        else: print('@', end = '', file = self.makeFilehandle)

      # Write the command line.
      if tool in precommands:
        print(precommands[tool], ' ', sep = '', end = '', file = self.makeFilehandle)
      executable = executables[tool]
      if path == '': print(executable, sep = '', end = '', file = self.makeFilehandle)
      else: print("$(", path, ")/", executable, sep = '', end = '', file = self.makeFilehandle)
      if tool in modifiers: print(' ', modifiers[tool], sep = '', end = '', file = self.makeFilehandle)
  
      # Check if the order in which the parameters appear matters.  For certain
      # tools, the command line is built up of a list of arguments, but each
      # argument isn't given an option.  For example, renaming a file has a 
      # command line 'mv A B', where A and B are filenames that have to appear
      # in the correct order.
      toolArgumentOrder = []
      if tool in argumentOrder:
        for argument in argumentOrder[tool]:
          if argument in self.arguments[task][internalLoopCounter]:
            if self.arguments[task][internalLoopCounter][argument] != '': toolArgumentOrder.append(argument)
      else:
        for argument in self.arguments[task][internalLoopCounter]: toolArgumentOrder.append(argument)

#FIXME CHECK ON THIS SECTION
#      argumentDict  = {}
#      for argument in tl.toolInfo[tool]['arguments']: argumentDict[argument] = True
#      if 'argument order' in tl.toolInfo[tool]:
#        for argument in tl.toolInfo[tool]['argument order']:
#          if argument in tl.toolArguments[task]:
#            argumentOrder.append(argument)
#            del(argumentDict[argument])
#          else:
#            self.error = False
#  
#            # If the argument is for an input or output, it is possible that these arguments
#            # have been removed if dealing with the stream.  Check if this is the case and
#            # if so, do not terminate.
#            if 'if output to stream' in tl.toolInfo[tool]['arguments'][argument]:
#              if tl.toolInfo[tool]['arguments'][argument]['if output to stream'] == 'do not include': del(argumentDict[argument])
#              else: self.error = True
#            elif 'if input is stream' in tl.toolInfo[tool]['arguments'][argument]:
#              if tl.toolInfo[tool]['arguments'][argument]['if input is stream'] == 'do not include': del(argumentDict[argument])
#              else: self.error = True
#            else: self.error = True
#            if self.error:
#              er.unknownArgumentInArgumentOrder(newLine, filename, tool, argument)
#              er.terminate()
#  
#        # Having stepped through all of the arguments included in the ordered list, check
#        # if there are any arguments left in the argumentDict dictionary.  This dictionary
#        # was built from all of the arguments for this tool and if it is not empty, then
#        # some of the arguments for this tool are not included in the list and thus would
#        # not be included in the command line.  Terminate with an error if this is the case,
#        if len(argumentDict) != 0:
#          #TODO Check this error.
#          er.missingArgumentsInOrderList(newLine, task, tool, argumentDict)
#          er.terminate()
#      else:
#        for argument in tl.toolArguments[task]: argumentOrder.append(argument)
#FIXME END OF SECTION TO CHECK  

      # Include all of the set options.
      for argument in toolArgumentOrder:

        # Check if the option is a flag.
        isFlag = False
  
        # Check if this argument is in the toolInfo structure.  Arguments dealing with
        # the stream may not be contained.
        inInfo    = True if argument in argumentInformation[tool] else False
        isReplace = False
        if tool in self.addedInformation:
          if argument in self.addedInformation[tool]: isReplace = True

        if argument == 'json parameters':
  
          # If a json file is being used to generate parameters, the configuration file
          # needs to contain a 'json block' argument.  This tells the script the name of
          # the block in the json file from which to extract parameters.
          jsonBlock = linkage[task]['json parameters']['json block']
          print(" \\\n\t`python $(GKNO_PATH)/getParameters.py ", end = '', file = self.makeFilehandle)
          print(self.arguments[task][internalLoopCounter][argument][0], ' ', jsonBlock, '`', sep = '', end = '', file = self.makeFilehandle)

        # If the argument is a replacement to handle a stream, do not interrogate the
        # tl.toolInfo structure as it doesn't contain the required values (the other
        # entries contain information on flags, data types etc).
        elif isReplace:

          # If the line is blank, do not print to file.
          if not ((argument == '') and (self.arguments[task][internalLoopCounter][argument] == '')):
            if self.arguments[task][internalLoopCounter][argument][0] == 'no value': print(" \\\n\t", argument, sep = '', end = '', file = self.makeFilehandle)
            else: print(" \\\n\t", argument, delimiter, self.arguments[task][internalLoopCounter][argument][0], sep = '', end = '', file = self.makeFilehandle)
        else:
  
          # Some tools do not require a --argument or -argument in front of each value,
          # but just demand a particular order.  The configuration file contains an
          # argument for these for bookkeeping purposes, but they should not be printed
          # to the command line. Also, commands can be included for instructing gkno to
          # print to stdout (e.g. use '>') or stderr ('2>').
          hideArgument = False
          writeNothing = False

          #FIXME useCat is a temporary fix for redirecting to a file.  Currently a redirect
          # from certain tools fails with the 'could not open stdout for writing' error.
          # For these tools, instead of redirecting to stdout out directly, the output is
          # piped through cat solving the problem, but inelegantly.
          useCat       = False
          useStdout    = False
          useStderr    = False
          if inInfo:
            if 'modify argument name on command line' in argumentInformation[tool][argument]:
              hideArgument = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'hide' else False
              useStdout    = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'stdout' else False
              useStderr    = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'stderr' else False
              writeNothing = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'omit' else False

            # If the tool is listed as outputting to the stream, but appears at the end of a loop
            # or as a standalone task, check that there is an option defining an output to write to.
            if 'if not output to stream' in argumentInformation[tool][argument]:
              useCat    = True
              useStdout = True

            if argumentInformation[tool][argument]['type'] == 'flag': isFlag = True

          # If the command is a flag, check if the value is 'set' or 'unset'.  If 'set',
          # write out the command.
          if isFlag:
            if self.arguments[task][internalLoopCounter][argument][0] == 'set': print(" \\\n\t", argument, sep = '', end = '', file = self.makeFilehandle)
          else:

            # Some command lines allow multiple options to be set and the command line can
            # therefore be repeated multiple times.  If the defined value is a list, this
            # is the case and the command should be written out once for each value in the
            # list.
            for value in self.arguments[task][internalLoopCounter][argument]:
  
              # If the value contains whitespace, include quotation marks around the value.
              if isinstance(value, basestring):
                if ' ' in value: value = str('"') + value + str('"')

              if hideArgument: print(" \\\n\t", value, sep = '', end = '', file = self.makeFilehandle)
              elif writeNothing: pass
              elif useCat: print(" \\\n\t| cat > ", value, sep = '', end = '', file = self.makeFilehandle)
              elif useStdout: print(" \\\n\t> ", value, sep = '', end = '', file = self.makeFilehandle)
              elif useStderr: print(" \\\n\t2> ", value, sep = '', end = '', file = self.makeFilehandle)
              else: print(" \\\n\t", argument, delimiter, value, sep = '', end = '', file = self.makeFilehandle)
  
        if task     != taskBlock[-1]: lineStart = " \\\n\t| "
        firstCommand = False

    # Write the stdout and stderr to file.
    if timing == 'set': print(') \\', file = self.makeFilehandle)
    else: print(' \\', file = self.makeFilehandle)
    if not useStdout: print("\t", self.redirect, ' ', self.outputID, '.stdout \\', sep = '', file = self.makeFilehandle)
    print("\t2", self.redirect, ' ', self.outputID, '.stderr', sep = '', file = self.makeFilehandle)
    print("\t@echo -e \"completed successfully.\"", sep = '', file = self.makeFilehandle)

  # Write initial information to the Makefile.
  def writeInitialInformation(self, taskToTool, taskBlock, iLoopIteration):
    if iLoopIteration == 0:
      if len(taskBlock) > 1:
        print('### Command line information for the following set of piped tools:', sep = '', file = self.makeFilehandle)
        for task in taskBlock:
          tool = taskToTool[task]
          print('###    ', task, ' (', tool, ')', sep = '', file = self.makeFilehandle)
      else:
        task = taskBlock[0]
        tool = taskToTool[task]
        print('### Command line information for ', task, ' (', tool, ')', sep = '', file = self.makeFilehandle)
    else: print(file = self.makeFilehandle)

  # Get the path of the executable.
  def getExecutablePath(self, sourcePath, paths, taskToTool, taskBlock, iLoopIteration):
    er = errors()

    if iLoopIteration == 0:
      self.pathList = []
      for task in taskBlock:
        tool = taskToTool[task]
        path = paths[tool]
  
        # Only print out the path if it isn't defined as 'null'.  Unix commands will
        # be defined as 'null' as they do not need to include a path, for example.
        pathVariable = ''
        if path != 'no path':
          pathVariable = (tool.replace(" ", "_")  + '_PATH').upper()
          print(pathVariable, "=$(TOOL_BIN)/", path, sep = "" , file = self.makeFilehandle)
  
        self.pathList.append(pathVariable)

  # Write the outputs for the task block to the Makefile. 
  def writeOutputsToMakefile(self, outputBlock): 
 
    #TODO Handle phony targets
    # Check if the target is a phony target.  If so, define the phony target. 
    if len(outputBlock) == 0: 
      phonyTarget = 'phonyTarget_' + str(self.phonyTargetID)
      self.phonyTargetID += 1
      print(phonyTarget, sep = '', end = ': ', file = self.makeFilehandle)
    else:

      # Determine how many output files there are.  If there are multiple output files, 
      # do not include them all on the same line.  If parallel execution of the makefile
      # is being used, this could lead to multiple instances of the same task being run.
      # Instead, Just add the first of the output files to the command line.  The remaining
      # output files are handled after the recipe has been written.  The remaining files are
      # listed as output files dependent on this first output file.
      self.primaryOutput = outputBlock.pop(0)
      print(self.primaryOutput, sep = '', end = ': ', file = self.makeFilehandle)

  # Write the dependencies for the task block to the Makefile.
  def writeDependenciesToMakefile(self, dependencyBlock):
    for counter, output in enumerate(dependencyBlock):

      # Some tools allow multiple inputs and so the 'output' variable may be a 
      # list of files.  If so, write out each file individually.
      isList = True if isinstance(output, list) else False
      endOfLine = ' ' if ( (counter + 1) < len(dependencyBlock)) else "\n"
      if isList:
        for filename in output: print(filename, end = ' ', file = self.makeFilehandle)
        print('', end = endOfLine, file = self.makeFilehandle)
      else:
        print(output, end = endOfLine, file = self.makeFilehandle)

  def handleAdditionalOutputs(self, outputs, dependencies):
    if len(outputs) != 0:
      print(file = self.makeFilehandle)
      for counter, output in enumerate(outputs):
        print(output, end = '', file = self.makeFilehandle)
        if counter + 1 == len(outputs): print(':', end = '', file = self.makeFilehandle)
        print(' ', end = '', file = self.makeFilehandle)

      # In order to avoid triggering multiple instances of the same task, these additional
      # output files need to include the primaryOutput as a dependent as well as all files
      # on which the primary output depends.  So, write the primaryOutput (i.e. the one 
      # that was used in the recipe) and all the files on which this depends as dependent.
      print(self.primaryOutput, end = '', file = self.makeFilehandle)
      if len(dependencies) != 0:
        for dependent in dependencies: print(' ', dependent, sep = '', end = '', file = self.makeFilehandle)
      print(file = self.makeFilehandle)
  
      # Now write the recipe to check if these files need regenerating.
      print("\t@if test -f $@; then \\", file = self.makeFilehandle)
      print("\t  touch $@; \\", file = self.makeFilehandle)
      print("\telse \\", file = self.makeFilehandle)
      print("\t  rm -f ", self.primaryOutput, "; \\", sep = '', file = self.makeFilehandle)
      print("\t  $(MAKE) -f ", self.filename, ' ', self.primaryOutput, '; \\', sep = '', file = self.makeFilehandle)
      print("\tfi", file = self.makeFilehandle)

  # If any intermediate files are marked as to be deleted after this task, put in the
  # command to delete them.
  def addFileDeletion(self, tasks, iLoopIteration):
    for task in tasks:
      if task in self.deleteFiles:
        print(file = self.makeFilehandle)
        for fileToDelete in self.deleteFiles[task][iLoopIteration]:
          print("\t@rm -f ", fileToDelete, sep = '', file = self.makeFilehandle)


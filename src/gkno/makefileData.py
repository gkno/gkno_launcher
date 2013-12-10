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
  def writeExecutablePaths(self, graph, config, fileHandle, taskList):
    print('### Executable paths.', file = fileHandle)
    for task in taskList:
      tool                       = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      pathVariable               = (tool.replace(" ", "_")  + '_PATH').upper()
      self.executablePaths[tool] = config.nodeMethods.getGraphNodeAttribute(graph, task, 'path')

      # Some tools (e.g. UNIX commands) have no path and shouldn't be given an executable.
      if self.executablePaths[tool] != 'no path':
        print(pathVariable, "=$(TOOL_BIN)/", self.executablePaths[tool], sep = "" , file = fileHandle)
    print(file = fileHandle)

  # Search through the tasks in the workflow and check for tasks outputting to a stream. Generate a
  # list of tasks for generating the makefiles. Each entry in the list should be a list of all tasks
  # that are piped together (in a pipeline with no streaming, this list will just be the workflow).
  def determineStreamingTaskList(self, graph, config, tasks):
    taskList     = []
    currentTasks = []
    for task in tasks:
      currentTasks.append(task)
      if not config.nodeMethods.getGraphNodeAttribute(graph, task, 'outputToStream'):
        taskList.append(currentTasks)
        currentTasks = []

    return taskList

  # Loop over all of the tasks in the workflow and write out all of the information for
  # executing each task.
  def writeTasks(self, graph, config, makefileName, fileHandle, taskList, deleteList, iteration):

    # Loop over the tasks. Note that each entry in taskList is a list of tasks that are piped
    # together. If there are no pipes, then the list will only contain a single task.
    for tasks in taskList:

      # Define the minimum and maximum iteration values. If a single iteration is being performed,
      # this will be the same, but if there is an internal loop, all the iterations need to be
      # written to the same file. Use the first task in tasks to define this.
      if iteration == 'all':
        minIteration = 1
        maxIteration = config.nodeMethods.getGraphNodeAttribute(graph, tasks[0], 'numberOfDataSets')
      else:
        minIteration = iteration
        maxIteration = iteration

      # Loop over the iterations.
      for counter in range(minIteration, maxIteration + 1):

        # Loop over all the tasks in this piped grouping to find the dependencies and outputs. An output that
        # is piped into the next tool is not an output and shouldn't be considered. Similarly, an input stream
        # should not be included.
        taskDependencies = []
        taskOutputs      = []
        for task in tasks:
          for dependency in config.getTaskDependencies(graph, task, iteration = counter): taskDependencies.append(dependency)
          for output in config.getTaskOutputs(graph, task, iteration = counter): taskOutputs.append(output)

        # Write out some text to the makefile.
        if len(tasks) == 1:
          print('### Command line information for ', task, ' (',  config.pipeline.tasks[task], ').', sep = '', file = fileHandle)
        else:
          print('### Command line information for the following streamed tasks: ', file = fileHandle)
          for task in tasks:
            print('###\t', task, ' (', config.pipeline.tasks[task], ')', sep = '', file = fileHandle)
  
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
        if len(tasks) == 1: print('\t@echo -e "Executing task: ', task, '...\c"', sep = '', file = fileHandle)
        else:
          text = '\t@echo -e "Executing piped tasks: '
          for task in tasks[:-1]: text += task + ', '
          text += tasks[-1]
          print(text, file = fileHandle, end = '')
          print('...\c"', file = fileHandle)
  
        # Loop over all of the tasks and write the executable commands.
        for task in tasks:

          # Determine if this task outputs to the stream. If so, just write a pipe and move on to the
          # next command.
          if task == tasks[0]: print('\t@', end = '', file = fileHandle)
          else: print('\t| ', end = '', file = fileHandle)

          stdoutUsed = self.writeCommand(graph, config, fileHandle, task, counter)
  
          # If the task does not output to a stream, finish the command.
          if task == tasks[-1]:
  
            # Write output and errors to the stdout and stderr files.
            self.writeStdouts(stdoutUsed, fileHandle)
    
            # Write that the task complete successfully.
            self.writeComplete(fileHandle)

        # Check if there are files that can be deleted at this point in the pipeline. If so, include
        # a command in the makefile to delete them.
        self.deleteFiles(tasks, deleteList, fileHandle)
  
        # If there are additional output files from this task, include an additional rule in the
        # makefile to check on their existence.
        if len(taskOutputs) != 0: self.writeRuleForAdditionalOutputs(makefileName, fileHandle, taskOutputs, primaryOutput, taskDependencies)

  # Write commands to delete files that are no longer required by the pipeline.
  def deleteFiles(self, tasks, deleteList, fileHandle):
    for task in tasks:
      if task in deleteList:
        print('### Remove files no longer required by the pipeline.', file = fileHandle)
        for filename in deleteList[task]: print('\t@rm -f ', filename, sep = '', file = fileHandle)
        print(file = fileHandle)

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
    tool       = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    precommand = config.nodeMethods.getGraphNodeAttribute(graph, task, 'precommand')
    modifier   = config.nodeMethods.getGraphNodeAttribute(graph, task, 'modifier')

    # Add the precommand if one exists.
    if precommand: print(precommand, end = ' ', file = fileHandle)

    # Write the path of the executable (if there is one - bash tools, for example, will not).
    if self.executablePaths[tool] != 'no path': print('$(', (tool + '_path').upper(), ')/', sep = '', end = '', file = fileHandle)

    # Print the executable.
    print(config.nodeMethods.getGraphNodeAttribute(graph, task, 'executable'), end = ' ', file = fileHandle)

    # Add the command modifier if one exists.
    if modifier: print(modifier, end = ' ', file = fileHandle)
    print('\\', sep = '', file = fileHandle)

    # Find all of the arguments for this task.
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
         # print('error in make.writeCommand', task, argument)
         # self.errors.terminate()
         valueList = {}

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
                    print(task, fileNodeID, config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'argument'), valueList)
                    self.errors.terminate()

              # TODO DO I NEED TO LOOK AT OUTPUTS?

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
    argumentOrder = config.tools.getGeneralAttribute(tool, 'argumentOrder')
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

    # Parse all of the option nodes.
    for nodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
      argument       = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'argument')
      values         = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
      isFile         = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'isFile')
      isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isFilenameStub')

      # If the option node points to a file and not a filename stub, do not include this value. All
      # non filename stub files will be accounted for using the file nodes,
      if (not isFile) or (isFile and isFilenameStub):
        if argument not in arguments: arguments[argument] = []
        arguments[argument].append((nodeID, values))

    # Now parse all of the file nodes and store the arguments for non filename stub files.
    for nodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
      isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isFilenameStub')
      if not isFilenameStub:
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
        argument     = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'argument')
        values       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        if argument not in arguments: arguments[argument] = []
        arguments[argument].append((optionNodeID, values))

    # Now parse all of the sucessor file nodes and store the arguments for non filename stub files.
    for nodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
      isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, task, nodeID,'isFilenameStub')
      optionNodeID   = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
      if not isFilenameStub:
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
        argument     = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'argument')
        values       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        if argument not in arguments: arguments[argument] = []
        arguments[argument].append((optionNodeID, values))

    return arguments

#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import gknoErrors
from gknoErrors import *

import os
import platform
import sys

class makefileData:
  def __init__(self):

    # Define the errors class.
    self.errors                 = gknoErrors()

    # Define the output path.
    self.outputPaths = []

    # Define information on the makefile structure. This is information on the number of phases 
    # and how many makefile each phase has.
    self.makefilesInPhase  = {}
    self.makefileNames     = {}
    self.makefileStructure = {}
    self.numberOfPhases    = 1
    self.tasksInPhase      = {}

    # Store the paths of all executable files.
    self.executablePaths = {}

    # Define a structure to hold missing files and one for files that need to be
    # removed prior to execution.
    self.missingFiles = []

    # Keep track of phony targets.
    self.phonyTargets = []

    # Check the platform. If 'Darwin', do not use the '-e' modifier in echo commands.
    if platform.system() == 'Darwin': self.echoModifier = ''
    else: self.echoModifier = '-e '

  # Generate the makefile for a tool/pipeline with a single set of data or an internal loop.
  # Only one makefile is required in this case.
  def generateSingleMakefile(self, graph, config, runName, sourcePath, gknoCommitID, outputPaths, version, date):

    # Set the output path for use in the makefile generation.
    self.getOutputPath(graph, config, outputPaths)

    # Open the makefile.                          
    makefileName             = runName + '.make'
    self.makefileNames[1]    = [makefileName]
    makefileHandle           = self.openMakefile(makefileName)
    self.makefilesInPhase[1] = 1

    # Write header information to the makefile if this hasn't already been done..
    self.writeHeaderInformation(sourcePath, runName, makefileName, makefileHandle, 1, 'all', version, date, gknoCommitID)

    # Write out the executable paths for all of the tools being used in the makefile.
    self.writeExecutablePaths(graph, config, makefileHandle, config.pipeline.workflow)

    # Detemine which files are dependencies, outputs and intermediate files.
    graphDependencies  = config.getGraphDependencies(graph, config.pipeline.workflow, key = 'all')
    graphOutputs       = config.getGraphOutputs(graph, config.pipeline.workflow, key = 'all')
    graphIntermediates = config.getGraphIntermediateFiles(graph, config.pipeline.workflow)

    # Write the intermediate files to the makefile.
    self.writeIntermediateFiles(makefileHandle, graphIntermediates, 'all')

    # Write the pipeline outputs to the makefile.
    self.writeOutputFiles(graph, config, makefileHandle, graphOutputs)

    # Search through the tasks in the workflow and check for tasks outputting to a stream. Generate a
    # list of tasks for generating the makefiles. Each entry in the list should be a list of all tasks
    # that are piped together (in a pipeline with no streaming, this list will just be the workflow).
    taskList = self.determineStreamingTaskList(graph, config, config.pipeline.workflow)

    # Write out the information for running each task.
    self.writeTasks(graph, config, makefileName, makefileHandle, taskList, 'all', graphIntermediates)

    # Close the makefile in preparation for execution. Again, if an internal loop is being run, the
    # file should only be closed at the end of the pipeline.
    self.closeMakefile(makefileHandle)

    # Check that all of the input files exist.
    self.checkFilesExist(graph, config, graphDependencies, sourcePath)

  # If multiple runs were requested, there are multiple makefiles to be generated.
  def generateMultipleMakefiles(self, graph, config, runName, sourcePath, gknoCommitID, outputPaths, version, date):

    # Determine the structure of the pipeline and break it up into phases and iterations.
    # Each phase and iteration within it needs its own makefile.
    self.determineMakefileStructure(graph, config)

    # Set the names of the makefiles.
    self.setMakefilenames(runName)

    # Set the output path for use in the makefile generation.
    self.getOutputPath(graph, config, outputPaths)

    # Loop over the phases and iterations and construct the makefiles.
    for phaseID in range(1, len(self.makefileNames) + 1):

      # Detemine intermediate files for this phase. The intermediate files are put in a dictionary
      # with the data set iteration as the key.
      graphIntermediates = config.getGraphIntermediateFiles(graph, self.tasksInPhase[phaseID])

      for iteration, makefileName in enumerate(self.makefileNames[phaseID]):
                                                      
        # The iteration needs to be sent to the various following routines in order to pick the files
        # necessary for the particular makefile.
        key = iteration + 1

        # Open the makefile.                          
        makefileHandle = self.openMakefile(makefileName)

        # Write header information to the makefile if this hasn't already been done..
        self.writeHeaderInformation(sourcePath, runName, makefileName, makefileHandle, phaseID, key, version, date, gknoCommitID)

        # Write out the executable paths for all of the tools being used in the makefile.
        self.writeExecutablePaths(graph, config, makefileHandle, self.tasksInPhase[phaseID])

        # Detemine which files are dependencies and outputs files.
        graphDependencies  = config.getGraphDependencies(graph, self.tasksInPhase[phaseID], key = key)
        graphOutputs       = config.getGraphOutputs(graph, self.tasksInPhase[phaseID], key = key)

        # Write the intermediate files to the makefile.
        self.writeIntermediateFiles(makefileHandle, graphIntermediates, key)

        # Write the pipeline outputs to the makefile.
        self.writeOutputFiles(graph, config, makefileHandle, graphOutputs)

        # Search through the tasks in the workflow and check for tasks outputting to a stream. Generate a
        # list of tasks for generating the makefiles. Each entry in the list should be a list of all tasks
        # that are piped together (in a pipeline with no streaming, this list will just be the workflow).
        taskList = self.determineStreamingTaskList(graph, config, self.tasksInPhase[phaseID])

        # Write out the information for running each task.
        self.writeTasks(graph, config, makefileName, makefileHandle, taskList, key, graphIntermediates)

        # Close the makefile in preparation for execution. Again, if an internal loop is being run, the
        # file should only be closed at the end of the pipeline.
        self.closeMakefile(makefileHandle)

        # Check that all of the input files exist.
        self.checkFilesExist(graph, config, graphDependencies, sourcePath)

  # Define the makefile structure. This involved identifying which tasks can be run in parallel
  # and how many data sets each task has. This results in breaking the pipeline into phases
  # which need to be executed sequentially, with iterations within each phase that can be run
  # in parallel.
  def determineMakefileStructure(self, graph, config):
    firstTask         = True
    self.currentPhase = 1
    for task in config.pipeline.workflow:

      # Determine the number of iterations of input and output files.
      numberOfInputDataSets  = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getPredecessorFileNodes(graph, task))
      numberOfOutputDataSets = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getSuccessorFileNodes(graph, task))

      # Check if any of the arguments have multiple iterations of data.
      numberOfInputArgumentIterations = self.getNumberOfDataSets(graph, config, task, config.nodeMethods.getPredecessorOptionNodes(graph, task))

      # If there are multiple sets of input arguments, check the number of input and output files. If there
      # are only one set of input and output data, the number of input and output data sets are equal to
      # the number of input argument iterations.
      if numberOfInputArgumentIterations != 1:
        if numberOfInputDataSets == 1 and numberOfOutputDataSets == 1:
          numberOfInputDataSets  = numberOfInputArgumentIterations
          numberOfOutputDataSets = numberOfInputArgumentIterations

      #if numberOfOutputDataSets > numberOfInputDataSets:
      #  #TODO ERROR
      #  print('makefileData.determineMakefileStructure')
      #  print('More output data sets than input data sets.')
      #  self.errors.terminate()

      # If this is the first task in the workflow, determine how many makefiles are required
      # for this task. This is the number of input or output data sets. Set the current makefiles
      # to these.
      if firstTask:
        self.numberOfFilesinPhase            = max(numberOfInputDataSets, numberOfOutputDataSets)
        self.makefileStructure[task]         = (self.currentPhase, self.numberOfFilesinPhase)
        self.makefilesInPhase[1]             = self.numberOfFilesinPhase
        self.tasksInPhase[self.currentPhase] = []
        firstTask                            = False
      else:

        # If there are more input data sets than output data sets, this must be the start of a 
        # new phase.
        if numberOfInputDataSets > numberOfOutputDataSets:

          # If the number of input data sets is not equal to the number of files in the current phase,
          # an error has occured.
          if numberOfInputDataSets != self.numberOfFilesinPhase:
            #TODO ERROR
            print('makefileData.determineMakefileStructure')
            print('Number of input data sets is different to the number of files in the phase.')
            print(numberOfInputDataSets, self.numberOfFilesinPhase)
            self.errors.terminate()
 
          # If the number of output data sets is smaller than the number of input data sets, there
          # must be a single output data set only. This essentially means that the task is taking the
          # outputs from multiple tasks and using them all to run. If this is the case, there must
          # be a single output data set.
          if numberOfOutputDataSets != 1:
            #TODO ERROR
            print('makefileData.determineMakefileStructure')
            print('A greedy task is accepting multiple inputs, but has more than one output data set.')
            self.errors.terminate()

          self.createNewPhase(1)

        # If the number of input data sets is equal to the number of output data sets, whether this
        # is the start of a new phase or not depends on the number of data sets output by the previous
        # phase.
        else:

          # If the number of input data sets differs from the number of output data sets from the
          # last task, this is the start of a new phase.
          if numberOfInputDataSets != self.numberOfFilesinPhase: self.createNewPhase(numberOfInputDataSets)

        # Add this task to the makefile structure.
        self.makefileStructure[task] = (self.currentPhase, self.numberOfFilesinPhase)
        if self.numberOfFilesinPhase != 1: config.nodeMethods.setGraphNodeAttribute(graph, task, 'hasMultipleIterations', True)
      self.tasksInPhase[self.currentPhase].append(task)

  # Get the number of data sets for a node.
  def getNumberOfDataSets(self, graph, config, task, nodeIDs):
    finalNumber = 0

    for nodeID in nodeIDs:
      optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
      numberOfDataSets = len(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))
      try: argument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
      except: argument = config.edgeMethods.getEdgeAttribute(graph, task, optionNodeID, 'longFormArgument')

      # Check to see if this particular argument is greedy.
      isGreedy = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isGreedy')
      if isGreedy: numberOfDataSets = 1
      if numberOfDataSets > finalNumber: finalNumber = numberOfDataSets

    return finalNumber

  # Create a new phase in the makefile structure.
  def createNewPhase(self, numberOfFiles):
    self.currentPhase += 1
    self.tasksInPhase[self.currentPhase]     = []
    self.numberOfPhases                      = self.currentPhase
    self.makefilesInPhase[self.currentPhase] = numberOfFiles
    self.numberOfFilesinPhase                = numberOfFiles

  # Set the names of the makefiles to be created.  If this is a single run, a single name
  # is required, otherwise, there will be a list of names for each of the created makefiles.
  def setMakefilenames(self, text):
 
    # If there is only a single phase, there is no need for phase information in the makefile
    # name.
    if self.numberOfPhases == 1:
      self.makefileNames[1] = []
      if self.makefilesInPhase[1] == 1: self.makefileNames[1].append(text + '.make')
      else:
        for count in range(1, self.makefilesInPhase[1] + 1): self.makefileNames[1].append(text + '_' + str(count) + '.make')

    # If there are phases, include the phase in the name of the makefiles.
    else:
      for phaseID in range(1, self.numberOfPhases + 1):
        self.makefileNames[phaseID] = []
        if self.makefilesInPhase[phaseID] == 1: self.makefileNames[phaseID].append(text + '_phase_' + str(phaseID) + '.make')
        else:
          for count in range(1, self.makefilesInPhase[phaseID] + 1):
            self.makefileNames[phaseID].append(text + '_phase_' + str(phaseID) + '_' + str(count) + '.make')

  # Get the output path for use with generating the makefiles.
  def getOutputPath(self, graph, config, outputPaths):

    # The output path is stored with the gkno specific nodes. Since the valiues are treated as all other
    # arguments, the value itself is the first (and only) value in the list associated with the first (and
    # only iteration).
    if not outputPaths: self.outputPaths[1] = '$(PWD)'
    else: self.outputPaths = outputPaths

    # If the chosen output path is not the current directory, check to see if the directory exists.
    for iteration in self.outputPaths:
      outputPath = self.outputPaths[iteration]
      if outputPath == '$(PWD)/': outputPath = './'
      if not os.path.isdir(outputPath):
        self.errors.missingOutputDirectory(graph, config, outputPath)
        config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-DO-NOT-EXECUTE', ['set'], write = 'replace')

  # Open the makefile and write the initial information to the file.
  def openMakefile(self, makefileName):
    makefileHandle = open(makefileName, 'w')
    makefileName   = os.path.abspath(makefileName)

    return makefileHandle

  # Write initial information to the makefiles.
  def writeHeaderInformation(self, sourcePath, pipelineName, makefileName, fileHandle, phaseID, iteration, version, date, gknoCommitID):
    print('### gkno Makefile', file = fileHandle)
    print('### Generated using gkno version ', version, ' (', date, ')', sep = '', file = fileHandle)
    print('### (git commit: ', gknoCommitID, ')', sep = '', file = fileHandle)
    print('### Running pipeline:', pipelineName, file = fileHandle)

    # Write phase information if there is more than one phase in the pipeline.
    if self.numberOfPhases != 1: print('### Phase ', str(phaseID), ' of ', str(self.numberOfPhases), sep = '', file = fileHandle)

    # If this phase has multiple data sets, write out which set this is.
    if self.makefilesInPhase[phaseID] > 1: print('### Data set ', str(iteration), ' of ', self.makefilesInPhase[phaseID], sep = '', file = fileHandle)

    # If there are multiple iterations, include the iteration in the stdout and stderr names.
    if iteration == 'all': stdoutName = pipelineName
    else: stdoutName = pipelineName + '_' + str(iteration)

    # Get the output path for stdout and stderr.
    if iteration in self.outputPaths: outputPath = self.outputPaths[iteration]
    elif len(self.outputPaths) != 1:
      print('ERROR - makefile.writeHeaderInformation.')
      self.errors.terminate()
    else: outputPath = self.outputPaths[1]

    print(file = fileHandle)
    print('### Paths to tools and resources.', file = fileHandle)
    print('GKNO_PATH=', sourcePath, "/src/gkno", sep = '', file = fileHandle)
    print('TOOL_BIN=', sourcePath, "/tools", sep = '', file = fileHandle)
    print('RESOURCES=', sourcePath + '/resources', sep = '', file = fileHandle)
    print('MAKEFILE_ID=', makefileName.split('/')[-1].split('.')[0], sep = '', file = fileHandle)
    print(file = fileHandle)
    print('### Standard output and errors files.', file = fileHandle)
    print('STDOUT=', outputPath, stdoutName, '.stdout', sep = '', file = fileHandle)
    print('STDERR=', outputPath, stdoutName, '.stderr', sep = '', file = fileHandle)
    print(file = fileHandle)

  # Write out all of the intermediate files.
  def writeIntermediateFiles(self, fileHandle, intermediates, key):
    print('.DELETE_ON_ERROR:', file = fileHandle)
    print('.INTERMEDIATE:', end = ' ', file = fileHandle)
    if intermediates:

      # Write out all intermediates. This is the case when only one makefile is
      # being written.
      if key == 'all':
        for iteration in intermediates:
          for nodeID, intermediateFile in intermediates[iteration]: print(intermediateFile, end = ' ', file = fileHandle)


      # If only intermediates for a particular iteration are required.
      else:
        if key in intermediates:
          for nodeID, intermediateFile in intermediates[key]: print(intermediateFile, end = ' ', file = fileHandle)

    print(file = fileHandle)
    print(file = fileHandle)

  # Write out all of the output files.
  def writeOutputFiles(self, graph, config, fileHandle, outputs):

    # Check if any of the tools in the pipeline (or the single tool being executed) produce
    # no output. If this is the case, the name of the task is added as output in 'all'. This
    # will be identified as a phony target and used as the target for that tool to ensure that
    # it is executed.
    self.phonyTargets = []
    for task in config.pipeline.workflow:
      tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      if config.tools.getGeneralAttribute(tool, 'noOutput'): self.phonyTargets.append(task)

    print('all:', end = ' ', file = fileHandle)

    # Add all phony targets.
    if self.phonyTargets:
      for phonyTarget in self.phonyTargets: print(phonyTarget, end = ' ', file = fileHandle)

    # Add all outputs.
    if outputs:
      for nodeID, outputFile in outputs: print(outputFile, end = ' ', file = fileHandle)
    print(file = fileHandle)
    print(file = fileHandle)

    # If there were phony targets, list these.
    if self.phonyTargets:
      print('.PHONY:', end = ' ', file = fileHandle)
      for phonyTarget in self.phonyTargets: print(phonyTarget, end = ' ', file = fileHandle)
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
      if not config.nodeMethods.getGraphNodeAttribute(graph, task, 'outputStream'):
        taskList.append(currentTasks)
        currentTasks = []

    return taskList

  # Loop over all of the tasks in the workflow and write out all of the information for
  # executing each task.
  def writeTasks(self, graph, config, makefileName, fileHandle, taskList, iteration, graphIntermediates):

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

        # Determine the task in which each intermediate file is last used. This will allow the files to
        # be deleted as early as possible in the pipeline.
        deleteList = {}
        if graphIntermediates: deleteList = config.setWhenToDeleteFiles(graph, graphIntermediates)

        # Loop over all the tasks in this piped grouping to find the dependencies and outputs. An output that
        # is piped into the next tool is not an output and shouldn't be considered. Similarly, an input stream
        # should not be included.
        taskDependencies = []
        taskOutputs      = []
        for task in tasks:
          isGreedy = config.nodeMethods.getGraphNodeAttribute(graph, task, 'isGreedy')
          for dependency in config.getTaskDependencies(graph, task, isGreedy, iteration = counter): taskDependencies.append(dependency)
          for output in config.getTaskOutputs(graph, task, iteration = counter): taskOutputs.append(output)

          # If this is a greedy task and files are to be deleted, include all iterations.
          if task in deleteList and isGreedy: deleteList = self.combineDeleteListIterations(task, deleteList)

        # Write out some text to the makefile.
        if len(tasks) == 1:
          print('### Command line information for ', task, ' (',  config.pipeline.taskAttributes[task].tool, ').', sep = '', file = fileHandle)
        else:
          print('### Command line information for the following streamed tasks: ', file = fileHandle)
          for task in tasks:
            print('###\t', task, ' (', config.pipeline.taskAttributes[task].tool, ')', sep = '', file = fileHandle)
  
        # Due to the vagaries of the makefile operation, if there are multiple outputs, it is
        # not acceptable to just list all of the outputs at the start of the rule. In reality,
        # to ensure proper operation, a single output is listed and then an additional rule is
        # included after the task to check for the existence of the remaining outputs.
        try: primaryOutput = taskOutputs.pop(0)
        except:

          # If there are no taskOutputs, this might be because the task has not output and a phony
          # target exists. Check if this is the case.
          if self.phonyTargets:
            if task in self.phonyTargets: primaryOutput = task
          else:
            hasDirectory = False
            tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
            for toolArgument in config.tools.getArguments(tool):
              if config.tools.getArgumentAttribute(tool, toolArgument, 'isOutput') and \
                 config.tools.getArgumentAttribute(tool, toolArgument, 'isDirectory'):
                hasDirectory = True
                taskOutputs.append('')
 
            if hasDirectory: primaryOutput = taskOutputs.pop(0)
            else: self.errors.noOutputFileGeneratingMakefile(task, config.pipeline.taskAttributes[task].tool)
            #self.errors.noOutputFileGeneratingMakefile(task, config.pipeline.taskAttributes[task].tool)
        print(primaryOutput, end = ': ', file = fileHandle)
  
        # Write out the task dependencies separated by spaces.
        for i in range(0, len(taskDependencies)): print(taskDependencies[i], end = ' ', file = fileHandle)
        print(file = fileHandle)
  
        # Include a line that will echo which task is being run.
        if len(tasks) == 1: print('\t@echo ', self.echoModifier, ' "Executing task: ', task, '...\c"', sep = '', file = fileHandle)
        else:
          text = '\t@echo ' + self.echoModifier + ' "Executing piped tasks: '
          for task in tasks[:-1]: text += task + ', '
          text += tasks[-1]
          print(text, file = fileHandle, end = '')
          print('...\c"', file = fileHandle)
  
        # Loop over all of the tasks and write the executable commands.
        for taskCounter, task in enumerate(tasks):

          # Determine if the input is a stream.
          inputIsStream = True if taskCounter != 0 else False

          # Determine if this task outputs to the stream. If so, just write a pipe and move on to the
          # next command.
          if task == tasks[0]: print('\t@', end = '', file = fileHandle)
          else: print('\t| ', end = '', file = fileHandle)

          stdoutUsed = self.writeCommand(graph, config, fileHandle, task, counter, inputIsStream)
  
          # If the task does not output to a stream, finish the command.
          if task == tasks[-1]:
  
            # Write output and errors to the stdout and stderr files.
            self.writeStdouts(stdoutUsed, fileHandle)
    
            # Write that the task complete successfully.
            self.writeComplete(fileHandle)

        # Check if there are files that can be deleted at this point in the pipeline. If so, include
        # a command in the makefile to delete them.
        self.deleteFiles(tasks, deleteList, counter, fileHandle)
  
        # If there are additional output files from this task, include an additional rule in the
        # makefile to check on their existence.
        if len(taskOutputs) != 0: self.writeRuleForAdditionalOutputs(makefileName, fileHandle, taskOutputs, primaryOutput, taskDependencies)

  # If a task is greedy, ensure that the list of files to delete contains all of the iterations.
  def combineDeleteListIterations(self, task, deleteList):
    newList = []
    for counter in deleteList[task]:
      for filename in deleteList[task][counter]:
        newList.append(filename)

    deleteList[task]    = {}
    deleteList[task][1] = newList

    return deleteList

  # Write commands to delete files that are no longer required by the pipeline.
  def deleteFiles(self, tasks, deleteList, counter, fileHandle):
    for task in tasks:
      if task in deleteList:
        if counter in deleteList[task]:
          print('### Remove files no longer required by the pipeline.', file = fileHandle)
          for filename in deleteList[task][counter]: print('\t@rm -f ', filename, sep = '', file = fileHandle)
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

    # Add the primaryOutput to the list of dependencies. This is the file that is listed as the output for
    # the rule. If running with multiple threads and none of the files exist, the original rule is executed
    # since the output file does not exist. This rule for the additional outputs is the executed in parallel
    # since none of these additional files exist either. By including the primaryOutput as a dependency, we
    # ensure that the original rule gets to run first and this check isn't performed until it has been
    # completed.
    print(primaryOutput, file = fileHandle)

    #print(file = fileHandle)
    print('\t@if test -f $@; then \\', file = fileHandle)
    print('\t  touch $@; \\', file = fileHandle)
    print('\telse \\', file = fileHandle)
    print('\t  rm -f ', primaryOutput, "; \\", sep = '', file = fileHandle)
    print('\t  $(MAKE) --no-print-directory -f ', makefileName, ' ', primaryOutput, '; \\', sep = '', file = fileHandle)
    print('\tfi', file = fileHandle)
    print(file = fileHandle)

  # Write the command line for the current task.
  def writeCommand(self, graph, config, fileHandle, task, iteration, inputIsStream):
    stdoutUsed = False

    # Define some tool attributes. These are extracted from the task node.
    tool       = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    precommand = config.nodeMethods.getGraphNodeAttribute(graph, task, 'precommand')
    modifier   = config.nodeMethods.getGraphNodeAttribute(graph, task, 'modifier')

    # If the input is not a piped stream, check to see if the tool demands a stream as input. If
    # so, the input file can be streamed as part of the command.
    if not inputIsStream:
      if config.tools.getGeneralAttribute(tool, 'inputIsStream'):

        # Set the inputIsStream, since the input is required to be a stream.
        inputIsStream = True

        # Determine which of the tools commands accepts the streaming input.
        streamArguments = []
        for fileNodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
          longFormArgument = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'longFormArgument')
          if config.tools.getArgumentAttribute(tool, longFormArgument, 'isStream'):
            streamArguments.append(longFormArgument)
            streamNodeID = fileNodeID

        # If no or multiple argument are identified as the stream accepting argument, terminate.
        if len(streamArguments) == 0: self.errors.noArgumentsAcceptingStream(task, tool, config.isPipeline)
        elif len(streamArguments) > 1: self.errors.multipleArgumentsAcceptingStream(task, tool, streamArguments, config.isPipeline)
        
        # Ensure that files have been defined for the stream.
        values = config.nodeMethods.getGraphNodeAttribute(graph, streamNodeID, 'values')
        if not values:
          if config.isPipeline:

            # TODO ERROR
            print('ERROR - makefile.writeCommand')
            self.errors.terminate()
            #self.errors.noFilesForPipelineStream(task, tool)
          else:
            shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, streamNodeID, task, shortFormArgument)
            self.errors.noFilesForToolStream(task, streamArguments[0], shortFormArgument)

        # Ensure that there is only a single value for this argument.
        filenames = values[iteration] if iteration in values else values[0]

        #TODO ERROR
        if len(filenames) == 0:
          print('ERROR - makefile.writeCommand - Number of files.')
          self.errors.terminate()

        elif len(filenames) > 1:
          print('ERROR - makefile.writeCommand - Number of files.')
          self.errors.terminate()

        # Write the file out to the stream.
        print('< ', filenames[0], ' \\', sep = '', file = fileHandle)
        print('\t', end = '', file = fileHandle)

    # Check if timing information is required.
    hasTiming         = True if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-TIMING', 'values')[1][0] == 'set' else False
    hasAdvancedTiming = True if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-TIMING-ADVANCED', 'values')[1][0] == 'set' else False
    if hasAdvancedTiming: print('(/usr/bin/time -v', end = ' ', file = fileHandle)
    elif hasTiming: print('(time ', end = ' ', file = fileHandle)

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

    # Check if there are any additional arguments for the tool used for this task that have a command
    # for execution at run time. It is possible that, while this argument was nort supplied on the
    # command line, it can be included if the command to execute has all the necessary values.
    arguments = self.getToolArgumentsWithCommands(graph, config, task, tool, arguments)

    # Check if the argument need to be written in any particular order. If not, generate the
    # order randomly. It is possible that there are arguments with no value. This is because
    # the argument order will contain all of the argument for the tool, but they might not all
    # be set. Remove any of these argument from the argumentOrder structure.
    argumentOrder = self.defineArgumentOrder(config, tool, arguments)

    # Write the arguments to the makefile.
    for counter, argument in enumerate(argumentOrder):

      # Loop over the nodes for this argument.
      for nodeID, values in arguments[argument]:

        # If this is not really an argument, but a request to read argument information from a
        # json file, this needs to be handled.
        if config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'readJson'):
          if iteration in values: valueList = values[iteration]
          elif iteration != 1: valueList = values[1]
          else: valueList = {}
          for value in valueList:
            executable = config.nodeMethods.getGraphNodeAttribute(graph, task, 'executable')
            print('\t`python $(GKNO_PATH)/getParameters.py ', value, ' ', executable, '` \\', sep = '', file = fileHandle)

        # Deal with actual arguments.
        else:

          # Determine if this argument is a flag or a file.
          isFlag    = True if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'dataType') == 'flag' else False
          isFile    = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'isFile')
          isGreedy  = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isGreedy')
  
          # If this argument is greedy, put all values into the first iteration. If the iteration parameter
          # is not equal to 1, fail, since the number of data sets should have been set to one given that the
          # argument is greedy.
          if isGreedy and len(values) != 1:
            if iteration != 1:
              #TODO ERROR
              print('makefileData.writeCommand')
              print('Greedy argument, but dealing with other than the 1st iteration')
              self.errors.terminate()
  
            valueList = []
            for iterationCount in values:
              for value in values[iterationCount]: valueList.append(value)
  
          # Deal with arguments that are not greedy.
          else:
  
            # If the iteration exists, put the values into valueList.
            if iteration in values: valueList = values[iteration]
  
            # If the iteration does not exist, use the value from the first iteration (assuming that it
            # exists).
            elif iteration != 1 and values: valueList = values[1]
            else: valueList = {}
  
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

          # If the input to this task is a stream and this argument has specific instructions for
          # this case, ensure that the command is properly handled.
          useArgument = None
          if inputIsStream and config.tools.getArgumentAttribute(tool, argument, 'inputStream'):
            includeArgument, useArgument, useValue = self.checkInputStream(config, tool, argument, includeArgument)

          # If the option refers to a file, then check, whether the option is a filename stub. Since the same
          # option can point to multiple tasks and the option can be a filename stub for one task, but a file
          # for another, determine this using the edge describing the individual argument. If the option is a
          # filename stub, use the values attached to the option node. If it isn't, find the associated file
          # node and use the values from there.
          if isFile:
            isPredecessor = config.nodeMethods.isPredecessor(graph, nodeID, task)
            if isPredecessor: isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isFilenameStub')
            else: isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'isFilenameStub')
            if not isFilenameStub:
              for fileNodeID in config.nodeMethods.getAssociatedFileNodeIDs(graph, nodeID):
  
                # Check that this file node points into or from the current task. Since this option may have been
                # associated with a filename stub, not all of the associated files are necessarily required by
                # this task.
                if config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'isInput'):
                  isAssociated = config.edgeMethods.checkIfEdgeAssociatedWithArgument(graph, fileNodeID, task, argument)
  
                  # Check that the iteration exists in the values of associated file nodes. Again, if not, use the
                  # values in the first iteration or all values if the argument is greedy.
                  if isAssociated:
                    fileValues = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')

                    # If the command has values.
                    if fileValues:
                      commandLineArgument = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'commandLineArgument')
    
                      # Deal with greedy arguments.
                      if isGreedy:
                        valueList = []
                        for iterationCount in fileValues:
                          for value in fileValues[iterationCount]: valueList.append(value)
    
                      # Deal with non greedy arguments.
                      else:
                        if iteration in fileValues: valueList = fileValues[iteration]
                        elif iteration != 1: valueList = fileValues[1]
                        else:
    
                          # TODO ERROR
                          print('Iteration not associated with file node values - make.writeCommand')
                          print(task, fileNodeID, config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument'), valueList)
                          self.errors.terminate()
  
            # Filename stubs.
            else:

              # Some arguments are listed as file name stubs, but still require the extension. In this cases,
              # ensure that the values all have the extension attached.
              tool       = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
              extensions = config.tools.getArgumentAttribute(tool, argument, 'extensions')
              if extensions != ['no extension']:

                # Modify the values.
                modifiedValues = []
                for value in valueList:

                  # Check if the value already has an allowed extension.
                  givenExtension = str('.') + str(value.split('.')[-1])
                  if givenExtension not in extensions: modifiedValues.append(value + extensions[0])
                  else: modifiedValues.append(value)

                valueList = deepcopy(modifiedValues)
                 
                # TODO DO I NEED TO LOOK AT OUTPUTS?

          # Determine if the value is to be contained in qutotaion marks.
          inQuotations = config.tools.getArgumentAttribute(tool, argument, 'inQuotations')
  
          # Write the arguments and or values to the makefile.
          for valueCounter, value in enumerate(valueList):

            # If timing information is being generated, the last argument needs to finish with
            # the close parenthesis.
            endText = ')' if (counter + 1 == len(argumentOrder)) and (valueCounter + 1 == len(valueList)) and (hasTiming or hasAdvancedTiming) else ''

            # If anything needs to be written to the makefile, write it.
            if includeArgument:
  
              # Determine the argument delimiter for this tool.
              delimiter = config.nodeMethods.getGraphNodeAttribute(graph, task, 'delimiter')

              # Determine if this argument is supposed to be written to the command line without a path. If not,
              # strip, the path from the value.
              if not config.tools.getArgumentAttribute(tool, argument, 'includePathOnCommandLine'):
                if '/' in value: value = value.split('/')[-1]

              # Ensure that Boolean values are in lower case.
              if isinstance(value, bool):
                if value: value = 'true'  
                else: value = 'false'

              # Modify the value to include qutation marks if necessary.
              if inQuotations: value = str('"') + str(value) + str('"')

              # If the argument has been modified due to receiving an input stream, use the given argument.
              if useArgument:

                # If the argument to be used is listed as none, just write the value.
                if useArgument == 'none': print('\t', useValue, endText, ' \\', sep = '', file = fileHandle)

                # If the argument is listed as 'original', use the same argument, but the value may be modified.
                elif useArgument == 'original': print('\t', commandLineArgument, delimiter, useValue, endText, ' \\', sep = '', file = fileHandle)

                # For any other value, use the value given in the configuration file.
                else: print('\t', useArgument, delimiter, useValue, endText, ' \\', sep = '', file = fileHandle)

              # Check if the argument is an output that writes to standard out.
              elif config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'stdout':
                print('\t>> ', value, endText, ' \\', sep = '', file = fileHandle)
                stdoutUsed = True
  
              # If the argument should be hidden, only write the value.
              elif config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'hide':
                print('\t', value, endText, ' \\', sep = '', file = fileHandle)
  
              # If the argument and value should be hidden, don't write anything.
              elif config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'modifyArgument') == 'omit': pass
  
              # Check if the argument is a flag.
              elif not isFlag: print('\t', commandLineArgument, delimiter, value, endText, ' \\', sep = '', file = fileHandle)
  
              # If the argument is a flag, check that the value is 'set' and if so, just write the argument.
              else:
                if value == 'set': print('\t', commandLineArgument, endText, ' \\', sep = '', file = fileHandle)

    return stdoutUsed

  # Get tool arguments with commands to evaluate.
  def getToolArgumentsWithCommands(self, graph, config, task, tool, arguments):
    for longFormArgument in config.tools.getGeneralAttribute(tool, 'argumentsWithCommands'):

      # Get the nodeID for the argument if the node exists.
      nodeID, values = arguments[longFormArgument] if longFormArgument in arguments else None, None

      # Determine if the command to be evaluated uses the value associated with this argument. It
      # is allowed that the argument can be given a value and then instead of using this value on 
      # the command line, the command to evaluate is given which includes the given value.
      instructions = config.tools.getArgumentAttribute(tool, longFormArgument, 'commandEvaluation')
      usesItself   = False
      useArguments = []
      for value in instructions.values:
        argument = instructions.values[value]
        if argument == longFormArgument: usesItself = True
        useArguments.append((argument, value))

      # Determine the nodeID for this argument.
      #nodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, longFormArgument, 'option')

      # If the node has not been assigned and the command uses the value associated with itself, it is not
      # possible to assign a command to the argument. If the argument were required, gkno would already have
      # terminated, so this argument can be left blank.
      if not nodeID and usesItself: return arguments

      # Record which IDs in the command should be replaced with the tool name.
      IDIsTool = []

      # Get all of the arguments required in the command and check that they all have values. Build up the
      # command values as the arguments are processed.
      commands   = {}
      firstValue = True
      for argument, ID in useArguments:

        # The argument could take the value 'tool' in which case, the tool name is used. In this
        # check, this can be ignored.
        if argument != 'tool':

          #TODO Can the following have multiple node IDs?
          argumentNodeID     = config.nodeMethods.getNodeForTaskArgument(graph, task, argument, 'option')[0]
          argumentNodeValues = config.nodeMethods.getGraphNodeAttribute(graph, argumentNodeID, 'values')

          # If the argument does not have values, the command cannot be constructed, so return leaving this
          # argument as is.
          if not argumentNodeValues: return arguments

          # If this is the first value to be added, determine the number of iterations and create the iterations
          # in 'commands'.
          if firstValue:
            firstValue = False
            for iteration in argumentNodeValues:
              commands[iteration] = [str('`') + instructions.command + str('`')]
              commands = self.replaceCommandID(iteration, argumentNodeValues[iteration], commands, ID)

          # If the commands has already been created, check that the number of iterations in commands is equal
          # to that in the values, or that one of them has one iteration. In the latter case, either expand the 
          # commands to the number of iterations in the values and for the values with only one iteration,
          # propogate that value through all iterations in commands.
          else:
            noIterationsInCommands = len(commands)
            noIterationsInValues   = len(argumentNodeValues)

            # First, if both the values and commands has one iteration.
            if noIterationsInCommands == noIterationsInValues:
              for iteration in commands: commands = self.replaceCommandID(iteration, argumentNodeValues[iteration], commands, ID)

            # If the commands has one iteration and the values has more than one.
            elif noIterationsInCommands == 1:
              for iteration in argumentNodeValues:
                if iteration not in commands: commands[iteration] = commands[1]
                commands = self.replaceCommandID(iteration, argumentNodeValues[iteration], commands, ID)

            # If the commands has multipls iterations and the values has one.
            elif noIterationsInValues == 1:
              for iteration in commands: commands = self.replaceCommandID(iteration, argumentNodeValues[1], commands, ID)

            # If both the commands and values have multiple iterations, but neither has one, terminate.
            else:
              #TODO ERROR
              print('ERROR - makefileData. getToolArgumentsWithCommands 2')
              self.errors.terminate()

        # If this argument is given the value 'tool', store this and deal with it at the end.
        else: IDIsTool.append(ID)

      # If any of the IDs in the command were to be replaced with the tool name, replace them now.
      for ID in IDIsTool:
        for iteration in commands: commands = self.replaceCommandID(iteration, [tool], commands, ID)

      # Replace the values with the commands.
      newArguments = []
      for tempNodeID, tempValues in arguments[longFormArgument]:
        newArguments.append((tempNodeID, commands))
      arguments[longFormArgument] = newArguments

    return arguments

  # Replace the ID in the command with values.
  def replaceCommandID(self, iteration, argumentValues, commands, ID):

    # If there are multiple values, it is unclear which value to include in the command, so terminate.
    if len(argumentValues) != 1:
      #TODO ERROR
      print('ERROR - replaceCommandID')
      self.errors.terminate()

    commands[iteration][0] = commands[iteration][0].replace(ID, argumentValues[0])

    return commands

  # If the input is a stream and the argument has specific instructions, ensure that the argument is correctly handled.
  def checkInputStream(self, config, tool, argument, includeArgument):

    # If the command line argument needs to be replace by a different value.
    if config.tools.getArgumentAttribute(tool, argument, 'inputStream') == 'replace':
      replaceArgument = config.tools.getArgumentAttribute(tool, argument, 'replaceArgument')['argument']
      replaceValue    = config.tools.getArgumentAttribute(tool, argument, 'replaceArgument')['value']
      return True, replaceArgument, replaceValue

    # If the argument should be omitted from the command line, set includeArgument to False.
    elif config.tools.getArgumentAttribute(tool, argument, 'inputStream') == 'do not include': return False, argument, None

  # Write outputs and errors to the stdout and stderr files.
  def writeStdouts(self, stdoutUsed, fileHandle):
    if not stdoutUsed: print('\t>> $(STDOUT) \\', file = fileHandle)
    print('\t2>> $(STDERR)', file = fileHandle)

  # Indicate that the task ran successfully.
  def writeComplete(self, fileHandle):

    # Write out that the task completed successfully.
    print('\t@echo ', self.echoModifier, ' "completed successfully."', sep = '', file = fileHandle)
    print(file = fileHandle)

  # Close the Makefile.
  def closeMakefile(self, fileHandle):
    fileHandle.close()

  # Check that all required files exist prior to executing any makefiles.
  def checkFilesExist(self, graph, config, filenames, sourcePath):
    for nodeID, filename in filenames:

      # If the filename begins with $(PWD), replace it with the path of the current working
      # directory.
      if filename.startswith('$(PWD)'): filename = os.getcwd() + filename.split('$(PWD)')[1]

      # If the filename begins with $(RESOURCES), include the full path of the resources directory.
      elif filename.startswith('$(RESOURCES)'): filename = sourcePath + '/resources/' + filename.split('$(RESOURCES)')[1]

      # If the filename begins with $(TOOL_BIN), include the full path of the tools directory.
      elif filename.startswith('$(TOOL_BIN)'): filename = sourcePath + '/tools/' + filename.split('$(TOOL_BIN)')[1]

      if not os.path.exists(filename): self.missingFiles.append(filename)

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
      argument       = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
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
        argument     = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
        values       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        if argument not in arguments: arguments[argument] = []
        arguments[argument].append((optionNodeID, values))

    # Now parse all of the sucessor file nodes and store the arguments for non filename stub files.
    for nodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
      isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, task, nodeID,'isFilenameStub')
      optionNodeID   = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
      if not isFilenameStub:
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)
        argument     = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'longFormArgument')
        values       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        if argument not in arguments: arguments[argument] = []
        arguments[argument].append((optionNodeID, values))

    return arguments

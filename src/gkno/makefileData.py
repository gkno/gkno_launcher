#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import errors
from errors import *

import os
import sys

class makefileData:
  def __init__(self):
    self.addedInformation       = {}
    self.arguments              = {}
    self.coreArguments          = {}
    self.dependencies           = {}
    self.finalArguments         = {}
    self.hasPipes               = False
    self.outputs                = {}
    self.taskBlocks             = []
    self.taskBlocksOutputs      = []
    self.taskBlocksDependencies = []

  # Initialise a list to contain the names of the makefiles.
  def initialiseNames(self):
    self.id        = 0
    self.filenames = []

  # Set the names of the makefiles to be created.  If this is a single run, a single name
  # is required, otherwise, there will be a list of names for each of the created makefiles.
  def getFilename(self, multiple, pipeline):
    self.id += 1
    if multiple: pipeline += '_' + str(self.id)
    self.filenames.append(pipeline + '.make')

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

  # Open the makefile and write the initial information to the file.
  def openMakefile(self, sourcePath, isPipeline, resourcePath):

    # Open a script file.
    self.makeFilehandle = open(self.filenames[self.id - 1], 'w')
    self.filename       = os.path.abspath(self.filenames[self.id - 1])

    print('### gkno Makefile', file = self.makeFilehandle)
    print(file = self.makeFilehandle)
    print('GKNO_PATH=', sourcePath, "/src/gkno", sep = '', file = self.makeFilehandle)
    print('TOOL_BIN=', sourcePath, "/tools", sep = '', file = self.makeFilehandle)
    if resourcePath == '': resourcePath = sourcePath + '/resources'
    print('RESOURCES=', resourcePath, sep = '', file = self.makeFilehandle)
    print('MAKEFILE_ID=', self.filename.split('/')[-1].split('.')[0], sep = '', file = self.makeFilehandle)
    print(file = self.makeFilehandle)
    print('.DELETE_ON_ERROR:', file = self.makeFilehandle)
    print('.PHONY: all', file = self.makeFilehandle)

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
        for iteration in self.deleteFiles[task]:
          for fileToDelete in iteration:
            print(fileToDelete, end = ' ', file = self.makeFilehandle)
      print(file = self.makeFilehandle)

  # Write out all of the output files generated.
  def writeAllOutputs(self):
    print(file = self.makeFilehandle)
    print('all:', end = "", file = self.makeFilehandle)

    allOutputs = []
    for outputBlock in reversed(self.taskBlockOutputs):
      for inputLoopIteration in outputBlock:
        for output in inputLoopIteration:
          allOutputs.append(output)

    for task in self.outputs:
      for inputLoopIteration in self.outputs[task]:
        for output in inputLoopIteration:
          if output in allOutputs: print(output, end = ' ', file = self.makeFilehandle)

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
      self.redirect = '>'
    else:
      if hasMultipleRuns: self.outputID = str(self.filename.split('.')[0]) + '_' + str(self.id)
      else: self.outputID = str(self.filename.split('.')[0])
      self.redirect = '>' if taskBlock == self.taskBlocks[0] else '>>'

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
  def generateCommand(self, argumentInformation, delimiters, precommands, executables, modifiers, argumentOrder, taskToTool, linkage, taskBlock, verbose, internalLoopCounter):
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
      if firstCommand: print('@', end = '', file = self.makeFilehandle)

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
          useStdout    = False
          useStderr    = False
          if inInfo:
            if 'modify argument name on command line' in argumentInformation[tool][argument]:
              hideArgument = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'hide' else False
              useStdout    = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'stdout' else False
              useStderr    = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'stderr' else False
              writeNothing = True if argumentInformation[tool][argument]['modify argument name on command line'] == 'omit' else False

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
              if hideArgument: print(" \\\n\t", value, sep = '', end = '', file = self.makeFilehandle)
              elif writeNothing: pass
              elif useStdout: print(" \\\n\t> ", value, sep = '', end = '', file = self.makeFilehandle)
              elif useStderr: print(" \\\n\t2> ", value, sep = '', end = '', file = self.makeFilehandle)
              else: print(" \\\n\t", argument, delimiter, value, sep = '', end = '', file = self.makeFilehandle)
  
        if task     != taskBlock[-1]: lineStart = " \\\n\t| "
        firstCommand = False

    # Write the stdout and stderr to file.
    print(' \\', file = self.makeFilehandle)
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
  def getExecutablePath(self, paths, taskToTool, taskBlock, iLoopIteration):
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
      print('NO OUTPUTS: NOT HANDLED PHONY') 
      exit(1) 
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

  # Close the Makefile.
  def closeMakefile(self):
    self.makeFilehandle.close()

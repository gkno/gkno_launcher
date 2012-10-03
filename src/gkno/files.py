#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import json
import os
import subprocess
from subprocess import PIPE
import sys
import traceback

class files:
  def __init__(self):
    self.dependenciesList  = []
    self.jsonToolFiles     = {}
    self.jsonPipelineFiles = {}
    self.makeFilehandle    = ''
    self.outputsList       = []
    self.phoneHomeID       = ''

  def getJsonData(self, filename):
    er = errors()

    # Check that the file exists.
    try: jsonData = open(filename)
    except: er.missingFile(True, '', filename)
    if er.error: er.terminate()

    try: inputData = json.load(jsonData)
    except:
      er.error = True
      exc_type, exc_value, exc_traceback = sys.exc_info()

    # If the json file has a problem, terminate the script with an error.
    if er.error:
      er.jsonOpenError(True, 0, exc_value, filename)
      er.terminate()

    return inputData

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):
      if files.endswith('.json'): self.jsonToolFiles[files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('.json'): self.jsonPipelineFiles[files] = True

  # If a pipeline is being run, search for the corresponding config file.
  def getPipelineConfigurationFile(self, gknoHelp, pl, path):
    if (gknoHelp.specificPipelineHelp) or (not gknoHelp.printHelp):
      self.jsonPipelineFile = path + "/" + pl.pipelineName + '.json'
      if pl.pipelineName + '.json' not in self.jsonPipelineFiles.keys():
        gknoHelp.specificPipelineHelp = False
        gknoHelp.unknownPipeline      = True
        gknoHelp.pipelineHelp         = True
        gknoHelp.printHelp            = True

# Open the pipeline configuration file and put the information into memory.
  def getPipelineDescription(self, tl, pl, verbose):
    er = errors()

    if verbose and tl.toolArguments['pipeline']['--verbose']: verbose = True

    length = len(pl.pipelineName + 'Executing pipeline: ') + 4
    text = '=' * length
    if verbose:
      print(text, file = sys.stdout)
      print('  Executing pipeline: ', pl.pipelineName, sep = '', file = sys.stdout)
      print(text, file = sys.stdout)
      print(file = sys.stderr)
      print('Reading in pipeline configuration file...', end = '', file = sys.stdout)
      sys.stdout.flush()
    jsonData = open(self.jsonPipelineFile)
    try: pl.information = json.load(jsonData)
    except:
      er.error = True
      exc_type, exc_value, exc_traceback = sys.exc_info()

    # If the json file has a problem, terminate the script with an error.
    if er.error:
      er.jsonOpenError(True, 1, exc_value, self.jsonPipelineFile)
      er.terminate()
    if verbose:
      print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

    return 'pipe/' + pl.pipelineName

  # From the list of json files, popluate a hash table with the names
  # and descriptions of the tools.
  def getToolDescriptions(self, tl, pl, sourcePath, verbose):
    er = errors()

    if verbose and tl.toolArguments['pipeline']['--verbose']: verbose = True

    if verbose:
      print('Reading in tool configuration files...', file = sys.stdout)
      sys.stdout.flush()
    for toolFile in self.jsonToolFiles:
      if verbose:
        print('     ', toolFile, '...', sep = '', end = '', file = sys.stdout)
        sys.stdout.flush()
      jsonData = open(sourcePath + '/' + toolFile)
      try: toolData = json.load(jsonData)
      except:
        er.error = True
        exc_type, exc_value, exc_traceback = sys.exc_info()

      # If the json file has a problem, terminate the script with an error.
      if er.error:
        er.jsonOpenError(True, 2, exc_value, toolFile)
        er.terminate()
      else:
        for tool in toolData['tools']:
          tl.toolInfo[tool] = toolData['tools'][tool]
        if verbose:
          print("done.", file = sys.stdout)
          sys.stdout.flush()

    if verbose:
      print(file = sys.stdout)
      sys.stdout.flush()

  # The set of tools and the associated parameters are set
  # in the config file, so build up the scripts to run the
  # pipeline.
  def generateMakefile(self, tl, pl, sourcePath, filename, makefileID):
    er = errors()

    # Open a script file.
    self.makeFilehandle = open(filename, 'w')
    self.filename       = os.path.abspath(filename)
  
    if tl.toolArguments['pipeline']['--verbose']:
      print("Generating Makefile...", end = '', file = sys.stdout)
      sys.stdout.flush()
    print('### gkno Makefile', file = self.makeFilehandle)
    print(file = self.makeFilehandle)
    print('GKNO_PATH=', sourcePath, "/src/gkno", sep = '', file = self.makeFilehandle)
    print('TOOL_BIN=', sourcePath, "/tools", sep = '', file = self.makeFilehandle)
    if pl.isPipeline: resourcesPath = '/resources' if pl.information['resource path'] == '' else '/resources/' + pl.information['resource path']
    else: resourcesPath = '/resources' if 'resource path' not in tl.toolInfo[tl.tool] else '/resources/' + tl.toolInfo[tl.tool]['resource path']
    print('RESOURCES=', sourcePath, resourcesPath, sep = '', file = self.makeFilehandle)
    print('MAKEFILE_ID=', self.filename.split('/')[-1].split('.')[0], sep = '', file = self.makeFilehandle)
    print(file = self.makeFilehandle)
  
    # Loop over each tool in the work flow and generate the command lines
    # for each.  Work in reverse order building up the dependencies.
    for counter in reversed(range(0, len(pl.information['workflow']))):
      task = pl.information['workflow'][counter]
      tool = pl.information['tools'][task]

    # Having established all the dependencies and the output files for each
    # tool, write out the commands for the Makefile.
    print('.DELETE_ON_ERROR:', file = self.makeFilehandle)
    print('.PHONY: all', file = self.makeFilehandle)

    # If any files are deleted during execution of the pipeline, mark them as
    # intermediate files.  This will ensure that if the Makefile is rerun, the
    # intermediate files will not be recreated.
    if len(pl.deleteFiles) != 0:
      print('.INTERMEDIATE:', end = '', file = self.makeFilehandle)
      for task in pl.deleteFiles:
        for argument in pl.deleteFiles[task]:
          for fileToDelete in pl.deleteFiles[task][argument]:
            print(fileToDelete, end = ' ', file = self.makeFilehandle)
      print(file = self.makeFilehandle)

    print(file = self.makeFilehandle)
    print('all:', end = "", file = self.makeFilehandle)

    # Determine the outputs and dependencies for each block of tasks.
    self.getOutputsAndDependents(tl, pl)
    allOutputs = []
    for outputBlock in reversed(self.outputsList):
      for output in outputBlock:
        allOutputs.append(output)

    for task in pl.finalOutputs:
      for output in pl.finalOutputs[task]:
        if output in allOutputs: print(output, end = ' ', file = self.makeFilehandle)

    print(file = self.makeFilehandle)
    print(file = self.makeFilehandle)

    # Loop over each of the task blocks in reverse order (if a task block consists
    # of multiple tasks, these tasks are in the correct order for piping) and generate
    # the list of outputs, dependencies and rules.
    for taskBlock, outputBlock, dependencyBlock in zip(reversed(pl.taskBlocks), reversed(self.outputsList), reversed(self.dependenciesList)):
      self.writeInitialInformation(pl, taskBlock)
      pathList = self.getExecutablePath(tl, pl, taskBlock)
      self.writeOutputsToMakefile(outputBlock)
      self.writeDependenciesToMakefile(dependencyBlock)
      lineStart    = "\t"
      firstCommand = True

      # Set the name of the stdout and stderr and output the name of the task to the
      # file.
      # If there are multiple runs of the pipeline, the stdout and stderr from each of
      # the commands in the makefile will be written out to files of the form
      # <task>_<ID>.stdout, where ID is an integer
      if tl.toolArguments['pipeline']['--task-stdout']:
        if pl.hasMultipleRuns: outputID = str(taskBlock[-1]) + '_' + str(makefileID)
        else: outputID = str(taskBlock[-1])
        redirect = '>'
      else:
        if pl.hasMultipleRuns: outputID = str(self.filename.split('.')[0]) + '_' + str(makefileID)
        else: outputID = str(self.filename.split('.')[0])
        redirect = '>' if taskBlock == pl.taskBlocks[0] else '>>'

      for task, path in zip(taskBlock, pathList):
        if firstCommand:
          if len(taskBlock) == 1:
            print("\t@echo -e \"Executing task: ", taskBlock[-1], '...\\c"', sep = '', file = self.makeFilehandle)
          else:
            print("\t@echo -e \"Executing piped tasks (", taskBlock[0], ' -> ', taskBlock[-1], ')...\\c"', sep = '', file = self.makeFilehandle)
        tool         = pl.information['tools'][task]
        usedStdout   = self.generateCommand(tl, pl, path, task, tool, lineStart, firstCommand)
        if task     != taskBlock[-1]: lineStart = " \\\n\t| "
        firstCommand = False

      # Write the stdout and stderr to file.
      print(' \\', file = self.makeFilehandle)
      if not usedStdout: print("\t", redirect, ' ', outputID, '.stdout \\', sep = '', file = self.makeFilehandle)
      print("\t2", redirect, ' ', outputID, '.stderr', sep = '', file = self.makeFilehandle)
      print("\t@echo -e \"completed successfully.\"", sep = '', file = self.makeFilehandle)

      # If any intermediate files are marked as to be deleted after this task, put in the
      # command to delete them.
      self.deleteFiles(tl, pl, task)
      print(file = self.makeFilehandle)

    # Close the Makefile.
    self.makeFilehandle.close()
    if tl.toolArguments['pipeline']['--verbose']:
      print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Determine the outputs and dependencies for each block of tasks
  # linked together by pipes.  If the block is a single task, then the outputs
  # and dependencies are just those of the tool.  If the block is a set of
  # linked tasks, we need only the outputs and dependent files that are not
  # linked between the tools.
  def getOutputsAndDependents(self, tl, pl):
    for taskBlock in pl.taskBlocks:

      # If the task block contains a single task, update the outputs and dependency lists
      # to include all listed files for this block.
      if len(taskBlock) == 1:
        self.outputsList.append(tl.outputs[taskBlock[0]])
        self.dependenciesList.append(tl.dependencies[taskBlock[0]])
      else:

        # Generate a list of all outputs and all dependencies, then check if any of the
        # outputs from any task in this block appear as dependencies for other tasks in
        # this block.  These should all be omitted as they are internal to the stream.
        tempOutputs      = {}
        tempDependencies = {}
        for task in taskBlock:
          for output in tl.outputs[task]:
            if isinstance(output, list):
              for outputList in output: tempOutputs[outputList] = True
            else:
              tempOutputs[output] = True
          for dependent in tl.dependencies[task]:
            if isinstance(dependent, list):
              for dependentList in dependent: tempDependencies[dependentList] = True
            else:
              tempDependencies[dependent] = True

        for dependent in tempDependencies:
          if dependent in tempOutputs:
            tempOutputs[dependent]      = False
            tempDependencies[dependent] = False
          #print(task, tool, "\n\t", tl.outputs[task], "\n\t", tl.dependencies[task])
          #if (len(tl.outputs[task]) == 1) and (tl.outputs[task][0].endswith('_phony')):
           #print(".PHONY: ", tl.outputs[task], sep = '', file = self.makeFilehandle)

          # Print out the output file and the list of dependencies.
          #else: print(' '.join(tl.outputs[task]), ': ', ' '.join(tl.dependencies[task]), sep = '', file = self.makeFilehandle)
        tempList = []
        for output in tempOutputs:
          if tempOutputs[output]: tempList.append(output)
        self.outputsList.append(tempList)
        tempList = []
        for dependent in tempDependencies:
          if tempDependencies[dependent]: tempList.append(dependent)
        self.dependenciesList.append(tempList)

  # Write information to stdout for each task block.
  def writeInformationToScreen(self, tl, pl, taskBlock):
    if tl.toolArguments['pipeline']['--verbose']:
      if len(taskBlock) == 1:
        tool = pl.information['tools'][taskBlock[0]]
        print("\t", taskBlock[0], " (", tool, ")...", sep = '', file = sys.stdout)
      else:
        print("\tpiped set of tasks:", sep = '', file = sys.stdout)
        for task in taskBlock:
          tool = pl.information['tools'][task]
          print("\t\t", task, " (", tool, ")...", sep = '', file = sys.stdout)
      sys.stdout.flush()

  # Write initial information to the Makefile.
  def writeInitialInformation(self, pl, taskBlock):
    if len(taskBlock) > 1:
      print('### Command line information for the following set of piped tools:', sep = '', file = self.makeFilehandle)
      for task in taskBlock:
        tool = pl.information['tools'][task]
        print('###    ', task, ' (', tool, ')', sep = '', file = self.makeFilehandle)
    else:
      task = taskBlock[0]
      tool = pl.information['tools'][task]
      print('### Command line information for ', task, ' (', tool, ')', sep = '', file = self.makeFilehandle)

  # Get the path of the executable.
  def getExecutablePath(self, tl, pl, taskBlock):
    er       = errors()
    pathList = []

    for task in taskBlock:
      tool = pl.information['tools'][task]
      try: path = tl.toolInfo[tool]['path']
      except: er.error = True
      if er.error:
        er.missingJsonEntry('path', tool)
        er.terminate()

      # Only print out the path if it isn't defined as 'null'.  Unix commands will
      # be defined as 'null' as they do not need to include a path, for example.
      pathVariable = ''
      if path != 'no path':
        pathVariable = (tool.replace(" ", "_")  + '_PATH').upper()
        print(pathVariable, "=$(TOOL_BIN)/", path, sep = "" , file = self.makeFilehandle)
  
      pathList.append(pathVariable)

    return pathList

  # Write the outputs for the task block to the Makefile.
  def writeOutputsToMakefile(self, outputBlock):

    # Check if the target is a phony target.  If so, define the phony target.
    #if (len(tl.outputs[task]) == 1) and (tl.outputs[task][0].endswith('_phony')):
    #  print(".PHONY: ", tl.outputs[task], sep = '', file = self.makeFilehandle)
    if len(outputBlock) == 0:
      print('NO OUTPUTS: NOT HANDLED PHONY')
      exit(1)
    else:
      for counter, output in enumerate(outputBlock):
        endOfLine = ' ' if ( (counter + 1) < len(outputBlock)) else ': '
        print(output, end = endOfLine, file = self.makeFilehandle)

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

  # Generate commands for the makefile
  def generateCommand(self, tl, pl, path, task, tool, lineStart, firstCommand):
    er        = errors()
    delimiter = tl.argumentDelimiters[tool]
    newLine   = True if tl.toolArguments['pipeline']['--verbose'] else False
    noTab     = 2 if tl.toolArguments['pipeline']['--verbose'] else 0
    useStdout = False

    # Print out the command line.
    print(lineStart, end = '', file = self.makeFilehandle)

    # If this is a single command, or the first command in a set of piped commands, 
    # start the line with the '@' character.  This will stop make 'echoing' the command
    # to the screen.
    if firstCommand: print('@', end = '', file = self.makeFilehandle)

    # Write the command line.
    if 'precommand' in tl.toolInfo[tool]:
      print(tl.toolInfo[tool]['precommand'], ' ', sep = '', end = '', file = self.makeFilehandle)
    if path == '': print(tl.toolInfo[tool]['executable'], sep = '', end = '', file = self.makeFilehandle)
    else: print("$(", path, ")/", tl.toolInfo[tool]['executable'], sep = '', end = '', file = self.makeFilehandle)
    if 'modifier' in tl.toolInfo[tool]:
      print(' ', tl.toolInfo[tool]['modifier'], sep = '', end = '', file = self.makeFilehandle)
  
    # Check if the order in which the parameters appear matters.  For certain
    # tools, the command line is built up of a list of arguments, but each
    # argument isn't given an option.  For example, renaming a file has a 
    # command line 'mv A B', where A and B are filenames that have to appear
    # in the correct order.
    argumentOrder = []
    argumentDict  = {}
    for argument in tl.toolInfo[tool]['arguments']: argumentDict[argument] = True
    if 'argument order' in tl.toolInfo[tool]:
      for argument in tl.toolInfo[tool]['argument order']:
        if argument in tl.toolArguments[task]:
          argumentOrder.append(argument)
          del(argumentDict[argument])
        else:
          self.error = False

          # If the argument is for an input or output, it is possible that these arguments
          # have been removed if dealing with the stream.  Check if this is the case and
          # if so, do not terminate.
          if 'if output to stream' in tl.toolInfo[tool]['arguments'][argument]:
            if tl.toolInfo[tool]['arguments'][argument]['if output to stream'] == 'do not include': del(argumentDict[argument])
            else: self.error = True
          elif 'if input is stream' in tl.toolInfo[tool]['arguments'][argument]:
            if tl.toolInfo[tool]['arguments'][argument]['if input is stream'] == 'do not include': del(argumentDict[argument])
            else: self.error = True
          else: self.error = True
          if self.error:
            er.unknownArgumentInArgumentOrder(newLine, noTab, task, tool, argument)
            er.terminate()

      # Having stepped through all of the arguments included in the ordered list, check
      # if there are any arguments left in the argumentDict dictionary.  This dictionary
      # was built from all of the arguments for this tool and if it is not empty, then
      # some of the arguments for this tool are not included in the list and thus would
      # not be included in the command line.  Terminate with an error if this is the case,
      if len(argumentDict) != 0:
        er.missingArgumentsInOrderList(newLine, noTab, task, tool, argumentDict)
        er.terminate()
    else:
      for argument in tl.toolArguments[task]: argumentOrder.append(argument)
 
    # Include all of the set options.
    for argument in argumentOrder:

      # Check if the option is a flag.
      isFlag = False

      # Check if this argument is in the toolInfo structure.  Arguments dealing with
      # the stream may not be contained.
      inInfo    = True if argument in tl.toolInfo[tool]['arguments'] else False
      isReplace = False
      if inInfo:
        if tl.toolInfo[tool]['arguments'][argument] == 'replacement': isReplace = True

      if argument == 'json parameters':

        # If a json file is being used to generate parameters, the configuration file
        # needs to contain a 'json block' argument.  This tells the script the name of
        # the block in the json file from which to extract parameters.
        if 'json block' not in pl.information['linkage'][task]['json parameters']:
          er.optionAssociationError(newLine, noTab, 'json block', 'json parameters', 'pipeline')
          er.terminate()
        else:
         jsonBlock = pl.information['linkage'][task]['json parameters']['json block']
         print(" \\\n\t`python $(GKNO_PATH)/getParameters.py ", end = '', file = self.makeFilehandle)
         print(tl.toolArguments[task][argument], ' ', jsonBlock, '`', sep = '', end = '', file = self.makeFilehandle)

      # If the argument is a replacement to handle a stream, do not interrogate the
      # tl.toolInfo structure as it doesn't contain the required values (the other
      # entries contain information on flags, data types etc).
      elif isReplace:

        # If the line is blank, do not print to file.
        if not ((argument == '') and (tl.toolArguments[task][argument] == '')):
          if tl.toolArguments[task][argument] == 'no value': print(" \\\n\t", argument, sep = '', end = '', file = self.makeFilehandle)
          else: print(" \\\n\t", argument, delimiter, tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)
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
          if 'modify argument name on command line' in tl.toolInfo[tool]['arguments'][argument]:
            hideArgument = True if tl.toolInfo[tool]['arguments'][argument]['modify argument name on command line'] == 'hide' else False
            useStdout    = True if tl.toolInfo[tool]['arguments'][argument]['modify argument name on command line'] == 'stdout' else False
            useStderr    = True if tl.toolInfo[tool]['arguments'][argument]['modify argument name on command line'] == 'stderr' else False
            writeNothing = True if tl.toolInfo[tool]['arguments'][argument]['modify argument name on command line'] == 'omit' else False

          if tl.toolInfo[tool]['arguments'][argument]['type'] == 'flag': isFlag = True

        # If the command is a flag, check if the value is 'set' or 'unset'.  If 'set',
        # write out the command.
        if isFlag:
          if tl.toolArguments[task][argument] == 'set': print(" \\\n\t", argument, sep = '', end = '', file = self.makeFilehandle)
        else:

          # Some command lines allow multiple options to be set and the command line can
          # therefore be repeated multiple times.  If the defined value is a list, this
          # is the case and the command should be written out once for each value in the
          # list.
          isList = isinstance(tl.toolArguments[task][argument], list)
          if isList:
            for value in tl.toolArguments[task][argument]:
              if hideArgument: print(" \\\n\t", value, sep = '', end = '', file = self.makeFilehandle)
              elif writeNothing: pass
              elif useStdout: print(" \\\n\t> ", value, sep = '', end = '', file = self.makeFilehandle)
              elif useStderr: print(" \\\n\t2> ", value, sep = '', end = '', file = self.makeFilehandle)
              else: print(" \\\n\t", argument, delimiter, value, sep = '', end = '', file = self.makeFilehandle)

          # If the option is given a value, print it out.
          elif tl.toolArguments[task][argument] != '':
            if tl.toolArguments[task][argument] == 'no value':
              print(" \\\n\t", argument, sep = '', end = '', file = self.makeFilehandle)
            else:
              if hideArgument: print(" \\\n\t", tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)
              elif writeNothing: pass
              elif useStdout: print(" \\\n\t> ", tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)
              elif useStderr: print(" \\\n\t2> ", tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)
              else: print(" \\\n\t", argument, delimiter, tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)

    return useStdout

  # If any intermediate files are marked as to be deleted after this step, add the command
  # to the rule.
  def deleteFiles(self, tl, pl, task):
    if task in pl.deleteFiles:
      print(file = self.makeFilehandle)
      for argument in pl.deleteFiles[task]:
        for fileToDelete in pl.deleteFiles[task][argument]:
          print("\t@rm -f ", fileToDelete, sep = '', file = self.makeFilehandle)

  # Ping the website with usage information.
  def phoneHome(self, sourcePath):
    print("Logging gkno usage with ID: ", self.phoneHomeID, "...", sep = '', end = '', file = sys.stdout)
    executable = sourcePath + '/src/gkno/ga.sh'
    subprocess.call([executable, self.phoneHomeID], stdout=PIPE, stderr=PIPE)
    print("done.", file = sys.stdout)
    sys.stdout.flush()

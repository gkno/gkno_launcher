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

  def getMultipleJson(self, filename):
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
      er.jsonOpenError(True, '', exc_value)
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

  # From the list of json files, popluate a hash table with the names
  # and descriptions of the tools.
  def getToolDescriptions(self, tl, pl, sourcePath, verbose):
    er = errors()

    if verbose and tl.toolArguments['pipeline']['--verbose']: verbose = True

    if verbose:
      print("Reading in tool configuration files...", file = sys.stdout)
      sys.stdout.flush()
    for toolFile in self.jsonToolFiles:
      if verbose:
        print("\t", toolFile, '...', sep = '', end = '', file = sys.stdout)
        sys.stdout.flush()
      jsonData = open(sourcePath + '/' + toolFile)
      try: toolData = json.load(jsonData)
      except:
        er.error = True
        exc_type, exc_value, exc_traceback = sys.exc_info()

      # If the json file has a problem, terminate the script with an error.
      if er.error:
        er.jsonOpenError(True, "\t\t", exc_value)
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
      if verbose: print(file = sys.stdout)
      er.error = True
      exc_type, exc_value, exc_traceback = sys.exc_info()

    # If the json file has a problem, terminate the script with an error.
    if er.error:
      er.jsonOpenError(True, "\t", exc_value)
      er.terminate()
    if verbose:
      print("done\n", file = sys.stdout)
      sys.stdout.flush()

    return 'pipe/' + pl.pipelineName

  # The set of tools and the associated parameters are set
  # in the config file, so build up the scripts to run the
  # pipeline.
  def generateMakefile(self, tl, pl, sourcePath, filename):
    er = errors()

    # Open a script file.
    self.makeFilehandle = open(filename, 'w')
    self.filename       = os.path.abspath(filename)
  
    if tl.toolArguments['pipeline']['--verbose']:
      print("Generating Makefile...", file = sys.stdout)
      sys.stdout.flush()
    print("### gkno Makefile\n", file = self.makeFilehandle)
    print("GKNO_PATH=", sourcePath, "/src/gkno", sep = "", file = self.makeFilehandle)
    print("TOOL_BIN=", sourcePath, "/tools", sep = "", file = self.makeFilehandle)
    print("RESOURCES=", sourcePath, "/resources\n", sep = "", file = self.makeFilehandle)
  
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
      lineStart = "\t"
      for task, path in zip(taskBlock, pathList):
        tool = pl.information['tools'][task]
        self.generateCommand(tl, pl, path, task, tool, lineStart)
        if task != taskBlock[-1]: lineStart = " \\\n\t| "
        self.deleteFiles(tl, pl, task)
      print(file = self.makeFilehandle)
      print(file = self.makeFilehandle)

    #for counter in reversed(range(0, len(pl.information['workflow']))):
    #  task           = pl.information['workflow'][counter]
    #  tool           = pl.information['tools'][task]
    #  pathVariable = self.writeInitialInformation(tl, task, tool)
    #  self.generateCommand(tl, pl, pathVariable, task, tool)
    #  self.deleteFiles(tl, pl, task)
    #  print(file = self.makeFilehandle)

    # Close the Makefile.
    self.makeFilehandle.close()
    if tl.toolArguments['pipeline']['--verbose']:
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
          for output in tl.outputs[task]: tempOutputs[output] = True
          for dependent in tl.dependencies[task]: tempDependencies[dependent] = True

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
      if path != 'null':
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
      endOfLine = ' ' if ( (counter + 1) < len(dependencyBlock)) else "\n"
      print(output, end = endOfLine, file = self.makeFilehandle)

  # Generate commands for the makefile
  def generateCommand(self, tl, pl, path, task, tool, lineStart):
    er = errors()
  
    # Print out the command line.
    print(lineStart, end = '', file = self.makeFilehandle)
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
    if 'ordered' in tl.toolInfo[tool]:
      optionList = {}
      if tl.toolInfo[tool]['ordered'] == 'true':
        for option in tl.toolArguments[task]:
          try: order = tl.toolInfo[tool]['arguments'][option]['order']
          except: er.error = True
          if er.error:
            er.missingOrderID(task, tool, option)
            er.terminate()

          if order in optionList:
            er.optionIDExists(task, tool, option)
            er.terminate()

          # Only include the option, if it is required.
          if tl.toolArguments[task][option] == 'set': optionList[order] = option
          elif (tl.toolArguments[task][option] != 'unset') and (tl.toolArguments[task][option] != ''):
            optionList[order] = option + ' ' + tl.toolArguments[task][option]

      orderList = sorted(optionList.iteritems())
      start     = int(orderList[0][0])
      end       = int(orderList[-1][0])
      while start <= end:
        if str(start) not in optionList: er.orderWarning(task, tool, start)
        else: print(" \\\n\t", optionList[str(start)], sep = "", end = "", file = self.makeFilehandle)
        start += 1
    else:

      # Include all of the set options.
      for argument in tl.toolArguments[task]:

        # Check if the option is a flag.
        isFlag = False
        if argument == 'json parameters':

          # If a json file is being used to generate parameters, the configuration file
          # needs to contain a 'json block' argument.  This tells the script the name of
          # the block in the json file from which to extract parameters.
          if 'json block' not in pl.information['linkage'][task]['json parameters']:
            er.optionAssociationError('json block', 'json parameters', 'pipeline')
            er.terminate()
          else:
            jsonBlock = pl.information['linkage'][task]['json parameters']['json block']
            print(" \\\n\t`python $(GKNO_PATH)/getParameters.py ", end = "", file = self.makeFilehandle)
            print(tl.toolArguments[task][argument], " ", jsonBlock, "`", sep = "", end = "", file = self.makeFilehandle)

        # If the argument is a replacement to handle a stream, do not interrogate the
        # tl.toolInfo structure as it doesn't contain the required values (the other
        # entries contain information on flags, data types etc).
        elif tl.toolInfo[tool]['arguments'][argument] == 'replacement':
          print(" \\\n\t", argument, " ", tl.toolArguments[task][argument], sep = "", end = "", file = self.makeFilehandle)

        else:
          if tl.toolInfo[tool]['arguments'][argument]['type'] == 'flag': isFlag = True

          # If the command is a flag, check if the value is 'set' or 'unset'.  If 'set',
          # write out the command.
          if isFlag:
            if tl.toolArguments[task][argument] == 'set': print(" \\\n\t", argument, sep = "", end = "", file = self.makeFilehandle)
          else:

            # Some command lines allow multiple options to be set and the command line can
            # therefore be repeated multiple times.  If the defined value is a list, this
            # is the case and the command should be written out once for each value in the
            # list.
            isList = isinstance(tl.toolArguments[task][argument], list)
            if isList:
              for value in tl.toolArguments[task][argument]:
                print(" \\\n\t", argument, ' ', value, sep = '', end = '', file = self.makeFilehandle)

            # If the option is given a value, print it out.
            elif tl.toolArguments[task][argument] != '':
              print(" \\\n\t", argument, ' ', tl.toolArguments[task][argument], sep = '', end = '', file = self.makeFilehandle)

  # If any intermediate files are marked as to be deleted after this step, add the command
  # to the rule.
  def deleteFiles(self, tl, pl, task):
    if task in pl.deleteFiles:
      print(file = self.makeFilehandle)
      for argument in pl.deleteFiles[task]:
        for fileToDelete in pl.deleteFiles[task][argument]:
          print("\trm -f ", fileToDelete, sep = '', file = self.makeFilehandle)

  # Ping the website with usage information.
  def phoneHome(self, sourcePath):
    print("Logging gkno usage with ID: ", self.phoneHomeID, "...", sep = '', end = '', file = sys.stdout)
    executable = sourcePath + '/src/gkno/ga.sh'
    subprocess.call([executable, self.phoneHomeID], stdout=PIPE, stderr=PIPE)
    print("done.", file = sys.stdout)
    sys.stdout.flush()

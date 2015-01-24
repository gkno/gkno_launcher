#!/bin/bash/python

from __future__ import print_function
from collections import deque
from copy import deepcopy

import fileHandling as fh
import makefileErrors
import stringOperations as stringOps

import json
import os
import sys

# Define a class to hold information about the command line.
class commandLineInformation():
  def __init__(self, graph, superpipeline, struct, task):

    # Store the task and tool.
    self.task     = task
    self.tool     = graph.getGraphNodeAttribute(task, 'tool')
    self.toolData = superpipeline.toolConfigurationData[self.tool]

    # Store if the task is greedy.
    self.isGreedy = graph.getGraphNodeAttribute(task, 'isGreedy')

    # Determine the number of command lines to be created for the task. This can be determined by finding
    # the phase in which the task resides in the pipeline execution structure, and then determining the
    # number of subphases and divisions within the phase. The total number of command lines is equal to the
    # product of these two values.
    self.phase          = struct.task[task]
    self.noSubphases    = struct.phaseInformation[self.phase].subphases
    self.noDivisions    = struct.phaseInformation[self.phase].divisions
    self.noCommandLines = self.noSubphases * self.noDivisions

    # Get the executable information.
    self.executable = self.toolData.executable
    self.modifier   = self.toolData.modifier
    self.path       = self.toolData.path
    self.precommand = self.toolData.precommand

    # Get the argument delimiter for this tool.
    self.delimiter = self.toolData.delimiter

    # Define and store the path to the executable.
    self.toolID = str(self.tool.upper() + '-PATH')

    # Store the command lines for this task.
    self.commands = []

    # Store the dependencies, intermediates, output files and files for standard out to write to, for each
    # command line.
    self.dependencies  = []
    self.intermediates = []
    self.outputs       = []
    self.stdouts       = []

# Define a class to build and manipulate makefiles.
class makefiles:
  def __init__(self):

    # Handle errors associated with makefile construction.
    self.errors = makefileErrors.makefileErrors()

    # Store the paths of all the tools executed in the pipeline.
    self.toolPaths = {}

    # Store information including command lines, dependencies and outputs for each task.
    self.executionInfo = {}

    # Record if multiple makefiles are to be generated.
    self.isMultipleMakefiles = False

    # Store the user specified ID to add to all makefile filesnames.
    self.makefileID = None

    # Create a dictionary to store the names of all the created makefiles. The dictionary
    # is keyed on the phase, subphase and the division.
    self.makefileNames   = {}
    self.makefilehandles = {}

  # Generate the command lines associated with a task.
  def generateCommandLines(self, graph, superpipeline, struct):

    # Loop over all the tasks in the pipeline, generating the command lines for each task.
    for task in graph.workflow:

      # Get the tool used to run the task and the data contained in the configuration file.
      tool     = graph.getGraphNodeAttribute(task, 'tool')
      toolData = superpipeline.toolConfigurationData[tool]

      # Check if the tool arguments need to be included in a defined order.
      argumentOrder = toolData.argumentOrder

      # Loop over all of the nodes and get the arguments that are going to be used and the
      # node IDs to which they connect. This will then be used to allow the arguments to 
      # be parsed in the order specified.
      nodeOrder = {}
      for nodeID in graph.getInputFileNodes(task): nodeOrder[str(graph.getArgumentAttribute(nodeID, task, 'longFormArgument'))] = (nodeID, 'input')
      for nodeID in graph.getOptionNodes(task): nodeOrder[str(graph.getArgumentAttribute(nodeID, task, 'longFormArgument'))] = (nodeID, 'option')
      for nodeID in graph.getOutputFileNodes(task): nodeOrder[str(graph.getArgumentAttribute(task, nodeID, 'longFormArgument'))] = (nodeID, 'output')

      # Generate a data structure for building the command line.
      data = commandLineInformation(graph, superpipeline, struct, task)
  
      # Store the tools path in the global makefiles dictionary toolPaths. If the path is listed
      # as 'none', do not include the path.
      if data.tool not in self.toolPaths and data.path != 'none': self.toolPaths[data.tool] = str(data.toolID + '=$(TOOL_BIN)/' + data.path)
  
      # The output of the method is a list of command lines, one command line for each execution
      # of the task. Each command line is itself a list of the command line executable and arguments.
      # Since each command line starts with the same exeutable command, initialise the output list as
      # numberOfCommandLines individual lists, each of which is the executable command.
      command = str(data.precommand + ' ') if data.precommand else ''
      command = command + str('$(' + data.toolID + ')/' + data.executable) if data.path != 'none' else command + str(data.executable)
      if data.modifier: command += str(' ' + data.modifier)
      for i in range(0, data.noCommandLines): data.commands.append(['\t@' + command + ' \\'])
  
      # Initialise the lists of dependencies and outputs to have the same length as the commands.
      for i in range(0, data.noCommandLines):
        data.dependencies.append([])
        data.intermediates.append([])
        data.outputs.append([])
        data.stdouts.append(str('\t>> $(STDOUT) \\'))

      # Loop over the argument order for the tool, getting information from the nodes in the correct
      # order.
      if argumentOrder:
        for argument in argumentOrder:
          if argument in nodeOrder: self.updateCommandLine(graph, task, data, nodeOrder[argument][0], nodeOrder[argument][1])

      # If the order was not specified, loop over the arguments in any order.
      else:
        for argument in nodeOrder: self.updateCommandLine(graph, task, data, nodeOrder[argument][0], nodeOrder[argument][1])

      # Finish the command lines with calls to write to stdout and stdin and indicating that the task is complete.
      for i in range(0, data.noCommandLines):
        data.commands[i].append(data.stdouts[i])
        data.commands[i].append('\t2>> $(STDERR)')
        data.commands[i].append('\t@echo -e "completed successfully"')
        data.commands[i].append('')
  
      # Store the command lines for the task.
      self.executionInfo[task] = data

  # Update a command line with information for an argument.
  def updateCommandLine(self, graph, task, data, nodeID, nodeType):

    # Update the command line depending on whether the argument points to an input/output file
    # or an option.
    if nodeType == 'option': self.addOption(graph, task, data, nodeID)
    elif nodeType == 'input': self.processFiles(graph, task, data, nodeID, isInput = True)
    else: self.processFiles(graph, task, data, nodeID, isInput = False)

  # Process file inputt/outputs.
  def processFiles(self, graph, task, data, nodeID, isInput):

    # Check if the node is a multinode and then handle accordingly.
    multinodeInput  = graph.getGraphNodeAttribute(task, 'multinodeInput')
    multinodeOutput = graph.getGraphNodeAttribute(task, 'multinodeOutput')

    # If this is a daughter node, disregard. All daughter nodes are handled when the parent
    # node is processed.
    if graph.getGraphNodeAttribute(nodeID, 'isDaughterNode'): pass

    # If this is a parent node, process the node and its daughters.
    # FIXME HANDLE STDOUT FOR SUBPHASE FILES.
    elif isInput and nodeID == multinodeInput: self.addSubphaseFiles(graph, task, data, nodeID, isInput)
    elif not isInput and nodeID == multinodeOutput: self.addSubphaseFiles(graph, task, data, nodeID, isInput)

    # If this is a single output node.
    else: self.addFiles(graph, task, data, nodeID, isInput)

  # Get all the command arguments for subphase input or output files.
  def addSubphaseFiles(self, graph, task, data, nodeID, isInput):

    # Initialise variables.
    i = 0

    # Get the daughter nodes.
    nodeIDs = [nodeID] + graph.getGraphNodeAttribute(nodeID, 'daughterNodes')

    # Check that the number of node IDs is the same as the number of subphases.
    #TODO ERROR
    if len(nodeIDs) != data.noSubphases: print('ERROR - makefiles.addSubphaseFiles - 1'); exit(1)

    # Get the argument associated with the node.
    argument = self.getToolArgument(graph, task, nodeIDs[0], isInput)

    # Check if this node consolidates the multinodes.
    isConsolidate = True if graph.getGraphNodeAttribute(task, 'consolidate') else False

    # Loop over the input multinodes and add the values to the command line. The order is important here.
    # The values for the first multinode should be applied to all the divisions. If there are N subphases,
    # with M divisions, the first M command lines should be for the input/ouput files associated with the
    # first subphase, with the options in those M command lines being the M different values etc.
    for nodeID in nodeIDs:
      values = graph.getGraphNodeAttribute(nodeID, 'values')

      # Check if this node contains intermediate files.
      isIntermediate = graph.getGraphNodeAttribute(nodeID, 'isIntermediate')

      # If there are less values than the number of divisions, there is a problem, unless this is a
      # consolidation node. In this case, all of the inputs files are being used in the same command line
      # and the number of command lines is reduced down to the number of subphases, e.g. the number of
      # divisions is reset to one. If this is the case, consolidate the command lines.
      #TODO ERROR
      if len(values) != data.noDivisions and not isConsolidate: print('ERROR - makefiles.getSubphaseCommands - 1'); exit(1)

      # Loop over the values and update the command lines for the task.
      for value in values:
        lineValue = self.getValue(graph, task, nodeID, value, isInput)

        #TODO ADD METHODS TO MODIFY VALUE. E,G, STREAMS
        line = self.buildLine(argument, data.delimiter, lineValue)
        if line: data.commands[i].append(line)

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(value))
        else: data.outputs[i].append(str(value))

        # If this is an intermediate file, add to the list of intermediate files.
        if isIntermediate:
          if str(value) not in data.intermediates[i]: data.intermediates[i].append(str(value))

        # If this is not a consolidation node, increment the counter.
        if not isConsolidate: i += 1

      # If this is a consolidation node, the counter was not incremented for each value, since all the
      # values should be attached to the same command line. However, when moving to the next node (e.g.
      # the next subphase), the counter needs to be incremented.
      if isConsolidate: i += 1

  # Add option values to the command lines.
  def addOption(self, graph, task, data, nodeID):

    # TODO CHECK FOR INFORMATION ON MODIFYING THE ARGUMENT AND THE VALUE.
    # Get the argument and values for the option node.
    argument = self.getToolArgument(graph, task, nodeID, isInput = True)
    values   = graph.getGraphNodeAttribute(nodeID, 'values')

    # If there is only a single value, apply this to all the command lines.
    if len(values) == 1:
      lineValue = self.getValue(graph, task, nodeID, values[0], isInput = True)
      line      = self.buildLine(argument, data.delimiter, lineValue)
      if line:
        for i in range(0, data.noCommandLines): data.commands[i].append(line)

    # If there is more than one values, ensure that the number of values is consistent with the
    # pipeline execution structure.
    else:

      # Ensure that there as many values as there are divisions.
      #TODO ERROR
      if len(values) != data.noDivisions: print('ERROR - makefiles.addOption - 1:', nodeID, values, data.noDivisions); exit(1)

      # Loop over the subphases and divisions and update the command lines.
      i = 0
      for j in range(0, data.noSubphases):
        for value in values:
          lineValue = self.getValue(graph, task, nodeID, value, isInput = True)
          line      = self.buildLine(argument, data.delimiter, lineValue)
          if line: data.commands[i].append(line)
          i += 1

  # Add input or output files to the command line (this method is only called for nodes that are not multinodes).
  def addFiles(self, graph, task, data, nodeID, isInput):

    # TODO CHECK FOR INFORMATION ON MODIFYING THE ARGUMENT AND THE VALUE.
    # Get the argument and values for the file node.
    argument = self.getToolArgument(graph, task, nodeID, isInput)
    values = graph.getGraphNodeAttribute(nodeID, 'values')

    # Check if this task generates multiple nodes.
    isGeneratesMultipleNode = graph.getGraphNodeAttribute(task, 'generateMultipleOutputNodes')
    isConsolidate           = graph.getGraphNodeAttribute(task, 'consolidate')

    # Check if this node is associated with intermediate files.
    isIntermediate = graph.getGraphNodeAttribute(nodeID, 'isIntermediate')

    # Determine if the task outputs to stdout.
    isStdout = graph.getArgumentAttribute(task, nodeID, 'isStdout') if not isInput else False

    # If there is only a single file, attach to all of the command lines.
    if len(values) == 1:
      lineValue = self.getValue(graph, task, nodeID, values[0], isInput)
      line      = self.buildLine(argument, data.delimiter, lineValue)
      for i in range(0, data.noCommandLines):

        # If this task outputs to stdout, put the values into a structure to return.
        if isStdout: data.stdouts[i] = str('\t>> ' + lineValue  + ' \\')
        elif line: data.commands[i].append(line)

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(values[0]))
        else: data.outputs[i].append(str(values[0]))

        # Add to the intermediates if necessary.
        if isIntermediate and str(values[0]) not in data.intermediates[i]: data.intermediates[i].append(str(values[0]))

    # If this is a greedy task, add all the values to each command line.
    elif isInput and data.isGreedy:
      for i in range(0, data.noCommandLines):
        for value in values:
          lineValue = self.getValue(graph, task, nodeID, value, isInput)
          line      = self.buildLine(argument, data.delimiter, lineValue)
          if line: data.commands[i].append(line)

          # Add the files to the dependencies or outputs for the command line.
          data.dependencies[i].append(str(value))

          # Add to the intermediates if necessary.
          if isIntermediate and str(value) not in data.intermediates[i]: data.intermediates[i].append(str(value))

    # If this is an input for a task that generates multiple nodes, and there are as many values as
    # there are subphases, add the files in the correct order. If there are N divisions, the first
    # file is used for the first subphase and so the first N command lines etc.
    elif isInput and isGeneratesMultipleNode:
      i = 0
      for value in values:
        lineValue = self.getValue(graph, task, nodeID, value, isInput)
        line      = self.buildLine(argument, data.delimiter, lineValue)
        for j in range(0, data.noDivisions):
          if line: data.commands[i].append(line)

          # Add the files to the dependencies or outputs for the command line.
          data.dependencies[i].append(str(value))

          # Add to the intermediates if necessary.
          if isIntermediate and str(value) not in data.intermediates[i]: data.intermediates[i].append(str(value))

          # Increment the counter.
          i += 1

    # If this is a consolidation node. In this case, all of the inputs files are being used in the
    # same command line and the number of command lines is reduced down to the number of subphases,
    # e.g. the number of divisions is reset to one. If this is the case, consolidate the command lines.
    elif not isInput and isConsolidate:
      i = 0
      for value in values:
        lineValue = self.getValue(graph, task, nodeID, value, isInput)
        line      = self.buildLine(argument, data.delimiter, lineValue)

        # If the task outputs to stdout, store the values to return.
        if isStdout: data.stdouts[i] = str('\t>> ' + lineValue + ' \\')
        elif line: data.commands[i].append(line)

        # Add the files to the dependencies or outputs for the command line.
        data.outputs[i].append(str(value))

        # Add to the intermediates if necessary.
        if isIntermediate and str(value) not in data.intermediates[i]: data.intermediates[i].append(str(value))

        # Increment the counter.
        i += 1

    # If there are as many files as there are divisions, add the files in the correct order.
    elif not isGeneratesMultipleNode and len(values) == data.noDivisions:
      for i, value in enumerate(values):
        lineValue = self.getValue(graph, task, nodeID, value, isInput)
        line      = self.buildLine(argument, data.delimiter, lineValue)

        # If the task outputs to stdout, store the values to return.
        if isStdout: data.stdouts[i] = str('\t>> ' + lineValue + ' \\')
        elif line: data.commands[i].append(line)

        # Add the files to the dependencies or outputs for the command line.
        if isInput: data.dependencies[i].append(str(value))
        else: data.outputs[i].append(str(value))

        # Add to the intermediates if necessary.
        if isIntermediate and str(value) not in data.intermediates[i]: data.intermediates[i].append(str(value))

    # If there are a different number of files to subphases, there is a problem.
    #TODO ERROR
    else: print('ERROR - makefileErrors.addFiles'); exit(1)

  # Generate the makefiles for this execution of gkno.
  def generateMakefiles(self, struct, pipeline, gknoArguments, arguments):

    # Check if multiple makefiles were requested.
    mm = gknoArguments['GKNO-MULTIPLE-MAKEFILES'].longFormArgument
    self.isMultipleMakefiles = True if mm in arguments else False

    # Check if a makefile ID was supplied.
    mid = gknoArguments['GKNO-MAKEFILE-ID'].longFormArgument
    if mid in arguments: self.makefileID = arguments[mid][0]

    # Define the baseName for the makefiles.
    baseName = str(pipeline + '-' + self.makefileID) if self.makefileID else str(pipeline)

    # Loop over all the phases and set the names of all of the makefiles. Also link each
    # phase/subphase/division to the makefile.
    if self.isMultipleMakefiles:
      for phase in struct.phaseInformation:
  
        # Add the phase to the makefile name (if there are multiple phases).
        if phase not in self.makefileNames: self.makefileNames[phase] = {}
        if len(struct.phaseInformation.keys()) == 1: phaseName = baseName
        else: phaseName = str(baseName + '-phase' + str(phase))
  
        for subphase in range(1, struct.phaseInformation[phase].subphases + 1):
  
          # Add the subphase to the makefile name (if there are multiple subphases).
          if subphase not in self.makefileNames[phase]: self.makefileNames[phase][subphase] = {}
          if struct.phaseInformation[phase].subphases == 1: name = phaseName
          else: name = str(phaseName + '-subphase' + str(subphase))
  
          # Add the makefile names.
          if struct.phaseInformation[phase].divisions == 1: self.makefileNames[phase][subphase][1] = str(name + '.make')
          else:
            for division in range(1, struct.phaseInformation[phase].divisions + 1):
              self.makefileNames[phase][subphase][division] = str(name + '-division' + str(division) + '.make')

    # If only a single makefile is being produced, everything links to the same makefile.
    else:
      for phase in struct.phaseInformation:
        if phase not in self.makefileNames: self.makefileNames[phase] = {}
        for subphase in range(1, struct.phaseInformation[phase].subphases + 1):
          if subphase not in self.makefileNames[phase]: self.makefileNames[phase][subphase] = {}
          if struct.phaseInformation[phase].divisions == 1: self.makefileNames[phase][subphase][1] = str(baseName + '.make')
          else:
            for division in range(1, struct.phaseInformation[phase].divisions + 1):
              self.makefileNames[phase][subphase][division] = str(baseName + '.make')

  # Get the makefile name for a given phase, subphase and division.
  def getMakefileName(self, phase, subphase, division):
    return self.makefileNames[phase][subphase][division]

  # Open all of the required makefiles.
  def openFiles(self, graph ,struct, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath):

    # If there are not multiple makefiles being made, then there is no need to loop over all the
    # phases etc, as all phases point to the same makefile. In this event, just open the single
    # makefile.
    if not self.isMultipleMakefiles: self.singleFileHeader(graph ,struct, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath)
    else: self.multifileHeader(graph ,struct, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath)

  # Write the header text to a single makefile.
  def singleFileHeader(self, graph ,struct, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath):

    # Define the filehandle.
    filehandle = fh.fileHandling.openFileForWriting(self.makefileNames[1][1][1])

    # Add header text to the file.
    self.addHeader(graph, struct, filehandle, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath, self.makefileNames[1][1][1], 1)

    # Loop over all the phases, subphases and divisions.
    allIntermediates = []
    allOutputs       = []
    tempOutputs      = []
    for phase in self.makefileNames:
      i = 0
      if phase not in self.makefilehandles: self.makefilehandles[phase] = {}
      for subphase in self.makefileNames[phase]:
        if subphase not in self.makefilehandles[phase]: self.makefilehandles[phase][subphase] = {}
        for division in self.makefileNames[phase][subphase]:

          # Add the header, intermediate files and all output files for the phase.
          intermediates = self.getFiles(struct, phase, 'intermediates', i)
          outputs       = self.getFiles(struct, phase, 'outputs', i)

          # Add the values to the larger lists.
          for intermediate in intermediates:
            if intermediate not in allIntermediates: allIntermediates.append(intermediate)
          for output in outputs:
            if output not in tempOutputs: tempOutputs.append(output)

          # Add the makefile handle to the data structure.
          self.makefilehandles[phase][subphase][division] = filehandle

          # Increment the counter.
          i += 1

    # Remove output files that are also marked as intermediates.
    for output in tempOutputs:
      if output not in allIntermediates: allOutputs.append(output)

    # Add the intermediate and output files.
    self.addIntermediateFiles(allIntermediates, filehandle)
    self.addOutputFiles(allOutputs, filehandle)

    # Remove the file created on successful execution of the makefile.
    self.removeOk(filehandle)

  # Write header text to multiple makefiles.
  def multifileHeader(self, graph, struct, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath):

    # Loop over all the phases, subphases and divisions.
    for phase in self.makefileNames:
      i = 0
      if phase not in self.makefilehandles: self.makefilehandles[phase] = {}
      for subphase in self.makefileNames[phase]:
        if subphase not in self.makefilehandles[phase]: self.makefilehandles[phase][subphase] = {}
        for division in self.makefileNames[phase][subphase]:

          # Create a new filehandle and add the header text.
          name       = self.makefileNames[phase][subphase][division]
          filehandle = fh.fileHandling.openFileForWriting(name)

          # Add the header, intermediate files and all output files for the phase.
          self.addHeader(graph, struct, filehandle, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath, name, phase)
          tempIntermediates = self.getFiles(struct, phase, 'intermediates', i)
          tempOutputs       = self.getFiles(struct, phase, 'outputs', i)

          # If this is the final task in the makefile, all output files should be included as outputs, not
          # intermediates, even if so marked. If this is not followed, there could be phases that produce
          # no output files, which would ensure that the makefile would not execute.
          finalOutputs = self.getFinalTaskOutputs(struct, phase, i)

          # Remove final outputs from the intermediates.
          intermediates = []
          for intermediate in tempIntermediates:
            if intermediate not in finalOutputs: intermediates.append(intermediate)

          # Remove intermediate files from the outputs.
          outputs = []
          for output in tempOutputs:
            if output not in intermediates: outputs.append(output)

          # Add the intermediate and output files.
          self.addIntermediateFiles(intermediates, filehandle)
          self.addOutputFiles(outputs, filehandle)

          # Remove the file created on successful execution of the makefile.
          self.removeOk(filehandle)

          # Add the makefile handle to the data structure.
          self.makefilehandles[phase][subphase][division] = filehandle

          # Increment the counter.
          i += 1

  # Add header text to the file.
  def addHeader(self, graph, struct, filehandle, commitID, date, version, pipeline, sourcePath, toolPath, resourcePath, name, phase):

    # Add basic text about the gkno version.
    print('### gkno makefile', file = filehandle)
    print('### Generated using gkno version: ', version, ' (', date, ')', sep = '', file = filehandle)
    print('### gkno commit: ', commitID, sep = '', file = filehandle)
    print('### Pipeline: ', pipeline, sep = '', file = filehandle)
    print(file = filehandle)
    print('### Set the shell to bash.', file = filehandle)
    print('SHELL=/bin/bash', file = filehandle)
    print(file = filehandle)

    # Include the paths to tools and resources.
    print('### Paths to tools and resources.', file = filehandle)
    print('GKNO_PATH=', sourcePath, sep = '', file = filehandle)
    print('TOOL_BIN=', toolPath, sep = '', file = filehandle)
    print('RESOURCES=', resourcePath, sep = '', file = filehandle)
    print('MAKEFILE_ID=', name.rsplit('.make', 1)[0], sep = '', file = filehandle)
    print(file = filehandle)

    # Define the stdout and stderr.
    print('### Standard output and error files.', file = filehandle)
    print('STDOUT=$(PWD)/', name, '.stdout', sep = '', file = filehandle)
    print('STDERR=$(PWD)/', name, '.stderr', sep = '', file = filehandle)
    print('COMPLETE_OK=$(PWD)/', name, '.ok', sep = '', file = filehandle)
    print(file = filehandle)

    # Remove file on failed execution.
    print('### If the pipeline terminates unexpectedly, delete all files that were in', file = filehandle)
    print('### the process of being generated.', file = filehandle)
    print('.DELETE_ON_ERROR:', file = filehandle)
    print(file = filehandle)

    # Determine which tasks are used in the phase, find the corresponding tools and finally their paths.
    # Include these paths in the makefile.
    print('### Executable paths.', file = filehandle)
    for task in struct.phaseInformation[phase].tasks:
      tool = graph.getGraphNodeAttribute(task, 'tool')
      if tool in self.toolPaths: print(str(tool), file = filehandle)
    print(file = filehandle)

    # List phony arguments. This is used solely for the file created on successful execution of the pipeline.
    print('### List all PHONY targets. These are targets that are not actual files.', file = filehandle)
    print('.PHONY: DELETE_COMPLETE_OK', file = filehandle)
    print(file = filehandle)

  # Get files for the task and phase.
  def getFiles(self, struct, phase, fileType, i):
    files = []

    # Loop over the tasks for this phase.
    for task in struct.phaseInformation[phase].tasks:

      # Define the files to loop over.
      if fileType == 'intermediates': fileList = self.executionInfo[task].intermediates
      elif fileType == 'outputs': fileList = self.executionInfo[task].outputs

      # Get the files. If there are multiple makefiles, only take the values from the current phase, subphase
      # and division.
      for value in fileList[i]:
        if value not in files: files.append(value)

    # Return the files.
    return files

  # Return the output files from the final task in this phase.
  def getFinalTaskOutputs(self, struct, phase, i):
    files = []

    # Get the files.
    for value in self.executionInfo[struct.phaseInformation[phase].tasks[-1]].outputs[i]:
      if value not in files: files.append(value)

    # Return the files.
    return files

  # Add intermediate files to the makefile.
  def addIntermediateFiles(self, intermediates, filehandle):

    # Write intermediate files to the makefile header. Files marked as intermediate are removed during
    # execution of the pipeline. By being marked as intermediate, reexecution of the pipeline will not
    # commence to regenerate the intermediate files.
    print('### The following files are intermediates. If the pipeline is rerun, rules for creating', file = filehandle)
    print('### will not be rerun unless files prior to these rules have been updated.', file = filehandle)
    print('.INTERMEDIATE: ', end = '', file = filehandle)

    # Add all the intermediates to the makefile.
    for intermediate in intermediates: print(intermediate, end = ' ', file = filehandle)
    print(file = filehandle)
    print(file = filehandle)


  # Add output files to the makefile.
  def addOutputFiles(self, outputs, filehandle):

    # List all the output files created by this makefile.
    print('### List all of the files that are required outputs of the pipeline.', file = filehandle)
    print('all: ', end = '', file = filehandle)

    # Add all the output files to the makefile.
    for output in outputs: print(output, end = ' ', file = filehandle)
    print(file = filehandle)
    print(file = filehandle)

  # Prior to pipeline execution, remove the 'ok' file prodiced by a previous successful execution.
  def removeOk(self, filehandle):
    print('### Remove the file indicating successful completion of the pipeline. This file needs', file = filehandle)
    print('### to be recreated if the pipeline is rerun to indicate successful completion.', file = filehandle)
    print('DELETE_COMPLETE_OK:', file = filehandle)
    print('\t@rm -f $(COMPLETE_OK)', file = filehandle)
    print(file = filehandle)

  # Close all the open makefiles.
  def closeFiles(self):

    # If only a single makefile was created, only a single file needs to be closed.
    if not self.isMultipleMakefiles: 
      filehandle = self.makefilehandles[1][1][1]

      # Prior to closing the file, include instructions for generating an 'ok' file indicating that the
      # makefile was successfully executed.
      print('### Generate a file indicating successful execution of makefile.', file = filehandle)
      print('$(COMPLETE_OK):', file = filehandle)
      print('\t@touch $(COMPLETE_OK)', file = filehandle)

      # Close the file.
      fh.fileHandling.closeFile(filehandle)

    # If multiple files were opened, close them all.
    else:
      for phase in self.makefilehandles:
        for subphase in self.makefilehandles[phase]:
          for division in self.makefilehandles[phase][subphase]:
            filehandle = self.makefilehandles[phase][subphase][division]

            # Prior to closing the file, include instructions for generating an 'ok' file indicating that the
            # makefile was successfully executed.
            print('### Generate a file indicating successful execution of makefile.', file = filehandle)
            print('$(COMPLETE_OK):', file = filehandle)
            print('\t@touch $(COMPLETE_OK)', file = filehandle)

            # Close the file.
            fh.fileHandling.closeFile(filehandle)

  # Add the command lines to the makefiles.
  def addCommandLines(self, graph, struct):

    # Loop over the phases, subphases and divisions.
    for phase in self.makefileNames:
      i = 0
      for subphase in self.makefileNames[phase]:
        for division in self.makefileNames[phase][subphase]:

          # Get the filehandle.
          filehandle = self.makefilehandles[phase][subphase][division]

          # Loop over the tasks for this makefile adding the command lines.
          for task in struct.phaseInformation[phase].tasks:
            print('### Command line information for the following task(s):', file = filehandle)
            print('### ', task, ' (', graph.getGraphNodeAttribute(task, 'tool'), ')', sep = '', file = filehandle)

            # Only include the first output in the rule. If there are additional outputs, these are handled after
            # the rule in the makefile.
            print(self.executionInfo[task].outputs[i][0], ':', sep = '', end = ' ', file = filehandle)
            for dependency in self.executionInfo[task].dependencies[i]: print(dependency, end = ' ', file = filehandle)
            print(file = filehandle)

            # Print to screen the task being executed.
            print('\t@echo -e "Executing task(s): ', task, '...\c"', sep = '', file = filehandle)

            # Print the command line.
            for line in self.executionInfo[task].commands[i]: print(line, file = filehandle)

          # Increment the counter.
          i += 1

  #######################################################
  ### Static methods for getting makefile information ###
  #######################################################

  # Return the argument to be written to the command line (and consequently, that stored in the commands
  # data structure). It is usually the case that the gkno argument does not correspond to the tool
  # argument.
  @staticmethod
  def getToolArgument(graph, task, nodeID, isInput):

    # If the argument is for an input file.
    if isInput:
      commandLineArgument = graph.getArgumentAttribute(nodeID, task, 'commandLineArgument')
      modifyArgument      = graph.getArgumentAttribute(nodeID, task, 'modifyArgument')

    # And if the argument is for an output file.
    else: 
      commandLineArgument = graph.getArgumentAttribute(task, nodeID, 'commandLineArgument')
      modifyArgument      = graph.getArgumentAttribute(task, nodeID, 'modifyArgument')

    # Return the argument to be used on the command line.
    if modifyArgument == 'omit': return None
    else: return commandLineArgument

  # Similar method to the getToolArgument except for the associated value.
  @staticmethod
  def getValue(graph, task, nodeID, value, isInput):

    # If the argument is for an input file.
    if isInput: modifyValue = graph.getArgumentAttribute(nodeID, task, 'modifyValue')

    # And if the argument is for an output file.
    else: modifyValue = graph.getArgumentAttribute(task, nodeID, 'modifyValue')

    # Return the argument to be used on the command line.
    if modifyValue == 'omit': return None
    else: return value

  # Build a line of the command line.
  @staticmethod
  def buildLine(argument, delimiter, value):

    # If neither the argument or the value are populated, return None.
    if not argument and not value: return None

    # If the value is defined, but the argument is not, this is a tool that does not use arguments on the
    # command line and so the command should be the value only.
    elif not argument: return '\t' + str(value) + ' \\'

    # If only the argument is defined, this is a flag, so only the argument is returned.
    elif not value: return '\t' + str(argument) + ' \\'

    # Finally, if both are defined, return the correctly delimited argument, value pair.
    else: return '\t' + str(argument) + str(delimiter) + str(value) + ' \\'
    line = '\t' + str(argument) + str(delimiter) + str(value) + ' \\'

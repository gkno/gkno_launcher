#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import os
import sys

class gknoErrors:

  # Initialise.
  def __init__(self):
    self.hasError  = False
    self.text      = []

  # Format the error message and write to screen.
  def writeFormattedText(self, errorType):
    firstLine = True
    secondLine = False
    maxLength = 93 - 5
    print(file = sys.stderr)
    for line in self.text:
      textList = []
      while len(line) > maxLength:
        index = line.rfind(' ', 0, maxLength)
        if index == -1:
          index = line.find(' ', 0, len(line))
          if index == -1:
            textList.append(line)
            line = ''
          else:
            textList.append(line[0:index])
            line = line[index + 1:len(line)]
        else:
          textList.append(line[0:index])
          line = line[index + 1:len(line)]

      if line != '' and line != ' ': textList.append(line)
      line = textList.pop(0)
      while line.startswith(' '): line = line[1:]

      if firstLine and errorType == 'error':
        print('ERROR:   %-*s' % (1, line), file=sys.stderr)
      elif firstLine and errorType == 'warning':
        print('WARNING: %-*s' % (1, line), file=sys.stderr)
      elif secondLine:
        print('DETAILS: %-*s' % (1, line), file=sys.stderr)
        secondLine = False
      else:
        print('         %-*s' % (1, line), file=sys.stderr)
      for line in textList:
        while line.startswith(' '): line = line[1:]

        if secondLine: print('DETAILS: %-*s' % (1, line), file=sys.stderr)
        else: print('         %-*s' % (1, line), file=sys.stderr)

      if firstLine:
        print(file=sys.stderr)
        firstLine = False
        secondLine = True

    # Clear self.text. If a warning was given, gkno will not terminate and so self.text may be reused.
    self.text = []

  ##################
  # Terminate gkno #
  ##################
  def terminate(self):
    print(file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    print('  TERMINATED: Errors found in running gkno.  See specific error messages above for resolution.', file=sys.stderr)
    print('================================================================================================', file=sys.stderr)
    exit(2)

  #######################################
  # Errors with the tool/pipeline name. #
  #######################################

  # gkno is being run in tool mode, but a pipeline name was supplied, or vice versa.
  def suggestMode(self, providedName, suggestedName, mode):
    if mode == 'tool': usage = 'gkno pipe ' + suggestedName + ' [options]'
    else: usage = 'gkno ' + suggestedName + ' [options]'

    # If the mode is 'tool', the alternative mode is 'pipeline' and vice versa.
    alternativeMode = 'tool' if mode == 'pipeline' else 'pipeline'

    self.text.append('Invalid ' + mode + ' name.')
    self.text.append('gkno is being run in ' + mode + ' mode, but the ' + mode + ' name provided is invalid. The provided name is, however, ' + \
    'a valid ' + alternativeMode + '. If this is not the intended tool/pipeline, please check the provided command line. If it is, please ' + \
    'use the following syntax:')
    self.text.append('\t')
    self.text.append('\t' + usage)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The provided name is neither a tool or a pipeline. Suggest the mode and name that is
  # closest to what was typed.
  def suggestMostLikely(self, mode, providedName, mostLikelyMode, mostLikelyName):

    # Define the usage syntax.
    if mostLikelyMode == 'tool': usage = 'gkno ' + mostLikelyName + ' [options]'
    else: usage = 'gkno pipe ' + mostLikelyName + ' [options]'

    self.text.append('Invalid tool/pipeline name.')
    self.text.append('gkno is being run in ' + mode + ' mode, but the given ' + mode + ' name is neither a valid tool or pipeline. The ' + \
    'provided name is most similar to the ' + mostLikelyMode + ', ' + mostLikelyName + '. If this was not the intended mode of operation, ' + \
    'please check the provided mode of operation (tool or pipeline) and the name. If this was the intended mode of operation, please use the ' + \
    'syntax:')
    self.text.append('\t')
    self.text.append('\t' + usage)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ##################################
  # Errors with configuration file #
  ##################################

  # The help class cannot find the tool. Most likely a problem with the configuration file.
  def problemWithTool(self, tool):
    self.text.append('Problem with configuration file for tool: ' + tool)
    self.text.append('Help cannot be displayed for the requested tool \'' + tool + '\'. A configuration file for the tool exists, however ' + \
    'the contents have not been successfully parsed. Please type \'gkno <tool>\' without the request for help. This should display an error ' + \
    'with the configuration file that requires fixing prior to requesting help with the tool.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A tool argument conflicts witht a gkno argument.
  def gknoToolError(self, config, graph, task, tool, longFormArgument, shortFormArgument, gknoArgument, isLongFormConflict):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Argument conflict.')
    text = 'The tool \'' + tool + '\''
    if config.isPipeline: text += ', used by task \'' + task + '\''
    text += ', has the argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' defined, but this conflicts with the gkno specific ' + \
    'argument \'' + gknoArgument + '\' as defined in the gkno configuration file. Please ensure that all of the tool arguments are unique and do ' + \
    'not conflict with gkno arguments.'
    self.text.append(text)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  #####################################
  # Error with pipeline construction. #
  #####################################

  # The pipeline contains an isolated node.
  def isolatedNodes(self, graph, config, isolatedNodes):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Isolated node in pipeline.')
    self.text.append('The following nodes do not share any files with any other task in the pipeline. This may be by design, but is often ' + \
    'a sign that the pipeline configuration file is not complete.')
    self.text.append('\t')
    for nodeID in isolatedNodes: self.text.append('\t' + nodeID)
    self.text.append('\t')
    self.writeFormattedText(errorType = 'warning')

  # Attempt to construct a filename when the basenode hasn't been set.
  def unsetBaseNode(self, graph, config, task, argument, baseArgument):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    self.text.append('Attempt to construct a filename from a non-existent file.')
    self.text.append('Task \'' + task + '\', argument \'' + argument + '\' has not been set on the command line and so is being constructed ' + \
    'using instructions from the tool (' + tool + ') configuration file. The construction uses the value of argument \'' + baseArgument + \
    '\' from the same task, but this has not been set. This problem is likely caused by an incomplete pipeline configuration file. ' + \
    'The argument \'' + baseArgument + '\' for task \'' + task + '\' should appear in one of the nodes in the pipeline configuration file; ' + \
    'either with a pipeline argument that is set as required, or as linked to a different task/argument in the pipeline. Please check the ' + \
    'pipeline configuration file for errors.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Attempt to get information from a non-existent node.
  def nodeNotInGraph(self, graph, config, nodeID, routine):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Error adding values to node')
    self.text.append('The routine \'' + routine + '\' attempted to get information about the node with ID \'' + nodeID + '\' but this node ' + \
    'is not in the pipeline graph.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # An output file has no name and no instructions on how to create it for a tool.
  def noToolOutputFilename(self, task, longFormArgument, shortFormArgument):
    self.text.append('Unable to set output filename for task: ' + task)
    self.text.append('The task \'' + task + '\' requires the name of an output file to be set by the user as the tool configuration file does ' + \
    'not provide instructions on how to construct the filename. Please perform one of the possible solutions:')
    self.text.append('\t')
    self.text.append('1. Provide instructions in the \'' + task + '\' configuration file describing how to construct the filename.')
    self.text.append('2. Set the filename using the argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' <filename>.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # An output file has no name and no instructions on how to create it.
  def noOutputFilename(self, task, tool, longFormArgument, shortFormArgument, pipelineArgument):
    self.text.append('Unable to set output filename for task: ' + task)
    self.text.append('The task \'' + task + '\' using tool \'' + tool + '\' requires the name of an output file to be set by the user as the ' + \
    'tool configuration file does not provide instructions on how to construct the filename and this file node is not connected to any other ' + \
    'tasks in the pipeline which might set the value for it. Please perform one of the possible solutions:')
    self.text.append('\t')
    self.text.append('1. Link this argument to another task in the pipeline which already has a set value.')
    self.text.append('2. Provide instructions in the \'' + tool + '\' configuration file describing how to construct the filename.')
    if pipelineArgument[0] == None: self.text.append('3. Set the filename using the syntax \'--' + task + ' [' + longFormArgument + ' <filename>].')
    else: self.text.append('3. Set the filename using ' + pipelineArgument[0] + ' <filename>.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  #################################
  # Errors with the command line. #
  #################################

  # A required pipeline argument is missing.
  def missingPipelineArgument(self, graph, config, argument, shortForm, description):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('The required command line argument ' + argument + ' (' + shortForm + ') is missing.')
    self.text.append('This argument is described as the following: ' + description)
    self.text.append('\t')
    self.text.append('Check the usage information for all required arguments.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A required argument is missing.
  def missingArgument(self, graph, config, task, argument, shortForm, description, isPipeline):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('A required command line argument is missing.')
    if isPipeline:
      self.text.append('The task \'' + task + '\' requires the argument \'' + argument + ' (' + shortForm + ')\' to be set, but it has ' + \
      'not been specified on the command line. This argument cannot be set using a pipeline argument and consequently must be set using the syntax:')
      self.text.append('\t')
      self.text.append('./gkno pipe <pipeline name> --' + task + ' [' + argument + ' <value>] [options]')
      self.text.append('\t')
      self.text.append('This argument is described as the following: ' + description)
      self.text.append('\t')
      self.text.append('It is recommended that the pipeline configuration file be modified to ensure that all arguments required by the pipeline ' + \
     'have a command line argument defined in the pipeline configuration file. Please see the documentation for further information on how this ' + \
      'can be accomplished.')

    # For tool mode.
    else:
      self.text.append('The tool \'' + task + '\' requires the argument \'' + argument + ' (' + shortForm + ')\' to be set, but it has ' + \
      'not been specified on the command line. ')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A file extension is invalid.
  def invalidExtension(self, filename, extensions, longForm, shortForm, task, argument, shortFormArgument):
    self.text.append('Incorrect extension on file: ' + filename)

    # If this file can be set with a pipeline argument, indicate the values.
    if longForm != None:
      self.text.append('The file defined for argument \'' + longForm + ' (' + shortForm + ')\' must take one of the following extensions:')

    # If this file is associated with an argument set directly to the tool using the syntax:
    # 'gkno pipe <pipeline name> --task [argument value]', indicate the task and argument and
    # the allowed extensions.
    else:
      self.text.append('The file defined for task \'' + task + '\', argument \'' + argument + ' (' + shortFormArgument + ')\' must take one \
of the following extensions:')

    # List the allowed extensions and write the error message.
    for counter, extension in enumerate(extensions): self.text.append('\t' + str(counter + 1) + ': ' + extension)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Invalid data type.
  def invalidDataType(self, graph, config, longFormArgument, shortFormArgument, description, value, expectedDataType):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('A command line argument was given an invalid value.')
    self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' was given the value \'' + value + \
    '\'. This value is invalid. The expected data type for this argument is \'' + expectedDataType + '\'. This argument is described as: ' + \
    description)
    self.text.append('\t')
    self.text.append('Please provide a valid value for this argument.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Multiple parameter sets were specified.
  def multipleParameterSetsSpecified(self, graph, config):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Multiple parameter set were specified on the command line.')
    self.text.append('Each tool or pipeline can be run using a set of predefined values contained in an parameter set using the --parameter-set ' + \
    '(-ps) argument on the command line. Only one parameter set can be defined on the pipeline, however multiple were set. Please check the ' + \
    'command line and ensure that only one parameter set is defined.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The parameter set name was not specified.
  def noParamaterSetNameProvided(self, graph, config, isPipeline):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Missing parameter set name.')
    self.text.append('Each tool or pipeline can be run using a set of predefined values contained in a parameter set using the --parameter-set ' + \
    '(-ps) argument on the command line. The command line syntax is:')
    self.text.append('\t')
    if isPipeline: self.text.append('gkno pipe <pipeline name> --parameter-set <parameter set name> [options]')
    else: self.text.append('gkno <tool name> --parameter-set <parameter set name> [options]')
    self.text.append('\t')
    self.text.append('Please ensure that the parameter set name is included on the command line. Use the --help argument to see all of the ' + \
    'available parameter sets. If the parameter set is set and help requested, the parameters included in the parameter set will be displayed.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The name of the file for the pipeline graph image is not provided.
  def noDrawFileProvided(self, graph, config):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Missing filename for pipeline image.')
    self.text.append('The command line argument \'--draw-pipeline-graph (-dpg)\' was set on the command line, but no filename was provided. ' + \
    'Please check the command line and include a name for the pipeline image file with the following syntax:')
    self.text.append('\t')
    self.text.append('--draw-pipeline-graph <filename>')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # A command line argument pointing to an argument list was specified, but the list is empty.
  def emptyArgumentList(self, argument, filename):
    print(file = sys.stderr)
    self.text.append('Empty argument list.')
    self.text.append('The command line argument \'' + argument + '\' was set on the command line, defining the file \'' + filename + \
    '\' as a list of values. The defined file is empty, however. Please ensure that a valid list of values is provided.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If an argument list is provided that uses a tool argument that has no pipeline argument.
  def noPipelineArgumentForlistArgument(self, tool, argument, toolArgument, listArgument):
    print(file = sys.stderr)
    self.text.append('Missing argument in pipeline configuration file.')
    self.text.append('The pipeline argument \'' + argument + '\' was set on the command line. This sets the argument \'' + toolArgument + '\' ' + \
    'in tool \'' + tool  + '\'. This argument defines a file containing a list of values. These values are then set on the command line using ' + \
    'the tool argument \'' + listArgument + '\'. There is no pipeline argument that points to this tool argument. Please ensure that the ' + \
    'pipeline configuration file contains an argument definition that points to this tool argument.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ######################################################
  # Errors with required files/directories/executables #
  ######################################################

  # If input files are missing, warn the user, but don't terminate gkno.
  def missingFiles(self, graph, config, files):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    tool = 'tool' if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'tool' else 'pipeline'
    self.text.append('Required files are missing.')
    self.text.append('The following files are required for this ' + tool + ' to run:')
    self.text.append('\t')
    for filename in files: self.text.append('\t' + filename)
    self.text.append('\t')
    self.writeFormattedText(errorType = 'warning')

  # If files/directories are present when they are not allowed to be, warn the user, but don't terminate gkno.
  def removeFiles(self, graph, config, files):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    tool = 'tool' if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'tool' else 'pipeline'
    self.text.append('Files are present that are not allowed.')
    self.text.append('The following files are present, but their presence will cause execution of the ' + tool + ' to fail:')
    self.text.append('\t')
    for filename in files: self.text.append('\t' + filename)
    self.text.append('\t')
    self.text.append('Please remove these files prior to executing the ' + tool + '.')
    self.text.append('\t')
    self.writeFormattedText(errorType = 'warning')

  # If input files are missing, warn the user, but don't terminate gkno.
  def missingOutputDirectory(self, graph, config, directory):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text = ['Output directory does not exist.']
    self.text.append('The output directory was defined as \'' + directory + '\'. This directory does not exist. Please check that the specified \
directory is correct, or create prior to execution of gkno. Automatic execution has been disabled.')
    self.writeFormattedText(errorType = 'warning')

  #######################################
  # Errors with constructing filenames. #
  #######################################

  # A argument required for building a filename is missing.
  def missingArgumentInFilenameConstruction(self, graph, config, task, longFormArgument, shortFormArgument, isPipeline):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('An argument required for constructing a filename is missing.')
    if isPipeline:
      self.text.append('The task \'' + task + '\' in the pipeline is attempting to construct a filename using other supplied commands. The ' + \
      'command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' is required for this construction. Please ensure that ' + \
      'this argument is set.')
    else:
      self.text.append('gkno is attempting to the generate a filename using instructions from the tool configuration file. An argument required ' + \
      'to do this is missing, however. Please ensure that the argument \'' + longFormArgument + '\' is set.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()
  
  # As above, except, for the specific case where gkno is running in pipeline mode and the required argument is
  # not a pipeline argument.
  def missingArgumentInFilenameConstructionNotPipelineArgument(self, graph, config, task, argument):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('An argument required for constructing a filename is missing.')
    self.text.append('gkno is attempting to generate a filename using instructions from the tool configuration file. An argument required \
to do this is missing. The required argument is \'' + argument + '\' for task \'' + task + '\' and there is no pipeline argument that sets this \
value. The value can be set using the syntax \'--' + task + ' [' + argument + ' <value>]\', however it would be preferable if a pipeline \
argument existed to set this value. Please see the documentation to see how to include this in the pipeline configuration file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If constructing a filename with the 'define method' failed to produce a filename.
  def failedToConstructDefinedFilename(self, task, tool, argument):
    self.text.append('Failed to construct a filename.')
    self.text.append('An attempt to construct the filename for an argument in task \'' + task + '\' failed. This construction failed to produce ' + \
    'a filename, so there is an error in the construction process. This may result if the filename is being constructed using values obtained ' + \
    'from a different argument which has not been given a value. Please check the instructions for constructing the filename for argument \'' + \
    argument + '\' in the configuration file for tool \'' + tool + '\' and ensure that the instructions are well formed and that any other ' + \
    'arguments required in this construction are set.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If the number of output iterations is not equal to the number of input iterations, and is
  # not equal to one.
  def invalidNumberOfOutputIterations(self, task, longFormArgument, shortFormArgument, givenNumber, expectedNumber):
    self.text.append('Failed to populate output filenames.')
    self.text.append('The task \'' + task + '\' has been given multiple sets (' + str(expectedNumber) + ') of input arguments, so this task will ' + \
    'run multiple times in the execution of this pipeline. The output argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' is ' + \
    'defined and has a different number of data sets as the input. In the event that only one data set is defined, the values can be modified ' + \
    'to generate the correct number of data sets, however, this argument already has ' + str(givenNumber) + ' values defined. It is unclear how ' + \
    'to proceed. Please check if values for this output argument have been defined and that the number of given values is either consistent with ' + \
    'the number of input data sets or that only a single value is defined. Alternatively, if the output argument can be constructed, this ' + \
    'argument can be omitted from the command line.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The extension operation is unknown.
  def unknownExtensionModification(self, tool, argument, value):
    self.text.append('Error constructing filename.')
    self.text.append('The argument \'' + argument + '\' associated with the tool \'' + tool + '\' can have its filename constructed ' + \
    'using instructions contained in the tool configuration file. The extension for the file can be modified and the desired approach ' + \
    'is defined in the field \'modify extension\' in the \'construct filename\' section associated with the argument. The supplied value \'' + \
    value + '\' is not valid. Please check the tool configuration files entry for this argument and ensure that the supplied values are all ' + \
    'valid.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # An extension is being stripped from a file, but the file has the wrong extension.
  def stripWrongExtension(self, value, extension):
    self.text.append('Error constructing filename.')
    self.text.append('In constructing a filename, certain operations require that the extension be removed. The extension is reinstated, if ' + \
    'required. The filename being worked on is \'' + value + '\', but the expected extension is \'' + extension + '\'. Please check that the ' + \
    'instructions for constructing the filename contained in the tool configuration file are correct.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  def invalidExtensionInConstruction(self, task, tool, longFormArgument, baseArgument, values):
    self.text.append('Error constructing filename.')
    self.text.append('Task \'' + task + '\' using tool \'' + tool + '\' requires a file to be defined for the tool argument \'' + longFormArgument + \
    '\'. This file is constructed using the values already set for the argument \'' + baseArgument + '\' for the same tool. The files associated ' + \
    'with this argument do not have the expected extension, however, so the filename could not be created. An example of a filename with an ' + \
    'unrecognised extension is \'' + values[1][0] + '\'. Please check the tool configuration file for tool \'' + tool + '\' to check the ' + \
    'allowed extensions. If the filename was set on the command line, please provide an allowed extension. If not, please check the pipeline ' + \
    'configuration file and ensure that linked tools are compatible.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Attempt to strip non-existent text from filename.
  def failedToRemoveText(self, task, tool, argument, value, removeText, isPipeline):
    self.text.append('Failed to remove text in filename construction.')
    if isPipeline: text = 'The tool \'' + tool + '\' associated with task \'' + task
    else: text = 'The tool \'' + tool
    self.text.append(text + '\' has the filename associated with argument \'' + argument + '\' constructed using instructions in the tool ' + \
    'configuration file. The instructions state that the text \'' + removeText + '\' should be removed from the filename, but the text is not ' + \
    'at the end of the supplied value \'' + value + '\'. Please check the filename construction instructions, or ensure that the filename used ' + \
    'for constructing this filename ends with the specified text.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  #############################
  # Error with defined files. #
  #############################

  # A defined file is missing.
  def missingFileCommandLine(self, graph, config, argument, filename):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('File defined on the command line is missing.')
    self.text.append('The command line argument \'' + argument + '\' defines a file \'' + filename + '\', but this file does not exist. Please ' + \
    'check the command line and ensure that the requested file exists.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ################################
  # Error with executable files. #
  ################################

  # If there are any missing executables, terminate.
  def missingExecutables(self, graph, config, missingExecutableList):
    if config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-VERBOSE', 'values')[1][0]: print(file = sys.stderr)
    self.text.append('Missing executable files')
    self.text.append('The following executable files are not available, but are required:')
    self.text.append('\t')
    for executable in missingExecutableList: self.text.append(executable)
    self.text.append('\t')
    self.text.append('Please ensure that gkno has been built or updated.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ####################################
  # Errors with multiple runs/loops. #
  ####################################

  # If a multiple run and internal loop file were simultaneously defined.
  def internalLoopAndMultipleRuns(self):
    self.text.append('Error with selected options.')
    self.text.append('Both the \'--multiple-runs (-mr)\' and the \'--internal-loop (-il)\' options were set on the command line. These options ' + \
    'are mututally exclusive, so they cannot both be set at the same time. Please check which of these options is required and remove the other ' + \
    'from the command line.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If more than one multlipe run or internal loop file were defined.
  def multipleMultipleRunsOrInternalLoops(self, hasMultipleRuns):
    self.text.append('Error with selected options.')
    if hasMultipleRuns: text = '--multiple-runs (-mr)'
    else: text = '--internal-loop (-il)'
    self.text.append('The \'' + text + '\' argument was set on the command line multiple times. This option defines a file containing a list of ' + \
    'arguments and associated values to be used and only a single file can be defined. Please ensure that the \'' + text + '\' argument only ' + \
    'appears once on the command line.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # Invalid value in the file.
  def invalidAttributeInMultipleRunsFile(self, filename, hasMultipleRuns, attribute, allowedAttributes):
    self.text.append('Invalid attribute in file: ' + filename)
    if hasMultipleRuns: text = '--multiple-runs (-mr)'
    else: text = '--internal-loop (-il)'
    self.text.append('The command line argument \'' + text + '\' was given the value \'' + filename + '\'. This file was found, but contains ' + \
    'the attribute \'' + attribute  + '\' which is not allowed in this file. The allowed attributes are:')
    self.text.append('\t')

    # Create a sorted list of the allowed attributes.
    allowed = []
    for attribute in allowedAttributes: allowed.append(attribute)

    # Add the attributes to the text to be written along with the expected type.
    for attribute in sorted(allowed):
      self.text.append(attribute + ':\t' + str(allowedAttributes[attribute][0]) + ', required = ' + str(allowedAttributes[attribute][1]))

    self.text.append('\t')
    self.text.append('Please remove or correct the invalid attribute in the configuration file.')
    self.writeFormattedText('error')
    self.terminate()

  # The data type is incorrect.
  def incorrectTypeInMultipleRunsFile(self, filename, hasMultipleRuns, attribute, value, expectedType):

    # Find the given type.
    isType    = self.findType(type(value))
    needsType = self.findType(expectedType)
    if isType == None: isType = 'Unknown'
    if needsType == None: needsType = 'Unknown'

    if hasMultipleRuns: argument = '--multiple-runs (-mr)'
    else: argument = '--internal-loop'

    self.text.append('Invalid attribute value in file: ' + filename)
    text = 'The file specified with the command line argument \'' + argument + '\' contains the attribute \'' + attribute + '\'. This attribute '
    if isType == 'list' or isType == 'dictionary':  text += 'is given a value '
    else: text += 'is given the value \'' + str(value) + '\'. This value is '
    text += 'of an incorrect type (' + isType + '); the expected type is \'' + needsType + '\'. Please correct ' + \
    'this value in the file.'
    self.text.append(text)
    self.writeFormattedText('error')
    self.terminate()

  # An attribute is missing.
  def missingAttributeInMultipleRunsFile(self, filename, hasMultipleRuns, attribute, allowedAttributes):
    if hasMultipleRuns: argument = '--multiple-runs (-mr)'
    else: argument = '--internal-loop'

    self.text.append('Missing attribute in file: ' + filename)
    self.text.append('The command line argument \'' + argument + '\' defined a file from which to take values to apply. The supplied ' + \
    'file is missing an attribute that is required; all the required attributes are listed below:')
    self.text.append('\t')

    # Create a sorted list of the required attributes.
    requiredAttributes = []
    for attribute in allowedAttributes:
       if allowedAttributes[attribute][1]: requiredAttributes.append(attribute)

    # Add the attributes to the text to be written along with the expected type.
    for attribute in sorted(requiredAttributes): self.text.append(attribute + ':\t' + str(allowedAttributes[attribute][0]))

    self.text.append('\t')
    self.text.append('Please add the missing attributes to the file.')
    self.writeFormattedText('error')
    self.terminate()

  # A data set in the file is not a list.
  def incorrectTypeForDataSet(self, filename, hasMultipleRuns):
    if hasMultipleRuns: argument = '--multiple-runs (-mr)'
    else: argument = '--internal-loop'

    self.text.append('Invalid entry in file: ' + filename)
    self.text.append('The file provided with the command line argument \'' + argument + '\' contains an invalid entry in the \'values\' ' + \
    'section. The \'values\' section is a list of lists. Each of these lists should be values corresponding to the arguments defined ' + \
    'in the \'arguments\' section of the file (in the same order). Please check the file and ensure that it conforms to these expectations.')
    self.writeFormattedText('error')
    self.terminate()

  # A data set in the file has the wrong number of entries.
  def incorrectNumberOfValues(self, filename, hasMultipleRuns):
    if hasMultipleRuns: argument = '--multiple-runs (-mr)'
    else: argument = '--internal-loop'

    self.text.append('Invalid set of values in file: ' + filename)
    self.text.append('The file provided with the command line argument \'' + argument + '\' contains an invalid entry in the \'values\' ' + \
    'section. The \'values\' section is a list of lists. Each of these lists should be values corresponding to the arguments defined ' + \
    'in the \'arguments\' section of the file (in the same order). One of the lists in this file does not have the same number of values as ' + \
    'there are defined arguments. Please check the file and ensure that it conforms to these expectations.')
    self.writeFormattedText('error')
    self.terminate()

  # Multiple argument lists are defined.
  def multipleArgumentListsDefined(self, argument, listArgument):
    self.text.append('Multiple argument lists defined.')
    self.text.append('The argument \'' + argument + '\' provides a list of values that apply to the argument \'' + listArgument + '\'. Another ' + \
    'list argument has already been defined, however. gkno cannot accept multiple argument lists, or argument lists coupled with multiple runs/' + \
    'internal loop files.')
    self.writeFormattedText('error')
    self.terminate()

  # Multiple runs are disabled.
  def multipleRunsDisabled(self, task):
    self.text.append('Multiple argument lists defined.')
    self.text.append('Multiple runs or internal loops have been requested (using the \'--multiple-runs\' or \'--internal-loop\') commands. ' + \
    'Another argument on the command line defines a file containing a list of values which is implemented as a multiple run or internal loop. ' + \
    'Both of these definitions point to arguments in the same task (\'' + task + '\'). gkno only permits a single argument per task to have ' + \
    'multiple data sets. Please modify the command line to reflect this requirement.')
    self.writeFormattedText('error')
    self.terminate()

  # An unknown command line argument was requested in a multiple runs file.
  def unknownArgumentMultipleRun(self, argument, filename):
    self.text.append('Unknown argument: ' + argument)
    self.text.append('The argument \'' + argument + '\' was included in the multiple runs/internal loop json file \'' + filename + '\', but is ' + \
    'not a valid argument for this pipeline. Please check and amend the contents of this file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # An unknown command line argument was requested in a multiple runs file.
  def unknownPipelineArgumentMultipleRun(self, argument, filename):
    self.text.append('Unknown pipeline argument: ' + argument)
    self.text.append('The argument \'' + argument + '\' was included in the multiple runs/internal loop json file \'' + filename + '\', but is ' + \
    'not a valid argument for this pipeline. Please check and amend the contents of this file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ########################
  # Errors checking data #
  ########################

  # An argument is given multiple values when that isn't allowed.
  def givenMultipleValues(self, task, longFormArgument, shortFormArgument, values):
    self.text.append('Argument given multiple values')
    self.text.append('The command line argument \'' + longFormArgument + ' (' + shortFormArgument + ')\' associated with task \'' + task + '\' ' + \
    'was given multiple values, but this argument is not permitted to take multiple values. The supplied values are:')
    self.text.append('\t')
    for value in values: self.text.append(str(value))
    self.text.append('\t')
    self.text.append('Please ensure that this value is only set once.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ####################################
  # Errors with makefile generation. #
  ####################################

  # No output files to write out.
  def noOutputFileGeneratingMakefile(self, task, tool):
    self.text.append('Error constructing makefile.')
    self.text.append('The makefile generation is trying to get output files for the task \'' + task + '\' but none exist. Please ensure ' + \
    'that output files are either supplied on the command line, that instructions appear in the tool (\'' + tool + '\') configuration ' + \
    'file on how to construct the filename and that an output file argument is listed as required.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a task requires a streaming input, but no stream was piped to it, the argument identified
  # in the tool configuration file as accepting the stream (is stream) has its file streamed
  # to the tool. None of the tools arguments have been identified as fulfilling this role.
  def noArgumentsAcceptingStream(self, task, tool, isPipeline):
    self.text.append('Error constructing makefile.')
    if isPipeline: text = 'The task \'' + task + '\' using tool \'' + tool + '\''
    else: text = 'The tool \'' + tool + '\''
    self.text.append(text + ' requires a streaming input, but no stream was piped to it. In this case, the argument identified in the tool ' + \
    'configuration file as accepting the stream (with the \'is stream\' field) has its file streamed to the tool. None of the tools ' + \
    'arguments have been identified as fulfilling this role, however, so no file can be streamed to the tool. Please ensure that the ' + \
    'configuration file for tool \'' + tool  + '\' has an argument with the \'is stream\' field set to true. The file associated with this ' + \
    'argument can then be used to provide the stream.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a task requires a streaming input, but multipe streams were piped to it, the argument identified
  # in the tool configuration file as accepting the stream (is stream) has its file streamed
  # to the tool.
  def multipleArgumentsAcceptingStream(self, task, tool, arguments, isPipeline):
    self.text.append('Error constructing makefile.')
    if isPipeline: text = 'The task \'' + task + '\' using tool \'' + tool + '\''
    else: text = 'The tool \'' + tool + '\''
    self.text.append(text + ' requires a streaming input, but multiple file streams are set. The argument identified in the tool ' + \
    'configuration file as accepting the stream (with the \'is stream\' field) has its file streamed to the tool. Multiple arguments for ' + \
    'this tool have been identified as fulfilling this role, however, so gkno cannot determine which file to stream. Please ensure that only ' + \
    'one argument in the configuration file for tool \'' + tool + '\' has an argument with the \'is stream\' field set to true. Presently ' + \
    'the following argument have been set:')
    self.text.append('\t')
    for argument in arguments: self.text.append('\t' + argument)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # No files are associated with the streaming argument
  def noFilesForToolStream(self, tool, longFormArgument, shortFormArgument):
    self.text.append('Error constructing makefile.')
    self.text.append('The tool \'' + tool + '\' requires a streaming input, but no file has been defined for the input. Please provide a ' + \
    'value for \'' + longFormArgument + ' (' + shortFormArgument + ')\'.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  ####################
  # General methods. #
  ####################

  # Given a value, return a string representation of the data type.
  def findType(self, providedType):
    if providedType == str: return 'string'
    elif providedType == int: return 'integer'
    elif providedType == float: return 'float'
    elif providedType == bool: return 'Boolean'
    elif providedType == dict: return 'dictionary'
    elif providedType == list: return 'list'
    else: return None

































  #############
  # File errors
  #############

  # If the requested json file cannot be succesfully read into a data structure, terminate citing
  # the errors generated by the Python json handler.
  def jsonOpenError(self, newLine, error, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed json file: ' + filename
    self.text.append(text)
    text = str(error) + '.'
    self.text.append(text)
    self.writeFormattedText('error')
    self.hasError = True

  ################################
  # Tool configuration file errors
  ################################

  # If the tool configuration file is missing the dictionary heading tools, terminate.
  def missingToolsBlockInConfig(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file does not contain a 'tools' block. This block contains " + 'all the information for a tool and must be ' + \
    'present.  Please check the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a field is defined in the configuration file, that gkno does not understand, terminate.
  def undefinedFieldInConfig(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    if ',' in field: field = field.replace(',', ' -> ')
    text = "The configuration file contains the field '" + field + "' for tool '" + tool + "'.  This field is not a valid entry for the " + \
    'configuration file.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a field is required by gkno and it does not appear in the configuration file, terminate.
  def missingRequiredFieldInConfig(self, newLine, filename, tool, missingVariables):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The following required variables for tool '" + tool + "' are missing from the configuration file:"
    self.text.append(text)
    for field in missingVariables:
      if ',' in field: field = field.replace(',', ' -> ')
      self.text.append('\t' + field)

    self.writeFormattedText()
    self.hasError = True

  # If the data type in the config file is different to that expected (as defined by the same
  # config file), terminate.
  def differentDataTypeInConfig(self, newLine, filename, tool, field, given, defined):
    if ',' in field: field = field.replace(',', ' -> ')
    if given == int: givenString = 'integer'
    elif given == float: givenString = 'float'
    elif given == bool: givenString = 'boolean'
    elif given == str: givenString = 'string'
    elif given == list: givenString = 'list'
    elif given == dict: givenString = 'dictionary'
    elif given == tuple: givenString = 'tuple'
    else: givenString = 'unknown'

    if defined == int: definedString = 'integer'
    elif defined == float: definedString = 'float'
    elif defined == bool: definedString = 'boolean'
    elif defined == str: definedString = 'string'
    elif defined == list: definedString = 'list'
    elif defined == dict: definedString = 'dictionary'
    elif defined == tuple: definedString = 'tuple'
    else: definedString = 'unknown'

    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = 'The data type (' + givenString + ") for field '" + field + "' "
    if tool != '': text += "in tool '" + tool + "' "
    text += 'is inconsistent with that expected (' + definedString + ').  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument appears in the argument order list that is not an argument associated with the
  # tool, terminate.
  def unknownArgumentInArgumentOrder(self, newLine, filename, tool, argument):
      if newLine: print(file=sys.stderr)
      text = 'Malformed configuration file: ' + filename
      self.text.append(text)
      text = "The configuration file for tool '" + tool + "' contains a list defining the order in which the arguments are to be written.  " + \
      'An unknown argument (' + argument + ') is present in this list.  Please check the configuration file and remove/repair invalid fields.'
      self.text.append(text)
      self.writeFormattedText()
      self.hasError = True

  # The argument order must contain a complete list of all arguments for the specified tool.  If
  # any arguments are missing from this list, terminate.
  def argumentMissingFromArgumentOrder(self, newLine, filename, tool, argument):
      if newLine: print(file=sys.stderr)
      text = 'Malformed configuration file: ' + filename
      self.text.append(text)
      text = "The configuration file for tool '" + tool + "' contains a list defining the order in which the arguments are to be written.  " + \
      'This list must contain all of the arguments defined for this tool, but the argument \'' + argument + "' is missing.  Please check " + \
      'the configuration file and remove/repair invalid fields.'
      self.text.append(text)
      self.writeFormattedText()
      self.hasError = True

  # If the argument is to be replaced in the event of the input being a stream, the field "replace
  # argument with" must be present.  If it is not, terminate.
  def replaceArgumentMissing(self, newLine, filename, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file for tool '" + tool + "' contains the argument '" + argument + "'.  This argument contains the field " + \
    '\'"if argument is stream" : "replace"\'.  This field instructs gkno that if the input to the tool is a stream, the command line argument ' + \
    'needs to be replaced by a different string.  The field "replace argument with" must, therefore, also be present.  This field is a ' + \
    'dictionary telling gkno what to replace the argument and value with, but is missing for this argument. Please check the configuration ' + \
    'file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument is being replaced (in the event of an input stream), the "replace argument with" dictionary must
  # include both an "argument" and "value".  If either of these fields are missing, terminate.
  def missingFieldInReplace(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The field '" + argument + "' in tool '" + tool + '\' needs to be a dictionary containing two fields: "argument" and "value".  ' + \
    "The field '" + field + "' is missing.  Please check the configuration file and remove/repair invalid fields."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is outputtng a stub, a list of output files must also be included.  If these are missing, teminate.
  def missingOutputsForStub(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' has the "stub" field set to true.  This means that the argument defines ' + \
    'an output stub.  In this case, there must also be a list of the filenames that will be produced by this tool.  These are defined using ' + \
    'the "outputs" field for this argument.  This is not present in this case.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the field 'list of input files' is associated with a tool, it must also include the 'apply by repeating
  # this argument' field.  Terminate if this is missing.
  def missingArgumentToRepeat(self, newLine, filename, tool, argument, field):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' has the "list of input files" field set to true.  This means that the ' + \
    "argument defines a file containing a list of input files.  In this case, there must also be reference to the command line argument " + \
    'which will accept these files as input.  This is defined using the "apply by repeating this argument" field for this argument.  This ' + \
    'is not present in this case.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the argument listed in 'apply by repeating this argument' is not an argument associated with this tool, 
  # terminate.
  def invalidArgumentInRepeat(self, newLine, filename, tool, argument, text, value):
    if newLine: print(file=sys.stderr)
    text = 'Malformed configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' for tool '" + tool + '\' contains the "apply by repeating this argument" field.  This field should ' + \
    "be accompanied by an argument associated with this tool.  The included value (" + value + ") is not a recognised command line argument " + \
    "for this tool.  Please check the configuration file and remove/repair invalid fields."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a Boolean was expected in the configuration file, but some other data type is present, terminate.
  def incorrectBooleanValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Command line error with argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' expects a Boolean as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
      "The value '" + value + "' is not accepted.  Please check and " + 'modify the command line.'
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Missing value for argument: ' + argument
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a Boolean as input.  gkno will accept the " + \
      "values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  " + 'Please check and modify the command line.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a Boolean was expected in the configuration file, but some other data type is present, terminate.
  def incorrectDefaultBooleanValue(self, newLine, task, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Default parameter error for argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a Boolean as input.  gkno will accept the " + \
    "values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  " + 'Please check and modify the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  def incorrectDefaultDataType(self, newLine, task, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect default data type for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The command line argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
    "'.  The given value (" + value + ') is not of this type.  Please check and rectify the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the 'additional files' section, terminate.
  def unknownFieldInAdditionalFiles(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field \'' + field + '\'.  This is not an allowed value.  ' + \
    'Please check and rectify the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the 'additional files' section, terminate.
  def unknownFieldInAdditionalFilesDictionary(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  This is a list of dictionaries, ' + \
    'and one of these contains the unknown field \'' + field + '\'.  This is not an allowed value.  Please check and rectify the tool ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the tyoe field does not have a valid value, terminate.
  def typeInAdditionalFieldsError(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  One of the dictionaries ' + \
    'within this has the field "type" set to \'' + field + '\'.  This field can only take the values "output" or "dependency".  Plase check ' + \
    'repair the toool configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a required field in the additional files section is missing, terminate.
  def missingFieldInAdditionalFiles(self, newLine, filename, tool, missingField, required):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  The following fields must ' + \
    'appear for each of the dictionaries in the list:'
    self.text.append(text)
    self.text.append('\t')
    for field in required: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'The field \'' + missingField + '\' is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional files has a set of defined filenames included, the type (output or dependency)
  # needs to be provided, but isn't.
  def missingTypeDefinedFilenamesInAdditionalFiles(self, newLine, filename, tool, missingField):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "defined filenames".  The following fields must ' + \
    'appear within this section:'
    self.text.append(text)
    self.text.append('\t')
    text = 'type: takes the value \'dependency\' or \'output\', depending on the nature of the additional files.'
    self.text.append(text)
    text = 'file list: the list of filenames to include as either dependencies or outputs.'
    self.text.append(text)
    self.text.append('\t')
    text = 'The field \'' + missingField + '\' is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional files has a set of defined filenames included, the type (output or dependency)
  # needs to be provided.  If this does not take the value 'output' or 'dependency', terminate.
  def unknownTypeDefinedFilenamesInAdditionalFiles(self, newLine, filename, tool, field):
    if newLine: print(file=sys.stderr)
    text = 'Unknown value in "additional files" section: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "defined filenames".  Within this section, there is a ' + \
    'list of filenames and the field "type".  The "type" field defines whether the additional files are dependencies for the tool or outputs ' + \
    'generated by the tool.  This must take the value "dependency" or "output".  The given value is: ' + field + '. Please check and repair the ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "link to thie argument" field in the "additional files" section contains an unknown
  # argument, terminate.
  def unknownArgumentInAdditionalFiles(self, newLine, filename, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unknown argument in "additional files" in configuration file: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' contains the field "from input arguments".  The "link to this argument" ' + \
    'field must be a valid argument for this tool.  The argument \'' + argument + '\' is unknown.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "remove extension" field in the "additional files" section is not a Boolean, terminate.
  def incorrectBooleanInAdditionalFiles(self, newLine, filename, tool, field, value):
    if newLine: print(file=sys.stderr)
    text = 'Invalid Boolean in "additional files" section of configuration file: ' + filename
    self.text.append(text)
    text = 'The "additional files" section for tool \'' + tool + '\' expects a Boolean value for the field \'' + field + '\'.  The given value \'' + \
    value + '\' is not a Boolean and is thus invalid.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ####################################
  # Pipeline configuration file errors
  ####################################

  # The pipeline workflow must consist of a set of ordered, uniquely named tasks.  The workflow
  # for the pipeline in question contains at least one non-uniquely named task.
  def multipleTasksWithSameName(self, newLine, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The pipeline workflow is an ordered list of tasks to perform.  Each of the tasks must be uniquely named, however, the task '" + task + \
    "' appears multiple times.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unrecognised section appears in the pipeline configuration file, terminate.
  def unknownSectionsInPipelineConfig(self, newLine, sections, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The configuration file contains the following sections that are unrecognised by gkno:'
    self.text.append(text)
    for section in sections: self.text.append("\t'" + section + "'")
    self.text.append('\t')
    text = 'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a dictionary was expected, but a different type obesrved, terminate.
  def pipelineSectionIsNotADictionary(self, newLine, sectionName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The '" + sectionName + "' section in the configuration file is not a dictionary of key/value pairs as required.  Please check " + \
    'and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a list was expected, but a different type obesrved, terminate.
  def pipelineSectionIsNotAList(self, newLine, sectionName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The section '" + sectionName + "' in the configuration file is not a list as required.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a task was observed that is not part of the workflow, terminate.
  def taskNotInWorkflow(self, newLine, sectionName, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The '" + sectionName + "' section in the configuration file contains a task (" + task + ') that is not in the pipeline workflow. ' + \
    'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline section is missing, terminate.
  def missingPipelineSection(self, newLine, sectionName, additionalText, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The configuration file does not contain the required '" + sectionName + "' section.  " + additionalText + '  Please check and ' + \
    'repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a task in the pipeline is associated with a tool with no configuration file of its own, terminate.
  def taskAssociatedWithNonExistentTool(self, newLine, task, tool, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The 'tools' in the configuration file contains a task (" + task + ') that is associated with a tool (' + tool + ') that is not ' + \
    'available in the gkno package.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing a description, terminate.
  def pipelineArgumentMissingDescription(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required description field. " + \
    "Please include a description of this argument for other users who may use this pipeline."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing the expected data type, terminate.
  def pipelineArgumentMissingType(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required description of the  " + \
    "data type.  Please include this \"type\" field for this argument in the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a pipeline argument is missing a short form, terminate.
  def pipelineArgumentMissingShortForm(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required short form.  All " + \
    "arguments are required to have a long form (--long-form) and a short form (-sf), for example.  Please include a short form value for this " + \
    "argument in the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If information from the arguments section is missing, terminate.
  def pipelineArgumentMissingInformation(self, newLine, argument, missingField, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in the arguments section of the configuration file does not contain the required field '" + \
    missingField + "'.  Please check and repair the configuration file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument links to a task not in the workflow, terminate.
  def invalidLinkedTaskInArguments(self, newLine, task, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The configuration file contains information for a task that is not present in the pipeline workflow (\'' + task + '\').  Please ' + \
    'check the configuration file and ensure that all pipeline arguments are for allowed tasks.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown argument, terminate.
  def invalidArgumentInConstruct(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\' contains the argument \'' + argument + '\' which is not a vaild ' + \
    'argument for this task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the construct filenames section contains an unknown field, terminate.
  def unknownFieldInConstruct(self, newLine, task, argument, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised field in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field \'' + field + \
    '\'.  The only fields allowed for the arguments in the "construct filenames" section are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If any of the required fields in the construct filenames section are missing, terminate.
  def missingFieldInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has certain required fields.  The task \'' + \
    task + '\', argument \'' + argument + '\' is missing the field \'' + field + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames, check that it is a dictionary. If
  # not, terminate.
  def additionalTextInConstructNotADict(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has the field "additional text from parameters" included.  This ' + \
    'field must be a dictionary, but is not.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames and the order field is missing,
  # terminate.
  def orderMissingInAdditionalTextInConstruct(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has certain required fields.  The task \'' + \
    task + '\', argument \'' + argument + '\' contains the "additional arguments from parameters" field.  When this field is present, a list ' + \
    'titled "order" must be present describing the order in which to include these parameters into the new filename.  Please check and repair ' + \
    'the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'additional text from parameters' field appears in construct filenames, and the order field is not a list, terminate.
  def additionalTextOrderInConstructNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section has the field "additional text from parameters" included.  The "order" ' + \
    'section within this should be a list of the additional pieces of text that will appear in the constructed filename.  This list must contain ' + \
    'all of the fields defined in the "additional text from parameters" section.  The "order" field is not a list in this configuration file.  ' + \
    'Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a name appearing in the "order" for the "additional text from parameters" is not defined with a link to a task
  # and argument, terminate.
  def missingTextDefinitionInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the field \'' + field + '\' in the "order" section in ' + \
    'task \'' + task + '\', argument \'' + argument + '\', but this isn\'t defined.  Each name appearing in the "order" - with the exception ' + \
    ' of "filename root" - needs to be defined with a link to a task and argument.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If required information is missing defining which argument to use in constructing a filename, terminate.
  def missingRootInformationInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section "filename root" field is set to "from argument" for task \'' + task + \
    '\', argument \'' + argument + '\'.  In this case, it is necessary that the "get root from task" and "get root from argument" fields are ' + \
    'also defined.  However, the field "' + field + '" is missing.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is "from argument" and the "remove input extension" field is not a Boolean, terminate.
  def invalidRootDataTypeInConstruct(self, newLine, task, argument, value, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field "remove input ' + \
    'extension" field.  This field is required to be a Boolean, but the given value (' + value  + ') is not. Please check and repair the ' + \
    'pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is "from argument" and the linked argument is invalid, terminate.
  def invalidRootArgumentInConstruct(self, newLine, task, argument, givenArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the field "get root from ' + \
    'argument" field.  This is set to \'' + givenArgument + '\' which is not vaild for the tool.  Please check and repair the pipeline ' + \
    'configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root text" field is missing when 'filename root' is set to 'from text', terminate.
  def filenameRootTextMissing(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing value in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' has the "filename root" field set to \'' + \
    'from text\'.  When this is set, the field \'filename root text\' must also be present with a string to be used as the root of the ' + \
    'filename.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the "filename root" field is set to an invalid value, terminate.
  def unknownRootValue(self, newLine, task, argument, field, allowed, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid value in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' has the "filename root" field set to \'' + \
    field + '\'.  This is not an allowed value for this field.  This field can take one of the following values:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowed: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If required information is missing defining which argument to use in constructing a filename, terminate.
  def missingFieldInTextDefinitionInConstruct(self, newLine, task, argument, field, additionalText, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing data in construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains a definition for \'' + field + '\' for task \'' + task + \
    '\', argument \'' + argument + '\' in the "additional text from parameters" section.  This definition is missing the required field \'' + \
    additionalText + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a defined argument for use in constructing a filename is not recognised, terminate.
  def invalidArgumentInConstructAdditional(self, newLine, task, argument, field, linkedTask, linkedArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the "additional text from parameters" section for task \'' + \
    task + '\', argument \'' + argument + '\'.  The defined parameter \'' + field + '\' is linked to the argument \'' + linkedArgument + \
    '\', but this argument is not recognised for the linked task \'' + linkedTask + '\'.  Please check and repair the configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a parameter is defined in the additional text section of the configuration file and it doesn't
  # appear in the "order" list, terminate.
  def definedTextNotInOrderInConstruct(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The pipeline configuration file "construct filenames" section contains the "additional text from parameters" section for task \'' + \
    task + '\', argument \'' + argument + '\'.  The defined parameter \'' + field + '\' does not appear in the "order" list and so cannot ' + \
    'be used in the filename construction. Please check the configuration file and ensure that all defined parameters appear in the "order" list.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the additional text field value for "remove extension" is not a Boolean, terminate.
  def invalidAdditionalDataTypeInConstruct(self, newLine, task, argument, additionalSection, value, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the construct filenames section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "construct filenames" section for task \'' + task + '\', argument \'' + argument + '\' contains the "additional text from ' + \
    'parameters" field.  Within this, the section titled \'' + additionalSection + '\' contains the field "remove extension".  This field is ' + \
    'required to be a Boolean, but the given value (' + value  + ') is not. Please check and repair the ' + \
    'pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an expected field is missingin the linkage section, terminate.
  def missingFieldInLinkage(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The field \'' + field + '\' is required ' + \
    'within this section, but is missing.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument not associated with the task, terminate.
  def invalidArgumentInLinkage(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\' contains the argument \'' + argument + '\' which is not associated with the ' + \
    'task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an unknown field, terminate.
  def unknownFieldInLinkage(self, newLine, task, argument, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised field in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' contains the field \'' + field + '\'.  The only ' + \
    'fields allowed for the arguments in the linkage section are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append('\t' + field)
    self.text.append('\t')
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown task, terminate.
  def invalidLinkedTask(self, newLine, task, argument, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid linked task in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' links to the task \'' + linkedTask + '\', which is ' + \
    'not in the pipeline workflow.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains an argument linked to an unknown argument, terminate.
  def invalidLinkedArgument(self, newLine, task, argument, linkedTask, linkedArgument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid linked argument in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' links to the task \'' + linkedTask + '\', argument \'' + \
    linkedArgument + '\'.  This is not a valid argument for this task.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the linkage section contains a list for the linkedTask or linkedArgument field and the
  # associated linkedTask/linkedArgument is not a list, fail.
  def linkedTaskArgumentIsNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Inconsistent lists in linkage section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The linkage section for task \'' + task + '\', argument \'' + argument + '\' contains a list for either the linked task or the ' + \
    'linked argument, but not both.  The \'link to this task\' and the \'link to this argument\' sections can be a list, but if either is, then ' + \
    'both must be.  The linked task list would contain the tasks from which to link an argument and the linked argument list would be the ' + \
    'arguments from each of the tasks (in the same order).  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unknown field appears in the "delete files" section, terminate.
  def unknownFieldInDeleteFiles(self, newLine, task, argument, field, filename):
    if newLine: print(file=sys.stderr)
    text = 'Unknown field in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The field \'' + field + \
    '\' is included for this argument, but this field is not valid.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the delete files section contains an invalid argument, terminate.
  def unknownArgumentInDeleteFiles(self, newLine, task, tool, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid argument in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  This task uses the tool \'' + \
    tool + '\' and this argument is not valid for this tool.  Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'output extension' list is included in the 'delete files' section and it is not
  # a list, terminate.
  def outputExtensionNotAListInDeleteFiles(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "output extension" field ' + \
    'is present for this argument, but it is not a list as expected.  The "output extension" list is used when the argument produces multiple ' + \
    'output files and so the specific files to be deleted are indicated with this list.  The "delete after task" field for this argument must ' + \
    'also be a list, indicating the task after which each file in the "output extension" list should be deleted.   Please check and repair ' + \
    'the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' field is missing, terminate.
  def deleteAfterTaskMissing(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Missing field in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'must be included for all arguments, but is missing here.  If the "output extension field is present, the "delete after task" field must ' + \
    'be a list with the same number of entries, otherwise, it is the task after whose successful operation the file should be deleted.  Please ' + \
    'check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' field is not a list when the "output extension" field is also present, terminate.
  def deleteAfterTaskNotAList(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Invalid data type in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'must be a list for this argument, since the "output extension" list was also included.  This list should include the task after which the ' + \
    'file should be deleted, for each of the file extensions included in the "output extension" list (in the same order).  ' + \
    'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the 'delete after task' list is not the same size as the 'output extension' list, terminate.
  def listsDifferentSizeInDeleteFiles(self, newLine, task, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The "delete after task" field ' + \
    'and the "output extension" lists are both included, but have different lengths.  For each extension in the "output extensions" list, there ' + \
    'must be a corresponding entry in the "delete after files" list describing which task to delete that particular file after.  Please check ' + \
    'and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the extension for the file to delete is not a valid extension for the tool, terminate.
  def invalidExtensionInDeleteFiles(self, newLine, task, argument, extension, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error in the "delete files" section of pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The "delete files" section for task \'' + task + '\' contains the argument \'' + argument + '\'.  The extension of the file ' + \
    'being deleted is set as \'' + extension + '\' but this is not the extension associated with outputs from this task.  Please check ' + \
    'and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #####################
  # Command line errors
  #####################

  # An unknown argument appears on the command line.
  def unknownArgument(self, newLine, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unknown command line argument: ' + argument
    self.text.append(text)
    text = "The argument '" + argument + "' is not associated with the tool or pipeline being executed.  Please check and repair the command line."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If commands for a specific tool are included, but the square brackets enclosing the arguments
  # are not terminated. fail.
  def unterminatedTaskSpecificOptions(self, newLine, task):
    if newLine: print(file=sys.stderr)
    text = 'Arguments for specific task are incomplete: ' + task
    self.text.append(text)
    text = 'Arguments for task \'' + task  + '\' are provided.  Arguments for a specific task must be enclosed in square brackets, but these ' + \
    'were not terminated.  Please check and amend the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ######################
  # Multiple runs errors
  ######################

  # If ths file containing the multiple runs data can't be found, terminate.
  def noMultipleRunFile(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'File not found: ' + filename
    self.text.append(text)
    text = "Multiple runs were requested with the --multiple-runs (-mr) command and the file '" + filename + "' was provided as the file " + \
    'containing the necessary information.  This file could not be found.  Please check the command line and the location of the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument appears in the multiple runs format list that is not an argument associated with the
  # tool, terminate.
  def unknownArgumentInMultipleRuns(self, newLine, filename, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs file: ' + filename
    self.text.append(text)
    text = 'The multiple runs file contains a list defining the command line arguments that will be modified in each run.  An unknown argument (' + \
    argument + ') is present in this list.  Please check the configuration file and remove/repair invalid fields.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a flag was given an invalid value in an parameter set, terminate.
  def flagGivenInvalidValueMultiple(self, newLine, filename, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised flag in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', in the multiple runs file expects flags as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
    "The value '" + value + "' is not accepted.  Please check the multiple runs file and rectify any errors in the data or order of the data."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the multiple runs file contains unexpected information for a Boolean value, terminate.
  def incorrectBooleanValueInMultiple(self, newLine, filename, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', in the multiple runs file expects Boolean values as input.  gkno will accept the values: 'true', 'True', 'false' or 'False'.  " + \
    "The value '" + value + "' is not accepted.  Please check the multiple runs file and rectify any errors in the data or order of the data."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a data type in the multiple runs file is not as expected, terminate.
  def incorrectDataTypeInMultiple(self, newLine, filename, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for in multiple runs file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += "', set in the multiple runs file expects a value of type '" + dataType + "'.  The given value (" + value + ') is not of this type.  ' + \
    'Please check the multiple runs file and rectify any errors in the data or order of the data.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # The data list must contain a multiple of the number of entries in the format of data list section.
  # gkno will read the expected format and then for each run, read the values for each value specified
  # in this list.  If there isn't an integral multiple, the values for each run are not given correctly,
  # so terminate.
  def incorrectNumberOfEntriesInMultipleJson(self, newLine, setID, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs input file: ' + filename
    self.text.append(text)
    text = 'The number of entries in the "values" section must be a multiple of the number of entries in the "arguments".  For each ' + \
    'makefile generated, the command line arguments defined in the "arguments" will be set with a value taken from the "values" ' + \
    'section.  This means that the "values" section is an ordered list of each argument in the format list repeated for the number ' + \
    'of runs required.  Please ensure that the multiple runs file is correctly built.'
    self.text.append(text)
    self.text.append('\t')
    text = 'The data set at fault is that with ID: ' + setID
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A required section is missing from the multiple runs file.
  def missingSectionMultipleRunsFile(self, newLine, filename, section):
    if newLine: print(file=sys.stderr)
    text = 'Malformed multiple runs input file: ' + filename
    self.text.append(text)
    text = 'The multiple-runs input file must contain two sections.  The first section is titled "arguments" and is a list ' + \
    'of the command line arguments for which data appears in the second section.  The second section is titled "values" and contains ' + \
    "the data.  The provided file is missing the '" + section + "' section.  Please check and repair the multiple runs file."
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #################
  # ParamaterSet errors
  #################

  # The requested information doesn't exist.
  def noParamaterSetInformation(self, newLine, path, name, parameterSet):
    if newLine: print(file=sys.stderr)
    self.text.append('No information for requested parameter set: ' + parameterSet)
    self.text.append(text)
    self.text.append('ParamaterSet information cannot be found.  A parameter set of the given name must be present in the configuration file (' + \
    path + name + '.json) or in the separate parameter set file (' + name + '_parameterSet.json) in the same directory.  The requested parameter ' + \
    'set (' + parameterSet + ') is not present in either of these files.  If the parameter set is being created, modify the external parameter ' + \
    'set file to contain this parameter set.')
    self.writeFormattedText()
    self.hasError = True

  # Each parameter set must include a description.
  def noParamaterSetDescription(self, newLine, parameterSet, filename):
    if newLine: print(file=sys.stderr)
    self.text.append('Malformed pipeline configuration file: ' + filename)
    self.text.append('The parameter set \'' + parameterSet + '\' does not contain a description as required.  Please check and repair the ' + \
    'configuration file.')
    self.writeFormattedText()
    self.hasError = True

  # Only one parameter set can be selected to avoid conflict between set parameters.
  def multipleParameterSets(self, newLine):
    if newLine: print(file=sys.stderr)
    self.text.append('Multiple parameter sets requested.')
    self.text.append('Parameter sets can be used to set certain parameters for the tool/pipeline.  Only one parameter set can be requested, ' + \
    'however.  Multiple parameter sets have been requested on the command line.  Please check the command line for repetition of the ' + \
    '--parameter-set (-ps) command and ensure that it appears only once (or not at all).')
    self.writeFormattedText()
    self.hasError = True

  # If the parameter set information for a Boolean value is not as expected, terminate.
  def incorrectBooleanValueInParamaterSet(self, newLine, name, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Error with argument (from parameter set): ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument '" + argument + "', set as part of the parameter set '" + name + "', expects a Boolean as input.  gkno will accept " + \
    "the values: 'true', 'True', 'false' or 'False'.  The value '" + value + "' is not accepted.  Please check the parameter set " + \
    'information in the configuration file (or parameter set file) and rectify any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the data type in the parameter set is not as expected, terminate.
  def incorrectDataTypeInParamaterSet(self, newLine, name, task, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    text = 'Incorrect data type for command line argument (in parameter set): ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The command line argument '" + argument + "', set as part of the parameter set '" + name + "', was specified for task '" + task + \
    "' and it expects a value of type '" + dataType + "'.  The given value (" + value + ') is not of this type.  Please check and rectify ' + \
    'the given command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a flag was given an invalid value in an parameter set, terminate.
  def flagGivenInvalidValueParamaterSet(self, newLine, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    text = 'Unrecognised flag for (parameter set) argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = 'If a flag argument is included in an parameter set, the value supplied with it must be either "set" or "unset" to instruct gkno ' + \
    "whether to include the argument on the command line or not.  The argument '" + argument + "' is a flag, but was supplied with the " + \
    "value '" + str(value) + "'.  Please check the entry for this argument in the parameter set section of the configuration file (or the " + \
    'separate parameter set configuration file).'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If there is an additional parameter sets file and it contains no parameter set information, terminate.
  def parameterSetsFileHasNoParameterSets(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with file: ' + filename
    self.text.append(text)
    text = 'The parameter sets file \'' + filename + '\' should only contain information about parameter sets for the tool/pipeline with which ' + \
    'it is associated.  This file does not contain the \'parameter sets\' block required.  Please check this parameter sets file for errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an parameter set description in an additional parameter set file has the same name as an parameter set in the
  # configuration file, terminate.
  def parameterSetNameAlreadyExists(self, newLine, parameterSet, filename):
    if newLine: print(file=sys.stderr)
    text = 'Multiple parameter set definitions with name: ' + parameterSet
    self.text.append(text)
    text = 'The parameter sets file \'' + filename + '\' contains an parameter set with the name \'' + parameterSet + '\', however, a ' + \
    'parameter set of this name is already present in the configuration file.  Please ensure that all of the parameter sets defined for a ' + \
    'specific tool/pipeline have unique names (only modify entries in the parameter sets file if possible).'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #################################
  # Errors with makefile generation
  #################################

  ##########################
  # Errors with dataChecking
  ##########################

  # If a file with multiple inputs contained can't be found, terminate.
  def noInputFileList(self, newLine, filename):
    if newLine: print(file=sys.stderr)
    text = 'File not found: ' + str(filename)
    self.text.append(text)
    text = "An input file list was included, but the file '" + str(filename) + "' could not be found.  Please check the command line and the " + \
    'location of the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the file containindg the list of input files is malformed (e.g. doesn't have the "filename
  # list" field and the format of this field is not a list, terminate.
  def malformedFilenameList(self, newLine, filename, task, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Malformed file list in file: ' + filename
    self.text.append(text)
    text = "The argument '" + argument + "' in task '" + task + "' defines a file containing a list of files that will be read in " + \
    'by the tool.  The format of the file is not recognised.  This file needs to be a json file with the key "filename list" defining a ' + \
    'list of files.  Please check and repair the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If multiple input files are designated as the filename constructor for constructing filenames, terminate
  # as gkno cannot determine which to use.
  def multipleFilenameConstructors(self, newLine, task, tool, argumentA, argumentB):
    if newLine: print(file=sys.stderr)
    text = 'Muliple files listed as filename constructors.'
    self.text.append(text)
    text = 'Multiple arguments for task \'' + task + '\' (tool: \'' + tool + '\') have the "use for filenames" field set to true.  If this ' + \
    'field is set to true, gkno will use this input file to construct other filenames, but if multiple arguments have this value set, gkno ' + \
    'cannot determine which argument to use.  The arguments \'' + argumentA + '\' and \'' + argumentB + '\' are both set to be used for ' + \
    'filename construction.  Please check and repair the configuration file for this tool.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an input filename is not defined and the tool configuration file indicates that the filename should not
  # be constructed according to rules in the pipeline configuration file, terminate as gkno requires a
  # filename.
  def missingFilenameNotToBeConstructed(self, newLine, task, tool, argument, shortForm, pipelineArgument, pipelineShortForm):
    if newLine: print(file=sys.stderr)
    text = 'Unable to construct missing filename.'
    self.text.append(text)
    text = 'A required filename is missing and cannot be constructed from other files as the "do not construct from input file" field has ' + \
    'been set in the tool configuration file.  The required file is for the task \'' + task + '\'.  This links to the tool \'' + tool + '\' and ' + \
    'the argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' within this tool.'
    self.text.append(text)
    self.text.append('\t')
    text = 'Please set the pipeline command line argument \'' + pipelineArgument
    if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
    text += '\' or check and modify the tool configuration file entry.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a filename is to be constructed, but no information was provided on how to construct it and the
  # task has multiple input files, gkno cannot determine which file to use for filename construction.
  # Terminate.
  def unknownFilenameConstructor(self, newLine, task, tool, argument):
    if newLine: print(file=sys.stderr)
    text = 'Unable to construct output filename.'
    self.text.append(text)
    text = 'The pipeline contains the task \'' + task + '\'.  This task uses the tool \'' + tool + '\'.  An output argument for this tool (' + \
    argument + ') needs a value, but was not set on the command line and has no instructions in the configuration file on how to construct ' + \
    'it.  This tool either has multiple inputs or the input file is also not specified, so gkno cannot construct the output file using the ' + \
    'input file as a template.'
    self.text.append(text)
    self.text.append('\t')
    text = 'Please make sure that all required arguments are set on the command line.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the extension for a file is not as expected, terminate.
  def fileExtensionError(self, newLine, task, argument, shortForm, link, filename, extension):
    if newLine: print(file=sys.stderr)
    text = 'Unexpected extension on file: ' + filename
    self.text.append(text)
    text = 'The file in question does not end with the expected extension \'' + extension + '\'.  This file is associated with task \'' + \
    task + '\', argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    if link != '':
      pipelineArgument  = link[0]
      pipelineShortForm = link[1]
      text += '\', which can be set directly on the command line using the pipeline argument \'' + pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
      text += '\'.'
    else: text += '\'.  '
    self.text.append(text)
    self.text.append('\t')
    text = 'Please check that all of the inputted files are correct.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a required field has not been set, terminate.
  def missingRequiredValue(self, newLine, task, argument, shortForm, isPipeline, pipelineArgument, pipelineShortForm):
    if newLine: print(file=sys.stderr)
    text = 'Required command line argument missing: '
    if pipelineArgument != '':
      text += pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ').'
    else:
      text += argument
      if shortForm != '': text += ' (' + shortForm + ').'
    self.text.append(text)
    text = 'Argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' for task \'' + task + '\' has not been set and is required for gkno to run.  '
    if pipelineArgument != '':
      text += 'This argument can be set from the command line with the pipeline argument \'' + pipelineArgument
      if pipelineShortForm != '': text += ' (' + pipelineShortForm + ')'
      text += '\'.  '
    text += 'Please set all required arguments for gkno to run.  For help with tool/pipeline operation, please use the --help argument for ' + \
    'extra information.'
    self.text.append(text)
    if isPipeline and pipelineArgument == '':
      self.text.append('\t')
      text = 'WARNING: This is a command for a tool internal to the pipeline and cannot be set directly on the command line.  It is likely ' + \
      'that this argument should be set using the linkage section of the configuration file.  Please check that this is the case.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # The given value for a parameter is of an unexpected type.
  def incorrectDataType(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Incorrect data type for command line argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The command line argument '" + a + "' expects a value of type '" + dataType + "'.  The given value (" + value + \
      ') is not of this type.  Please check and rectify the given command line.'
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Incorrect data type for command line argument: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The command line argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
      "'.  The given value (" + value + ') is not of this type.  Please check and rectify the given command line.'
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A command line argument appears on the command line multiple times.  Each argument can only be
  # set once to avoid confilct between requested parameters.
  def multipleDefinitionsForSameArgument(self, newLine, task, argument, shortForm):
    if newLine: print(file=sys.stderr)
    text = 'Multiple definitions for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = "The argument was specified multiple times for the task '" + task + "'.  In order to specify the same command line argument " + \
    'multiple times, the configuration file (for the associated tool) must contain \' "allow multiple definitions" : true\' in the definition ' + \
    'of the argument.  Please check the command line and if this argument should be allowed multiple definitions, ensure that the ' + \
    'corresponding configuration file reflects this.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # A flag is defined multiple times.
  def multipleDefinitionsForFlag(self, newLine, task, argument, shortForm):
    if newLine: print(file=sys.stderr)
    text = 'Multiple definitions for command line argument: ' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    self.text.append(text)
    text = 'The command line argument (' + argument + ") for task '" + task + "' is a flag.  This argument can only appear on the command " + \
    'line once, but it is defined multiple times.  Please check the command line for repetition of this flag.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Non-flag arguments require a value to be set.
  def missingArgumentValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Missing value for argument: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' expects a value of type '" + dataType + "', but no value was provided.  Please check the command line."
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Missing value for argument: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "' and it expects a value of type '" + dataType + \
      "', but no value was provided.  Please check the command line."
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # Flags should not be accompanies be a value.
  def flagGivenValue(self, newLine, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value):
    if newLine: print(file=sys.stderr)
    if argumentType == 'tool' or argumentType == 'pipeline':
      a  = argument if argumentType == 'tool' else pipeArgument
      sf = shortForm if argumentType == 'tool' else pipeShortForm
      text = 'Value given to flag: ' + a
      if sf != '': text += ' (' + sf + ')'
      self.text.append(text)
      text = "The argument '" + a + "' is a flag and doesn't expect a value to be supplied.  The value '" + value + "' was provided on the " + \
      "command line.  Please check the given command line."
      self.text.append(text)
    elif argumentType == 'pipeline task':
      text = 'Value given to flag: ' + argument
      if shortForm != '': text += ' (' + shortForm + ')'
      self.text.append(text)
      text = "The argument '" + argument + "' was specified for task '" + task + "'.  This argument is a flag and doesn't expect a value to " + \
      "be supplied.  The value '" + value + "' was provided on the command line.  Please check the given command line."
      self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is instructed to accept a stream as input, but instructions are not included in the
  # configuration file, terminate.
  def noInputStreamInstructions(self, newLine, task, tool):
    if newLine: print(file=sys.stderr)
    text = 'Insufficient information for handling streaming tools.'
    self.text.append(text)
    text = 'The task \'' + task + '\' which uses the tool \'' + tool  + '\' accepts a stream as input as part of this pipeline.  However, ' + \
    'no instructions appear in the configuration file for this tool on how to deal with an input stream.  Please modify the tool configuration ' + \
    'file to allow accepting an input stream, or modify the pipeline configuration file to remove the streamed input.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If a tool is instructed to output to stream, but instructions are not included in the
  # configuration file, terminate.
  def noOutputStreamInstructions(self, newLine, task, tool):
    if newLine: print(file=sys.stderr)
    text = 'Insufficient information for handling streaming tools.'
    self.text.append(text)
    text = 'The task \'' + task + '\' using tool \'' + tool + '\' is instructed to output to a stream, however, the configuration file for ' + \
    'this tool provides no instructions on outputting to a stream.  Please modify the tool configuration ' + \
    'file to allow accepting an input stream, or modify the pipeline configuration file to remove the streamed input.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If there is an unrecognised field in the 'additional dependencies' section, fail.
  def unrecognisedFieldInAdditionalDependencies(self, newLine, task, field, allowedFields, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The \'additional dependencies\' section contains dependency information for the task \'' + task + '\'.  An unrecognised field (' + \
    field + ') was included for this task.  The allowed fields for each task are:'
    self.text.append(text)
    self.text.append('\t')
    for field in allowedFields: self.text.append(field)
    text = 'Please check and repair the pipeline configuration file.'
    self.text.append('\t')
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the task output section in the additional dependencies points to an unknown task, fail.
  def unknownTaskInAdditionalDepedenciesTaskOutput(self, newLine, task, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed pipeline configuration file: ' + filename
    self.text.append(text)
    text = 'The \'additional dependencies\' section contains information for task \'' + task + '\'.  Within the \'task output\' section, ' + \
    'the task \'' + linkedTask + '\' is listed as a task from which to get a dependency, but this is not a task in the pipeline workflow.  ' + \
    'Please check and repair the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  ######################
  # Internal loop errors
  ######################

  # If an internal loop file was specified on the command line, but the pipeline does not
  # have any internal loop information set up, terminate.
  def internalLoopRequestedButUndefined(self, newLine, pipelineName, filename):
    if newLine: print(file=sys.stderr)
    text = 'Attempt to use internal loop when none is defined: ' + filename
    self.text.append(text)
    text = 'The command line includes the \'--internal-loop\' argument, requesting that the pipeline loop over certain tasks in the ' + \
    'workflow.  This is only permissible for pipelines where information about internal loops has been provided in the configuration file. ' + \
    'The pipeline being run (' + pipelineName + ') does not have any information abomut an internal loop.  Please remove the internal loop ' + \
    'request from the command line, or modify the pipeline to accept internal loops.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an unrecognised section appears in the file, terminate.
  def missingSectionsInternalLoop(self, newLine, section, filename):
    if newLine: print(file=sys.stderr)
    text = 'Malformed internal loop file: ' + filename
    self.text.append(text)
    text = 'The file does not contain the required section \'' + section + '\'.  Please check and repair the file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument in the internal loop file is for a task outside of the internal loop, fail.
  def argumentForTaskOutsideInternalLoop(self, newLine, argument, shortForm, linkedTask, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'arguments\' section of the file contains a list of arguments that are set in the \'values\' section.  These arguments must ' + \
    'link to tasks within the internal loop (see the pipeline configuration file for these tasks), but the argument \'' + argument
    if shortForm != '': text += ' (' + shortForm + ')'
    text += '\' links ' + \
    'to the task \'' + linkedTask + '\' which is not in the loop.  Please correct the internal loop file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If an argument in the internal loop file is unknown, fail.
  def unknownArgumentInternalLoop(self, newLine, argument, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'arguments\' section of the file contains a list of arguments that are set in the \'values\' section.  The argument \'' + \
    argument + '\' is unknown.  Please correct the internal loop file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If one of the blocks of values has a different number of values as arguments supplied, fail.
  def incorrectNumberOfValuesInInternalLoopFile(self, newLine, blockID, noValues, noArguments, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The \'values\' section of the file should be blocks of values, each with an ID.  There must be the same number of entries in each ' + \
    'of these blocks of values as there are arguments in the \'arguments\' section.  The block of values with ID \'' + str(blockID) + '\' has ' + \
    str(noValues) + ' entries, but ' + str(noArguments) + ' are expected.  Please check the internal loop file and fix any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If the data type is wrong, terminate.
  def incorrectDataTypeinInternalLoop(self, newLine, blockID, argument, value, dataType, filename):
    if newLine: print(file=sys.stderr)
    text = 'Error with the internal loop file: ' + filename
    self.text.append(text)
    text = 'The value \'' + value + '\' appearing in the \'values\' section in block \'' + str(blockID) + '\' is associated with the argument \'' + \
    argument + '\'.  This argument expects a value of type \'' + dataType + '\' but the supplied value is not of this type.  Please check the ' + \
    'internal loop file and fix any errors.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  # If gkno is instructed to delete a file after a task in the internal loop, whcn the file
  # was the output of a task before the internal loop, there may be problems.  The tasks in
  # the internal loop may all require this file, so it shouldn't be deleted until after all
  # iterations are complete.
  def deleteFileInLoop(self, newLine, task, deleteAfterTask):
    if newLine: print(file=sys.stderr)
    text = 'Error with deleting files during pipeline operation.'
    self.text.append(text)
    text = 'The "delete files" section in the pipeline configuration file instructs gkno to delete files generated in task \'' + task + \
    '\' after execution of task \'' + deleteAfterTask + '\'.  gkno does not allow files to be deleted after a task included in an internal ' + \
    'loop unless the file to delete was generated by another task within the loop, which is not the case in this pipeline.  Please check and ' + \
    'modify the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText()
    self.hasError = True

  #####################
  # Admin mode errors
  #####################
  
  def attemptingRemoveUnknownResource(self, resourceName, dest=sys.stderr):
    self.errorType = 'WARNING'
    print("WARNING: Resource '" + resourceName + "' was not removed because it is unknown", file=dest)

  def extractTarballFailed(self, filename, dest=sys.stderr):
    print("ERROR: Could not extract contents of"+filename, file=dest)

  def gitSubmoduleUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/submodule_update.* files for more details.", file=dest)

  def gitUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/gkno_update.* files for more details.", file=dest)

  # If the specified file containing the list of files to skip is missing.
  def cannotSkipAndCompile(self, dest=sys.stderr):
    self.text.append('Invalid arguments for gkno build.')
    self.text.append('The \'--skip-tools (-st)\' argument was set in conjuction with the \'--compile-tools (-ct)\'. These arguments cannot ' + \
    'set simultaneously. Please provide either a list of tools to skip or to compile, but not both')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The user requested that not all tools be built, but failed to provide a list of tools to skip.
  def missingSkipList(self, dest=sys.stderr):
    self.text.append('Missing list of tools to skip.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a json format file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. Please either build all tools using \'gkno build\' or remove tools by using the ' + \
    'command \'gkno build --skip-list list.json\'.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If the specified file containing the list of files to skip is missing.
  def missingSkipListFile(self, filename, dest=sys.stderr):
    self.text.append('Missing file containing list of tools to skip.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a json format file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. The specified file \'' + filename + '\' cannot be found. Please check the name of ' + \
    'the supplied file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a tool listed as a tool to skip is not a tool in gkno.
  def invalidToolToSkip(self, filename, tool, availableTools, dest=sys.stdout):
    self.text.append('Invalid tool in list of tools to not compile.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. The specified file \'' + filename + '\' contains the tool \'' + tool + '\' which ' + \
    'is not a tool in gkno. Please ensure that all of the tools listed in the file are present in the following list of available tools:')
    self.text.append('\t')
    for tool in availableTools: self.text.append(tool)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # The user requested that not all tools be built, but failed to provide a list of tools to skip.
  def missingCompileList(self, dest=sys.stderr):
    self.text.append('Missing list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. Please either build all tools using \'gkno build\' or select the tools to compile ' + \
    'by using the command \'gkno build --compile-list list.json\'.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If the specified file containing the list of files to skip is missing.
  def missingCompileListFile(self, filename, dest=sys.stderr):
    self.text.append('Missing file containing list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. The specified file \'' + filename + '\' cannot be found. Please check the name of ' + \
    'the supplied file.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a tool listed as a tool to skip is not a tool in gkno.
  def invalidToolToCompile(self, filename, tool, availableTools, dest=sys.stdout):
    self.text.append('Invalid tool in list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. The specified file \'' + filename + '\' contains the tool \'' + tool + '\' which ' + \
    'is not a tool in gkno. Please ensure that all of the tools listed in the file are present in the following list of available tools:')
    self.text.append('\t')
    for tool in availableTools: self.text.append(tool)
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  def gknoAlreadyBuilt(self):
    print("Already built.", file=sys.stdout)

  def gknoNotBuilt(self, dest=sys.stderr):
    print("ERROR: 'gkno build' must be run before performing this operation", file=dest)

  def invalidResourceArgs(self, mode, dest=sys.stderr):
    print("ERROR: Invalid arguments or order used. Type 'gkno", mode, "--help' for a usage example.", file=dest)
    
  def noCurrentReleaseAvailable(self, resourceName, dest=sys.stderr):
    print("ERROR: Resource: " + resourceName + " has no release marked as 'current'. Cannot fetch.", file=dest)

  def noReleaseUrlFound(self, resourceName, releaseName, dest=sys.stderr):
    print("ERROR: Could not fetch files for resource: "+resourceName+", release: "+releaseName+" - URL not found", file=dest)

  def requestedUnknownResource(self, resourceName, dest=sys.stderr):
    print("ERROR: Requested resource '" + resourceName + "' is not recognized", file=dest)

  def resourceAlreadyAdded(self, resourceName, dest=sys.stderr):
    print("WARNING: Requested resource '" + resourceName + "' has already been added to gkno", file=dest)

  def resourceFetchFailed(self, resourceName, dest=sys.stderr):
    print("ERROR:  See logs/build_"+resourceName+".* files for more details.", file=dest)
  
  def toolBuildFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/build_"+toolName+".* files for more details.", file=dest)

  def toolUpdateFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/update_"+toolName+".* files for more details.", file=dest)

  def urlRetrieveFailed(self, url, dest=sys.stderr):
    print("ERROR: Could not retrieve file at "+url, file=dest)
    
  def dependencyCheckFailed(self, missing, unknown, incompatible, dest=sys.stderr):
    if len(missing) > 0:
      print("    Missing:", file=dest)
      for dep in missing:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
    if len(incompatible) > 0:
      print("    Not up-to-date:", file=dest)
      for dep in incompatible:
        print("        ", dep.name, 
              "    minimum version: ", dep.minimumVersion, 
              "    found version: "  , dep.currentVersion, sep="", file=dest)
      print("", file=dest)
    if len(missing) > 0 or len(incompatible) > 0:
      print("", file=dest)
      print("gkno (and its components) require a few 3rd-party utilities", file=dest)
      print("to either build or run properly.  To obtain/update the utilities ", file=dest)
      print("listed above, check your system's package manager or search the ", file=dest)
      print("web for download instructions.", file=dest)
      print("", file=dest)

    # ODD CASE
    if len(unknown) > 0:
      print("----------------------------------------", file=dest)
      print("The following utilities have version numbers that could not be ", file=dest)
      print("determined by gkno:", file=dest)
      for dep in unknown:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
      print("This indicates a likely bug or as-yet-unseen oddity.", file=dest)
      print("Please contact the gkno development team to report this issue.  Thanks.", file=dest)
      print("", file=dest)
      print("----------------------------------------", file=dest)
      print("", file=dest)

  # If some of the tools failed to build, write a warning.
  def failedToolBuilds(self, tools):
    self.text.append('Not all tools were built successfully.')
    self.text.append('While building gkno, some of the tools failed to compile successfully. Please check the log files to determine the ' + \
    'cause of the failures and rebuild. In the meantime, all other tools and pipelines not containing the failed tools can be used. The ' + \
    'tools that failed to build are:')
    self.text.append('\t')
    for tool in tools:
      if not tools[tool]: self.text.append('\t' + str(tool))
    self.text.append('\t')
    self.writeFormattedText(errorType = 'warning')
    self.terminate()

  # If a tool is added, but the tool name is not provided.
  def noToolNameProvided(self, tools):
    self.text.append('No tool name provided.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but no tool name was provided. If adding a tools, the syntax \'' + \
    './gkno add-tool <tool name> miust be used, where <tool name> is one of the following tools:')
    for tool in tools: self.text.append('\t' + tool.name)
    self.text.append('\t')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a tool is added, but the tool added is invalid.
  def invalidToolAdded(self, tools):
    self.text.append('Attempt to add an invalid tool.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but the requested tool is not available in gkno. The tool ' + \
    'added must be one of the following:')
    for tool in tools: self.text.append('\t' + tool.name)
    self.text.append('\t')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

  # If a tool is added, but the tool is already available.
  def toolAlreadyBuilt(self):
    self.text.append('Attempt to add a tool that is already present.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but the requested tool is already available. Only tools that ' + \
    'have previously been omitted from the build can be added.')
    self.writeFormattedText(errorType = 'error')
    self.terminate()

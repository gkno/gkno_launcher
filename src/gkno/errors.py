#!/usr/bin/python

from __future__ import print_function
import os
import sys

class errors:
  def __init__(self):
    self.error = False
    self.text  = []

  # Write out key value pairs in a formatted manner.  These may be tool and
  # description or command line argument and description or whatever else is
  # required.
  def writeFormattedText(self, noTab):

    # Set the maximum width of the line.
    maxLength   = 93 - (5 * noTab)

    for line in self.text:
      textList = []
      while len(line) > maxLength:
        index = line.rfind(' ', 0, maxLength)
        textList.append(line[0:index])
        line = line[index + 1:len(line)]
      if (line != '') and (line != ' '): textList.append(line)

      line = textList.pop(0)
      print("%-*sERROR: %-*s" % ((5 * noTab), '', 1, line), file = sys.stdout)
      for line in textList:  print('%-*sERROR: %-*s' % ((5 * noTab), '', 1, line), file = sys.stdout)

  ##############
  # File errors.
  ##############

  # If attempting to perform multiple runs and no file is supplied, throw an error.
  def missingFileForMultipleRuns(self, newLine, noTab):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'File containing information for multiple runs \'--multiple-runs (-mr)\' is not supplied.'
    self.text.append(text)
    self.error = True

  # If a file has an unexpected extension, flag the problem.
  def fileExtensionError(self, newLine, noTab, option, filename, extension):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'File \'' + filename + '\' does not end with the expected extension \'' + extension + '\'' + ' (option: \'' + option + '\')'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True
  
  ##############
  # Json errors.
  ##############

  # If a json configuration file is malformed, terminate the script with an error.
  def jsonOpenError(self, newLine, noTab, error, filename):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'json file \'' + filename + '\' is malformed: \'' + str(error) + '\'.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # If a required field in a tool configuration file is missing.
  def missingFieldForTool(self, newLine, noTab, task, argument, field, value):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Required field \'' + field + '\' in configuration file for \'' + task + '\' argument ' + argument + '\' is '
    if value == '': text += 'missing.'
    else: text += 'invalid (value: \'' + value + '\')'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # When parsing the pipeline configuration file, there are a list of commands that
  # are either pipeline specific or associated with a contained tool.  If the 'tool'
  # value is not present in the file, throw an error.
  def optionAssociationError(self, newLine, noTab, message, argument, tool):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Value \'' + message + '\' is missing for argument \'' + argument + '\' in the \'' + tool + '\' configuration file.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # The pipeline configuration file contains an argument that points to a constituent
  # tool, however the tool argument it points to is invalid.
  def incorrectArgumentInPipelineConfigurationFile(self, newLine, noTab, tool, argument, linkedArgument):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'The pipeline configuration file \'arguments\' block defines \'' + argument + '\' as linked to \'' + linkedArgument + \
    '\' in tool \'' + tool + '\''
    self.text.append(text)
    text = 'This argument (\'' + linkedArgument + '\') does not exist for this tool.  Please check the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True
    self.error = True

  ######################
  # Command line errors.
  ######################

  # If a command line argument expects a value (e.g. it is not a flag), but no value
  # was supplied, throw an error.
  def expectedValueForArgument(self, newLine, noTab, task, argument, dataType, givenValue):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Argument \'' + argument + '\' for task \'' + task + '\' requires a value of type \'' + dataType + '\''
    if givenValue == '': text += ' but no data was given.'
    else: text += '. The received value was: ' + givenValue
    self.text.append(text)
    if dataType == 'flag':
      text = 'No value is expected for a flag.'
      self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # A required value is not given.
  def missingRequiredValue(self, newLine, noTab, task, tool, argument, shortForm, tl, pl):
    self.text = []
    if newLine: print(file = sys.stderr)
    if shortForm == '':
      text = 'Argument \'' + argument + '\' for tool \'' + task + ' (' + tool + ')\' is required and not set.  '
    else:
      text = 'Argument \'' + argument + ' (' + shortForm + ')\' for tool \'' + task + ' (' + tool + ')\' is required and not set.  '
    self.text.append(text)

    if pl.isPipeline:
      for pipelineArgument in pl.information['arguments']:
        pipelineTask      = pl.information['arguments'][pipelineArgument]['link to this task']
        if pipelineTask  == 'pipeline': continue
        linkedArgument    = pl.information['arguments'][pipelineArgument]['link to this argument']
        if (pipelineTask == task) and (linkedArgument == argument):
          description     = tl.toolInfo[tool]['arguments'][argument]['description']
          if 'short form argument' in pl.information['arguments'][pipelineArgument]:
            pipelineAlt = pl.information['arguments'][pipelineArgument]['short form argument']
            text = 'This can be set on the command line using the pipeline argument \'' + pipelineArgument + ' (' + pipelineAlt + ')\'.'
            self.text.append(text)
            text = '\'' + pipelineArgument + ' (' + pipelineAlt + ')\' description: ' + description
            self.text.append(text)
          else:
            text = 'This can be set on the command line using the pipeline argument \'' + pipelineArgument + '\'.'
            self.text.append(text)
            text = '\'' + pipelineArgument +'\' description: ' + description
            self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # The input file used for constructing an output file is blank.
  def noInputFilenameForFilenameConstruction(self, newLine, noTab, task, tool, outputFile, argument, pipelineArgument, shortform, tl):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Constructing output filename \'' + outputFile + '\' in task \'' + task + ' (\'' + tool + '\')\' failed.'
    self.text.append(text)
    text = 'Input filename (argument \'' + argument + '\') used in the construction is blank.'
    self.text.append(text)
    if pipelineArgument != '':
      description = tl.toolInfo[tool]['arguments'][argument]['description']
      text = 'This can be set on the command line using the pipeline argument \'' + pipelineArgument + ' (' + shortform + ')\'.'
      self.text.append(text)
      text = '\'' + pipelineArgument + '\' description: '+  description
      self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # If a command line argument is given a value with the wrong data type, throw an error.
  def incorrectDataType(self, newLine, noTab, tool, argument, value, dataType):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Argument \'' + argument + '\' in tool \'' + tool + '\' expects a value of data type \'' + dataType + '\'. Given \'' + value + '\'.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  ##############
  # Tool errors.
  ##############

  def unknownTool(self, newLine, noTab, task, tool):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Task name \'' + task + '\' is associated with tool \'' + tool + '\' but this tool is not available in the gkno package. ' + \
    'Please ensure that the configuration file is correct.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  ##################
  # Pipeline errors.
  ##################

  # A tool name in the pipeline configuration file is not associated with an actual tool.
  def unassociatedTask(self, newLine, noTab, task):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Task \'' + task + '\' appearing in the pipeline \'workflow\' does not appear in the \'tools\' section of the pipeline ' + \
    'configuration file.  Consequently, it is unknown which tool to use for this task.  Please check the \'workflow\' and \'tools\'' + \
    ' sections of the pipeline configuration file.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # Each tool name appearing in the pipeline configuration file is required
  # to be unique to avoid ambiguous linkages.  If repeated names are discovered
  # give an error and terminate.
  def repeatedTool(self, newLine, noTab, task):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'Task name \'' + task + '\' appears multiple times in the pipeline configuration file. Ensure that all task names in the ' + \
    '\'workflow\' section of the pipeline configuration file are unique.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  ##################
  # Instance errors.
  ##################

  # If an invalid pipeline instance is requested, throw an error and list the available
  # instances for this pipeline.
  def invalidPipelineInstance(self, newLine, noTab, instance, instances):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'A different instance of the pipeline was requested (\'' + instance + '\') but this is not a valid instance.'
    self.text.append(text)
    if len(instances) == 0:
      text = 'There are no additional instances for this pipeline, so the --instance (-is) argument cannot be used.'
      self.text.append(text)
    else:
      text = 'The available instances for this pipeline are:'
      self.text.append(text)
      for availableInstance in instances: self.text.append(availableInstance)
    self.writeFormattedText(noTab)
    self.error = True

  # If the instance argument is not an argument in the pipeline.
  def invalidArgumentInInstance(self, newLine, noTab, instance, argument):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'The argument \'' + argument + '\' appears in the list of arguments for instance \'' + instance + '\' but this is not ' + \
    'a valid argument for this pipeline.  Please check the instance arguments in the configuration file.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  #############################
  # Errors generating makefile.
  #############################

  # If the json file specifies an order for the arguments and an unknown argument
  # is encountered.
  def unknownArgumentInArgumentOrder(self, newLine, noTab, task, tool, argument):
    self.text = []
    if newLine: print(file = sys.stderr)
    text = 'The configuration file specifies an order for the command line arguments for task \'' + task + ' (' + tool + \
    ')\'.  The ordered list contains an unknown argument: ' + argument + '.'
    self.text.append(text)
    self.writeFormattedText(noTab)
    self.error = True

  # If the json file specifies an order for the arguments, but not all of the arguments
  # for the tool appear in the list.

  def missingArgumentsInOrderList(self, newLine, noTab, task, tool, argumentDict):
    self.text     = []
    if newLine: print(file = sys.stderr)
    text = 'The configuration file specifies an order for the command line arguments for task \'' + task + ' (' + tool + \
    ')\'.  The following arguments would not be included on the command line as they do not appear in this ordered list:'
    self.text.append(text)
    for argument in argumentDict: self.text.append(argument)
    self.writeFormattedText(noTab)
    self.error = True



















  # If an unknown command line argument is given.
  def unknownToolArgument(self, pad, tool, argument):
    print(pad, 'ERROR: Argument \'', argument, '\' for tool \'', tool, '\' is not recognised.', sep = '', end = '', file = sys.stderr)
    print(' Please check command line.', sep = '', file = sys.stderr)
    sys.stderr.flush()
    self.error = True

  # If there is an unknown command line argument when running a pipeline (e.g.
  # it is not a pipeline argument, nor is it a tool name within the pipeline).
  def unknownPipelineArgument(self, pad, argument):
    print(pad, 'ERROR: Argument \'', argument, '\' is neither a pipeline argument or a tool name.', sep = '', end = '', file = sys.stderr)
    print(' Please check command line.', sep = '', file = sys.stderr)
    sys.stderr.flush()
    self.error = True

  # If the command line argument is a tool name, a list of tool specific commands must
  # follow (in quotation marks).  If not, then there is an error.
  def commandLineToolError(self, pad, pipelineName, tool):
    print(pad, 'ERROR: Commands for tool \'', tool, '\' expected in the form:', sep = '', file = sys.stderr)
    print(pad, "\tgkno pipe ", pipelineName, ' [options] -', tool, ' "[tool options]"', sep = '', file = sys.stderr)
    self.error = True

  # When parsing the command line for a pipeline, if any of the pipeline arguments (as
  # specified in the pipeline configuration file) point to a tool that is not in the
  # pipeline, fail.
  def associatedToolNotInPipeline(self, text, tool, argument):
    print(text, 'ERROR: Pipeline argument \'', argument, '\' is associated with a tool that is not ', sep = '', end = '', file = sys.stderr)
    print('part of the pipeline (\'', tool, '\')', sep = '', file = sys.stderr)
    self.error = True

  # A supplied argument is invalid.
  def invalidArgument(self, newLine, pad, text, argument, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Invalid argument (', argument, ') in the \'', text, '\' section ', sep = '', file = sys.stderr)
    print(pad, 'ERROR: of the pipeline configuration file for tool \'', tool, '\'.', sep = '', file = sys.stderr)
    self.error = True

  # The tool configuration file has multiple input files designated for use as output
  # filename constructors.
  def multipleFilenameConstructors(self, pad, task, tool, argumentA, argumentB):
    print(pad, 'ERROR: Task \'', task, '\' (tool \'', tool, '\')\' has multiple input files designated ', sep = '', end = '', file = sys.stderr)
    print('as filename generators: \'', argumentA, '\' and \'', argumentB, '\'.', sep = '', file = sys.stderr)
    self.error = True

  # If an output filename is to be constructed from an input filename and the specific
  # input argument to use was not specified and there are multiple inputs to the task,
  # gkno cannot determine which argument to use.
  def unknownFilenameConstructor(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Filename for output argument \'', argument, '\' in task \'', task, sep = '', end = '', file = sys.stderr)
    print(' (\'', tool, '\')\' cannot be determined.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Either no or multiple input files exist and none are designated for use in filename creation.', sep = '', file = sys.stderr)
    self.error = True

  # If the input is a list of files, the json file must also contain information on which
  # command line argument should be used for putting these files on the command line.
  def noArgumentToRepeat(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: A list of files was selected for task \'', task, '\' argument \'', argument, '\'.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The json file for this tool (\'', tool, '\') and argument does not contain the value:', sep = '', file = sys.stderr)
    print(pad, 'ERROR: \'apply by repeating this argument\' with the argument to use on the command line.', sep = '', file = sys.stderr)
    self.error = True

  # If the argument associated with the filename list is invalid.
  def invalidArgumentToRepeat(self, newLine, pad, task, tool, argument, linkedArgument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: A list of files was selected for task \'', task, '\' argument \'', argument, '\'.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The command line argument (\'', linkedArgument, '\') to input these files', sep = '', file = sys.stderr)
    print(pad, 'ERROR: is not valid for tool (\'', tool, '\').  Please check the json file.', sep = '', file = sys.stderr)
    self.error = True

  # If the list of filenames is not a list or is missing the correct title.
  def malformedFilenameList(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: The json file containing the list of filenames is malformed', sep = '', file = sys.stderr)
    print(pad, 'ERROR: This file should contain the heading \'filename list\' and be followed by a json list.', sep = '', file = sys.stderr)
    self.error = True

  # The pipeline configuration file may contain a block describing how to construct the
  # name of an output file.  In this description, the 'additional text from variables'
  # block may appear describing the tool and argument from which to take a variable.  If
  # these are missing, the filename cannot be constructed.
  def noDescriptionOfVariable(self, pad, tool, argument, text):
    print(pad, 'ERROR: Unable to construct filename for \'', tool, '\' argument \'', argument, '\'.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: Variable \'', text, '\' appearing in the \'order\' list needs to be described.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: See documentation and ensure that the configuration file is well constructed.', sep = '', end = '', file = sys.stderr)
    print(file = sys.stderr)
    self.error = True

  # Same as above, except the description is present, but either the tool or argument
  # is not.
  def missingVariableForFilenameConstruction(self, pad, tool, argument, text):
    print(pad, 'ERROR: Unable to construct filename for \'', tool, '\' argument \'', argument, '\'.', sep = '', end = '', file = sys.stderr)
    print(pad, 'ERROR: Either the \'tool\' or \'argument\' fields are missing for \'', text, '\'.', sep = '', end = '', file = sys.stderr)
    print(file = sys.stderr)
    self.error = True

  # As above, but all of the information is present, but the variable to which the json
  # file points to does not exist.
  def nonExistentTaskOrArgumentInConstruction(self, newLine, pad, task, argument, text, addTask, addArgument, taskError):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Unable to construct filename for \'', task, '\' argument \'', argument, '\'.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Variable \'', text, '\' comes from \'', addTask, '\' argument \'', addArgument, '\'.', sep = '', file = sys.stderr)
    if taskError: print(pad, 'ERROR: This tool (\'', addTask, '\') does not exist.', sep = '', file = sys.stderr)
    else: print(pad, 'ERROR: This argument (\'', addArgument, '\') does not exist.', sep = '', file = sys.stderr)
    self.error = True

  # If the data type specified in the configuration file is unknown, throw an error.
  def unknownDataType(self, newLine, pad, tool, argument, dataType):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Unknown data type \'', dataType, '\' for option \'', argument, '\' in the \'', tool, sep = '', end = '', file = sys.stderr)
    print('\' configuration file.', file = sys.stderr)
    self.error = True

  # If the pipeline configuration contains a tool or task that is invalid.
  def invalidToolTaskName(self, newLine, pad, jsonSection, isTask, tool):
    if newLine: print(file = sys.stderr)
    if isTask: toolOrTask = 'task'
    else: toolOrTask = 'tool'
    print(pad, 'ERROR: Invalid ', toolOrTask, ' \'', tool, '\' in the \'', jsonSection, '\' section of ', sep = '', end = '', file = sys.stderr)
    print('the pipeline configuration file.', sep = '', file = sys.stderr)
    self.error = True

  # If an invalid stub extension is referenced.
  def invalidStubExtension(self, newLine, pad, task, argument, extension):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Request to delete file with an invalid stub extension (\'', extension, '\').', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Error in \'delete files\' section, task \'', task, '\' with argument \'', argument, '\'.', sep = '', file = sys.stderr)
    self.error = True

  # If a command line argument is provided and it isn't a flag, but no value is assigned,
  # this an error.
  def missingCommandLineArgumentValue(self, newLine, pad, tool, command, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Command line argument \'', argument, '\' for task \'', tool, '\' is not a flag, ', sep = '', file = sys.stderr)
    print(pad, 'ERROR: but, no value is given.  Please check command line.', sep = '', file = sys.stderr)
    self.error = True

  # If multiple output arguments are listed as able to output to the stream, gkno
  # cannot pipe the output to another task and so will terminate.
  def multipleOutputsToStream(self, newLine, pad, task, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task, ' (', tool, ')\' outputs to the stream so pipes can be used to link tools.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Only one output is allowed to output to the stream for each tool (multiple specified).', sep = '', file = sys.stderr)
    self.error = True

  # If the last task in the pipeline is outputting to the stream, terminate.
  def lastTaskOutputsToPipe(self, newLine, pad, task):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Final task in the pipeline (\'', task, '\') cannot output to the stream.', sep = '', file = sys.stderr)
    self.error = True

  # If multiple input arguments are listed as able to accept a stream as input, gkno
  # cannot determine how to define the pipes.
  def multipleOutputsToStream(self, newLine, pad, task, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task, ' (', tool, ')\' accepts an input stream so pipes can be used to link tools.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Only one input is allowed to accept a stream for each tool (multiple specified).', sep = '', file = sys.stderr)
    self.error = True

  # If a task outputs a stream, one of the output command line arguments needs to provide
  # some information on how to handle the stream.  If none is provided, throw an error.
  def noOutputStreamInstructions(self, newLine, pad, task, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task, ' (', tool, ')\' outputs a stream so pipes can be used to link tools.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: None of the output arguments have instructions on how to handle a stream.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Consult documentation on how to pipe together tools.', sep = '', file = sys.stderr)
    self.error = True

  # If the input file argument is to be replaced with a different argument if accepting the
  # input from a stream, the entry 'replace argument with', must appear in the configuration
  # file.  Throw an error if it does not.
  def noReplacementFoundWhenStreaming(self, newLine, pad, task, tool, argument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task ,' (', tool, ')\' accepts a stream as input.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The configuration file indicates that argument \'', argument, '\' is to be replaced.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The entry \'replace argument with\' must be present for this argument.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Either it isn\'t present or the \'argument\' or \'value\' fields were missing.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Consult documentation on how to pipe together tools.', sep = '', file = sys.stderr)
    self.error = True

  # If a task accepts its input from a stream, one of the input command line
  # arguments needs to provide some information on how to handle the stream.  If
  # none is provided, throw an error.
  def noInputStreamInstructions(self, newLine, pad, task, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task, ' (', tool, ')\' accepts an input stream so pipes can be used to link tools.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: None of the input arguments have instructions on how to handle a stream.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Consult documentation on how to pipe together tools.', sep = '', file = sys.stderr)
    self.error = True

  # If a replacement argument is being used to handle a streaming input, the argument
  # must not already be present in the tl.toolInfo structure.
  def replacementArgumentAlreadyPresent(self, newLine, pad, task, tool, replacementArgument):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Task \'', task, ' (', tool, ')\' accepts an input stream so pipes can be used to link tools.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The input argument is being replaced by the argument \'', argument, '\' but', sep = '', file = sys.stderr)
    print(pad, 'ERROR: this argument is already a valid argument for the tool.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Consult documentation on how to pipe together tools.', sep = '', file = sys.stderr)
    self.error = True

  # If a configuration file is being exported and the filename to be exported already exists,
  # throw an error and give a list of all of the currently existing pipelines.
  def outputJsonExists(self, newLine, pad, io, name):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Exporting new configuration file \'', name, '\', but this already exists.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Following is a list of existing configuration files.  Select a name not contained here.', sep = '', file = sys.stderr)
    for json in io.jsonPipelineFiles: print(pad, "\t", json, sep = '', file = sys.stderr)
    self.error = True

  # Missing pipeline json configuration file.
  def missingFile(self, newLine, pad, filename):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Unable to find file: ', filename, sep = '', file = sys.stderr)
    self.error = True

  # If multiple runs are being performed, the input json must contain a block
  # explaining th data that is contained within the file.  Throw an error if this
  # block is missing.
  def missingJsonFormatForMultipleRuns(self, newLine, pad):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: The multiple-runs input file must contain a block describing the contained data.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: The title of this block should be \'format of data list\'.', sep = '', file = sys.stderr)
    self.error = True

  # If the json file listing the input parameters has the wrong number of entries
  # throw an error.
  def incorrectNumberOfEntriesInMultipleJson(self, newLine, pad):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: The multiple-runs input file has the wrong number of entries.', sep = '', file = sys.stderr)
    print(pad, 'ERROR: Please check the entries in the data list.', sep = '', file = sys.stderr)
    self.error = True

  # Terminate the script after errors have been found.
  def terminate(self):
    print(file = sys.stderr)
    print('================================================================================================', file = sys.stderr)
    print('  TERMINATED: Errors found in running gkno.  See specific error messages above for resolution.', file = sys.stderr)
    print('================================================================================================', file = sys.stderr)
    exit(1)








  # If no pipeline name is supplied.
  def missingPipelineName(self):
    print("ERROR: Pipeline mode was selected, but no pipeline name was supplied.", file = sys.stderr)
    self.error = True

  # Missing pipeline json configuration file.
  def missingPipelineJsonFile(self, jsonFile):
    print("ERROR: Unable to find pipeline configuration file: ", jsonFile, sep = "", file = sys.stderr)

  # If the pipeline configuration contains an option that is not in the tool
  # configuration file, there is an error in the linkage section of the pipeline
  # configuration file.
  def invalidToolName(self, newLine, pad, text, tool):
    if newLine: print(file = sys.stderr)
    print(pad, 'ERROR: Invalid tool name \'', tool, '\' in the \'', text, '\' section of the pipeline ', sep = '', end = '', file = sys.stderr)
    print('configuration file.', sep = '', file = sys.stderr)
    self.error = True

  # If an expected json block is missing from the file.
  def missingJsonEntry(self, value, tool):
    print("\t\tERROR: The json file for tool '", tool, "' is missing the entry '", value, "'.", sep = '', file = sys.stderr)
    self.error = True

  # Unknown command in the tools dependency list.
  def unknownArgumentInDependency(self, task, tool, argument):
    print(file = sys.stderr)
    print("\t\tERROR: Unknown argument '", argument, "' in the dependency 'arguments' for tool '", sep = '', end = '', file = sys.stderr)
    print(task, " (", tool, ")'", sep = '', file = sys.stderr)
    self.error = True

  # Error for a missing required component in a json tool option.
  def toolArgumentsError(self, text, tool, option):
    print("\t\tERROR: The '", text, "' value is not present in the tool configuration file for '", option, sep = "", end = "", file = sys.stderr)
    print("' in '", tool, "'", sep = "", file = sys.stderr)
    self.error = True

  # If a configuration file contains a default value for a flag and it isn't 'set' or 'unset',
  # throw an error.
  def unknownFlagDefault(self, task, option, value):
    print("\t\tERROR: Configuration file entry for '", task, "' flag '", option, "' should be 'set', ", sep = "", end = "", file = sys.stderr)
    print(" 'unset' or not provided.", sep = "", file = sys.stderr)
    self.error = True

  # If a value is assigned to a flag on the command line, terminate the script.
  def assignedValueToFlag(self, tool, argument):
    print("\tERROR: A value was assigned to the flag '", argument, "' in the tool '", tool, "'.", sep = "", file = sys.stderr)
    self.error = True

  # Fail if an unknown option is specified on the command line.
  def unknownOption(self, startText, tool, argument):
    print(startText, "ERROR: Unknown command line argument '", argument, "' for tool '", tool, "'", sep = "", file = sys.stderr)
    self.error = True

  # For output files designated as stubs, a list of the output extensions
  # is required.  Fail if these are missing.
  def stubNoOutputs(self, tool, option):
    print("ERROR: Output name for '", tool, "' is a stub, but the output names to be produced are not included.", sep = "", file = sys.stderr)
    print("ERROR: Ensure that the configuration file contains a list under the '", option, sep = "", end = "", file = sys.stderr)
    print("' option called \"outputs\".", file = sys.stderr)
    exit(1)

  # When building up the list of dependent files, inputs that are stubs need to have
  # the dependent files constructed.  For this to be possible the 'outputs' value
  # needs to be present in the configuration file. Terminate if it is not.
  def missingStubOutputsDependency(self, task, tool, option):
    print("\t\tERROR: Input '", option, "' to tool '", task, " (", tool, ")' is a stub.", sep = "", file = sys.stderr)
    print("\t\tERROR: A list of file extensions is required in the configuration file to determine dependent files.", sep = "", file = sys.stderr)
    print("\t\tERROR: Ensure the configuration file contains the value 'outputs' listing the extensions.", file = sys.stderr)
    self.error = True

  # The additional files section of the configuration file contains an unknown file
  # type.
  def unknownDependencyOrOutput(self, task, fileType):
    print("\t\tERROR: Unknown file type '", fileType, "' in the 'additional files' section of the pipeline", sep = '', file = sys.stderr)
    print("\t\tERROR: configuration file for tool '", task, "'.", sep = '', file = sys.stderr)

  # If the input file for the first tool in the pipeline is unset, terminate the script.
  def inputFileError(self, tool, option):
    print("\t\tERROR: Required input '", option, "' to the tool '", tool, "' is not specified.", sep = "", file = sys.stderr)
    self.error = True

  def unsetRequiredVariable(self, task, tool, option):
    print("\t\tERROR: Required variable '", option, "' in tool '", task, " (", tool, ")' is unset.", sep = "", file = sys.stderr)
    self.error = True

  # If a file on which a tool is dependent is not defined, the script should fail with
  # an error message.
  def missingDependentFile(self, task, tool, option, isHidden):
    print("\t\tERROR: Tool '", task, " (", tool, ")' requires '", option, "' to be set in order to run.", sep = '', file = sys.stderr)
    if isHidden:
      print("\t\tERROR: This is a hidden option (i.e. is not set on the command line).", file = sys.stderr)
      print("\t\tERROR: Ensure that the pipeline configuration file links a file to this option.", file = sys.stderr)

  # If a tools input is linked to the output of another tool and its output is
  # a stub, then the configuration file must contain reference to the required
  # extension (e.g. which of the output files to use).  If this isn't provided,
  # the script should fail.
  def missingExtension(self, task, tool, option, inputToolName, inputTool):
    print("\t\tERROR: Input to tool '", task, " (", tool, ")' is defined by the output from '", sep = "", end = "", file = sys.stderr)
    print(inputToolName, " (", inputTool, ")' which is a stub.", sep = "", file = sys.stderr)
    print("\t\tERROR: Ensure the linkage section of the pipeline configuration file contains 'extension'", sep = "", file = sys.stderr)
    print("\t\tERROR: defining which of the files to use.", file = sys.stderr)
    self.error = True

  # If an incorrect command line for a tool is provided, the command line to get
  # help on the allowable arguments for that tool is printed to screen.  If the
  # help command is not provided for the tool, this cannot be printed out.
  def noHelpForTool(self, tool):
    print("ERROR: The argument for help for tool '", tool, "' is not present in the configuration file.", sep = "", file = sys.stderr)
    self.error = True

  # If the number of files for the rename task is incorrect, fail.
  def fileCountError(self, task, filename):
    print("\t\tERROR: The rename task requires a single input and output file for tool '", task, "'", sep = "", file = sys.stderr)
    os.remove(filename)
    self.terminate()

  # If the output from a tool is not defined by a command line argument, but the
  # configuration file contains a reference to the command line argument that
  # should be used to generate the file name and this reference is missing, fail.
  # If a requested command is not defined, throw an error.
  def missingCommand(self, task, tool, command):
    print("\tERROR: The output file for tool '", task, " (", tool, ")' requires command '", sep = "", end = "", file = sys.stderr)
    print(command, "'.", sep = "", file = sys.stderr)
    print("\tERROR: This command is not defined.", file = sys.stderr)
    self.error = True

  # For tools where the option order is important, each option must be provided
  # with an ID.  If this is not present for any of the parameters, fail.
  def missingOrderID(self, task, tool, option):
    print("\t\tERROR: The option order for tool '", task, " (", tool, ")' is important", sep = "", file = sys.stderr)
    print("\t\tERROR: Option '", option, "' does not have the 'order' parameter defined", sep = "", file = sys.stderr)
    self.error = True

  # If the position in the order of the command line arguments has already been defined,
  # fail.
  def optionIDExists(self, task, tool, option):
    print("\t\tERROR: The option order for tool '", task, " (", tool, ")' is important", sep = "", file = sys.stderr)
    print("\t\tERROR: Option '", option, "' has a non-unique value of the 'order' parameter", sep = "", file = sys.stderr)
    self.error = True

  # If the order list of arguments is missing a number, print a warning to the screen, but
  # do not terminate.  For example, if a tool has two arguments and the ids given in the
  # configuration file are 1 and 3, check that there isn't supposed to be an option 2.
  def orderWarning(self, task, tool, order):
    print("\t\tWARNING: Tool '", task, " (", tool, ")' has ordered arguments and '", order, "' is missing", sep = "", file = sys.stderr)

  # If the tool configuration file contains a dependency type that is unknown, throw
  # an error.
  def unknownDependencyType(self, text, dependencyType):
    print(text, "ERROR: Unknown format for dependencies '", dependencyType, "'.  Check documentation for allowed types.", sep = '', file = sys.stderr)
    self.error = True

  # List the allowed inputs.
  def allowableInputs(self, pl, tl):
    print("\nThe following tools can have parameters modified:", file = sys.stderr)
    for task in tl.toolArguments.keys():
      tool = pl.information['tools'][task]
      print("\t--", task, ":\t\"", task, " (", tool, ") specific options\"", sep = "", file = sys.stderr)
    print("\nPipeline specific options:", file = sys.stderr)
    for option in pl.information['arguments']:
      print("\t", option, sep = "", end = "", file = sys.stderr)
      if 'short form argument' in pl.information['arguments'][option]:
        print(" (", pl.information['arguments'][option]['short form argument'], ")", sep = "", end = "", file = sys.stderr)
      if 'description' in pl.information['arguments'][option]:
        print(":\t", pl.information['arguments'][option]['description'], sep = '', end = '', file = sys.stderr)
      print(file = sys.stderr)

  #####################
  # Admin mode errors
  #####################
  
  def attemptingRemoveUnknownResource(self, resourceName, dest=sys.stderr):
    print("WARNING: Resource '" + resourceName + "' was not removed because it is unknown", file=dest)

  def extractTarballFailed(self, filename, dest=sys.stderr):
    print("ERROR: Could not extract contents of"+filename, file=dest)

  def gitSubmoduleUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/submodule_update.* files for more details.", file=dest)

  def gitUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/gkno_update.* files for more details.", file=dest)

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
    

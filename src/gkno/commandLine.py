#!/usr/bin/python

from __future__ import print_function
import sys

import errors
from errors import *

class commandLine:

  # Constructor.
  def __init__(self):
    self.toolOptions = {}

  # Print basic information including version to the screen.
  def printInformation(self, version, date):
    print("=============================", sep = "", file = sys.stdout)
    print(" Boston College gkno package\n", sep = "", file = sys.stdout)
    print(" Version: ", version, sep = '', file = sys.stdout)
    print(" Date:    ", date, sep = '', file = sys.stdout)
    print("=============================\n", sep = "", file = sys.stdout)

  # Check the first entry on the command line is valid.
  def getMode(self, tl):
    mode = ''
    er   = errors()

    # If a mode of operation has not been defined, show the gkno
    # launcher usage information.
    try: argument = sys.argv[1]
    except:
      er.usage(tl)
      er.error = True
    if er.error: exit(1)

    # If a pipeline has been selected set the mode to pipe
    if argument == "pipe": mode = "pipe"

    # If a non-existent tool has been selected, show the launcher
    # usage information.
    else:
      if argument in tl.toolInfo.keys(): mode = argument
      else:
        er.usage(tl)
        er.error = True
      if er.error: exit(1)

    return mode

  # The command line can only include arguments for the individual tool specified.
  # In order to use the same routines as the pipeline, modify the command line to
  # be of the form:
  #
  # gkno pipe dummy --tool "options"
  def resetCommandLine(self, tool):
    if len(sys.argv) > 2:
      path = sys.argv[0]
      options = ' '.join(sys.argv[2:len(sys.argv)])
      sys.argv = []
      sys.argv.append(path)
      sys.argv.append('pipe')
      sys.argv.append('dummy')
      sys.argv.append('--' + tool)
      sys.argv.append(options)

  # Parse the command line.
  def parseCommandLine(self, tl, pl, io):
    er      = errors()
    counter = 3
    print("Parsing the command line...", file = sys.stdout)
    sys.stdout.flush()

    # Loop through all of the command line arguments.  If the argument begins
    # with a '-' (or '--'), check if the next argument (if one exists) begins
    # with a '-' or not. If so, populate a hash with the key as the first
    # argument and the value as the second.  If not, set the value as 'flag'.
    while(True):
      try: argument = sys.argv[counter]
      except: break

      # If the argument is '-h' or '--help', call the help.
      if (argument == '-h') or argument == ('--help'):
        er.pipelineUsage(io.jsonPipelineFiles)
        er.allowableInputs(pl, tl)
        exit(0)

      elif argument.startswith('-'):

        # Get the next argument on the command line if one exists.
        try: nextArgument = sys.argv[counter + 1]
        except: nextArgument = ''

        # The syntax -tool="options" is acceptable, so check if the argument
        # contains an = sign and split the argument if it does.
        includesEquals = False
        if '=' in argument:
          includesEquals   = True
          positionOfEquals = argument.find('=')
          nextArgument     = argument[positionOfEquals + 1:len(argument)]
          argument         = argument[0:positionOfEquals]

        print("\t", argument, ":", sep = '', end = '')
        sys.stdout.flush()

        # Strip off the leading dashes and determine if the option is a tool
        # name or a pipeline specific input.
        if argument.startswith('--'): rawArgument  = argument[2:len(argument)]
        elif argument.startswith('-'): rawArgument = argument[1:len(argument)]

        # Check if the argument is the name of one of the tools in the pipeline.
        # If so, the following argument is a list of commands to be applied to that
        # specific tool.  If not, this should be a pipeline specific command.
        if rawArgument in tl.toolOptions.keys():
          toolName = rawArgument
          tool     = pl.information['tools'][rawArgument]
          print(" Setting paramenters for tool '", toolName, " (", tool, ")'...", sep = "", file = sys.stdout)
          sys.stdout.flush()
          if nextArgument == '':
            print(file = sys.stdout)
            sys.stdout.flush()
            er.commandLineToolError(rawArgument)
            er.terminate()
          else:

            # The inputs for a tool can be a list of multiple arguments.  Break the
            # list up into the constituent parts and process each argument in turn.
            arguments = nextArgument.split()
            toolCounter = 0
            while toolCounter < len(arguments):
              argument = arguments[toolCounter]

              # If help was requested, print out tool usage.
              if argument == '-h' or argument == '--help':
                er.toolUsage(tl, tool)
                exit(0)
              if toolCounter < (len(arguments) - 1): value = arguments[toolCounter + 1]
              else: value = ''
              print("\t\t", argument, ":", sep = '', end = '', file = sys.stdout)
              sys.stdout.flush()
              self.processToolOption(tl, pl, toolName, argument, value)
              if not value.startswith('-'): toolCounter += 1
              toolCounter += 1
          if not includesEquals: counter += 1

        # If the argument is defined as an allowable input for the particular pipeline.
        elif argument in pl.information['arguments']:
          try: toolName = pl.information['arguments'][argument]['tool']
          except: er.optionAssociationError('tool', argument, 'pipeline')
          if er.error: er.terminate()

          # If the argument is not tied to a particular tool, but is a pipeline argument.
          if toolName == 'pipeline': self.processPipelineOption(tl, pl, argument, nextArgument)

          # If the argument is tied to a particular tool.
          else:
            command = self.identifyToolOption(tl, pl, toolName, argument)
            self.processToolOption(tl, pl, toolName, command, nextArgument)

          if nextArgument != '': counter += 1

        # If the argument is neither a tool name or one of the allowed pipeline options
        # in its long form, the argument is either a short form argument or an error.
        else:

          # Check if this command is the short-form for one of the pipeline options.  If
          # not, the command is unknown and the script should fail.
          isAlt = False
          for command in pl.information['arguments']:
            if 'alternative' in pl.information['arguments'][command]:
              alt = pl.information['arguments'][command]['alternative']
              if argument == alt:
                isAlt = True
                break

          # If this is a short form option, convert to the long form and process as before.
          if isAlt:

            # Set to the long form.
            argument = command
            try: toolName = pl.information['arguments'][argument]['tool']
            except: er.optionAssociationError('tool', argument, 'pipeline')
            if er.error: er.terminate()

            # Process the command line argument.
            if toolName == 'pipeline': self.processPipelineOption(tl, pl, argument, nextArgument)
            else:
              command = self.identifyToolOption(tl, pl, toolName, argument)
              self.processToolOption(tl, pl, toolName, command, nextArgument)
            if nextArgument != "": counter += 1
          else:
            er.unknownOption(":\n\t\t", 'pipeline', argument)
            er.terminate()

      # If the argument doesn't begin with a '-', this is an error.
      else:
        er.unknownOption("\t\t", 'pipeline', argument)
        er.terminate()

      # Iterate the counter.
      counter += 1
    print(file = sys.stdout)

  # If an option was given on the command line for an argument not associated with any
  # of the individual tools (i.e. it is a pipeline level option), check the data types
  # and update the pipeline class data structure.
  def processPipelineOption(self, tl, pl, argument, value):
    er = errors()

    # Extract and check the data type.
    try: dataType = pl.information['arguments'][argument]['type']
    except: er.optionAssociationError('type', argument, 'pipeline')
    if er.error: er.terminate()
    value = self.checkDataType(tl, pl, 'pipeline', argument, value, dataType)

    # Print the modified pipeline argument to screen and modify in the pipeline
    # class data structure.
    print(" modified '", argument, "' in 'pipeline' from '", pl.options[argument], sep = "", end = "", file = sys.stdout)
    pl.options[argument] = value
    print("' to '", value, "'", sep = "")
    sys.stdout.flush()

  # If an option was given on the command line for an argument that is associated with
  # one of the individual tools, check the data types and update the tools class data structure.
  def identifyToolOption(self, tl, pl, toolName, argument):
    er = errors()

    # Identify the tool and command for which this argument is intended.
    tool = pl.information['tools'][toolName]
    try: command = pl.information['arguments'][argument]['command']
    except: er.optionAssociationError('command', argument, 'pipeline')
    if er.error: er.terminate()

    # Ensure that this command exists for the tool.
    if command not in tl.toolInfo[tool]['options']:
      print(":", file = sys.stderr)
      er.invalidOption('arguments', command, toolName)
      er.terminate()

    return command

  def processToolOption(self, tl, pl, toolName, argument, value):
    er = errors()
    tool = pl.information['tools'][toolName]

    # Check if this option is valid for the tool.
    if argument not in tl.toolInfo[tool]['options']:
      print(file = sys.stdout)
      er.unknownOption("\t\t\t", toolName, argument)
      er.toolUsage(tl, toolName)
      er.terminate()

    # Extract and check the data type.
    try: dataType = tl.toolInfo[tool]['options'][argument]['type']
    except: er.error = True
    if er.error:
       print(file = sys.stdout)
       sys.stdout.flush()
       er.optionAssociationError('type', argument, tool)
       er.terminate()
    value = self.checkDataType(tl, pl, tool, argument, value, dataType)

    # Print the modified tool argument to screen and modify in the tool
    # class data structure.
    print(" modified '", argument, "' in '", toolName, "' from '", tl.toolOptions[toolName][argument], sep = "", end = "", file = sys.stdout)
    tl.toolOptions[toolName][argument] = value
    print("' to '", value, "'", sep = "")
    sys.stdout.flush()

  # Check that the argument has the correct data type.
  def checkDataType(self, tl, pl, tool, argument, value, dataType):
    er = errors()

    # For some command line arguments, multiple entries are permitted and the 'value' can
    # be a list.  If so, check the data type of each member of the list.
    isList = False
    if isinstance(value, list):
      valueList = value
      isList    = True
    else:
      valueList = []
      valueList.append(value)

    # Loop over the list
    for listValue in valueList:

      # If the argument is a flag, check that the value either doesn't exist or begins
      # with a dash as no value should be supplied with the flag.
      if dataType == 'flag':
        if listValue.startswith('-'):
          er.assignedValueToFlag(tool, argument)
          er.terminate()
  
        # Flip the flags setting from set to unset or vice versa.
        if listValue == 'set': listValue = 'unset'
        elif listValue == 'unset': listValue = 'set'
        else: listValue = 'set'
  
      # If the argument expects a Boolean.
      elif dataType == 'bool':
  
        # Ensure that a valid argument has been provided.
        if (listValue != 'True') and (listValue != 'False'):
          print(file = sys.stdout)
          er.incorrectDataType(tool, argument, listValue, dataType)
          er.terminate()
        elif listValue == True: listValue = True
        elif listValue == False: listValue = False
  
      # If the argument demands a string, no checks are required.
      elif dataType == 'string':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(tool, argument, listValue, dataType)
          er.terminate()
  
      # If the argument demands an integer, check that the supplied value is an integer.
      elif dataType == 'integer':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(tool, argument, listValue, dataType)
          er.terminate()
  
        # Try to convert the string from the command line into an integer.  If this
        # fails, throw an error.
        try: listValue = int(listValue)
        except: er.incorrectDataType(tool, argument, listValue, 'integer')
        if er.error: er.terminate()
      elif dataType == 'float':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(tool, argument, listValue, dataType)
          er.terminate()
  
        # Try to convert the string from the command line into a float.  If this
        # fails, throw an error.
        try: listValue = float(listValue)
        except: er.incorrectDataType(tool, argument, listValue, 'floating point')
        if er.error: er.terminate()
      else:
        er.unknownDataType(tool, argument, dataType)
        er.terminate()

    # If the value was not a list, it was converted to a list for checking.  Return to the
    # original single value.
    if not isList: value = valueList[0]

    return value

  # Loop over the tools and check that all required information has been set.
  def checkParameters(self, tl, pl):
    er = errors()

    print("Checking that all required information has been provided and setting up dependencies/outputs...", file = sys.stdout)
    for toolName in pl.information['workflow']:
      tool = pl.information['tools'][toolName]
      print("\t", toolName, " (", tool, ")...", sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()

      if toolName not in tl.outputs: tl.outputs[toolName] = ''
      if toolName not in tl.dependencies: tl.dependencies[toolName] = ''
      for option in tl.toolInfo[tool]['options']:

        # Check that the 'required' element is in the option block.
        isRequired  = False
        isOptionSet = False
        try: required = tl.toolInfo[tool]['options'][option]['required']
        except: er.toolOptionsError('required', tool, option)
        if er.error: er.terminate()
        if required == 'true': isRequired = True

        # Check if the option has a value.  Non-required elements may remain unset and
        # this is allowed.
        value = ''
        if option in tl.toolOptions[toolName]:
          value = tl.toolOptions[toolName][option]
          if value != '': isOptionSet = True

        # If the value is required and no value has been provided, fail.
        if isRequired and not isOptionSet:
          print(file = sys.stdout)
          er.missingRequiredValue(toolName, tool, option)
          er.terminate()

      print("done.", file = sys.stdout)

    print(file = sys.stdout)

  # Check the filename extension.  If the filename is not a stub and the
  # name soesn't end with the expected extension, throw an error.
  def checkExtension(self, tl, toolName, tool, option):
    er = errors()

    # First check if the filename is a stub.
    stub     = False
    correct  = False
    if 'stub' in tl.toolInfo[tool]['options'][option]:
      if tl.toolInfo[tool]['options'][option]['stub'] == 'true': stub = True

    if not stub:
      try:

        # The extension could be a list of allowable extensions separated by pipes.
        # Split the extension on the pipes and check the files extension against
        # all the allowed extensions.
        extensions = tl.toolInfo[tool]['options'][option]['extension'].split('|')

        # If the extension is listed as null, do not check the extension as it is
        # permitted to be anything.
        if (len(extensions) == 1) and (extensions[0] == 'null'):
          next
        else:
          for extension in extensions:
            extension = '.' + extension
            if tl.toolOptions[toolName][option].endswith(extension):
              correct = True
              break

          # If all the extensions have been checked and the files extension did not
          # match any of them, throw an error.
          if not correct:
            print(file = sys.stdout)
            er.extensionError(option, tl.toolOptions[toolName][option], tl.toolInfo[tool]['options'][option]['extension'])
      except: er.toolOptionsError('extension', tool, option)
      if er.error: er.terminate()

  # Check to see if the input file has a path or not.  If not, determine if the
  # file is a resource file or not and set the path to the resources path if
  # it is a resource file, otherwise set it to the input path.
  def setPath(self, pl, tl, toolName, tool, option, isInput, isOutput, isResource):

    # Check if the file already contains a path (e.g. already contains the
    # '/' character.
    if '/' not in tl.toolOptions[toolName][option]:
      filePath = ''
      if isResource: filePath = pl.options['--resource-path'] + '/' + tl.toolOptions[toolName][option]
      elif isInput:  filePath = pl.options['--input-path']    + '/' + tl.toolOptions[toolName][option]
      elif isOutput: filePath = pl.options['--output-path']   + '/' + tl.toolOptions[toolName][option]
      tl.toolOptions[toolName][option] = filePath

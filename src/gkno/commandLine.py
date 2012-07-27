#!/usr/bin/python

from __future__ import print_function
import sys

import errors
from errors import *

class commandLine:

  # Constructor.
  def __init__(self):
    pass

  # Check the first entry on the command line is valid.
  def getMode(self, io, gknoHelp, tl, pl):

    # If a mode of operation has not been defined, show the gkno
    # launcher usage information.
    #terminate = False
    try:
      argument = sys.argv[1]

      # If a pipeline has been selected set the mode to pipe and get the name of
      # the pipeline.
      if argument == "pipe":
        pl.isPipeline   = True
        pl.pipelineName = ''

        try: pl.pipelineName = sys.argv[2]
        except:
          gknoHelp.pipelineHelp = True
          gknoHelp.printHelp    = True

      # If this isn't a pipeline, the argument should be the name of a tool.
      else:
        tl.tool = argument

    except:
      gknoHelp.generalHelp = True
      gknoHelp.printHelp   = True

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, gknoHelp, pl):
    for count, argument in enumerate(sys.argv):
      if (argument == '--help') or (argument == '-h'):

        # If there are arguments on the command line after the help command, write
        # a warning to screen as this may be a typo.
        if count != (len(sys.argv) - 1): gknoHelp.extraArgumentsWarning()

        # Determine where the help is requested.  The request could be for general
        # usage help, help with a tool, or help with a pipeline.
        #
        # Begin with general or tool help.
        if not pl.isPipeline:
          if count == 1:
            gknoHelp.generalHelp  = True
            gknoHelp.printHelp    = True
          elif count == 2:
            gknoHelp.toolHelp   = True
            gknoHelp.printHelp  = True
        else:
          if count == 2:
            gknoHelp.pipelineHelp = True
            gknoHelp.printHelp    = True
          elif count == 3:
            gknoHelp.specificPipelineHelp = True
            gknoHelp.printHelp            = True


    # Remove the path, 'pipe' and pipeline name from the command line if gkno is
    # being run in pipeline mode, or the path and tool name if in tool mode, leaving
    # just the user specified arguments.
    if pl.isPipeline: countMax = 4
    else: countMax = 3
    for i in range(1, countMax):
      if len(sys.argv) != 0: sys.argv.pop(0)

  # Parse the command line in tool mode.  Here all of the arguments are associated
  # with the specified tool or the pipeline.  Check to see that there are no
  # conflicts between the tool and pipeline arguments and update the tl.toolArguments
  # data structure with given values.
  def parseToolCommandLine(self, gknoHelp, io, tl, pl, commandLine, task, tool, verbose):
    er           = errors()
    modifiedTool = ''
    if verbose: print('Parsing the command line...', end = '', file = sys.stdout)
    sys.stdout.flush()
    while(len(commandLine) != 0):
      argument           = commandLine.pop(0)
      isPipelineArgument = False
      isToolArgument     = False

      # Check if the argument is a pipeline argument (long or short form).
      if argument in pl.information['arguments']:
        isPipelineArgument = True
      else:
        for pipelineArgument in pl.information['arguments']:
          if 'alternative' in pl.information['arguments'][pipelineArgument]:
            shortFormArgument = pl.information['arguments'][pipelineArgument]['alternative']
            if argument == shortFormArgument:
              isPipelineArgument = True
              argument           = pipelineArgument

      # Check if the argument is a tool argument (long or short form).
      if argument in tl.toolArguments[task]:
        isToolArgument = True
      else:
        for toolArgument in tl.toolArguments[task]:
          if 'alternative' in tl.toolInfo[tool]['arguments'][toolArgument]:
            shortFormArgument = tl.toolInfo[tool]['arguments'][toolArgument]['alternative']
          if argument == shortFormArgument:
            isToolArgument = True
            argument       = toolArgument

      # Check that there is no conflict between the tool and the pipeline arguments.  If
      # a tool argument is the same as a pipeline argument, gkno cannot distinguish between
      # them and will fail.
      if isToolArgument: modifiedTool = task
      if isPipelineArgument: modifiedTool = 'pipeline'
      if isToolArgument and isPipelineArgument:
        print("FAIL")
        exit(1)

      # If the argument is neither a tool argument or a pipeline argument, then fail with
      # the tool usage information along with the additional message explaining which
      # argument is unknown.
      if not isToolArgument and not isPipelineArgument:
        print(file = sys.stdout)
        gknoHelp.toolUsage(tl, tool)
        er.unknownToolArgument("\n", modifiedTool, argument)
        exit(1)

      # If the next argument does not begin with a '-', assume that it is the value associated
      # with the current argument.
      isLastArgument = True
      try:
        nextArgument   = commandLine[0]
        isLastArgument = False
      except: nextArgument = ''
      if not nextArgument.startswith('-') and not isLastArgument:
        tl.toolArguments[modifiedTool][argument] = nextArgument
        commandLine.pop(0)

      # If the next argument begins with a '-', then this option must be a flag (this
      # will be checked later).  As the flag has been set, set the value in tl.toolArguments
      # to set.
      else: tl.toolArguments[modifiedTool][argument] = 'set'

    if verbose: print('done.', file = sys.stdout)
    if verbose: print(file = sys.stdout)
    sys.stdout.flush()

  # Parse the command line in pipeline mode.  Here arguments are either pipeline
  # arguments or the name of a constituent tool.  If the argument is the name of
  # a tool, the following argument needs to be a list of arguments in quotation
  # marks for that tool.
  def parsePipelineCommandLine(self, gknoHelp, io, tl, pl):
    er   = errors()

    print('Parsing the command line...', file = sys.stdout)
    sys.stdout.flush()
    while(len(sys.argv) != 0):
      argument = sys.argv.pop(0)
      isPipelineArgument = False
      isToolName         = False

      # Check if the argument is a pipeline argument (long or short form).
      if argument in pl.information['arguments']:
        isPipelineArgument = True
      else:
        for pipelineArgument in pl.information['arguments']:
          if 'alternative' in pl.information['arguments'][pipelineArgument]:
            shortFormArgument = pl.information['arguments'][pipelineArgument]['alternative']
            if argument == shortFormArgument:
              isPipelineArgument = True
              argument           = pipelineArgument

      # Check if the argument is a tool name.
      if argument.startswith('--'): task = argument[2:]
      elif argument.startswith('-'):  task = argument[1:]
      if task in tl.toolArguments.keys(): isToolName = True

      # If the argument is neither a tool name or a pipeline argument, then fail with
      # the pipeline usage information along with the additional message explaining which
      # argument caused the problem.
      if not isToolName and not isPipelineArgument:
        print(file = sys.stdout)
        gknoHelp.specificPipelineUsage(pl)
        er.unknownPipelineArgument("\n", argument)
        exit(1)

      # If the argument is a tool name, the next argument on the command line is a list of
      # commands specifically for that tool.  If there is no following argument, throw an
      # exception
      if isToolName:
        print("\tProcessing command line arguments for tool '", task, '\'...', sep = '', end = '', file = sys.stdout)
        sys.stdout.flush()
        try: nextArgument = sys.argv[0]
        except: 
          er.commandLineToolError("\n\t\t", pl.pipelineName, task)
          er.error = True
        if er.error: er.terminate()

        # Send the command line to the parseToolCommandLine routine to set up the
        # individual tool options.
        toolCommandLine = nextArgument.split()
        tool            = pl.information['tools'][task]
        self.parseToolCommandLine(gknoHelp, io, tl, pl, toolCommandLine, task, tool, False)
        sys.argv.pop(0)
        print('done.', file = sys.stdout)
        sys.stdout.flush()

      # If the argument is a pipeline argument, check that the argument points to a tool
      # in the pipeline and that the tool argument it points to is valid, then modify the
      # tl.toolArguments structure.
      elif isPipelineArgument:
        tool    = pl.information['arguments'][argument]['tool'] if 'tool' in pl.information['arguments'][argument] else ''
        command = pl.information['arguments'][argument]['command'] if 'command' in pl.information['arguments'][argument] else ''
        isLastArgument = False
        try: nextArgument = sys.argv[0]
        except:
          nextArgument   = ''
          isLastArgument = True
        if not nextArgument.startswith('-') and not isLastArgument:
          if tool == 'pipeline': tl.toolArguments[tool][argument] = nextArgument
          else: tl.toolArguments[tool][command] = nextArgument
          sys.argv.pop(0)

        # If the next argument begins with a '-', then this option must be a flag (this
        # will be checked later).  As the flag has been set, set the value in tl.toolArguments
        # to set.
        else: tl.toolArguments[tool][argument] = 'set'

    print(file = sys.stdout)
    sys.stdout.flush()

  # Check to see if the input file has a path or not.  If not, determine if the
  # file is a resource file or not and set the path to the resources path if
  # it is a resource file, otherwise set it to the input path.
  def setPaths(self, tl, pl, task, tool):
    print("\t\tChecking file paths...", end = '', file = sys.stdout)
    sys.stdout.flush()

    # Loop over all the tool arguments and check if the argument is for an input or output
    # file.
    for argument in tl.toolArguments[task]:

      # If the value is blank, prior to constructing the Makefiles, each
      # argument is checked and if the argument is not set and is required, gkno 
      # will catch the omission.
      if (tl.toolArguments[task][argument] == '') or (argument == 'json parameters'): continue
      if tl.toolArguments[task][argument] == 'json parameters': print("WOOOOP")

      # Check if an input, output or resource file.
      isInput    = True if tl.toolInfo[tool]['arguments'][argument]['input'] == 'true' else False
      isOutput   = True if tl.toolInfo[tool]['arguments'][argument]['output'] == 'true' else False
      isResource = True if tl.toolInfo[tool]['arguments'][argument]['resource'] == 'true' else False

      if isInput or isOutput:

        # Check if the file already contains a path (e.g. already contains the
        # '/' character.
        if '/' not in tl.toolArguments[task][argument]:
          filePath = ''
          if isResource: filePath = tl.toolArguments['pipeline']['--resource-path'] + '/' + tl.toolArguments[task][argument]
          elif isInput:  filePath = tl.toolArguments['pipeline']['--input-path']    + '/' + tl.toolArguments[task][argument]
          elif isOutput: filePath = tl.toolArguments['pipeline']['--output-path']   + '/' + tl.toolArguments[task][argument]
          tl.toolArguments[task][argument] = filePath

        # Check that the file has the correct extension.
        self.checkExtension(tl, task, tool, argument, isOutput)

    print('done.', file = sys.stdout)
    sys.stdout.flush()

  # Check the filename extension.  If the filename is not a stub and the
  # name soesn't end with the expected extension, throw an error.
  def checkExtension(self, tl, task, tool, argument, isOutput):
    er      = errors()
    correct = False

    # First check if the filename is a stub.
    isStub = False
    if 'stub' in tl.toolInfo[tool]['arguments'][argument]: isStub = True if tl.toolInfo[tool]['arguments'][argument]['stub'] == 'true' else False

    # Only find the extension and check the files if the filename isn't a stub.
    if not isStub:

      # The extension could be a list of allowable extensions separated by pipes.
      # Split the extension on the pipes and check the files extension against
      # all the allowed extensions.
      if 'extension' in tl.toolInfo[tool]['arguments'][argument]:
        extensions = tl.toolInfo[tool]['arguments'][argument]['extension'].split('|')

        # If the extension is listed as null, do not check the extension as it is
        # permitted to be anything.
        if (len(extensions) == 1) and (extensions[0] == 'null'): next
        else:
          for extension in extensions:
            extension = '.' + extension
            if tl.toolArguments[task][argument].endswith(extension):
              correct = True
              break

          # If all the extensions have been checked and the files extension did not
          # match any of them, throw an error.
          if not correct and isOutput:
            tl.toolArguments[task][argument] += '.' + extensions[0]
          elif not correct:
            print(file = sys.stdout)
            er.extensionError(argument, tl.toolArguments[task][argument], tl.toolInfo[tool]['arguments'][argument]['extension'])
            er.terminate()
      else:
        er.toolArgumentsError('extension', tool, argument)
        er.terminate()

  # Loop over the tools and check that all required information has been set.
  def checkParameters(self, tl, pl, task, tool):
    er = errors()

    print("\t\tChecking all required information is set and valid...", end = '', file = sys.stdout)
    sys.stdout.flush()
    for argument in tl.toolArguments[task]:
      if argument == 'json parameters': continue
      isRequired = True if tl.toolInfo[tool]['arguments'][argument]['required'] == 'true' else False

      # Check if the option has a value.  Non-required elements may remain unset and
      # this is allowed.
      isArgumentSet = True if tl.toolArguments[task][argument] != '' else False

      # If the value is required and no value has been provided, fail.
      if isRequired and not isArgumentSet:
        er.missingRequiredValue(True, "\t\t\t", task, tool, argument)
        er.terminate()

      # If the value is set, check that the data type is correct.
      elif isArgumentSet:
        default = self.checkDataType(tl, pl, task, tool, argument)

    print('done.', file = sys.stdout)
    sys.stdout.flush()

  # Check that the argument has the correct data type.
  def checkDataType(self, tl, pl, task, tool, argument):
    er       = errors()
    value    = tl.toolArguments[task][argument]
    dataType = tl.toolInfo[tool]['arguments'][argument]['type']

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
          er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, dataType)
          er.terminate()
        elif listValue == True: listValue = True
        elif listValue == False: listValue = False
  
      # If the argument demands a string, no checks are required.
      elif dataType == 'string':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, dataType)
          er.terminate()
  
      # If the argument demands an integer, check that the supplied value is an integer.
      elif dataType == 'integer':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, dataType)
          er.terminate()
  
        # Try to convert the string from the command line into an integer.  If this
        # fails, throw an error.
        try: listValue = int(listValue)
        except: er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, 'integer')
        if er.error: er.terminate()
      elif dataType == 'float':
        if (listValue == '') or (listValue.startswith('-')):
          print(file = sys.stdout)
          er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, dataType)
          er.terminate()
  
        # Try to convert the string from the command line into a float.  If this
        # fails, throw an error.
        try: listValue = float(listValue)
        except: er.incorrectDataType(True, "\t\t\t", tool, argument, listValue, 'floating point')
        if er.error: er.terminate()
      else:
        er.unknownDataType(True, "\t\t\t", tool, argument, dataType)
        er.terminate()

    # If the value was not a list, it was converted to a list for checking.  Return to the
    # original single value.
    if not isList: value = valueList[0]

    return value

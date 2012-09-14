#!/usr/bin/python

from __future__ import print_function
import sys

import errors
from errors import *

class commandLine:

  # Constructor.
  def __init__(self, tl, admin):

    # Check to see if the verbose argument is set.
    if 'pipeline' not in tl.toolArguments: tl.toolArguments['pipeline'] = {}
    tl.toolArguments['pipeline']['--verbose'] = True
    for counter, argument in enumerate(sys.argv):
      if (argument == '--verbose') or (argument == '-vb'):
        admin.isVerbose = True
        if counter + 1 < len(sys.argv):
          if sys.argv[counter + 1] == 'True': 
            tl.toolArguments['pipeline']['--verbose'] = True
          else: tl.toolArguments['pipeline']['--verbose'] = False

  # Check the first entry on the command line is valid.
  def getMode(self, io, gknoHelp, tl, pl, admin):

    # If a mode of operation has not been defined, show the gkno
    # launcher usage information.
    #terminate = False
    try:
      argument = sys.argv[1]

      # If a pipeline has been selected set the mode to pipe and get the name of
      # the pipeline.
      if argument == 'pipe':
        pl.isPipeline   = True
        pl.pipelineName = ''

        try: pl.pipelineName = sys.argv[2]
        except:
          gknoHelp.pipelineHelp = True
          gknoHelp.printHelp    = True

      # If the test described in the 'Getting started with gkno' tutorial is
      # requested, set the mode to 'pipe' and set the pipelineName to run-test.
      elif argument == 'run-test':
        pl.isPipeline   = True
        pl.pipelineName = 'run-test'

      # If any admin operation was requested, set requested mode.
      # (We'll parse for add'l args later.)
      elif argument in admin.allModes:
        admin.isRequested = True
        admin.mode = argument

      # If this isn't a pipeline or admin command, the argument should be the name of a tool.
      else:
        tl.tool = argument

    except:
      gknoHelp.generalHelp = True
      gknoHelp.printHelp   = True

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, gknoHelp, pl, admin):
    for count, argument in enumerate(sys.argv):
      if (argument == '--help') or (argument == '-h'):

        # If there are arguments on the command line after the help command, write
        # a warning to screen as this may be a typo.
        if count != (len(sys.argv) - 1): gknoHelp.extraArgumentsWarning()

        # Determine where the help is requested.  The request could be for general
        # usage help, help with a tool, help with a pipeline, or help with an admin op.
        
        # gkno --help
        if count == 1:
          gknoHelp.generalHelp  = True
          gknoHelp.printHelp    = True

        # gkno pipe --help
        # gkno <admin> --help
        # gkno <tool> --help
        elif count == 2:
          if pl.isPipeline:
            gknoHelp.pipelineHelp = True
            gknoHelp.printHelp    = True
          elif admin.isRequested:
            gknoHelp.adminHelp = True
            gknoHelp.printHelp = True
          else:
            gknoHelp.toolHelp   = True
            gknoHelp.printHelp  = True
      
        # gkno pipe <pipe> --help
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

  # Check if the pipeline is going to be run multiple times.
  def checkForMultipleRuns(self, io, pl):
    er = errors()

    # Get the name of the file containing a list of all of the inputs, check that
    # the file exists and is a valid json.
    #
    # When iterating over the arguments in the multiple runs data structure,
    # the command line will have to be built each time.  All of the arguments
    # on the command line that are not in the multiple runs file need to be
    # included on each command line, so store this information.
    self.baseCommandLine = []
    while(True):
      if len(sys.argv) >= 1: argument = sys.argv.pop(0)
      else: break
      if (argument == '--multiple-runs') or (argument == '-mr'):
        try: multipleName = sys.argv.pop(0)
        except: er.missingFileForMultipleRuns(False, '')
        if er.error: er.terminate()
        pl.hasMultipleRuns = True
      else: self.baseCommandLine.append(argument)

    # If multiple runs are being performed, open the json file with the information
    # for the multiple runs and populate the relevant data structures.
    if pl.hasMultipleRuns:

      # Open the json file.
      inputData = io.getJsonData(multipleName)
  
      # Populate a data structure with the information from the json file.
      # First the format of the data list is defined.
      if 'format of data list' not in inputData:
        er.missingJsonFormatForMultipleRuns(True, '', 'format of data list')
        er.terminate()
  
      if 'data list' not in inputData:
        er.missingJsonFormatForMultipleRuns(True, '', 'data list')
        er.terminate()
  
      for argument in inputData['format of data list']: pl.multipleRunsListFormat.append(argument)
      pl.multipleRunsInputArguments = inputData['data list']
  
      # Check the number of input arguments in the list is consistent with the
      # format.  For example, if there are n entries in the format list, then
      # there must be a multiple of m x n, entries in the inputArguments list,
      # where m is the number of runs to be performed.
      pl.multipleRunsNumberOfArguments = len(pl.multipleRunsListFormat)
      numberOfInputArguments           = len(pl.multipleRunsInputArguments)
  
      if numberOfInputArguments % pl.multipleRunsNumberOfArguments != 0:
        er.incorrectNumberOfEntriesInMultipleJson(True, '')
        er.terminate()
  
      pl.numberOfMultipleRuns          = numberOfInputArguments / pl.multipleRunsNumberOfArguments

  # Build the command line using the information in the multiple runs data structure.
  def buildCommandLineMultipleRuns(self, pl):
    sys.argv = []
    for argument in self.baseCommandLine: sys.argv.append(argument)
    for count in range(0, pl.multipleRunsNumberOfArguments):
      argument = pl.multipleRunsListFormat[count]
      value    = pl.multipleRunsInputArguments.pop(0)
      sys.argv.append(argument)
      sys.argv.append(value)

  # Parse the command line in tool mode.  Here all of the arguments are associated
  # with the specified tool or the pipeline.  Check to see that there are no
  # conflicts between the tool and pipeline arguments and update the tl.toolArguments
  # data structure with given values.
  def parseToolCommandLine(self, gknoHelp, io, tl, pl, commandLine, task, tool, verbose):
    er           = errors()
    modifiedTool = ''
    verbose = True if verbose and (tl.toolArguments['pipeline']['--verbose']) else False
    if verbose:
      print('Parsing the command line...', end = '', file = sys.stdout)
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
          if 'short form argument' in pl.information['arguments'][pipelineArgument]:
            shortFormArgument = pl.information['arguments'][pipelineArgument]['short form argument']
            if argument == shortFormArgument:
              isPipelineArgument = True
              argument           = pipelineArgument

      # Check if the argument is a tool argument (long or short form).
      if argument in tl.toolArguments[task]:
        isToolArgument = True
      else:
        for toolArgument in tl.toolArguments[task]:
          if 'short form argument' in tl.toolInfo[tool]['arguments'][toolArgument]:
            shortFormArgument = tl.toolInfo[tool]['arguments'][toolArgument]['short form argument']
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

        # Some tools allow the same argument to be set multiple times.  For example, bamtools
        # allows the inclusion of any number of input bam files by repeated use of the -in
        # argument.  If this is the case, add the new value to a list, otherwise just set a
        # single value.
        hasMultiple = False
        if argument in tl.toolInfo[tool]['arguments']:
          if 'allow multiple definitions' in tl.toolInfo[tool]['arguments'][argument]:
            if tl.toolInfo[tool]['arguments'][argument]['allow multiple definitions'] == 'true': hasMultiple = True

        if hasMultiple:
          if tl.toolArguments[modifiedTool][argument] == '':
            tl.toolArguments[modifiedTool][argument] = []
          tl.toolArguments[modifiedTool][argument].append(nextArgument)
        else:
          tl.toolArguments[modifiedTool][argument] = nextArgument
        commandLine.pop(0)

      # If the next argument begins with a '-', then this option must be a flag (this
      # will be checked later).  As the flag has been set, set the value in tl.toolArguments
      # to set.
      else: tl.toolArguments[modifiedTool][argument] = 'set'

    if verbose:
      print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Parse the command line in pipeline mode.  Here arguments are either pipeline
  # arguments or the name of a constituent tool.  If the argument is the name of
  # a tool, the following argument needs to be a list of arguments in quotation
  # marks for that tool.
  def parsePipelineCommandLine(self, gknoHelp, io, tl, pl):
    toolsWrittenToScreen = False
    writingOnNewLine     = False
    er                   = errors()
    verbose = True if tl.toolArguments['pipeline']['--verbose'] else False

    if verbose:
      print('Parsing the command line...', end = '', file = sys.stdout)
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
          if 'short form argument' in pl.information['arguments'][pipelineArgument]:
            shortFormArgument = pl.information['arguments'][pipelineArgument]['short form argument']
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
        if verbose: print(file = sys.stdout)
        gknoHelp.specificPipelineUsage(tl, pl)
        er.unknownPipelineArgument("\n", argument)
        exit(1)

      # If the argument is a tool name, the next argument on the command line is a list of
      # commands specifically for that tool.  If there is no following argument, throw an
      # exception
      if isToolName:
        if tl.toolArguments['pipeline']['--verbose']:
          if verbose:
            if not writingOnNewLine:
              print(file = sys.stdout)
              writingOnNewLine = True
            print("\tProcessing command line arguments for tool '", task, '\'...', sep = '', end = '', file = sys.stdout)
            sys.stdout.flush()
          toolsWrittenToScreen = True
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
        if verbose:
          print('done.', file = sys.stdout)
          sys.stdout.flush()
          toolsWrittenToScreen = True

      # If the argument is a pipeline argument, check that the argument points to a tool
      # in the pipeline and that the tool argument it points to is valid, then modify the
      # tl.toolArguments structure.
      elif isPipelineArgument:
        linkToTask     = pl.information['arguments'][argument]['link to this task'] if 'link to this task' in pl.information['arguments'][argument] else ''
        linkToArgument = pl.information['arguments'][argument]['link to this argument'] if 'link to this argument' in pl.information['arguments'][argument] else ''
        dataType       = pl.information['arguments'][argument]['type'] if 'type' in pl.information['arguments'][argument] else ''
        isLastArgument = False
        try: nextArgument = sys.argv[0]
        except:
          nextArgument   = ''
          isLastArgument = True
        if not nextArgument.startswith('-') and not isLastArgument:
 
          # If the supplied argument is a Boolean, ensure that it is treated as a Boolean.
          if nextArgument == 'True': nextArgument = True
          if nextArgument == 'False': nextArgument = False
          if linkToTask   == 'pipeline': tl.toolArguments[linkToTask][argument] = nextArgument
          else:

            # Some tools allow multiple definitions of the same argument, for example
            # bamtools can allow for multiple input bam files.  Check if this is such
            # an argument and handle appropriately.
            allowMultipleEntries = False
            linkToTool = pl.information['tools'][linkToTask]
            if 'allow multiple definitions' in tl.toolInfo[linkToTool]['arguments'][linkToArgument]:
              if tl.toolInfo[linkToTool]['arguments'][linkToArgument]['allow multiple definitions'] == 'true': allowMultipleEntries = True

            if allowMultipleEntries:
              if tl.toolArguments[linkToTask][linkToArgument] == '':
                tl.toolArguments[linkToTask][linkToArgument] = []
              tl.toolArguments[linkToTask][linkToArgument].append(nextArgument)
            else:
              tl.toolArguments[linkToTask][linkToArgument] = nextArgument

          sys.argv.pop(0)

        # If the next argument begins with a '-', then this option must be a flag (this
        # will be checked later).  As the flag has been set, set the value in tl.toolArguments
        # to set.
        elif nextArgument.startswith('-') and (dataType == 'flag'): tl.toolArguments[linkToTask][argument] = 'set'

        # If this is the last argument and the argument is not a flag then there is an
        # error.  A value must be set.
        elif (dataType != 'flag') and (isLastArgument or (nextArgument.startswith('-'))):
          er.missingCommandLineArgumentValue(False, "\t\t", linkToTask, linkToArgument, argument)
          er.terminate()

    if verbose:
      if not toolsWrittenToScreen: print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Check to see if the input file has a path or not.  If not, determine if the
  # file is a resource file or not and set the path to the resources path if
  # it is a resource file, otherwise set it to the input path.
  def setPaths(self, tl, pl, task, tool):
    if tl.toolArguments['pipeline']['--verbose']:
      print("\t\tChecking file paths...", end = '', file = sys.stdout)
      sys.stdout.flush()

    # Loop over all the tool arguments and check if the argument is for an input or output
    # file.
    for argument in tl.toolArguments[task]:

      # If the value is blank, prior to constructing the Makefiles, each
      # argument is checked and if the argument is not set and is required, gkno 
      # will catch the omission.
      if (tl.toolArguments[task][argument] == '') or (argument == 'json parameters'): continue

      # Check if an input, output or resource file.
      isInput    = True if tl.toolInfo[tool]['arguments'][argument]['input'] == 'true' else False
      isOutput   = True if tl.toolInfo[tool]['arguments'][argument]['output'] == 'true' else False
      isResource = True if tl.toolInfo[tool]['arguments'][argument]['resource'] == 'true' else False

      if isInput or isOutput:

        # Check if there is a list of filenames, rather than a single value.
        isFileList = True if isinstance(tl.toolArguments[task][argument], list) else False

        # Check the paths and the extension.
        if isFileList:
          fileList = []
          for filename in tl.toolArguments[task][argument]:
            intermediateFilename = self.setFile(tl, filename, isInput, isOutput, isResource)
            finalFilename        = self.checkExtension(tl, task, tool, argument, isOutput, intermediateFilename)
            fileList.append(finalFilename)
          tl.toolArguments[task][argument] = fileList
        else:
          intermediateFilename = self.setFile(tl, tl.toolArguments[task][argument], isInput, isOutput, isResource)
          finalFilename        = self.checkExtension(tl, task, tool, argument, isOutput, intermediateFilename)
          tl.toolArguments[task][argument] = finalFilename

    if tl.toolArguments['pipeline']['--verbose']:
      print('done.', file = sys.stdout)
      sys.stdout.flush()

  # Provided the filename, check if resource, input or output and set the file accordingly.
  def setFile(self, tl, filename, isInput, isOutput, isResource):

    # Check if the file already contains a path (e.g. already contains the
    # '/' character.
    filePath = ''
    if '/' not in filename:
      if isResource: filePath = tl.toolArguments['pipeline']['--resource-path'] + '/' + filename
      elif isInput:  filePath = tl.toolArguments['pipeline']['--input-path']    + '/' + filename
      elif isOutput: filePath = tl.toolArguments['pipeline']['--output-path']   + '/' + filename

    # If the file path is given, ensure that the full path is given. For example,
    # if './file' is specified, modify the './' to the full path of the current
    # directory.  If the path specified is a parameter and as such begins with '$(',
    # do not modify the path.
    else:
      if not filename.startswith('$('):
        givenPath = filename.split('/')
        filename  = givenPath.pop()
        givenPath = '/'.join(givenPath)
        filePath  = os.path.abspath(givenPath) + '/' + filename
      else: filePath = filename

    return filePath

  # Check the filename extension.  If the filename is not a stub and the
  # name soesn't end with the expected extension, throw an error.
  def checkExtension(self, tl, task, tool, argument, isOutput, filename):
    er      = errors()
    correct = False
    newLine = True if tl.toolArguments['pipeline']['--verbose'] else False
    pad     = "\t\t\t" if tl.toolArguments['pipeline']['--verbose'] else ''

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
        if (len(extensions) == 1) and (extensions[0] == 'no extension'): next
        else:
          for extension in extensions:
            extension = '.' + extension
            if filename.endswith(extension):
              correct = True
              break

          # If all the extensions have been checked and the files extension did not
          # match any of them, throw an error.
          if not correct and isOutput:
            filename += '.' + extensions[0]
          elif not correct:
            er.extensionError(newLine, pad, argument, filename, tl.toolInfo[tool]['arguments'][argument]['extension'])
            er.terminate()
      else:
        er.missingFieldForTool(newLine, pad, tool, argument, 'extension', '')
        er.terminate()

    return filename

  # Loop over the tools and check that all required information has been set.
  def checkParameters(self, tl, pl, gknoHelp, task, tool, checkRequired):
    er      = errors()
    newLine = True if tl.toolArguments['pipeline']['--verbose'] else False
    pad     = "\t\t\t" if tl.toolArguments['pipeline']['--verbose'] else ''

    if tl.toolArguments['pipeline']['--verbose']:
      print("\t\tChecking all required information is set and valid...", end = '', file = sys.stdout)
      sys.stdout.flush()
    for argument in tl.toolArguments[task]:
      if argument == 'json parameters': continue
      isRequired = True if tl.toolInfo[tool]['arguments'][argument]['required'] == 'true' else False

      # Check if the option has a value.  Non-required elements may remain unset and
      # this is allowed.
      isArgumentSet = True if tl.toolArguments[task][argument] != '' else False

     # If the value is required and no value has been provided, terminate.
      if isRequired and checkRequired and not isArgumentSet:

        # Check if the argument is an input file and if so, if the input is coming from
        # the stream.  If so, this does not need to be set.
        isInput = True if tl.toolInfo[tool]['arguments'][argument]['input'] == 'true' else False
        inputIsStream = False
        if isInput:
          previousTask = ''
          for currentTask in pl.information['workflow']:
            if currentTask == task: break
            else: previousTask = currentTask
          if 'tools outputting to stream' in pl.information:
            if previousTask in pl.information['tools outputting to stream']: inputIsStream = True
        
        # If the input to task is not a stream and the input is not set,
        # terminate with an error.
        if not inputIsStream:
          er.missingRequiredValue(newLine, pad, task, tool, argument, tl, pl)
          er.terminate()

        # If the input to this task is a stream, check if this particular argument has
        # instructions on how to handle the stream.  If it doesn't have any, then this
        # input still needs to be set.
        else:
          ignoreInput = True if 'if input is stream' in tl.toolInfo[tool]['arguments'][argument] else False
          if not ignoreInput:
            er.missingRequiredValue(newLine, pad, task, tool, argument, tl, pl)
            er.terminate()

      # If the value is set, check that the data type is correct.
      elif isArgumentSet:
        default = self.checkDataType(tl, pl, task, tool, argument)

    if tl.toolArguments['pipeline']['--verbose']:
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

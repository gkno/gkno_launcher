#!/usr/bin/python

from __future__ import print_function
import sys

import errors
from errors import *

import files
from files import *

class commandLine:

  # Constructor.
  def __init__(self, tl, admin):
    self.arguments       = {}
    self.argumentList    = []
    self.linkedArguments = {}
    self.uniqueArguments = {}

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

  # Parse through the command line and put all of the arguments into a list.
  def getCommandLineArguments(self, tool, isPipeline, pipeArguments, pipeShortForms, workflow):
    skip = False
    for count, argument in enumerate(sys.argv[1:]):
      if skip: skip = False
      else: 

        # Check the next argument on the command line.  If it does not begin with a '-', then this
        # is assumed to be a value that goes with the current arguments.  Add the pair to the list
        # of arguments as a tuple.
        try: nextArgument = sys.argv[count + 2]
        except: nextArgument = '-'

        # The command line will include an instruction on whether to run a pipe or the name of the
        # tool.  Ignore this argument.
        if argument != tool and argument != 'pipe' and argument != 'run-test':
          if argument in pipeShortForms: argument = pipeShortForms[argument]
          if argument not in self.uniqueArguments: self.uniqueArguments[argument] = 1
          else: self.uniqueArguments[argument] += 1

        # Check if the next argument starts with a '-'.  If so, the next argument on the command line
        # is not a value to accompany this argument, but is a new argument.  This is either because
        # the current argument is a flag or the argument is the name of a task within the pipeline.
        # If the argument is the name of a task in the workflow, the next entry on the command line
        # should be the value for this argument.
        if nextArgument.startswith('-'):

          # Check if the argument is the name of a task.
          task = ''
          if argument.startswith('-'): task = argument[1:]
          if argument.startswith('--'): task = argument[2:]

          if task in workflow:
            self.argumentList.append((argument, nextArgument))
            skip = True
          elif argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentList.append((argument, ''))
        else:
          if argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentList.append((argument, nextArgument))
          skip = True

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, gknoHelp, isPipeline, pipelineName, admin):
    er = errors()

    # Check if '--help' or '-h' were included in the command line.  If so, determine what help
    # was requested.  Pipeilne, tool, admin or general help.
    helpSet    = False
    verboseSet = False
    for argument in sys.argv[1:]:
      if argument == '--help' or argument == '-h': helpSet = True
      if argument == '--verbose' or argument == '-vb': verboseSet = True

    if helpSet:

      # If '--help' is the only argument on the command line, there are only two unique arguments:
      # the path and '--help'.  This case calls for general help.
      if len(sys.argv) == 2:
        gknoHelp.generalHelp  = True
        gknoHelp.printHelp    = True
      else:

        # If a pipeline is being run, check if help is required on general pipelines, or on a specific
        # pipeline.
        if isPipeline:
          if pipelineName == '--help' or pipelineName == '-h':
            gknoHelp.pipelineHelp = True
            gknoHelp.printHelp    = True
          else:
            gknoHelp.specificPipelineHelp = True
            gknoHelp.printHelp            = True
  
        # Help with admin.
        elif admin.isRequested:
          gknoHelp.adminHelp = True
          gknoHelp.printHelp = True
  
        # If pipeline or admin help wasn't requested, then tool help is required.
        else:
          gknoHelp.toolHelp   = True
          gknoHelp.printHelp  = True

    # Check if the verbose argument was included.
    verbose = True
    if verboseSet:
      value = ''
      for count, argument in enumerate(sys.argv[1:]):
        if argument == '--verbose' or argument == '-vb':
          try: value = sys.argv[count + 2]
          except: value = ''
          break
      if value == 'false' or value == 'False': verbose = False
      elif value == 'true' or value == 'True': admin.isVerbose = True
      else:
        er.incorrectBooleanValue(False, '', 'pipeline', argument, '', '', '', value)
        er.terminate()
      
    return verbose

  # Parse through all of the commands stored in the argumentsList and check that they are all valid.
  # If they are, put them in a new structure that groups all of the arguments with their respective
  # task.  This structure is returned.
  def assignArgumentsToTasks(self, tool, shortForms, isPipeline, pipelineArguments, pipeArguments, pipeShortForms, workflow, verbose):
    er   = errors()
    task = tool if not isPipeline else ''

    # Parse through the list of arguments supplied on the command line and determine which task in
    # the pipeline they belong to.  Modify the argumentList to include the task as well as the
    # argument and value.  This routine does not check that the arguments are valid or correctly
    # formed: those checks are performed in the parseCommandLine routine.
    for argument, value in self.argumentList:
      argumentName = ''
      if argument in pipeArguments or argument in pipeShortForms:
        argumentName = pipeShortForms[argument] if argument in pipeShortForms else argument
        taskLink     = pipeArguments[argumentName]['link to this task']
        argumentLink = pipeArguments[argumentName]['link to this argument'] if 'link to this argument' in pipeArguments[argumentName] else 'pipeline'

        # Do not add 'pipeline' arguments to the new structure.
        if argumentLink != 'pipeline':
          if taskLink not in self.linkedArguments: self.linkedArguments[taskLink] = []
          self.linkedArguments[taskLink].append(('pipeline', argumentName, argumentLink, value))

        # Add pipeline arguments to their own structure.
        else:
          shortForm = pipeArguments[argumentName]['short form argument']
          dataType = pipeArguments[argumentName]['type']
          value = self.checkDataType(task, 'pipeline', argumentName, shortForm, '', '', value, dataType, verbose)
          pipelineArguments[argumentName] = value

      # If a pipeline is being run, the name of a task in the workflow is an allowed command line
      # argument.  If this is the case, there may be multiple arguments supplied for that specific
      # task, so place all of these in the modifiedList.
      elif isPipeline:
        if argument.startswith('-'): task = argument[1:]
        if argument.startswith('--'): task = argument[2:]
        if task in workflow:
          taskArguments = value.split(' ')
          while True:

            # Get the first entry in the list.  Terminate the loop if there is nothing left in the list.
            try: taskArgument = taskArguments.pop(0)
            except: break

            # Get the next value in the list if one exists.
            try: nextTaskArgument = taskArguments[0]
            except: nextTaskArgument = '-'

            if nextTaskArgument.startswith('-'):
              if task not in self.linkedArguments: self.linkedArguments[task] = []
              self.linkedArguments[task].append(('pipeline task', taskArgument, taskArgument, ''))
            else:
              if task not in self.linkedArguments: self.linkedArguments[task] = []
              self.linkedArguments[task].append(('pipeline task', taskArgument, taskArgument, nextTaskArgument))
              taskArguments.pop(0)

        # If gkno is being run in the pipe mode, the allowed options (pipeline argument or pipeline task)
        # have also been covered.  Any other command line arguments are unrecognised.
        else:
          er.unknownArgument(verbose, argument)
          er.terminate()

      # If a single tool is being run, the argument must be for this tool (again, checks on the
      # validity of the argument are checked later).
      elif not isPipeline:
        argumentName = shortForms[task][argument] if argument in shortForms[task] else argument
        if task not in self.linkedArguments: self.linkedArguments[task] = []
        self.linkedArguments[task].append(('tool', argumentName, argumentName, value))

      # If gkno is being run as a tool, the only allowed options (a general pipeline argument such
      # as --verbose, or a tool argument) have been covered.  If gkno is being run in the pipe mode,
      # the allowed options (pipeline argument or pipeline task) have also been covered.  Any other
      # command line arguments are unrecognised.
      else:
        er.unknownArgument(verbose, argument)
        er.terminate()

  # All of the arguments on the command line have been added to the linkedArguments structure.  In
  # this structure, each task in the pipeline has all of the arguments associated with it stored
  # with their given values along with the argument in the form understood by the tool the task points
  # to.  Now parse through all of these and check that the values supplied are valid.
  def parseCommandLine(self, tool, arguments, shortForms, isPipeline, workflow, pipeArguments, pipeShortForms, taskToTool, verbose):
    er = errors()

    # Initialise the self.arguments structure.  This will hold all of the commands ready for building
    # command lines in the final scripts.
    if isPipeline:
      for task in workflow: self.arguments[task] = {}
    else:
      task                 = tool
      taskToTool[task]     = task
      self.arguments[task] = {}

    # Parse through all of the supplied arguments and values, task by task.
    for task in self.linkedArguments:

      # Get the name of the tool that the argument is for.  Note that in a pipeline, the workflow
      # is a list of unique tasks.  Each task is associated with a tool.
      tool = taskToTool[task]

      # Parse through all of the arguments for this task.
      for argumentType, pipeArgument, argument, value in self.linkedArguments[task]:

        # Check that the argument is valid for the tool it is intended.
        if argument not in arguments[tool]:
          er.unknownArgument(verbose, argument)
          er.terminate()

        # Get the expected data type associated with the argument.
        dataType = arguments[tool][argument]['type']

        # Get the short form of the argument.
        pipeShortForm = ''
        shortForm     = ''
        if argumentType == 'pipeline': pipeShortForm = pipeArguments[pipeArgument]['short form argument']
        shortForm = arguments[tool][argument]['short form argument'] if 'short form argument' in arguments[tool][argument] else ''

        # Check that a value was supplied for the argument if it is not a flag.  If there is an
        # error, determine if the argument was defined as a pipeline argument, or as a direct
        # argument for the tool.  The error message needs to reflect the argument inputted by the
        # user.
        if dataType != 'flag' and value == '':
          er.missingArgumentValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType)
          er.terminate()

        # If the argument is a flag and it was supplied with an argument, terminate.
        if dataType == 'flag' and value != '':
          er.flagGivenValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
          er.terminate()

        # If the argument is not a flag, check that the data type given is consistent with expectation.
        if dataType != 'flag':
          value = self.checkDataType(task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType, verbose)

          # Check if this command line argument has already been seen.  Some arguments can have multiple
          # values and so can appear on the command line multiple times (for example the --bam command in
          # freebayes can be set multiple times to allow multiple BAM files to be read in).  If this is
          # allowed, the argument definition should include the 'allow multiple definitions' in its 
          # information.
          if argument in self.arguments[task]:
            if argument in arguments[tool]:
              if 'allow multiple definitions' not in arguments[tool][argument]:
                er.multipleDefinitionsForSameArgument(verbose, task, argument, shortForm)
                er.terminate()
              else: self.arguments[task][argument].append(value)
            else: exit('haven\'t handled yet, command line: 312')
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append(value)

        # If the argument is a flag, mark this flag as set.
        else:
          if argument in self.arguments[task]:
            er.multipleDefinitionsForFlag(verbose, task, argument, shortForm)
            er.terminate()
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append('set')

  # Check that the argument has the correct data type.
  def checkDataType(self, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType, verbose):
    er = errors()

    # If the argument expects a Boolean, check that the given value is either 'true', 'True', 'false' or
    # 'False'.
    if dataType == 'bool':
  
      # Ensure that a valid argument has been provided.
      if (value == 'true') or (value == 'True'): value = True
      elif (value == 'false') or (value == 'False'): value = False
      else:
        er.incorrectBooleanValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
        er.terminate()
  
    # If the argument demands a string, no checks are required.
    elif dataType == 'string': pass

    # If the argument demands an integer, check that the supplied value is an integer.
    elif (dataType == 'integer'):
      try: value = int(value)
      except: er.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if er.error: er.terminate()

    # If the argument demands a floating point...
    elif dataType == 'float':
      try: value = float(value)
      except: er.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if er.error: er.terminate()

    return value
























  # Parse the command line in tool mode.  Here all of the arguments are associated
  # with the specified tool or the pipeline.  Check to see that there are no
  # conflicts between the tool and pipeline arguments and update the tl.toolArguments
  # data structure with given values.
  def parseToolCommandLine(self, gknoHelp, io, tl, pl, commandLine, task, tool, verbose):
    er           = errors()
    modifiedTool = ''
    verbose      = True if verbose and (tl.toolArguments['pipeline']['--verbose']) else False
    newLine      = True if verbose else False
    if verbose:
      print('Parsing the command line...', end = '', file = sys.stdout)
      sys.stdout.flush()

    # Parse the command line.
    while(len(commandLine) != 0):
      argument           = commandLine.pop(0)
      isPipelineArgument = False
      isToolArgument     = False

#      # Check if the argument is a pipeline argument (long or short form).
#      if argument in pl.information['arguments']:
#        isPipelineArgument = True
#      else:
#        for pipelineArgument in pl.information['arguments']:
#          if 'short form argument' in pl.information['arguments'][pipelineArgument]:
#            shortFormArgument = pl.information['arguments'][pipelineArgument]['short form argument']
#            if argument == shortFormArgument:
#              isPipelineArgument = True
#              argument           = pipelineArgument

      # Check if the argument is a tool argument (long or short form).
#      if argument in tl.toolArguments[task]:
#        isToolArgument = True
#      else:
#        for toolArgument in tl.toolArguments[task]:
#          if 'short form argument' in tl.toolInfo[tool]['arguments'][toolArgument]:
#            shortFormArgument = tl.toolInfo[tool]['arguments'][toolArgument]['short form argument']
#          if argument == shortFormArgument:
#            isToolArgument = True
#            argument       = toolArgument

      # Check that there is no conflict between the tool and the pipeline arguments.  If
      # a tool argument is the same as a pipeline argument, gkno cannot distinguish between
      # them and will fail.
#      if isToolArgument: modifiedTool = task
#      if isPipelineArgument: modifiedTool = 'pipeline'
#      if isToolArgument and isPipelineArgument:
#        print("FAIL")
#        exit(1)

      # If the argument is neither a tool argument or a pipeline argument, then fail with
      # the tool usage information along with the additional message explaining which
      # argument is unknown.
#      if not isToolArgument and not isPipelineArgument:
#        print(file = sys.stdout)
#        gknoHelp.toolUsage(tl, tool)
#        er.unknownToolArgument("\n", modifiedTool, argument)
#        exit(1)

      # If the next argument does not begin with a '-', assume that it is the value associated
      # with the current argument.
#      isLastArgument = True
#      try:
#        nextArgument   = commandLine[0]
#        isLastArgument = False
#      except: nextArgument = ''

      # Get the expected data type for this command line argument.
#      if not isPipelineArgument:
#        dataType = tl.toolInfo[tool]['arguments'][argument]['type'] if 'type' in tl.toolInfo[tool]['arguments'][argument] else ''
#      else:
#        dataType = pl.information['arguments'][argument]['type'] if 'type' in pl.information['arguments'][argument] else ''

      # If the next argument begins with a '-', e.g. it is the next argument, or this is the
      # last argument on the command line and the expected data type is not 'flag', then data
      # is missing and gkno needs to terminate with an error.
      #if (dataType != 'flag') and (nextArgument.startswith('-') or isLastArgument):
      #  er.expectedValueForArgument(newLine, task, argument, dataType, '')
      #  er.terminate()

      if not nextArgument.startswith('-') and not isLastArgument:

        # If the data type for this argument is 'flag', then there is an error since a value
        # was given.
        #if dataType == 'flag':
        #  er.expectedValueForArgument(newLine, modifiedTool, argument, dataType, nextArgument)
        #  er.terminate()

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
          if dataType == 'bool':
            if nextArgument == 'True': tl.toolArguments[modifiedTool][argument] = True
            elif nextArgument == 'False': tl.toolArguments[modifiedTool][argument] = False
            else:
              er.expectedValueForArgument(newLine, modifiedTool, argument, dataType, nextArgument)
              er.terminate()
          else: tl.toolArguments[modifiedTool][argument] = nextArgument
        commandLine.pop(0)

      # If the next argument begins with a '-', then this option must be a flag (this
      # will be checked later).  As the flag has been set, set the value in tl.toolArguments
      # to set.
      else:
        tl.toolArguments[modifiedTool][argument] = 'set'

  # Parse the command line in pipeline mode.  Here arguments are either pipeline
  # arguments or the name of a constituent tool.  If the argument is the name of
  # a tool, the following argument needs to be a list of arguments in quotation
  # marks for that tool.
  def parsePipelineCommandLine(self, gknoHelp, io, tl, pl, commandLine):
    toolsWrittenToScreen = False
    writingOnNewLine     = False
    er                   = errors()
    verbose              = True if tl.toolArguments['pipeline']['--verbose'] else False
    newLine              = True if verbose else False

    if verbose:
      print('Parsing the command line...', end = '', file = sys.stdout)
      sys.stdout.flush()
    while(len(commandLine) != 0):
      argument = commandLine.pop(0)
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
            print('     Processing command line arguments for tool \'', task, '\'...', sep = '', end = '', file = sys.stdout)
            sys.stdout.flush()
          toolsWrittenToScreen = True
        try: nextArgument = commandLine[0]
        except: 
          er.commandLineToolError("\n\t\t", pl.pipelineName, task)
          er.error = True
        if er.error: er.terminate()

        # Send the command line to the parseToolCommandLine routine to set up the
        # individual tool options.
        toolCommandLine = nextArgument.split()
        tool            = pl.information['tools'][task]
        self.parseToolCommandLine(gknoHelp, io, tl, pl, toolCommandLine, task, tool, False)
        commandLine.pop(0)
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
        try: nextArgument = commandLine[0]
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

          commandLine.pop(0)

        # If the next argument begins with a '-', then this option must be a flag (this
        # will be checked later).  As the flag has been set, set the value in tl.toolArguments
        # to set.
        elif nextArgument.startswith('-') and (dataType == 'flag'): tl.toolArguments[linkToTask][argument] = 'set'

        # If this is the last argument and the argument is not a flag then there is an
        # error.  A value must be set.
        elif (dataType != 'flag') and (isLastArgument or (nextArgument.startswith('-'))):
          er.expectedValueForArgument(newLine, linkToTask, argument, dataType, nextArgument)
          er.terminate()

    if verbose:
      if not toolsWrittenToScreen: print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

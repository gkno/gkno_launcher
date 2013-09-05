#!/usr/bin/python

from __future__ import print_function
import sys

import gknoErrors
from gknoErrors import *

import files
from files import *

import nodeAttributes
from nodeAttributes import *

import pipelineAttributes
from pipelineAttributes import *

class commandLine:

  # Constructor.
  def __init__(self):
    self.arguments          = {}
    self.argumentDictionary = {}
    self.argumentList       = []
    self.errors             = gknoErrors()
    self.linkedArguments    = {}
    self.nodeMethods        = nodeClass()
    self.uniqueArguments    = {}

  # Check if a mode has been defined.  The mode is either 'pipe', 'run-test' or
  # a tool name.  If nothing is set, then no mode is chosen and the general help
  # message will be displayed.
  def isModeSet(self):
    isSet = True
    try:
      argument = sys.argv[1]

      # If help is requested, a mode isn't set.
      if argument == '-h' or argument == '--help': isSet = False

    except: isSet = False

    return isSet

  # Check the first entry on the command line is valid.
  def isPipelineMode(self):
    isPipeline   = False
    hasName      = False
    pipelineName = ''

    # If a pipeline has been selected set the mode to pipe and get the name of
    # the pipeline.
    if sys.argv[1] == 'pipe':
      isPipeline   = True
      hasName      = True
      try: pipelineName = sys.argv[2]
      except: hasName = False

    # If the pipeline being run is run-test, the 'pipe' command is not required.
    elif sys.argv[1] == 'run-test':
      isPipeline   = True
      hasName      = True
      pipelineName = 'run-test'

    return isPipeline, hasName, pipelineName

  # If an admin operation has been requested, check which admin mode is required.
  def isAdminMode(self, adminModes):
    isAdmin = False
    if sys.argv[1] in adminModes: isAdmin = True

    return isAdmin

  # Parse through the command line and put all of the arguments into a list.
  def getCommandLineArguments(self, graph, pipe, tool, isPipeline, verbose):
    count = 1
    while True:
      try: argument = sys.argv[count]
      except: break

      # Check the next argument on the command line.  If it does not begin with a '-', then this
      # is assumed to be a value that goes with the current arguments.  Add the pair to the list
      # of arguments as a tuple.
      try: nextArgument = sys.argv[count + 1]
      except: nextArgument = '-'

      # If arguments for a task within the pipeline are being set on the command line, all of the
      # task specific arguments must be contained within square brackets.  If the nextArgument is
      # identified as beginning with a square bracket, find the end of the task specific commands.
      if nextArgument.startswith('['):

        # First check if nextArgument ends with a ']'.  If there is only a single command in the
        # square brackets, the command is a flag and no spaces are included, this woule be the case.
        if nextArgument.endswith(']'):
          nextArgument = nextArgument[1:len(nextArgument) - 1]

        else:
          taskArgumentCounter = 2
          while True:
            try: buildTaskArguments = sys.argv[count + taskArgumentCounter]
            except: self.errors.hasError = True
  
            # If the square brackets aren't closed, terminate.
            if self.errors.hasError:
              self.errors.unterminatedTaskSpecificOptions(verbose, argument)
              self.errors.terminate()
  
            nextArgument += ' ' + buildTaskArguments
            if not buildTaskArguments.endswith(']'): taskArgumentCounter += 1
            else:
             count += taskArgumentCounter - 1
  
             # Strip off the square brackets.
             nextArgument = nextArgument[1:len(nextArgument) - 1]
             break

      # The command line will include an instruction on whether to run a pipe or the name of the
      # tool.  Ignore this argument.
      if argument != tool and argument != 'pipe' and argument != 'run-test':
        for node in graph.nodes(data = False):
          if self.nodeMethods.getGraphNodeAttribute(graph, node, 'nodeType') != 'task':
            if self.nodeMethods.getGraphNodeAttribute(graph, node, 'isPipelineArgument'):
              if argument == self.nodeMethods.getGraphNodeAttribute(graph, node, 'shortForm'):
                argument = self.nodeMethods.getGraphNodeAttribute(graph, node, 'argument')
                break

        if argument not in self.argumentDictionary: self.argumentDictionary[argument] = []
        # FIXME DELETE REFERENCE TO uniqueArguments.
        #if argument not in self.uniqueArguments: self.uniqueArguments[argument] = 1
        #else: self.uniqueArguments[argument] += 1

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

        isTask = False
        if task in graph.nodes(data = False):

          # The task is a node in the pipeline, but check that the node is a task node.
          if self.nodeMethods.getGraphNodeAttribute(graph, task, 'nodeType') == 'task':

            # FIXME DELETE REFERENCE TO argumentList.
            #self.argumentList.append((argument, nextArgument))
            self.argumentDictionary[argument].append(nextArgument)
            count += 1
            isTask = True

        if not isTask:
          # FIXME DELETE REFERENCE TO argumentList.
          #if argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentList.append((argument, ''))
          if argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentDictionary[argument].append('')

      else:
        # FIXME DELETE REFERENCE TO argumentList.
        #if argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentList.append((argument, nextArgument))
        if argument != tool and argument != 'pipe' and argument != 'run-test': self.argumentDictionary[argument].append(nextArgument)
        count += 1
      count += 1

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, gknoHelp, isPipeline, pipelineName, admin):

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
        self.errors.incorrectBooleanValue(False, '', 'pipeline', argument, '', '', '', value)
        self.errors.terminate()
      
    return verbose

  # Attach the values supplied on the command line to the nodes.
  def attachPipelineArgumentsToNodes(self, graph, pipe, toolData):
    for argument in self.argumentDictionary:
      node = self.nodeMethods.getNodeForPipelineArgument(graph, argument)
      if node == None:                     
        taskArgument = argument            
        if taskArgument.startswith('--'): taskArgument = argument[2:len(argument)]
        if taskArgument.startswith('-'): taskArgument = argument[1:len(argument)]
        if taskArgument in graph.nodes(data = False): node = taskArgument

      # If the command line argument does not correspond to a node, fail.
      if node == None:
        print('unknown command:', argument)
      else:

        # TODO Deal with multiple runs and parallel execution loops.
        hasMultipleRuns      = False
        hasParallelExecution = False
        if hasMultipleRuns or hasParallelExecution:
          print('Not yet handled multiple runs or parallel execution.')

        # There is only a single set of data for the pipeline, so only a single set of values
        # is required.
        else:

          # Handle command line arguments that correspond to a data node first.  Deal with arguments
          # pointing to a task node afterwards.
          if not self.nodeMethods.getGraphNodeAttribute(graph, node, 'nodeType') == 'task':
            self.nodeMethods.setGraphNodeAttribute(graph, node, 'numberOfDataSets', 1)
            self.nodeMethods.setGraphNodeAttribute(graph, node, 'values', ('1', self.argumentDictionary[argument]))

          # Now deal with arguments pointing to task nodes.
          else:

            # Join together all of the arguments for this task into a string.
            argumentString = self.argumentDictionary[argument].pop(0)
            for argumentList in self.argumentDictionary[argument]: argumentString += ' ' + argumentList
            taskArguments = argumentString.split(' ')
            while True:
    
              # Get the first entry in the list.  Terminate the loop if there is nothing left in the list.
              try: taskArgument = taskArguments.pop(0)
              except: break
    
              # Get the next value in the list if one exists.
              try: nextTaskArgument = taskArguments[0]
              except: nextTaskArgument = '-'

              # Ensure that we are using the long form argument.
              task           = node
              associatedTool = self.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
              longForm       = toolData.getLongFormArgument(associatedTool, taskArgument)
    
              # If the argument is a flag, the next argument will start with a '-'.
              if nextTaskArgument.startswith('-'):

                # Determine if an edge exists for this argument.  If so, get the node associated with the
                # data for this edge.  If not, create the node.
                sourceNode = self.nodeMethods.getNodeForTaskArgument(graph, node, longForm)
                if sourceNode == None:
                  sourceNode = 'NODE' + str(pipe.nodeIDInteger)
                  pipe.nodeIDInteger += 1
                  graph.add_node(sourceNode, attributes = toolData.attributes[associatedTool].arguments[longForm])
              else:

                #if task not in self.linkedArguments: self.linkedArguments[task] = []
                #self.linkedArguments[task].append(('pipeline task', taskArgument, taskArgument, nextTaskArgument))
                sourceNode = self.nodeMethods.getNodeForTaskArgument(graph, node, longForm)

                # If there is no edge for this argument, there is no node containing the data.  Generate
                # a new node, populate it with the supplied value and connect the node to the task.
                if sourceNode == None:
                  sourceNode = 'NODE' + str(pipe.nodeIDInteger)
                  pipe.nodeIDInteger += 1
                  graph.add_node(sourceNode, attributes = toolData.attributes[associatedTool].arguments[longForm])
                  
                taskArguments.pop(0)

              # Add an edge from the source node to the task.
              edge          = edgeAttributes()
              edge.argument = longForm
              graph.add_edge(sourceNode, task, attributes = edge)

  # Parse through all of the commands stored in the argumentList and check that they are all valid.
  # If they are, put them in a new structure that groups all of the arguments with their respective
  # task.  This structure is returned.
  def assignArgumentsToTasks(self):#, tool, shortForms, isPipeline, pipelineArguments, pipeArguments, pipeShortForms, workflow, verbose):
    task = tool if not isPipeline else ''

    # Parse through the list of arguments supplied on the command line and determine which task in
    # the pipeline they belong to.  Modify the argumentList to include the task as well as the
    # argument and value.  This routine does not check that the arguments are valid or correctly
    # formed: those checks are performed in the parseCommandLine routine.
    for argument, value in self.argumentList:
      argumentName = ''
      print(argument)
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
          dataType  = pipeArguments[argumentName]['type']
          value     = self.checkDataType(task, 'pipeline', argumentName, shortForm, '', '', value, dataType, verbose)
          if dataType == 'flag': pipelineArguments[argumentName] = 'set'
          else: pipelineArguments[argumentName] = value

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
          self.errors.unknownArgument(verbose, argument)
          self.errors.terminate()

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
        self.errors.unknownArgument(verbose, argument)
        self.errors.terminate()

  # All of the arguments on the command line have been added to the linkedArguments structure.  In
  # this structure, each task in the pipeline has all of the arguments associated with it stored
  # with their given values along with the argument in the form understood by the tool the task points
  # to.  Now parse through all of these and check that the values supplied are valid.
  def parseCommandLine(self, tool, arguments, shortForms, isPipeline, workflow, pipeArguments, pipeShortForms, taskToTool, verbose):

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
          self.errors.unknownArgument(verbose, argument)
          self.errors.terminate()

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
        # usself.errors.
        if dataType != 'flag' and value == '':
          self.errors.missingArgumentValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType)
          self.errors.terminate()

        # If the argument is a flag and it was supplied with an argument, terminate.
        if dataType == 'flag' and value != '':
          self.errors.flagGivenValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
          self.errors.terminate()

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
                self.errors.multipleDefinitionsForSameArgument(verbose, task, argument, shortForm)
                self.errors.terminate()
              else: self.arguments[task][argument].append(value)
            else: exit('haven\'t handled yet, command line: 312')
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append(value)

        # If the argument is a flag, mark this flag as set.
        else:
          if argument in self.arguments[task]:
            self.errors.multipleDefinitionsForFlag(verbose, task, argument, shortForm)
            self.errors.terminate()
          else:
            self.arguments[task][argument] = []
            self.arguments[task][argument].append('set')

  # Check that the argument has the correct data type.
  def checkDataType(self, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType, verbose):

    # If the argument expects a Boolean, check that the given value is either 'true', 'True', 'false' or
    # 'False'.
    if dataType == 'bool':
  
      # Ensure that a valid argument has been provided.
      if (value == 'true') or (value == 'True'): value = True
      elif (value == 'false') or (value == 'False'): value = False
      else:
        self.errors.incorrectBooleanValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
        self.errors.terminate()
  
    # If the argument demands a string, check that a value is provided.
    elif dataType == 'string':
      if value == '':
        self.errors.missingArgumentValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, dataType)
        self.errors.terminate()

    # If the argument demands an integer, check that the supplied value is an integself.errors.
    elif (dataType == 'integer'):
      try: value = int(value)
      except: self.errors.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if self.errors.hasError: self.errors.terminate()

    # If the argument demands a floating point...
    elif dataType == 'float':
      try: value = float(value)
      except: self.errors.incorrectDataType(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value, dataType)
      if self.errors.hasError: self.errors.terminate()

    # If a value was provided to a flag...
    elif dataType == 'flag':
      if value != '':
        self.errors.flagGivenValue(verbose, task, argumentType, pipeArgument, pipeShortForm, argument, shortForm, value)
        self.errors.terminate()

    return value

#!/bin/bash/python

from __future__ import print_function

import commandLineErrors
from commandLineErrors import *
import graph as gr

import json
import os
import sys

# Define a class for handling the command line and operations around it.
class commandLine:
  def __init__(self):

    # Define errors.
    self.errors = commandLineErrors()

    # Store all of the arguments with their values. These will be broken up into arguments that
    # are for individual tasks within the main pipeline, gkno specific arguments and pipeline
    # arguments.
    self.arguments         = {}
    self.gknoArguments     = {}
    self.pipelineArguments = {}

    # For tasks supplied on the command line, store the task and the list of arguments. Also, store
    # the broken out arguments (e.g. after the string associated with the task is parsed).
    self.tasksAsArguments = {}
    self.taskArguments    = {}

    # Store commands. These could be instructions on the mode of usage etc.
    self.commands = []

    # Parse the command line and store all the arguments with their values.
    argument        = None
    isTaskArguments = False
    for entry in sys.argv[1:]:
      isArgument = entry.startswith('-')

      # If this is a continuation of arguments for a specific task, append the arguments to
      # the task arguments. If the entry terminates with ']', the task arguments are complete.
      if isTaskArguments:
        if entry.endswith(']'):
          taskArguments += ' ' + entry[:-1]
          isTaskArguments = False
          self.arguments[argument].append(taskArguments)

          # Reset the argument and the taskArguments now the task arguments have been handled.
          taskArguments = ''
          argument      = ''
        else: taskArguments += ' ' + entry

      # If the entry starts with a '['. this is the start of a set of arguments to be applied to
      # a task within in the pipeline. Find all the commands in the square brackets and associate
      # with the task argument.
      elif argument and entry.startswith('['):
        isTaskArguments = True
        taskArguments   = ''
        taskArguments  += entry[1:]

      # Only process the entry if not part of task arguments contained in square brackets.
      else:

        # If this and the previous entry were not arguments, this should be a command and
        # is stored.
        if not argument and not isArgument: self.commands.append(entry)
  
        # If the previous command line entry was an argument, check if this entry is an argument or
        # not. If not, store this as the value for the previous argument.
        elif argument and not isArgument:
          self.arguments[argument].append(entry)
          argument = None
  
        # If the previous entry was an argument and this is an argument, then the previous entry is
        # assumed to be a flag. Append None to the list of arguments for the flag and then create
        # the list in self.arguments for the current argument.
        elif argument and isArgument:
          self.arguments[argument].append(None)
          argument                 = entry
          if argument not in self.arguments: self.arguments[argument] = []
  
        # If this entry is an argument and the previous entry was not, store this entry as an argument.
        elif not argument and isArgument:
          argument                 = entry
          if argument not in self.arguments: self.arguments[argument] = []

    # If the end of the command line is reached and argument is still populated, this is assumed
    # to be a flag and should be added.
    if argument and not self.arguments[argument]: self.arguments[argument] = [None]

    # If the mode of operation is to provide information on help categories, store the help category.
    self.category = None

  # Determine if gkno is being run in admin mode.
  def isAdmin(self, modes):
    try:
      if self.commands[0] in modes: return True, self.commands[0]
    except: return False, None
    return False, None

  # Determine the mode in which gkno is being run. This is either in 'admin' mode for general gkno
  # admin (resource management, building, updating etc.), 'help' for different categories of help
  # or 'run' for running tools or pipelines.
  def determineMode(self, isAdmin, gkno):
    if isAdmin: return 'admin'

    # Check if json files for the web page were requested.
    if gkno.options['GKNO-WEB'].longFormArgument in self.arguments or gkno.options['GKNO-WEB'].shortFormArgument in self.arguments: return 'web'

    # Check if help for gkno specific arguments was requested.
    if gkno.options['GKNO-ARGUMENTS'].longFormArgument in self.arguments or gkno.options['GKNO-ARGUMENTS'].shortFormArgument in self.arguments:
      return 'gkno help'

    # If help is requested, return the mode 'help'.
    if gkno.options['GKNO-HELP'].longFormArgument in self.arguments or gkno.options['GKNO-HELP'].shortFormArgument in self.arguments: return 'help'

    # Check if help categories were requested.
    if gkno.options['GKNO-CATEGORIES'].longFormArgument in self.arguments or gkno.options['GKNO-CATEGORIES'].shortFormArgument in self.arguments:
      if gkno.options['GKNO-CATEGORIES'].longFormArgument in self.arguments:
        self.category = self.arguments[gkno.options['GKNO-CATEGORIES'].longFormArgument][0]
      elif gkno.options['GKNO-CATEGORIES'].shortFormArgument in self.arguments:
        self.category = self.arguments[gkno.options['GKNO-CATEGORIES'].shortFormArgument][0]

      return 'categories'

    # Check if a list of all pipeline was requested.
    if gkno.options['GKNO-ALL-PIPELINES'].longFormArgument in self.arguments: return 'list-all'
    if gkno.options['GKNO-ALL-PIPELINES'].shortFormArgument in self.arguments: return 'list-all'

    # If no information is provided (e.g. no admin, tool or pipeline), return 'help' as the mode.
    if len(self.commands) == 0 and len(self.arguments) == 0: return 'help'

    # If none of the above, return 'run',
    return 'run'

  # Determine the path to the configuration files, if set.
  def getConfigurationFilePath(self, options):
    longFormArgument  = options['GKNO-CONFIGURATION-DIRECTORY'].longFormArgument
    shortFormArgument = options['GKNO-CONFIGURATION-DIRECTORY'].shortFormArgument

    # If the path is defined, get the path.
    path = None
    if longFormArgument in self.arguments: path = self.arguments[longFormArgument][0]
    elif shortFormArgument in self.arguments: path = self.arguments[shortFormArgument][0]

    # If the path is defined, check that the path exists.
    # TODO ERROR
    if path and not os.path.isdir(path): print('commandLine.getConfigurationFilePath - PATH DOESN\'T EXIST'); exit(1)

    # Remove trailing '/'.
    if path and path.endswith('/'): path = path.rstrip('/')

    # Return the path.
    return path

  # Determine the name of the pipeline being run (tools are considered pipelines of a single task).
  def determinePipeline(self):

    # If no pipeline name was supplied return None. The mode will be help, so a general help message
    # will be provided to the user.
    if not self.commands: return None

    # If there are multiple commands from the pipeline, the command line is invalid. If not in admin
    # mode, the command line can only include a single entry that is not an argument or accompanying
    # value.
    # TODO ERROR
    if len(self.commands) != 1: self.errors.invalidCommandLine()

    # Return the pipeline name.
    return self.commands[0]

  # Process the command line arguments.
  def processArguments(self, superpipeline, gknoLongForms, gknoShortForms):

    # Get the name of the top level pipeline.
    pipeline = superpipeline.pipeline

    # Loop over all of the supplied command line arguments, ensure that they are in their long form
    # versions and consolidate. Check that all of the arguments are valid for the pipeline being run
    # or are gkno specific arguments.
    for argument in self.arguments:
      values                     = self.arguments[argument]
      pipelineShortFormArguments = superpipeline.pipelineConfigurationData[pipeline].shortFormArguments

      # First check if the argument is the name of a task in the superpipeline.
      if argument.strip('-') in superpipeline.tasks:
        if argument.strip('-') in self.tasksAsArguments: 
          for value in values: self.tasksAsArguments[argument.strip('-')].append(value)
        else: self.tasksAsArguments[argument.strip('-')] = values

      # If this is a long form argument, check to see if it is a gkno specific argument or a valid pipeline
      # argument.
      elif argument in gknoLongForms:
        if argument in self.gknoArguments:
          for value in values: self.gknoArguments[argument].append(value)
        else: self.gknoArguments[argument] = values

      # Check if this is a valid gkno short form argument.
      elif argument in gknoShortForms:
        if gknoShortForms[argument] in self.gknoArguments:
          for value in values: self.gknoArguments[gknoShortForms[argument]].append(value)
        else: self.gknoArguments[gknoShortForms[argument]] = values

      # Check if this is a valid long form pipeline argument.
      elif argument in superpipeline.pipelineConfigurationData[pipeline].longFormArguments:
        if argument in self.pipelineArguments:
          for value in values: self.pipelineArguments[argument].append(value)
        else: self.pipelineArguments[argument] = values

      # Check if this is a valid short form pipeline argument.
      elif argument in superpipeline.pipelineConfigurationData[pipeline].shortFormArguments:
        if pipelineShortFormArguments[argument] in self.pipelineArguments:
          for value in values: self.pipelineArguments[pipelineShortFormArguments[argument]].append(value)
        else: self.pipelineArguments[pipelineShortFormArguments[argument]] = values

      # If the argument is invalid.
      else:  self.errors.invalidArgument(argument)

  # Determine the name (if any) of the requested parameter set.
  def getParameterSetName(self, arguments, gkno):

    # Loop over the gkno specific arguments looking for the --parameter-set argument,
    for argument in arguments:
      if argument == gkno.options['GKNO-PARAMETER-SET'].longFormArgument:

        # Only one parameter set can be defined.
        if len(arguments[argument]) != 1: self.errors.multipleParameterSets()

        # Return the name of the parameter set.
        return arguments[argument][0]

    # If no parameter set was defined, return None.
    return None

  # For all tasks inputted on the command line, extract all the arguments supplied to the tasks.
  def parseTasksAsArguments(self, superpipeline):

    # Parse tasksAsNodes. Each entry is a task in the pipeline and has associated with it a list of
    # arguments to apply to that task. Parse all of these arguments and identify the graph node that
    # they point to. If there is no associated node, add the argument to a list of nodes that require
    # creating.
    for task in self.tasksAsArguments:
      arguments = {}

      # Get the tool associated with this task.
      tool = superpipeline.tasks[task]

      # Loop over all arguments supplied to this task (it is allowed that the same task is supplied
      # on the command line multiple times.
      for string in self.tasksAsArguments[task]:

        # Break the string associated with the task into a list.
        argumentList = string.split(' ')

        # Parse all the commands supplied for this task.
        argument = None
        for counter, entry in enumerate(argumentList):
          if entry.startswith('-'):
  
            # If this entry starts with a '-' and isArgument is true, then the previous entry also started
            # with a '-'. This implies that the previous entry was a flag argument.
            if argument:
              arguments[argument] = ['set']

              # Check that the argument is a valid argument for this tool and convert to the long form
              # version if necessary.
              argument = superpipeline.toolConfigurationData[tool].getLongFormArgument(entry)
              #TODO ERROR
              if argument not in superpipeline.toolConfigurationData[tool].arguments.keys():
                print('ERROR - parseTasksAsArguments - 1', tool, entry); exit(0)
              arguments[argument] = []
  
            # If isArgument is false, then this is a new argument (either it is the first argument in the
            # list, or the previous entry was a value associated with a different argument).
            else:

              # Check that the argument is a valid argument for this tool and convert to the long form
              # version if necessary.
              #TODO ERROR
              argument = superpipeline.toolConfigurationData[tool].getLongFormArgument(entry)
              if argument not in superpipeline.toolConfigurationData[tool].arguments.keys():
                print('ERROR - parseTasksAsArguments - 2', tool, entry); exit(0)
              if argument not in arguments: arguments[argument] = []
  
          # If this entry does not begin with a dash and there is no defined argument, then the previous
          # entry also did not start with a '-' and so there is a problem with the supplied arguments.
          elif not argument: print('ERROR - command.associateArgumentsWithGraphNodes - 1'); exit(0)
  
          # If this entry does not begin with a '-'. but the argument is set, this is a value for the argument,
          # so associate the value with the argument.
          elif argument:
            arguments[argument].append(entry)
            argument = None

        # If the previous list ended on a flag, the value will not have been set. Set it here.
        if argument: arguments[argument] = ['set']

      # Store the list of arguments for each task.
      self.taskArguments[task] = arguments

  # Associate the command line arguments with the graph nodes.
  def associateArgumentsWithGraphNodes(self, graph, superpipeline):
    associatedNodes = []

    # Loop over all the arguments supplied to individual tasks.
    for taskAddress in self.taskArguments:
      for argument in self.taskArguments[taskAddress]:
        values = self.taskArguments[taskAddress][argument]

        # Get the tool associated with this task.
        tool     = superpipeline.tasks[taskAddress]
        toolData = superpipeline.toolConfigurationData[tool]

        # Search the successor and predecessor nodes for this task for the argument supplied.
        foundArgument    = False
        associatedNodeID = None
        for nodeID in gr.pipelineGraph.CM_getInputNodes(graph, taskAddress):
          longFormArgument = gr.pipelineGraph.CM_getArgumentAttribute(graph, nodeID, taskAddress, 'longFormArgument')
          if longFormArgument == argument:
            foundArgument    = True
            associatedNodeID = nodeID
            break

        # Only check the output nodes if the argument has not already been associated with an input node.
        if not foundArgument:
          for nodeID in gr.pipelineGraph.CM_getOutputNodes(graph, taskAddress):
            longFormArgument = gr.pipelineGraph.CM_getArgumentAttribute(graph.graph, nodeID, taskAddress, 'longFormArgument')
            if longFormArgument == argument:
              foundArgument    = True
              associatedNodeID = nodeID
              break

        # Add the node to the list.
        if associatedNodeID: associatedNodes.append((taskAddress, associatedNodeID, tool, argument, values, False))
        else: associatedNodes.append((taskAddress, str(taskAddress + '.' + argument), tool, argument, values, True))

    # Return the list with information on the nodes to create.
    return associatedNodes

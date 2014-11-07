#!/bin/bash/python

from __future__ import print_function

import commandLineErrors
from commandLineErrors import *

import json
import os
import sys

# Define a class for handling the command line and operations around it.
class commandLine:
  def __init__(self):

    # Define errors.
    self.errors = commandLineErrors()

    # Store all of the arguments with their values.
    self.arguments = {}

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

          # Reses the argument and the taskArguments now the task arguments have been handled.
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

  # Determine if gkno is being run in admin mode.
  def isAdmin(self, modes):
    try:
      if self.commands[0] in modes: return True, self.commands[0]
    except: return False, None
    return False, None

  # Determine the mode in which gkno is being run. This is either in 'admin' mode for general gkno
  # admin (resource management, building, updating etc.), 'help' for different categories of help
  # or 'run' for running tools or pipelines.
  def determineMode(self, isAdmin):
    if isAdmin: return 'admin'

    # If help is requested, return the mode 'help'.
    if '-h' in self.arguments or '--help' in self.arguments: return 'help'

    # If no information is provided (e.g. no admin, tool or pipeline), return 'help' as the mode.
    if len(self.commands) <= 1 and len(self.arguments) == 0: return 'help'

    # If none of the above, return 'run',
    return 'run'

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

#!/usr/bin/python

from __future__ import print_function
import os
import sys

class helpClass:
  def __init__(self):
    self.printHelp            = False
    self.generalHelp          = False
    self.pipelineHelp         = False
    self.specificPipelineHelp = False
    self.toolHelp             = False
    self.adminHelp            = False
    self.unknownPipeline      = False
    self.unknownTool          = False
    self.unknownAdminMode     = False

  # If usage information needs to be printed out, determine the exact level
  # of usage information to provide, write to screen and then terminate.
  def printUsage(self, io, tl, pl, admin, version, date, path):

    # General gkno usage.
    if self.generalHelp:
      self.printHeader(version, date)
      self.usage(io, tl)

    # gkno tool mode usage.
    elif self.toolHelp:
      if self.unknownTool:
        self.printToolModeUsage(tl)
        self.unknownToolMessage(tl.tool)
      else:
        self.printHeader(version, date)
        self.toolUsage(tl, tl.tool)

    # General pipeline help.
    elif self.pipelineHelp:
      self.printHeader(version, date)
      self.pipelineUsage(io, tl, pl, path)
      if self.unknownPipeline: self.unknownPipelineMessage(pl.pipelineName)

    # Specific pipeline help.
    elif self.specificPipelineHelp:
      self.printHeader(version, date)
      self.specificPipelineUsage(tl, pl)

    elif self.adminHelp:
      self.printHeader(version, date)
      self.adminUsage(admin)

    # Terminate.
    exit(0)

  # If the command line contains a help request ('--help' or '-h') and there
  # are further arguments on the command line, print a warning to screen.
  def extraArgumentsWarning(self):
    print('WARNING: Help requested (--help, -h), but additional command line arguments are present.  Check the command line.', file = sys.stdout)
    print(file = sys.stdout)
    sys.stdout.flush()

  # For most of the usage requests, the version number and date are printed out
  # at the start of the message.  Print these here.
  def printHeader(self, version, date):
    print(file = sys.stdout)
    print('===============================', file = sys.stdout)
    print('  Boston College gkno package', file = sys.stdout)
    print(file = sys.stdout)
    print('  version: ', version, sep = '', file = sys.stdout)
    print('  date:    ', date, sep = '', file = sys.stdout)
    print('===============================', file = sys.stdout)
    print(file = sys.stdout)

  # Print usage information.
  def usage(self, io, tl):
    print("\tThe gkno package can be run in two different modes: TOOL mode or PIPE mode.", file = sys.stdout)
    print("\tThe TOOL mode runs a single tool and the PIPE mode runs a predetermined pipeline of tools.", file = sys.stdout)
    print("\tSee below for usage instructions for each mode.", file = sys.stdout)
    print(file = sys.stdout)

    # Print out a list of available tools.
    self.printToolModeUsage(tl)

    # Print out pipeline help.
    self.printPipelineModeUsage(io)

  # Print usage information on the tool mode of operation.
  def printToolModeUsage(self, tl):
    print('=============', file = sys.stdout)
    print('  tool mode', file = sys.stdout)
    print('=============', file = sys.stdout)
    print(file = sys.stdout)
    print("Usage: gkno <tool name> [options]", file = sys.stdout)
    print(file = sys.stdout)
    print("\t<tool name>:", file = sys.stdout)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    length = 0
    for tool in tl.toolInfo.keys():
      if len(tool) > length: length = len(tool)
    length += 5

    sortedKeys = sorted(tl.toolInfo.keys())
    for tool in sortedKeys:

      # Get the tool description.
      description = tl.toolInfo[tool]['description']
      printTool = tool + ":"
      if not tl.hiddenTools[tool]: print("\t\t%-*s%-*s" % (length, printTool, 1, description), file = sys.stdout)
    print(file = sys.stdout)

  # Print usage information on the pipeline mode of operation.
  def printPipelineModeUsage(self, io):
    print('=================', file = sys.stdout)
    print('  pipeline mode', file = sys.stdout)
    print('=================', file = sys.stdout)
    print(file = sys.stdout)
    print("Usage: gkno pipe <pipeline name> [options]", file = sys.stdout)
    print(file = sys.stdout)
    print("\t<pipeline name>:", file = sys.stdout)

    sortedKeys = sorted(io.jsonPipelineFiles.keys())
    for pipeline in sortedKeys:
      pipeline = pipeline[0:(len(pipeline) - 5)]
      print("\t\t", pipeline, sep = '', file = sys.stdout)
    sys.stdout.flush()

  # Print out tool usage.
  def toolUsage(self, tl, tool):
    print('===================', file = sys.stdout)
    print('  gkno tool usage', file = sys.stdout)
    print('===================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno ', tool, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Split the tool inputs into a required and an optional set.
    defaultArguments  = []
    optionalArguments = []
    requiredArguments = []
    for argument in tl.toolInfo[tool]['arguments']:
      required = True if 'required' in tl.toolInfo[tool]['arguments'][argument] else False
      default  = True if 'default' in tl.toolInfo[tool]['arguments'][argument] else False
      if required: required = True if tl.toolInfo[tool]['arguments'][argument]['required'] == 'true' else False
      if required:
        if default: defaultArguments.append(argument)
        else: requiredArguments.append(argument)
      else: optionalArguments.append(argument)

    sDefaultArguments  = sorted(defaultArguments)
    sRequiredArguments = sorted(requiredArguments)
    sOptionalArguments = sorted(optionalArguments)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    length = 0
    sortedKeys = sorted(tl.toolInfo[tool]['arguments'])
    for argument in sortedKeys:
      length = len(argument) if (len(argument) > length) else length
    length += 5

    if len(sRequiredArguments) != 0:
      print("\trequired arguments:", file = sys.stdout)
      for argument in sRequiredArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description']
        print("\t\t%-*s%-*s" % (length, printArgument, 1, description), file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sDefaultArguments) != 0:
      print("\trequired arguments with set defaults:", file = sys.stdout)
      for argument in sDefaultArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description'].split('|')
        dataType      = tl.toolInfo[tool]['arguments'][argument]['type']
        for counter, desc in enumerate(description):
          if counter == 0: print("\t\t%-*s%-*s%-*s" % (length, printArgument, 10, dataType, 1, desc), file = sys.stdout)
          else: print("\t\t%-*s%-*s" % ((length + 10), ' ', 1, desc), file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sOptionalArguments) != 0:
      print("\toptional arguments:", file = sys.stdout)
      for argument in sOptionalArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description'].split('|')
        dataType      = tl.toolInfo[tool]['arguments'][argument]['type']
        for counter, desc in enumerate(description):
          if counter == 0: print("\t\t%-*s%-*s%-*s" % (length, printArgument, 10, dataType, 1, desc), file = sys.stdout)
          else: print("\t\t%-*s%-*s" % ((length + 10), ' ', 1, desc), file = sys.stdout)
        
      print(file = sys.stdout)
      sys.stdout.flush()

  # Print usage information for pipelines:
  def pipelineUsage(self, io, tl, pl, path):
    print('=======================', file = sys.stdout)
    print('  gkno pipeline usage', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('\t<pipeline name>:', file = sys.stdout)

    # Determine the length of the longest pipeline name.
    length = 0
    sortedKeys = sorted(io.jsonPipelineFiles.keys())
    for pipeline in sortedKeys:
      length = len(pipeline) if (len(pipeline) > length) else length

    for pipeline in sortedKeys:

      # For each available pipeline, open the json and get the pipeline description.
      io.jsonPipelineFile = path + '/config_files/pipes/' + pipeline
      io.getPipelineDescription(tl, pl, False)

      pipeline       = pipeline[0:-5] + ':'
      if 'description' in pl.information: description = pl.information['description']
      else: description = 'No description'
      print("\t\t%-*s%-*s" % (length, pipeline, 1, description), file = sys.stdout)
    sys.stdout.flush()

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def specificPipelineUsage(self, tl, pl):
    length = len(pl.pipelineName) + 26
    print('=' * length)
    print('  gkno pipeline usage - ', pl.pipelineName, sep = '', file = sys.stdout)
    print('=' * length)
    print(file = sys.stdout)
    print('Usage: gkno pipe ', pl.pipelineName, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the decription of the pipeline.
    description = pl.information['description'] if 'description' in pl.information else 'No description'
    print('Description:', file = sys.stdout)
    print("\t", description, sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # List the options available at the pipeline level.

    # Loop over all the allowable arguments and determine if there is a short form and
    # the length of the combined '--argument (-a)' text.
    length            = 0
    arguments         = {}
    requiredArguments = {}
    for argument in pl.information['arguments']:
      text        = argument
      description = 'No description'
      if 'short form argument' in pl.information['arguments'][argument]: text += ' (' + pl.information['arguments'][argument]['short form argument'] + ')'
      if 'description' in pl.information['arguments'][argument]: description = pl.information['arguments'][argument]['description']
      text += ':'
      length = len(text) if (len(text) > length) else length
      userEntry = False
      if 'user entry required' in pl.information['arguments'][argument]: 
        if pl.information['arguments'][argument]['user entry required'] == 'true': userEntry = True
      if userEntry: requiredArguments[text] = description
      else: arguments[text] = description
    length += 4

    if len(requiredArguments) != 0:
      print("\tRequired pipeline specific arguments:\t", file = sys.stdout)
      sortedArguments = sorted(requiredArguments.keys())
      for argument in sortedArguments:
        print("\t\t%-*s%-*s" % (length, argument, 1, requiredArguments[argument]), file = sys.stdout)
      print(file = sys.stdout)

    if len(arguments) != 0:
      print("\tOptional pipeline specific arguments:\t", file = sys.stdout)
      sortedArguments = sorted(arguments.keys())
      for argument in sortedArguments:
        print("\t\t%-*s%-*s" % (length, argument, 1, arguments[argument]), file = sys.stdout)
      print(file = sys.stdout)

    # List the names of the tools in the pipeline.  These can appear as command line arguments
    # in order to modify parameters for the specified tool.
    print("\tThe following tools can have parameters modified:", file = sys.stdout)
    length = 0
    for task in pl.information['workflow']:
      length = len(task) if (len(task) > length) else length
    length += 5

    sortedTasks = sorted(pl.information['workflow'])
    for task in sortedTasks:
      tool  = pl.information['tools'][task]
      if not tl.hiddenTools[tool]:
        task += ':'
        print("\t\t--%-*s%-*s parameters" % (length, task, 1, tool), file = sys.stdout)
    sys.stdout.flush()

  # If help for admin operation was requested
  def adminUsage(self, admin):
    pass # FIXME

  # If help for a specific tool was requested, but that tool does not exist,
  # print an error after the usage information.
  def unknownToolMessage(self, tool):
    print(file = sys.stdout)
    print('=======================', file = sys.stdout)
    print('  Additional messages', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('ERROR: Requested tool \'', tool, '\' does not exist.  Check available tools in usage above.', sep = '', file = sys.stdout)
    sys.stdout.flush()

  # If a pipeline was requested, but no configuration file can be found, add
  # this extra error at the end of the usage information.
  def unknownPipelineMessage(self, pipeline):
    print(file = sys.stdout)
    print('=======================', file = sys.stdout)
    print('  Additional messages', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('ERROR: Requested pipeline \'', pipeline, '\' does not exist.  Check available pipelines in usage above.', sep = '', file = sys.stdout)
    sys.stdout.flush()

  def unknownAdminMessage(self, admin):
    pass # FIXME

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
    self.unknownPipeline      = False
    self.unknownTool          = False

  # If usage information needs to be printed out, determine the exact level
  # of usage information to provide, write to screen and then terminate.
  def printUsage(self, io, tl, pl, version, date, path):

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
      self.pipelineUsage(io, pl, path)
      if self.unknownPipeline: self.unknownPipelineMessage(pl.pipelineName)

    # Specific pipeline help.
    elif self.specificPipelineHelp:
      self.printHeader(version, date)
      self.specificPipelineUsage(pl)

    # Terminate.
    exit(0)

  # If the command line contains a help request ('--help' or '-h') and there
  # are further arguments on the command line, print a warning to screen.
  def extraArgumentsWarning(self):
    print('WARNING: Help requested (--help, -h), but additional command line arguments are present.  Check the command line.', file = sys.stderr)
    print(file = sys.stderr)
    sys.stderr.flush()

  # For most of the usage requests, the version number and date are printed out
  # at the start of the message.  Print these here.
  def printHeader(self, version, date):
    print(file = sys.stderr)
    print('===============================', file = sys.stderr)
    print('  Boston College gkno package', file = sys.stderr)
    print(file = sys.stderr)
    print('  version: ', version, sep = '', file = sys.stderr)
    print('  date:    ', date, sep = '', file = sys.stderr)
    print('===============================', file = sys.stderr)
    print(file = sys.stderr)

  # Print usage information.
  def usage(self, io, tl):
    print("\tThe gkno package can be run in two different modes: TOOL mode or PIPE mode.", file = sys.stderr)
    print("\tThe TOOL mode runs a single tool and the PIPE mode runs a predetermined pipeline of tools.", file = sys.stderr)
    print("\tSee below for usage instructions for each mode.", file = sys.stderr)
    print(file = sys.stderr)

    # Print out a list of available tools.
    self.printToolModeUsage(tl)

    # Print out pipeline help.
    self.printPipelineModeUsage(io)

  # Print usage information on the tool mode of operation.
  def printToolModeUsage(self, tl):
    print('=============', file = sys.stderr)
    print('  tool mode', file = sys.stderr)
    print('=============', file = sys.stderr)
    print(file = sys.stderr)
    print("Usage: gkno <tool name> [options]", file = sys.stderr)
    print(file = sys.stderr)
    print("\t<tool name>:", file = sys.stderr)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    length = 0
    for tool in tl.toolInfo.keys():
      if len(tool) > length: length = len(tool)
    length += 5

    for tool in tl.toolInfo.keys():

      # Get the tool description.
      description = tl.toolInfo[tool]['description']
      printTool = tool + ":"
      print("\t\t%-*s%-*s" % (length, printTool, 1, description), file = sys.stderr)
    print(file = sys.stderr)

  # Print usage information on the pipeline mode of operation.
  def printPipelineModeUsage(self, io):
    print('=================', file = sys.stderr)
    print('  pipeline mode', file = sys.stderr)
    print('=================', file = sys.stderr)
    print(file = sys.stderr)
    print("Usage: gkno pipe <pipeline name> [options]", file = sys.stderr)
    print(file = sys.stderr)
    print("\t<pipeline name>:", file = sys.stderr)
    for pipeline in io.jsonPipelineFiles.keys():
      pipeline = pipeline[0:(len(pipeline) - 5)]
      print("\t\t", pipeline, sep = '', file = sys.stderr)
    sys.stderr.flush()

  # Print out tool usage.
  def toolUsage(self, tl, tool):
    print('===================', file = sys.stderr)
    print('  gkno tool usage', file = sys.stderr)
    print('===================', file = sys.stderr)
    print(file = sys.stderr)
    print('Usage: gkno ', tool, ' [options]', sep = '', file = sys.stderr)
    print(file = sys.stderr)
    print("\toptions:", file = sys.stderr)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    length = 0
    for option in tl.toolInfo[tool]['arguments']:
      length = len(option) if (len(option) > length) else length
    length += 5

    for option in tl.toolInfo[tool]['arguments']:
      printOption = option + ':'
      description = tl.toolInfo[tool]['arguments'][option]['description']
      print("\t\t%-*s%-*s" % (length, printOption, 1, description), file = sys.stderr)
    sys.stderr.flush()

  # Print usage information for pipelines:
  def pipelineUsage(self, io, pl, path):
    print('=======================', file = sys.stderr)
    print('  gkno pipeline usage', file = sys.stderr)
    print('=======================', file = sys.stderr)
    print(file = sys.stderr)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stderr)
    print(file = sys.stderr)
    print('\t<pipeline name>:', file = sys.stderr)

    # Determine the length of the longest pipeline name.
    length = 0
    for pipeline in io.jsonPipelineFiles.keys():
      length = len(pipeline) if (len(pipeline) > length) else length

    for pipeline in io.jsonPipelineFiles.keys():

      # For each available pipeline, open the json and get the pipeline description.
      io.jsonPipelineFile = path + '/config_files/pipes/' + pipeline
      io.getPipelineDescription(pl, False)

      pipeline       = pipeline[0:-5] + ':'
      if 'description' in pl.information: description = pl.information['description']
      else: description = 'No description'
      print("\t\t%-*s%-*s" % (length, pipeline, 1, description), file = sys.stderr)
    sys.stderr.flush()

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def specificPipelineUsage(self, pl):
    print('=======================', file = sys.stderr)
    print('  gkno pipeline usage', file = sys.stderr)
    print('=======================', file = sys.stderr)
    print(file = sys.stderr)
    print('Usage: gkno pipe ', pl.pipelineName, ' [options]', sep = '', file = sys.stderr)
    print(file = sys.stderr)

    # List the options available at the pipeline level.
    print("\tPipeline specific options:\t", file = sys.stderr)

    # Loop over all the allowable arguments and determine if there is a short form and
    # the length of the combined '--argument (-a)' text.
    length       = 0
    arguments    = {}
    for argument in pl.information['arguments']:
      text        = argument
      description = 'No description'
      if 'alternative' in pl.information['arguments'][argument]: text += ' (' + pl.information['arguments'][argument]['alternative'] + ')'
      if 'description' in pl.information['arguments'][argument]: description = pl.information['arguments'][argument]['description']
      text += ':'
      length = len(text) if (len(text) > length) else length
      arguments[text] = description
    length += 4

    for argument in arguments.keys():
      print("\t\t%-*s%-*s" % (length, argument, 1, arguments[argument]), file = sys.stderr)
    print(file = sys.stderr)

    # List the names of the tools in the pipeline.  These can appear as command line arguments
    # in order to modify parameters for the specified tool.
    print("\tThe following tools can have parameters modified:", file = sys.stderr)
    length = 0
    for task in pl.information['workflow']:
      length = len(task) if (len(task) > length) else length
    length += 5

    for task in pl.information['workflow']:
      tool      = pl.information['tools'][task]
      task += ':'
      print("\t\t--%-*s%-*s parameters" % (length, task, 1, tool), file = sys.stderr)
    sys.stderr.flush()

  # If help for a specific tool was requested, but that tool does not exist,
  # print an error after the usage information.
  def unknownToolMessage(self, tool):
    print(file = sys.stderr)
    print('=======================', file = sys.stderr)
    print('  Additional messages', file = sys.stderr)
    print('=======================', file = sys.stderr)
    print(file = sys.stderr)
    print('ERROR: Requested tool \'', tool, '\' does not exist.  Check available tools in usage above.', sep = '', file = sys.stderr)
    sys.stderr.flush()

  # If a pipeline was requested, but no configuration file can be found, add
  # this extra error at the end of the usage information.
  def unknownPipelineMessage(self, pipeline):
    print(file = sys.stderr)
    print('=======================', file = sys.stderr)
    print('  Additional messages', file = sys.stderr)
    print('=======================', file = sys.stderr)
    print(file = sys.stderr)
    print('ERROR: Requested pipeline \'', pipeline, '\' does not exist.  Check available pipelines in usage above.', sep = '', file = sys.stderr)
    sys.stderr.flush()

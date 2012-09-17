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

  # If usage information needs to be printed out, determine the exact level
  # of usage information to provide, write to screen and then terminate.
  def printUsage(self, io, tl, pl, admin, version, date, path):

    # General gkno usage.
    if self.generalHelp:
      self.printHeader(version, date)
      self.usage(io, tl, admin, path)

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

    # Admin mode help.
    elif self.adminHelp:
      self.printHeader(version, date)
      self.adminModeUsage(admin)

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
  def usage(self, io, tl, admin, path):
    print('The gkno package can be run in three different modes:', file=sys.stdout)
    print('     ADMIN mode:     lets you manage gkno itself', file = sys.stdout)
    print('     TOOL mode:      runs a single tool', file=sys.stdout)
    print('     PIPE mode:      runs a predetermined pipeline of tools', file=sys.stdout)
    print(file = sys.stdout)
    print('See below for usage instructions for each mode.', file = sys.stdout)
    print(file = sys.stdout)

    # Print out admin help.
    self.printAdminModeUsage(admin)

    # Print out a list of available tools.
    self.printToolModeUsage(tl)

    # Print out pipeline help.
    self.printPipelineModeUsage(io, path)

  # Print usage information on the admin mode of operation.
  def printAdminModeUsage(self, admin):
    print('==============', file = sys.stdout)
    print('  admin mode'  , file = sys.stdout)
    print('==============', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno <admin operation> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('     <admin operation>:', file = sys.stdout)

    # For the purposes of formatting the screen output, find the longest admin
    # operation name and use this to define the format length.
    length = 0
    for mode in admin.allModes:
      if len(mode) > length : length = len(mode)
    length += 5

    for mode in admin.allModes:

      # Get the tool description.
      description = admin.modeDescriptions[mode]
      printTool = mode + ":"
      self.writeFormattedText(printTool, description, length, 2, '')
    print(file = sys.stdout)

  # Print usage information on the tool mode of operation.
  def printToolModeUsage(self, tl):
    print('=============', file = sys.stdout)
    print('  tool mode', file = sys.stdout)
    print('=============', file = sys.stdout)
    print(file = sys.stdout)
    print("Usage: gkno <tool name> [options]", file = sys.stdout)
    print(file = sys.stdout)
    print('     <tool name>:', file = sys.stdout)

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
      printTool   = tool + ":"

      if not tl.hiddenTools[tool]: self.writeFormattedText(printTool, description, length, 2, '')
    print(file = sys.stdout)

  # Print usage information on the pipeline mode of operation.
  def printPipelineModeUsage(self, io, path):
    print('=================', file = sys.stdout)
    print('  pipeline mode', file = sys.stdout)
    print('=================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('     <pipeline name>:', file = sys.stdout)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    sortedKeys = sorted(io.jsonPipelineFiles.keys())
    length = 0
    for pipeline in sortedKeys:
      pipeline = pipeline[0:(len(pipeline) - 5)]
      if len(pipeline) > length: length = len(pipeline)
    length += 5

    for pipeline in sortedKeys:

      # Open the json file and get the pipeline description.
      pipelineFile = path + '/config_files/pipes/' + pipeline
      jsonData     = io.getJsonData(pipelineFile)
      description  = jsonData['description'] if 'description' in jsonData else 'No description'

      pipeline = pipeline[0:(len(pipeline) - 5)] + ':'
      self.writeFormattedText(pipeline, description, length, 2, '')
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
      print('     required arguments:', file = sys.stdout)
      for argument in sRequiredArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description']
        dataType      = tl.toolInfo[tool]['arguments'][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sDefaultArguments) != 0:
      print('     required arguments with set defaults:', file = sys.stdout)
      for argument in sDefaultArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description']
        dataType      = tl.toolInfo[tool]['arguments'][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sOptionalArguments) != 0:
      print('     optional arguments:', file = sys.stdout)
      for argument in sOptionalArguments:
        printArgument = argument + ':'
        description   = tl.toolInfo[tool]['arguments'][argument]['description']
        dataType      = tl.toolInfo[tool]['arguments'][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
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
      description    = pl.information['description'] if 'description' in pl.information else 'No description'
      self.writeFormattedText(pipeline, description, length, 2, '')
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
    self.writeFormattedText('', description, 0, 1, '')
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
      print('     Required pipeline specific arguments:', file = sys.stdout)
      sortedArguments = sorted(requiredArguments.keys())
      for argument in sortedArguments:
        self.writeFormattedText(argument, requiredArguments[argument], length, 2, '')
      print(file = sys.stdout)

    if len(arguments) != 0:
      print('     Optional pipeline specific arguments:', file = sys.stdout)
      sortedArguments = sorted(arguments.keys())
      for argument in sortedArguments:
        self.writeFormattedText(argument, arguments[argument], length, 2, '')
      print(file = sys.stdout)

    # List the names of the tools in the pipeline.  These can appear as command line arguments
    # in order to modify parameters for the specified tool.
    print('     The following tools can have parameters modified:', file = sys.stdout)
    length = 0
    for task in pl.information['workflow']:
      length = len(task) if (len(task) > length) else length
    length += 5

    sortedTasks = sorted(pl.information['workflow'])
    for task in sortedTasks:
      tool  = pl.information['tools'][task]
      if not tl.hiddenTools[tool]:
        task += ':'
        self.writeFormattedText('--' + task, tool, length + 2, 2, '')
    sys.stdout.flush()

  # Write out key value pairs in a formatted manned.  These may be tool and
  # description or command line argument and description or whatever else is
  # required.
  def writeFormattedText(self, key, value, length, noTabs, dataType):

    # Set the maximum width of the line.
    maxLength   = 100

    # Determine the amount of text prior to the value.
    startLength = length + (5 * noTabs) + 3
    if dataType != '': startLength += 10

    valueList = []
    while len(value) > (maxLength - startLength):
      index = value.rfind(' ', 0, (maxLength - startLength))
      valueList.append(value[0:index])
      value = value[index + 1:len(value)]
    if value != '': valueList.append(value)

    value = valueList.pop(0)
    if dataType == '':
      print("%-*s%-*s%-*s" % ((5 * noTabs), '', length, key, 1, value), file = sys.stdout)
      for value in valueList:  print('%-*s%-*s%-*s' % ((5 * noTabs), ' ', length, ' ', 1, value), file = sys.stdout)
    else:
      print("%-*s%-*s%-*s%-*s" % ((5 * noTabs), '', length, key, 10, dataType, 1, value), file = sys.stdout)
      for value in valueList:  print('%-*s%-*s%-*s' % ((5 * noTabs) + 10, ' ', length, ' ', 1, value), file = sys.stdout)

  # If an admin mode's help was requested.
  def adminModeUsage(self, admin):
    if   admin.mode == "build"           : self.buildUsage(admin)
    elif admin.mode == "update"          : self.updateUsage(admin)
    elif admin.mode == "add-resource"    : self.addResourceUsage(admin)
    elif admin.mode == "remove-resource" : self.removeResourceUsage(admin)
    elif admin.mode == "update-resource" : self.updateResourceUsage(admin)
  
  # If build help was requested
  def buildUsage(self, admin):
    print('====================', file = sys.stdout)
    print('  gkno build usage'  , file = sys.stdout)
    print('====================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno build', file = sys.stdout)
    print(file = sys.stdout)
    print('Description:', file=sys.stdout)
    print('\t', admin.modeDescriptions["build"], file=sys.stdout)

  # If update help was requested
  def updateUsage(self, admin):
    print('=====================', file = sys.stdout)
    print('  gkno update usage'  , file = sys.stdout)
    print('=====================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno update', file = sys.stdout)
    print(file = sys.stdout)
    print('Description:', file=sys.stdout)
    print('\t', admin.modeDescriptions["update"], file=sys.stdout)

  # If addResource help was requested
  def addResourceUsage(self, admin):
    print('===========================', file = sys.stdout)
    print('  gkno add-resource usage'  , file = sys.stdout)
    print('===========================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno add-resource [organism] [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('Description: ', admin.modeDescriptions["add-resource"], file=sys.stdout)
    print(file=sys.stdout)
    print('Arguments & Options:', file=sys.stdout)
    print('    [organism]        Name of organism to add. By default, this will fetch the ', file=sys.stdout)
    print('                      newest release hosted by the gkno project. By not specifying ', file=sys.stdout)
    print('                      a release (see below), gkno will track this organism for ', file=sys.stdout)
    print('                      new genome releases. When the gkno project hosts a new ', file=sys.stdout)
    print('                      release, the next you type "gkno update" it will be listed ', file=sys.stdout) 
    print('                      as available for adding. See "gkno update --help" for more info.', file=sys.stdout)
    print('                      If you omit this argument, then a list of available organisms ', file=sys.stdout)
    print('                      will be shown. Most organisms have recognized aliases that ', file=sys.stdout)
    print('                      may be used. See organism list for examples', file=sys.stdout) 
    print('    --release [name]  Fetch resources for a specific genome release. This argument ', file=sys.stdout)
    print('                      must follow a named organism. If you use the --release option ', file=sys.stdout)
    print('                      but do not specify a release name, then a list of all releases ', file=sys.stdout)
    print('                      available will be shown', file = sys.stdout)
    print(file=sys.stdout)
    print('Examples: ', file=sys.stdout)
    print('    gkno add-resource                                List all organisms hosted by the gkno project', file=sys.stdout)
    print('    gkno add-resource homo_sapiens                   Fetch resources for current human genome release', file=sys.stdout)
    print('    gkno add-resource human                          Same as above, but using an alias', file=sys.stdout)
    print('    gkno add-resource human --release                List all hosted human genome releases', file=sys.stdout)
    print('    gkno add-resource human --release build_36.2     Fetch resources for human build_36.2', file=sys.stdout)
    print(file=sys.stdout)
    print('For more information, see the admin mode tutorial at http://www.gkno.me', file=sys.stdout)

  # If removeResource help was requested
  def removeResourceUsage(self, admin):
    print('==============================', file = sys.stdout)
    print('  gkno remove-resource usage'  , file = sys.stdout)
    print('==============================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno remove-resource [organism] [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('Description: ', admin.modeDescriptions["remove-resource"], file=sys.stdout)
    print(file=sys.stdout)
    print('Arguments & Options:', file=sys.stdout)
    print('    [organism]        Name of organism to remove. This will delete all resource ', file=sys.stdout)
    print('                      files for all releases of this genome. By not specifying ', file=sys.stdout)
    print('                      a release (see below), gkno will also stop tracking this ', file=sys.stdout)
    print('                      organism for new genome releases. If you omit this ', file=sys.stdout)
    print('                      argument, then a list of all organisms you have resources ', file=sys.stdout)
    print('                      for will be shown. Most organisms have recognized aliases ', file=sys.stdout)
    print('                      that may be used. See organism list for examples', file=sys.stdout) 
    print('    --release [name]  Only remove the resources for a specific genome release. ', file=sys.stdout)
    print('                      This argument must follow a named organism. If you use the ', file=sys.stdout)
    print('                      --release option but do not specify a release name, then a ', file=sys.stdout)
    print('                      list of all of your releases will be shown', file = sys.stdout)
    print(file=sys.stdout)
    print('Examples: ', file=sys.stdout)
    print('    gkno remove-resource                                List all organisms you have added', file=sys.stdout)
    print('    gkno remove-resource homo_sapiens                   Remove all resource files for human genome', file=sys.stdout)
    print('    gkno remove-resource human                          Same as above, but using an alias', file=sys.stdout)
    print('    gkno remove-resource human --release                List all human genome releases you have added', file=sys.stdout)
    print('    gkno remove-resource human --release build_36.2     Remove only data files for human build_36.2', file=sys.stdout)
    print(file=sys.stdout)
    print('For more information, see the admin mode tutorial at http://www.gkno.me', file=sys.stdout)

  # If updateResource help was requested
  def updateResourceUsage(self, admin):
    print('==============================', file = sys.stdout)
    print('  gkno update-resource usage'  , file = sys.stdout)
    print('==============================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno update-resource <organism>', file = sys.stdout)
    print(file = sys.stdout)
    print('Description: ', admin.modeDescriptions["update-resource"], file=sys.stdout)
    print(file=sys.stdout)
    print('Arguments & Options:', file=sys.stdout)
    print('    <organism>        Name of organism to update (required). This will fetch the ', file=sys.stdout)
    print('                      newest release hosted by the gkno project. Note - updating ', file=sys.stdout)
    print('                      in this manner will change the directory pointed to by the ', file=sys.stdout)
    print('                      "current" symlink (shortcut). To add the new release\'s ', file=sys.stdout)
    print('                      data without touching the "current" directory, instead use ', file=sys.stdout)
    print('                      "gkno add-resource <organism>" with a named release.', file=sys.stdout)
    print(file=sys.stdout)
    print('Examples: ', file=sys.stdout)
    print('    gkno update-resource homo_sapiens     Fetch resources for current human genome release', file=sys.stdout)
    print('    gkno update-resource human            Same as above, but using an alias', file=sys.stdout)
    print(file=sys.stdout)
    print('For more information, see the admin mode tutorial at http://www.gkno.me', file=sys.stdout)

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


#!/usr/bin/python

from __future__ import print_function

import configurationClass
from configurationClass import *

import os
import sys

class helpClass:
  def __init__(self):
    self.adminHelp            = False
    self.availablePipelines   = []
    self.availableTools       = []
    self.generalHelp          = False
    self.nodeMethods          = nodeClass()
    self.pipelineHelp         = False
    self.printHelp            = False
    self.specificPipelineHelp = False
    self.toolHelp             = False
    self.unknownPipeline      = False
    self.unknownTool          = False

  # Define lists of all available tools and pipelines.
  def setAvailableToolsAndPipelines(self, tools, pipelines):

    # Tool list.
    self.availableTools = tools

    # Pipeline list.
    for pipelineFile in pipelines:
      pipeline = pipelineFile.replace('.json', '')

      # Ignore 'instances' files.
      if not pipeline.endswith('_instances'): self.availablePipelines.append(pipeline)

  # If usage information needs to be printed out, determine the exact level
  # of usage information to provide, write to screen and then terminate.
  def printUsage(self, graph, config, workflow, admin, version, date, path):

    # General gkno usage.
    if self.generalHelp:
      self.usage(graph, config, admin, path)

    # gkno tool mode usage.
    elif self.toolHelp:
      if self.unknownTool:
        self.printToolModeUsage(config)
        self.unknownToolMessage(graph, config.pipeline.pipelineName)
      else:
        self.toolUsage(graph, config.pipeline.pipelineName)

    # General pipeline help.
    elif self.pipelineHelp:
      self.pipelineUsage(graph, config, path)
      if self.unknownPipeline: self.unknownPipelineMessage()

    # Specific pipeline help.
    elif self.specificPipelineHelp:
      self.specificPipelineUsage(graph, config, workflow)

    # Admin mode help.
    elif self.adminHelp:
      self.adminModeUsage(admin)

    # Terminate.
    exit(0)

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
  def usage(self, graph, config, admin, path):
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
    self.printToolModeUsage(config)

    # Print out pipeline help.
    self.printPipelineModeUsage(path)

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
  def printToolModeUsage(self, config):
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
    for tool in self.availableTools:
      if len(tool) > length: length = len(tool)
    length += 5

    sortedKeys = sorted(self.availableTools)
    for tool in sortedKeys:

      # Get the tool description.
      description = config.tools.attributes[tool].description
      printTool   = tool + ":"

      if not config.tools.attributes[tool].isHidden: self.writeFormattedText(printTool, description, length, 2, '')
    print(file = sys.stdout)

  # Print usage information on the pipeline mode of operation.
  def printPipelineModeUsage(self, path):
    print('=================', file = sys.stdout)
    print('  pipeline mode', file = sys.stdout)
    print('=================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('     <pipeline name>:', file = sys.stdout)

    # For the purposes of formatting the screen output, find the longest tool
    # name and use this to define the format length.
    sortedKeys = sorted(self.availablePipelines)
    length = 0
    for pipeline in sortedKeys:
      if len(pipeline) > length: length = len(pipeline)
    length += 5

    for pipeline in sortedKeys:

      # Open the json file and get the pipeline description.
      pipelineFile = path + '/config_files/pipes/' + pipeline + '.json'

      # Create a pipieline configuration file object.
      config       = configurationClass()
      data         = config.fileOperations.readConfigurationFile(pipelineFile)
      description  = data['description']

      pipeline = pipeline + ':'
      self.writeFormattedText(pipeline, description, length, 2, '')
    sys.stdout.flush()

  # Print out tool usage.
  def toolUsage(self):
    print('===================', file = sys.stdout)
    print('  gkno tool usage', file = sys.stdout)
    print('===================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno ', tool, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the tool description.
    print('     Description:', file = sys.stdout)
    self.writeFormattedText(tl.descriptions[tool], ' ', 2, 2, ' ')
    print(file = sys.stdout)
    sys.stdout.flush()

    # If this pipeline has different instances, print them to screen.
    if len(tl.instances[tool]) > 0:
      print('     Instances:', file = sys.stdout)
      length = 0
      for instance in tl.instances[tool]: length = len(instance) if len(instance) > length else length
      length += 4

      sortedInstances = sorted(tl.instances[tool])
      for instance in sortedInstances:
        description = tl.instances[tool][instance]['description']
        self.writeFormattedText(instance + ":", description, length, 2, '')
      print(file = sys.stdout)

    # Split the tool inputs into a required and an optional set.
    defaultArguments  = []
    optionalArguments = []
    requiredArguments = []
    for argument in tl.argumentInformation[tool]:
      default  = True if 'default' in tl.argumentInformation[tool][argument] else False
      required = tl.argumentInformation[tool][argument]['required']
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
    sortedKeys = sorted(tl.argumentInformation[tool])
    for argument in sortedKeys:
      if 'short form argument' in tl.argumentInformation[tool][argument]:
        shortForm = tl.argumentInformation[tool][argument]['short form argument']
        newLength = len(argument) + len(shortForm) + 3
      else: newLength = len(argument)
      length = newLength if (newLength > length) else length
    length += 5

    if len(sRequiredArguments) != 0:
      print('     Required arguments:', file = sys.stdout)
      for argument in sRequiredArguments:
        if 'short form argument' in tl.argumentInformation[tool][argument]:
          shortForm = tl.argumentInformation[tool][argument]['short form argument']
          printArgument = argument + ' (' + shortForm + '):'
        else: printArgument = argument + ':'
        description   = tl.argumentInformation[tool][argument]['description']
        dataType      = tl.argumentInformation[tool][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sDefaultArguments) != 0:
      print('     required arguments with set defaults:', file = sys.stdout)
      for argument in sDefaultArguments:
        if 'short form argument' in tl.argumentInformation[tool][argument]:
          shortForm     = tl.argumentInformation[tool][argument]['short form argument']
          printArgument = argument + ' (' + shortForm + '):'
        else: printArgument = argument + ':'
        description   = tl.argumentInformation[tool][argument]['description']
        dataType      = tl.argumentInformation[tool][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

    if len(sOptionalArguments) != 0:
      print('     Optional arguments:', file = sys.stdout)
      for argument in sOptionalArguments:
        if 'short form argument' in tl.argumentInformation[tool][argument]:
          shortForm = tl.argumentInformation[tool][argument]['short form argument']
          printArgument = argument + ' (' + shortForm + '):'
        else: printArgument = argument + ':'
        description   = tl.argumentInformation[tool][argument]['description']
        dataType      = tl.argumentInformation[tool][argument]['type']
        self.writeFormattedText(printArgument, description, length, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Print usage information for pipelines:
  def pipelineUsage(self, graph, config, path):
    print('=======================', file = sys.stdout)
    print('  gkno pipeline usage', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('     <pipeline name>:', file = sys.stdout)

    # Determine the length of the longest pipeline name.
    length = 0
    sortedKeys = sorted(self.availablePipelines)
    for pipeline in sortedKeys:
      length = len(pipeline) if (len(pipeline) > length) else length

    for pipeline in sortedKeys:

      # For each available pipeline, open the json and get the pipeline description.
      pipelineFile = path + '/config_files/pipes/' + pipeline
      pipeline     = pipeline + ':'
      if pipeline[-10:-1] != 'instances':
        data         = config.fileOperations.readConfigurationFile(pipelineFile + '.json')
        description  = data['description'] if 'description' in data else 'No description provided'
        self.writeFormattedText(pipeline, description, length, 2, '')
    sys.stdout.flush()

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def specificPipelineUsage(self, graph, config, workflow):
    length = len(config.pipeline.pipelineName) + 26
    print('=' * length)
    print('  gkno pipeline usage - ', config.pipeline.pipelineName, sep = '', file = sys.stdout)
    print('=' * length)
    print(file = sys.stdout)
    print('Usage: gkno pipe ', config.pipeline.pipelineName, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the decription of the pipeline.
    description = config.pipeline.description
    print('     Description:', file = sys.stdout)
    self.writeFormattedText('', description, 0, 2, '')
    print(file = sys.stdout)

    # Write out the pipeline workflow.
    print('     Workflow:', file = sys.stdout)
    length = 0
    for task in workflow: length = len(task) if (len(task) > length) else length
    length += 4
    for task in workflow:
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      description    = config.nodeMethods.getGraphNodeAttribute(graph, task, 'description')
      self.writeFormattedText(task + ":", description, length, 2, '')
    print(file = sys.stdout)

    # If this pipeline has different instances, print them to screen.
    # TODO Sort instances
    if len(config.pipeline.instances) > 0:
      print('     Instances:', file = sys.stdout)
      length = 0
      for instance in config.pipeline.instances: length = len(instance) if len(instance) > length else length
      length += 4

      sortedInstances = sorted(config.pipeline.instances)
      for instance in sortedInstances:
        description = config.pipeline.instances[instance]['description']
        self.writeFormattedText(instance + ":", description, length, 2, '')
      print(file = sys.stdout)

    # List the options available at the pipeline level.
    #
    # Loop over all the allowable arguments and determine if there is a short form and
    # the length of the combined '--argument (-a)' text.
    length            = 0
    arguments         = {}
    requiredArguments = {}
    for node in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, node, 'nodeType') == 'option':
        if config.nodeMethods.getGraphNodeAttribute(graph, node, 'isPipelineArgument'):
          description = config.nodeMethods.getGraphNodeAttribute(graph, node, 'description')
          shortForm   = config.nodeMethods.getGraphNodeAttribute(graph, node, 'shortForm')
          text        = config.nodeMethods.getGraphNodeAttribute(graph, node, 'argument') + ' (' + shortForm + '):'
          length      = len(text) if (len(text) > length) else length
          isRequired  = config.nodeMethods.getGraphNodeAttribute(graph, node, 'isRequired')
          if isRequired: requiredArguments[text] = description
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
    for task in workflow:
      length = len(task) if (len(task) > length) else length
    length += 5

    sortedTasks = sorted(workflow)
    for task in sortedTasks:
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      isHidden       = config.tools.attributes[associatedTool].isHidden
      if not isHidden:
        task += ':'
        self.writeFormattedText('--' + task, associatedTool, length + 2, 2, '')
    sys.stdout.flush()

  # Write out key value pairs in a formatted manned.  These may be tool and
  # description or command line argument and description or whatever else is
  # required.
  def writeFormattedText(self, key, value, length, noTab, dataType):

    # Set the maximum width of the line.
    maxLength   = 100

    # Determine the amount of text prior to the value.
    startLength = length
    if dataType != '': startLength += 10

    valueList = []
    while len(value) > (maxLength - startLength):
      index = value.rfind(' ', 0, (maxLength - startLength))
      if index == -1:
        index = value.find(' ', 0, len(value))
        if index == -1:
          valueList.append(value)
          value = ''
        else:
          valueList.append(value[0:index])
          value = value[index + 1:len(value)]
      else:
        valueList.append(value[0:index])
        value = value[index + 1:len(value)]
    if value != '': valueList.append(value)

    value = valueList.pop(0)
    if dataType == '':
      print("%-*s%-*s%-*s" % ((5 * noTab), '', length, key, 1, value), file = sys.stdout)
      for value in valueList:  print('%-*s%-*s%-*s' % ((5 * noTab), '', length, '', 1, value), file = sys.stdout)
    else:
      print("%-*s%-*s%-*s%-*s" % ((5 * noTab), '', length, key, 10, dataType, 1, value), file = sys.stdout)
      for value in valueList:  print('%-*s%-*s%-*s%-*s' % ((5 * noTab), '', length, '', 10, '', 1, value), file = sys.stdout)

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


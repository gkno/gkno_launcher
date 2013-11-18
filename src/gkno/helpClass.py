#!/usr/bin/python

from __future__ import print_function

#import configurationClass
#from configurationClass import *

import os
import sys

class helpClass:
  def __init__(self):
    self.adminHelp            = False
    self.generalHelp          = False
    self.pipelineHelp         = False
    self.printHelp            = False
    self.specificPipelineHelp = False
    self.toolHelp             = False

    # Store information on the available tools and pipelines.
    self.availablePipelines   = {}
    self.availableTools       = {}
    self.invalidPipeline      = False
    self.invalidTool          = False
    self.pipelineLength       = 0
    self.toolLength           = 0

    # Instances information.
    self.availableInstances = {}
    self.pipelineInstances  = {}
    self.toolInstances      = {}
    self.instanceLength     = 0

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, isPipeline, pipelineName, admin, mode):

    # Check if '--help' or '-h' were included in the command line.  If so, determine what help
    # was requested.  Pipeilne, tool, admin or general help.
    for argument in sys.argv[1:]:
      if argument == '--help' or argument == '-h': self.printHelp = True

    # If the run mode was determined to be 'help', set printHelp to True.
    if mode == 'help':
      self.printHelp   = True
      self.generalHelp = True

    if self.printHelp:

      # If '--help' is the only argument on the command line, there are only two unique arguments:
      # the path and '--help'.  This case calls for general help.
      if len(sys.argv) == 2 and mode == 'help': self.generalHelp  = True
      else:

        # If a pipeline is being run, check if help is required on general pipelines, or on a specific
        # pipeline.
        if isPipeline:
          self.pipelineHelp         = True
          self.specificPipelineHelp = True
          if pipelineName == '--help' or pipelineName == '-h' or pipelineName == None or self.invalidPipeline: self.specificPipelineHelp = False

        # Help with admin.
        elif admin.isRequested: self.adminHelp = True

        # If pipeline or admin help wasn't requested, then tool help is required.
        else: self.toolHelp = True

  # If usage information needs to be printed out, determine the exact level
  # of usage information to provide, write to screen and then terminate.
  def printUsage(self, graph, config, gknoConfig, admin, path, name):

    # Get information on all the available tools and pipelines.
    self.getToolsAndPipelines(config, gknoConfig, path)

    # General gkno usage.
    if self.generalHelp: self.usage(graph, config, gknoConfig, admin, path)

    # gkno tool mode usage.
    elif self.toolHelp:
      if self.invalidTool:
        self.printToolModeUsage(config, gknoConfig, path)
        self.invalidToolMessage(name)
      else: self.toolUsage(config, gknoConfig, name, path)

    # General pipeline help.
    elif self.pipelineHelp:
      if self.invalidPipeline:
        self.printPipelineModeUsage(config, gknoConfig, path)
        if self.invalidPipeline: self.invalidPipelineMessage(name)
      else:
        self.printPipelineModeUsage(config, gknoConfig, path)

    # Admin mode help.
    elif self.adminHelp: self.adminModeUsage(admin)

    # Terminate.
    exit(0)

  # Print usage information.
  def usage(self, graph, config, gknoConfig, admin, path):
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
    self.printToolModeUsage(config, gknoConfig, path)

    # Print out pipeline help.
    self.printPipelineModeUsage(config, gknoConfig, path)

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
      if len(mode) > length: length = len(mode)
    length += 5

    for mode in admin.allModes:

      # Get the tool description.
      description = admin.modeDescriptions[mode]
      printTool   = mode + ":"
      self.writeFormattedText(printTool, description, length, 2, '')
    print(file = sys.stdout)

  # Print usage information on the tool mode of operation.
  def printToolModeUsage(self, config, gknoConfig, path):
    print('=============', file = sys.stdout)
    print('  tool mode', file = sys.stdout)
    print('=============', file = sys.stdout)
    print(file = sys.stdout)
    print("Usage: gkno <tool name> [options]", file = sys.stdout)
    print(file = sys.stdout)
    print('     <tool name>:', file = sys.stdout)

    # Write the tools to screen.
    for tool in sorted(self.availableTools.keys()):
      if not self.availableTools[tool][1]: self.writeFormattedText(tool + ':', self.availableTools[tool][0], self.toolLength + 5, 2, '')
    print(file = sys.stdout)

  # Print usage information on the pipeline mode of operation.
  def printPipelineModeUsage(self, config, gknoConfig, path):
    print('=================', file = sys.stdout)
    print('  pipeline mode', file = sys.stdout)
    print('=================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)
    print('     <pipeline name>:', file = sys.stdout)

    # Write the tools to screen.
    for pipeline in sorted(self.availablePipelines.keys()):
       self.writeFormattedText(pipeline + ':', self.availablePipelines[pipeline], self.pipelineLength + 5, 2, '')
    print(file = sys.stdout)

  # Get information on all avilable tools and pipelines.
  def getToolsAndPipelines(self, config, gknoConfig, path):

    # Open each tool file, check that it is a valid json file and get the tool description and
    # whether the tool is hidden.
    for filename in gknoConfig.jsonFiles['tools']:
      #TODO REMOVE TEMP
      filePath           = path + '/config_files/temp/tools/' + filename
      tool               = filename[:len(filename) - 5]
      data               = config.fileOperations.readConfigurationFile(filePath)
      self.toolInstances = config.tools.processConfigurationData(tool, data)
      description        = config.tools.getToolAttribute(tool, 'description')
      isHidden           = True if config.tools.getToolAttribute(tool, 'isHidden') else False

      # For the purposes of formatting the screen output, find the longest tool
      # name and use this to define the format length.
      if len(tool) > self.toolLength: self.toolLength = len(tool)
      self.availableTools[tool] = (description, isHidden)

    # Open each pipeline file, check that it is a valid json file and get the pipeline description and
    # whether the tool is hidden.
    for filename in gknoConfig.jsonFiles['pipelines']:
      #TODO REMOVE TEMP
      filePath               = path + '/config_files/temp/pipes/' + filename
      pipeline               = filename[:len(filename) - 5]
      data                   = config.fileOperations.readConfigurationFile(filePath)
      self.pipelineInstances = config.pipeline.processConfigurationData(data, filePath)
      description            = config.pipeline.description

      # For the purposes of formatting the screen output, find the longest tool
      # name and use this to define the format length.
      if len(pipeline) > self.pipelineLength: self.pipelineLength = len(pipeline)
      self.availablePipelines[pipeline] = description

  # Get instances information.
  def getInstances(self, config, gknoConfig, path, mode, name):

    # Get the instances contained in the tool configuration file.
    instances = self.toolInstances if mode == 'tool' else self.pipelineInstances
    for instance in instances.keys():
      self.availableInstances[instance] = instances[instance]['description']
      if len(instance) > self.instanceLength: self.instanceLength = len(instance)

    # Now get any external instances.
    filename = name + '_instances.json'
    if mode == 'tool':
      text     = 'tool instances'
      filePath = path + '/config_files/temp/tools/' + filename
    else:
      text     = 'pipeline instances'
      filePath = path + '/config_files/temp/pipes/' + filename

    if filename in gknoConfig.jsonFiles[text]:
      data     = config.fileOperations.readConfigurationFile(filePath)
      for instance in data['instances']:
        self.availableInstances[instance] = data['instances'][instance]['description']
        if len(instance) > self.instanceLength: self.instanceLength = len(instance)

  # If help for a specific tool was requested, but that tool does not exist,
  # print an error after the usage information.
  def invalidToolMessage(self, tool):
    print(file = sys.stdout)
    print('=======================', file = sys.stdout)
    print('  Additional messages', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('ERROR: Requested tool \'', tool, '\' does not exist.  Check available tools in usage above.', sep = '', file = sys.stdout)
    sys.stdout.flush()

  # If a pipeline was requested, but no configuration file can be found, add
  # this extra error at the end of the usage information.
  def invalidPipelineMessage(self, pipeline):
    print(file = sys.stdout)
    print('=======================', file = sys.stdout)
    print('  Additional messages', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('ERROR: Requested pipeline \'', pipeline, '\' does not exist.  Check available pipelines in usage above.', sep = '', file = sys.stdout)
    sys.stdout.flush()

  # Print out tool usage.
  def toolUsage(self, config, gknoConfig, tool, path):
    print('===================', file = sys.stdout)
    print('  gkno tool usage', file = sys.stdout)
    print('===================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno ', tool, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the tool description.
    print('     Description:', file = sys.stdout)
    self.writeFormattedText(self.availableTools[tool][0], ' ', 2, 2, ' ')
    print(file = sys.stdout)
    sys.stdout.flush()

    # If this pipeline has different instances, print them to screen.
    self.getInstances(config, gknoConfig, path, 'tool', tool)
    if self.availableInstances:
      print('     Instances:', file = sys.stdout)
      for instance in sorted(self.availableInstances.keys()):
         self.writeFormattedText(instance + ":", self.availableInstances[instance], self.instanceLength + 4, 2, '')
      print(file = sys.stdout)

    # Split the tool inputs into a required and an optional set.
    optionalArguments = {}
    requiredArguments = {}
    argumentLength    = 0
    for argument in config.tools.configurationData[tool]['arguments'].keys():
      shortForm = config.tools.getArgumentData(tool, argument, 'short form argument')
      if (len(argument) + len(shortForm)) > argumentLength: argumentLength = len(argument) + len(shortForm)
      if config.tools.getArgumentData(tool, argument, 'required'): requiredArguments[argument] = shortForm
      else: optionalArguments[argument] = shortForm

    # Sort the required and optional arguments.
    sortedRequiredArguments = sorted(requiredArguments.keys())
    sortedOptionalArguments = sorted(optionalArguments.keys())

    # Print out the required arguments.
    if sortedRequiredArguments:
      print('     Required arguments:', file = sys.stdout)
      for argument in sortedRequiredArguments:
        argumentText  = argument + ' (' + requiredArguments[argument] + '):'
        description   = config.tools.getArgumentData(tool, argument, 'description')
        dataType      = config.tools.getArgumentData(tool, argument, 'data type')
        self.writeFormattedText(argumentText, description, argumentLength + 5, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

    # Print out the optional arguments.
    if sortedOptionalArguments:
      print('     Optional arguments:', file = sys.stdout)
      for argument in sortedOptionalArguments:
        argumentText  = argument + ' (' + optionalArguments[argument] + '):'
        description   = config.tools.getArgumentData(tool, argument, 'description')
        dataType      = config.tools.getArgumentData(tool, argument, 'data type')
        self.writeFormattedText(argumentText, description, argumentLength + 5, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def specificPipelineUsage(self, graph, config, gknoConfig, name, workflow, path):
    length = len(name) + 26
    print('=' * length)
    print('  gkno pipeline usage - ', name, sep = '', file = sys.stdout)
    print('=' * length)
    print(file = sys.stdout)
    print('Usage: gkno pipe ', name, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the decription of the pipeline.
    print('     Description:', file = sys.stdout)
    self.writeFormattedText('', config.pipeline.description, 0, 2, '')
    print(file = sys.stdout)

    # Write out the pipeline workflow.
    print('     Workflow:', file = sys.stdout)
    length = 0
    for task in workflow: length = len(task) if (len(task) > length) else length
    for task in workflow:
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      description    = config.nodeMethods.getGraphNodeAttribute(graph, task, 'description')
      self.writeFormattedText(task + ":", description, length + 4, 2, '')
    print(file = sys.stdout)

    # If this pipeline has different instances, print them to screen.
    self.getToolsAndPipelines(config, gknoConfig, path)
    self.getInstances(config, gknoConfig, path, 'pipe', name)
    if self.availableInstances:
      print('     Instances:', file = sys.stdout)
      for instance in sorted(self.availableInstances.keys()):
         self.writeFormattedText(instance + ":", self.availableInstances[instance], self.instanceLength + 4, 2, '')
      print(file = sys.stdout)

    # List the options available at the pipeline level.
    #
    # Loop over all the allowable arguments and determine if there is a short form and
    # the length of the combined '--argument (-a)' text.
    length            = 0
    arguments         = {}
    optionNodeIDs     = config.nodeMethods.getNodes(graph, 'option')
    requiredArguments = {}
    optionalArguments = {}
    for argument in config.pipeline.argumentData:
      description = config.pipeline.argumentData[argument].description
      shortForm   = config.pipeline.argumentData[argument].shortForm
      text        = argument + ' (' + shortForm + '):'
      length      = len(text) if (len(text) > length) else length

      # First check if the pipeline requires the argument. If not, check if the tool
      # requires the argument.
      isRequired = config.pipeline.argumentData[argument].isRequired
      if not isRequired:
        nodeID             = config.pipeline.argumentData[argument].nodeID
        associatedTask     = config.pipeline.nodeTaskInformation[nodeID][0][0]
        associatedArgument = config.pipeline.nodeTaskInformation[nodeID][0][1]
        associatedTool     = config.nodeMethods.getGraphNodeAttribute(graph, associatedTask, 'tool')
        isRequired         = config.tools.getArgumentData(associatedTool, associatedArgument, 'required')
      if isRequired: requiredArguments[text] = description
      else: optionalArguments[text] = description

    if requiredArguments:
      print('     Required pipeline specific arguments:', file = sys.stdout)
      for argument in sorted(requiredArguments.keys()):
        self.writeFormattedText(argument, requiredArguments[argument], length + 4, 2, '')
      print(file = sys.stdout)

    if optionalArguments:
      print('     Optional pipeline specific arguments:', file = sys.stdout)
      for argument in sorted(optionalArguments.keys()):
        self.writeFormattedText(argument, optionalArguments[argument], length + 4, 2, '')
      print(file = sys.stdout)

    # List the names of the tools in the pipeline.  These can appear as command line arguments
    # in order to modify parameters for the specified tool.
    print('     The following tasks can have parameters modified:', file = sys.stdout)
    length = 0
    for task in workflow: length = len(task) if (len(task) > length) else length

    for task in sorted(workflow):
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      isHidden       = self.availableTools[associatedTool][1]
      if not isHidden: self.writeFormattedText('--' + task + ':', associatedTool, length + 5, 2, '')
    sys.stdout.flush()

    # Terminate.
    exit(0)

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

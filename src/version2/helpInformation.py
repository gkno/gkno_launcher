#!/usr/bin/python

from __future__ import print_function
from difflib import SequenceMatcher

import helpErrors as err

import os
import sys

class helpInformation:
  def __init__(self):

    # Define the errors class.
    self.errors = err.helpErrors()

    # Define allowed help categories.
    self.helpCategories                      = {}
    self.helpCategories['1000G-pipelines']   = 'Analyses performed similarly to 1000 Genomes project analyses.'
    self.helpCategories['BAM-processing']    = 'Pipelines primarily focused on manipulating BAM files.'
    self.helpCategories['Alignment']         = 'Read alignment tasks are performed as part of the pipeline.'
    self.helpCategories['FASTA-processing']  = 'Pipelines involving manipulation of reference FASTA files.'
    self.helpCategories['Reference-free']    = 'Analysis of genomes without use of the genome reference.'
    self.helpCategories['Simulation']        = 'Simulation-based pipelines.'
    self.helpCategories['SV-discovery']      = 'Pipelines including detection of structural variations.'
    self.helpCategories['Variant-discovery'] = 'Pipelines including variant discovery tasks.'
    self.helpCategories['Variant-graph']     = 'Alignments using a variant graph are incorporated.'
    self.helpCategories['VCF-processing']    = 'Process VCF files.'
    self.helpCategories['Visualisation']     = 'Visualisation and plotting pipelines.'

#    # Record whether help is required.
#    self.writeHelp = False
#
#    # Suppress writing out header.
#    self.suppressHeader = False
#
#    # Store if all tools/pipelines are to be written to screen.
#    self.allTools     = False
#    self.allPipelines = False
#
#    # Decide if help is required for tools/pipelines or all.
#    self.toolHelp     = False
#    self.pipelineHelp = False
#
#    # Keep track of whether help on a specific pipeline was requested.
#    self.specificPipelineHelp = False
#
#    # Determine if the help is sorted at the category or tool level.
#    self.helpCategories = False
#
#    # Store if help on admin features was requested.
#    self.adminHelp = False
#
#    # Store information on available categories and groups.
#    self.availableToolCategories     = {}
#    self.availableToolGroups         = {}
#    self.availablePipelineCategories = {}
#
#    # Store the category for which constituent tools/pipelines should be printed.
#    self.requestedCategory = None
#
#    # Store information on the available tools and pipelines.
#    self.availablePipelines   = {}
#    self.availableTools       = {}
#    self.invalidPipeline      = False
#    self.invalidTool          = False
#    self.pipelineLength       = 0
#    self.toolLength           = 0
#
#    # Keep track of tools with malformed configuration files.
#    self.failedTools     = {}
#    self.failedPipelines = {}
#
#    # Keep track of experimental tools and pipelines.
#    self.experimentalTools      = {}
#    self.developmentalPipelines = {}
#
#    # Define the allowed tool/pipeline categories and groups.
#    self.defineToolCategories()
#    self.definePipelineCategories()

  # Provide general help.
  def generalHelp(self, admin):
    print(file = sys.stdout)
    print('The gkno package can be run in the following modes:', file = sys.stdout)
    print('     ADMIN mode:    allows management of gkno and it\'s resources,', file = sys.stdout)
    print('     PIPELINE mode: executes a predetermined pipeline', file = sys.stdout)
    print(file = sys.stdout)
    print('See below for usage instructions for each mode.', file = sys.stdout)
    print(file = sys.stdout)

    # Write out admin help.
    self.adminModeUsage(admin)

    # Write out pipeline usage information.
    self.pipelineUsage()

    # Terminate gkno.
    exit(0)

  # Print usage information on the admin mode of operation.
  def adminModeUsage(self, admin):
    print('  ==================', file = sys.stdout)
    print('  =   admin mode   =', file = sys.stdout)
    print('  ==================', file = sys.stdout)
    print(file = sys.stdout)
    print('  Usage: gkno <admin operation> [options]', file = sys.stdout)
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

  # Print out help on gkno arguments.
  def gknoArgumentHelp(self):
    print(file = sys.stdout)
    print('  ==================', file = sys.stdout)
    print('  = gkno arguments =', file = sys.stdout)
    print('  ==================', file = sys.stdout)
    print(file = sys.stdout)
    text = 'There is a set of arguments that can be applied to all gkno pipelines. The operation of these arguments is explained below:'
    self.writeFormattedText('', text, 0, 1, '')

    # Terminate gkno.
    exit(0)

  # Print out how to use pipelines.
  def pipelineUsage(self):
    print('  =======================', file = sys.stdout)
    print('  = gkno pipeline usage =', file = sys.stdout)
    print('  =======================', file = sys.stdout)
    print(file = sys.stdout)
    print('  Usage: gkno [pipeline] [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    self.writeFormattedText('', 'All pipelines in gkno are classified according to a category. To see a list of these categories, use the command', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --pipeline-categories (-pcat)', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'To see a list of all pipelines in a category, type:', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --tool-categories (-pcat) [category]', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'To see all available pipeliness, type:', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --all-pipelines (-apo)', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')











#######################
### REMOVE OR AMEND ###
#######################


  # Print out info on pipeline categories.
  def writePipelineCategories(self):
    if not self.suppressHeader:
      print('========================', file = sys.stdout)
      print('gkno pipeline categories', file = sys.stdout)
      print('========================', file = sys.stdout)
      print(file = sys.stdout)
      text = 'Following is a list of pipeline categories. To see all of the pipelines in a specific category, use the command line: \'gkno ' + \
      '--pipeline-categories <category>\''
      self.writeFormattedText('', text, 0, 1, '')
      self.writeFormattedText('', '\t', 0, 1, '')

    length = 0
    for category in self.allowedPipelineCategories.keys():
      if len(category) > length: length = len(category)

    for category in sorted(self.allowedPipelineCategories.keys()):
      description   = self.allowedPipelineCategories[category]
      printCategory = category + ": "
      self.writeFormattedText(printCategory, description, length + 2, 2, '')

  # Write out all the tools/pipelines within a category.
  def writeCategory(self, isToolHelp, allowedCategories, category):
    print('====================', file = sys.stdout)
    print('gkno help categories', file = sys.stdout)
    print('====================', file = sys.stdout)
    print(file = sys.stdout)

    # Check that the requested category is valid. If not, find the closest category to that written.
    isInvalidCategory = False
    if category not in allowedCategories:
      isInvalidCategory = True
      providedCategory  = category
      category          = self.findCategory(category, allowedCategories)

    runType = 'tools' if isToolHelp else 'pipelines'
    self.writeFormattedText('', 'Following is a list of ' + runType + ' in the category \'' + category + '\'', 0, 1, '')
    print(file = sys.stdout)

    # Write out the tools and pipelines that fall into the category.
    if isToolHelp: available = self.availableToolCategories
    else: available = self.availablePipelineCategories

    # Check that there are tools/pipelines in the category.
    try: values = available[category]
    except:
      self.writeFormattedText('', 'The requested category (' + category + ') does not contain any ' + runType + '.', 0, 1, '')
      exit(0)

    # Write out the tools/pipelines.
    length = 0
    for value in values.keys():
      if len(value) > length: length = len(value)

    for value in sorted(values.keys()):
      description = values[value]
      printValue  = value + ": "
      self.writeFormattedText(printValue, description, length + 2, 2, '')

    # If the entered category did not exactly match one of the supplied categories, provide
    # a warning that the provided list was based on the assumed most likely category.
    if isInvalidCategory: self.invalidCategory(providedCategory, category)

  # Compare the given category against all the available categories and determine which
  # was the most likely.
  def findCategory(self, category, allowedCategories):
    maxRatio           = 0
    mostLikelyCategory = ''
    for allowedCategory in allowedCategories:
      match = SequenceMatcher(None, allowedCategory, category)
      ratio = match.ratio()
      if ratio > maxRatio:
        maxRatio           = ratio
        mostLikelyCategory = allowedCategory

    return mostLikelyCategory

  # If the requested category is not available, write out the available categories.
  def invalidCategory(self, providedCategory, category):

    # Suppress writing the header when writing available categories.
    self.suppressHeader = True

    # Define text for the output message.
    print(file = sys.stdout)
    print('===============', file = sys.stdout)
    print('    WARNING    ', file = sys.stdout)
    print('===============', file = sys.stdout)
    print(file = sys.stdout)
    self.writeFormattedText('', 'The requested category \'' + providedCategory + '\' is not valid. The shown tools are available ' + \
    'in the \'' + category + '\' category. If this was not the desired category, please check the command line.', 0, 1, '')
    print(file = sys.stdout)

  # Get parameter set information.
  def getParameterSets(self, graph, config, jsonFiles, toolConfigurationFilesPath, pipelineConfigurationFilesPath, mode, name):

    # Define information based on whether a tool or pipeline is being run.
    if mode == 'tool':
      isPipeline       = False
      text             = 'tool parameter sets'
      filePath         = toolConfigurationFilesPath
      externalFilename = name + '_parameterSets'
      externalFilePath = filePath + externalFilename + '.json'
    elif mode == 'pipe':
      isPipeline       = True
      text             = 'pipeline parameter sets'
      filePath         = pipelineConfigurationFilesPath
      externalFilename = name + '_parameterSets'
      externalFilePath = filePath + externalFilename + '.json'

    # Open the pipeline configuration file and process the parameter set data.
    configurationData = config.fileOperations.readConfigurationFile(filePath + name + '.json')
    config.parameterSets.checkParameterSets(graph, name, configurationData['parameter sets'], isPipeline, isExternal = False)

    # Now get any external parameter sets.
    if externalFilename + '.json' in jsonFiles[text]:
      configurationData = config.fileOperations.readConfigurationFile(externalFilePath)
      config.parameterSets.checkParameterSets(graph, name, configurationData['parameter sets'], isPipeline, isExternal = True)

  # Write out parameter sets.
  def writeParameterSets(self, config, tool, parameterSetName):
    if parameterSetName == 'default': print('     Parameter set for: ', parameterSetName, sep = '', file = sys.stdout)
    else: print('     Parameter set (including default parameters) for: ', parameterSetName, sep = '', file = sys.stdout)

    # Get the length of the longest argument in the parameter set.
    argumentLength = 0
    for argument, values in config.parameterSets.getArguments(tool, 'default', isPipeline = False):
      if len(argument) > argumentLength: argumentLength = len(argument)
    for argument, values in config.parameterSets.getArguments(tool, parameterSetName, isPipeline = False):
      if len(argument) > argumentLength: argumentLength = len(argument)

    # Write out the values.
    arguments = {}
    for argument, values in config.parameterSets.getArguments(tool, 'default', isPipeline = False): arguments[argument] = values
    for argument, values in config.parameterSets.getArguments(tool, parameterSetName, isPipeline = False): arguments[argument] = values
    for argument in sorted(arguments):
      firstValue = True
      for value in arguments[argument]:
        if firstValue:
          self.writeFormattedText(argument + ':', str(value), argumentLength + 5, 2, '')
          firstValue = False
        else: self.writeFormattedText('', str(value), argumentLength + 5, 2, '')

  # Write out the gkno specific options.
  def gknoOptions(self, graph, config):
    print('     General gkno arguments:', file = sys.stdout)

    # Find the length of the longest argument.
    argumentLength = 0
    for nodeID in config.nodeMethods.getNodes(graph, 'general'):
      longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'longFormArgument')
      shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'shortFormArgument')
      argumentText      = longFormArgument + ' (' + shortFormArgument + ')'
      if len(argumentText) > argumentLength: argumentLength = len(argumentText)

    # Write out the arguments.
    arguments = {}
    for nodeID in config.nodeMethods.getNodes(graph, 'general'):
      arguments[config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'longFormArgument')] = nodeID

    for longFormArgument in sorted(arguments):
      nodeID            = arguments[longFormArgument]
      longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'longFormArgument')
      shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'shortFormArgument')
      argumentText      = longFormArgument + ' (' + shortFormArgument + ')'
      description       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'description')
      dataType          = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'dataType')
      self.writeFormattedText(argumentText + ':', description, argumentLength + 5, 2, dataType)

    print(file = sys.stdout)

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def writeSpecificPipelineUsage(self, graph, config, jsonFiles, name, toolConfigurationFilesPath, parameterSetName):
    length = len(name) + 26
    print('=' * length)
    print('  gkno pipeline usage - ', name, sep = '', file = sys.stdout)
    print('=' * length)
    print(file = sys.stdout)
    print('Usage: gkno pipe ', name, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the decription of the pipeline.
    print('     Description:', file = sys.stdout)
    self.writeFormattedText('', config.pipeline.attributes.description, 0, 2, '')
    print(file = sys.stdout)

    # Write out the pipeline workflow.
    print('     Workflow:', file = sys.stdout)
    length = 0
    for task in config.pipeline.workflow: length = len(task) if (len(task) > length) else length
    for task in config.pipeline.workflow:
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      description    = config.nodeMethods.getGraphNodeAttribute(graph, task, 'description')
      self.writeFormattedText(task + ":", description, length + 4, 2, '')
    print(file = sys.stdout)

    # If this pipeline has different parameter sets, print them to screen.
    if config.parameterSets.parameterSetAttributes[name]:
      print('     Parameter sets:', file = sys.stdout)

      # Find the length of the longest parameter set name.
      parameterSetLength = 0
      for parameterSet in config.parameterSets.parameterSetAttributes[name].keys():
        if len(parameterSet) > parameterSetLength: parameterSetLength = len(parameterSet)

      for parameterSet in sorted(config.parameterSets.parameterSetAttributes[name].keys()):
         self.writeFormattedText(parameterSet + ":", config.parameterSets.parameterSetAttributes[name][parameterSet].description, parameterSetLength + 4, 2, '')
      print(file = sys.stdout)

    # Write out all of the gkno options.
    self.gknoOptions(graph, config)

    # List the options available at the pipeline level.
    #
    # Loop over all the allowable arguments and determine if there is a short form and
    # the length of the combined '--argument (-a)' text.
    length            = 0
    arguments         = {}
    optionNodeIDs     = config.nodeMethods.getNodes(graph, 'option')
    requiredArguments = {}
    optionalArguments = {}
    for longFormArgument in config.pipeline.pipelineArguments:
      description       = config.pipeline.pipelineArguments[longFormArgument].description
      shortFormArgument = config.pipeline.pipelineArguments[longFormArgument].shortFormArgument
      configNodeID      = config.pipeline.pipelineArguments[longFormArgument].configNodeID
      text              = longFormArgument + ' (' + shortFormArgument + '):'
      length            = len(text) if (len(text) > length) else length

      # First check if the pipeline requires the argument. If not, check if the tool
      # requires the argument. If the tool has construction instructions, the argument
      # does not need to be listed as required.
      isRequired                  = config.pipeline.pipelineArguments[longFormArgument].isRequired
      hasConstructionInstructions = False
      if not isRequired:

        # Check the tasks.
        if config.pipeline.nodeAttributes[configNodeID].tasks:
          for associatedTask in config.pipeline.nodeAttributes[configNodeID].tasks:
            associatedTool     = config.pipeline.taskAttributes[associatedTask].tool
            associatedArgument = config.pipeline.nodeAttributes[configNodeID].tasks[associatedTask]
            if config.tools.getArgumentAttribute(associatedTool, associatedArgument, 'isRequired'): isRequired = True
            if config.tools.getArgumentAttribute(associatedTool, associatedArgument, 'constructionInstructions'):
              hasConstructionInstructions = True
              break

        # If iSRequired is still False, check for greedy tasks.
        if not isRequired and config.pipeline.nodeAttributes[configNodeID].greedyTasks:
          for associatedTask in config.pipeline.nodeAttributes[configNodeID].greedyTasks:
            associatedTool     = config.pipeline.taskAttributes[associatedTask].tool
            associatedArgument = config.pipeline.nodeAttributes[configNodeID].greedyTasks[associatedTask]
            if config.tools.getArgumentAttribute(associatedTool, associatedArgument, 'isRequired'): isRequired = True
            if config.tools.getArgumentAttribute(associatedTool, associatedArgument, 'constructionInstructions'):
              hasConstructionInstructions = True
              break

      if isRequired and not hasConstructionInstructions: requiredArguments[text] = description
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
    for task in config.pipeline.workflow: length = len(task) if (len(task) > length) else length

    self.getTools(config, jsonFiles, toolConfigurationFilesPath)
    for task in sorted(config.pipeline.workflow):
      associatedTool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      if associatedTool in self.availableTools: isHidden = self.availableTools[associatedTool][1]
      elif associatedTool in self.experimentalTools: isHidden = self.experimentalTools[associatedTool][1]
      if not isHidden: self.writeFormattedText('--' + task + ':', associatedTool, length + 5, 2, '')
    print(file = sys.stdout)
    sys.stdout.flush()

    # Write out all of the values included in the selected parameter set, if there are any.
    if config.parameterSets.getArguments(name, parameterSetName, isPipeline = True): self.writeParameterSets(config, name, parameterSetName)

    # Terminate.
    exit(0)

  # If a pipeline was requested, but no configuration file can be found, add
  # this extra error at the end of the usage information.
  def invalidPipelineMessage(self, pipeline):
    text = 'The requested pipeline \'' + pipeline + '\' does not exist. Use \'gkno --pipeline-categories (-pcat)\' to see all available pipeline ' + \
    'categories. If the category is known, include the category (\'gkno --pipeline-categories (-pcat) [category]\') to see all of the pipelines ' + \
    'available for that category. To see a list of all available pipelines, use \'gkno --all-pipelines (-apo)\''
    self.writeFormattedText('', text, 0, 0, 'ERROR:')
    sys.stdout.flush()

  # If help for a specific tool was requested, but that tool does not exist,
  # print an error after the usage information.
  def invalidToolMessage(self, tool):
    text = 'The requested tool \'' + tool + '\' does not exist. Use \'gkno --tool-categories (-tcat)\' to see all available tool categories. If the ' + \
    'category is known, include the category (\'gkno --tool-categories (-tcat) [category]\') to see all of the tools available for that category. ' + \
    'To see a list of all available tools, use \'gkno --all-tools (-ato)\''
    self.writeFormattedText('', text, 0, 0, 'ERROR:')
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

  # Print usage information on the tool mode of operation.
  def writeToolModeUsage(self, config, admin):
    print('=============', file = sys.stdout)
    print('  tool mode', file = sys.stdout)
    print('=============', file = sys.stdout)
    print(file = sys.stdout)
    print('NOTE: Tools preceded by a \'!\' cannot be used due to the absence of a required executable', file = sys.stdout)
    print('file. To use these tools ensure that the required executables have been succesfully compiled.', file = sys.stdout)
    print(file = sys.stdout)
    print("Usage: gkno <tool name> [options]", file = sys.stdout)
    print(file = sys.stdout)

    # Write the tools to screen.
    toolGroups = {}
    for tool in sorted(self.availableTools.keys()):
      allToolsCompiled = True
      for requiredTool in config.tools.getGeneralAttribute(tool, 'requiredCompiledTools'):
        if requiredTool not in admin.userSettings['compiled tools']: allToolsCompiled = False

      # Get the tool group to which this tool belongs.
      toolGroup = config.tools.getGeneralAttribute(tool, 'helpGroup')
      if toolGroup not in toolGroups: toolGroups[toolGroup] = []

      # If the tool requires tools to be compiled and they are not, prepend the tool name with a '!'. This
      # indicates that the tool is not available.
      toolText = tool if allToolsCompiled else str('!') + tool
      if not self.availableTools[tool][1]: toolGroups[toolGroup].append((tool, toolText))

    sortedGroups = sorted(list(toolGroups.keys()))
    for toolGroup in sortedGroups:
      print('     ', toolGroup, ':', sep = '', file = sys.stdout)
      for tool, toolText in toolGroups[toolGroup]: self.writeFormattedText(toolText + ':', self.availableTools[tool][0], self.toolLength + 5, 2, '')
      print(file = sys.stdout)

    # Now list any tool configuration files that are listed as experimental..
    if self.experimentalTools:
      print('     The following tools have been identified as experimental, so should be used with caution:', file = sys.stdout)
      print(file = sys.stdout)
      for tool in sorted(self.experimentalTools.keys()):
        allToolsCompiled = True
        for requiredTool in config.tools.getGeneralAttribute(tool, 'requiredCompiledTools'):
          if requiredTool not in admin.userSettings['compiled tools']: allToolsCompiled = False
  
        # If the tool requires tools to be compiled and they are not, prepend the tool name with a '!'. This
        # indicates that the tool is not available.
        toolText = tool if allToolsCompiled else str('!') + tool
        if not self.experimentalTools[tool][1]: self.writeFormattedText(toolText + ':', self.experimentalTools[tool][0], self.toolLength + 5, 2, '')
      print(file = sys.stdout)

    # Now list any tool configuration files that have errors.
    if self.failedTools:
      print('     The following tools have malformed configuration files, so are currently unusable:', file = sys.stdout)
      print(file = sys.stdout)
      for tool in sorted(self.failedTools.keys()):
        self.writeFormattedText(tool + ':', self.failedTools[tool], self.toolLength + 5, 2, '')
      print(file = sys.stdout)
 
    # Terminate.
    exit(0)

  # Print usage information on the pipeline mode of operation.
  def writePipelineModeUsage(self, config):
    print('=================', file = sys.stdout)
    print('  pipeline mode', file = sys.stdout)
    print('=================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe <pipeline name> [options]', file = sys.stdout)
    print(file = sys.stdout)

    # Write the pipelines to screen.
    sortedPipelines = sorted(list(self.availablePipelines.keys()))
    for pipeline in sortedPipelines: self.writeFormattedText(pipeline + ':', self.availablePipelines[pipeline][0], self.pipelineLength + 5, 2, '')
    print(file = sys.stdout)

    # Write the developmental pipelines to screen.
    if self.developmentalPipelines:
      print('     The following pipelines have been identified as developmental, so should be used with caution:', file = sys.stdout)
      print(file = sys.stdout)
      for pipeline in sorted(self.developmentalPipelines.keys()):
         self.writeFormattedText(pipeline + ':', self.developmentalPipelines[pipeline], self.pipelineLength + 5, 2, '')
      print(file = sys.stdout)

    # Now list any pipeline configuratiobn files that have errors.
    if self.failedPipelines:
      print('     The following pipelines have malformed configuration files, so are currently unusable:', file = sys.stdout)
      print(file = sys.stdout)
      for pipeline in sorted(self.failedPipelines.keys()):
        self.writeFormattedText(pipeline + ':', self.failedPipelines[pipeline], self.pipelineLength + 5, 2, '')
      print(file = sys.stdout)

    # Terminate.
    exit(0)

  # If an admin mode's help was requested.
  def selectAdminModeUsage(self, admin):
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

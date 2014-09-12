#!/usr/bin/python

from __future__ import print_function

import gknoErrors
from gknoErrors import *

import os
import sys

class helpClass:
  def __init__(self):

    # Record whether help is required.
    self.writeHelp = False

    # Suppress writing out header.
    self.suppressHeader = False

    # Store if all tools/pipelines are to be written to screen.
    self.allTools     = False
    self.allPipelines = False

    # Decide if help is required for tools/pipelines or all.
    self.toolHelp     = False
    self.pipelineHelp = False

    # Keep track of whether help on a specific pipeline was requested.
    self.specificPipelineHelp = False

    # Determine if the help is sorted at the category or tool level.
    self.helpCategories = False

    # Store if help on admin features was requested.
    self.adminHelp = False

    # Store information on available categories and groups.
    self.availableToolCategories     = {}
    self.availableToolGroups         = {}
    self.availablePipelineCategories = {}

    # Store the category for which constituent tools/pipelines should be printed.
    self.requestedCategory = None

    # Store information on the available tools and pipelines.
    self.availablePipelines   = {}
    self.availableTools       = {}
    self.invalidPipeline      = False
    self.invalidTool          = False
    self.pipelineLength       = 0
    self.toolLength           = 0

    # Keep track of tools with malformed configuration files.
    self.failedTools     = {}
    self.failedPipelines = {}

    # Keep track of experimental tools and pipelines.
    self.experimentalTools      = {}
    self.developmentalPipelines = {}

    # Define the errors class.
    self.errors = gknoErrors()

    # Define the allowed tool/pipeline categories and groups.
    self.defineToolCategories()
    self.definePipelineCategories()

  # Define allowed tool categories.
  def defineToolCategories(self):
    self.allowedToolCategories = {}

    self.allowedToolCategories['Aligners']                = 'Read aligners/mappers.'
    self.allowedToolCategories['Annotation']              = 'Functional annotation of genetic variants.'
    self.allowedToolCategories['Bamtools']                = 'Tools included in the Bamtools library.'
    self.allowedToolCategories['BAM-processing']          = 'Tools for manipulating BAM files.'
    self.allowedToolCategories['BWA']                     = 'BWA mapping and file processing.',
    self.allowedToolCategories['FASTA-processing']        = 'Tools for processing FASTA files.'
    self.allowedToolCategories['FASTQ-processing']        = 'Tools for processing FASTQ files.'
    self.allowedToolCategories['Genome-regions']          = 'Tools to manipulate genome region coordinates.'
    self.allowedToolCategories['General-file-processing'] = 'Tools for processing files.'
    self.allowedToolCategories['Jellyfish']               = 'Jellyfish package tools.'
    self.allowedToolCategories['Kmer-processing']         = 'Tools for processing kmers.'
    self.allowedToolCategories['Marthlab-software']       = 'Tools developed in the lab of Gabor Marth.'
    self.allowedToolCategories['Michigan-software']       = 'Tools developed at the University of Michigan.'
    self.allowedToolCategories['Mosaik']                  = 'Mosaik mapping and file processing.'
    self.allowedToolCategories['Rufus']                   = 'Rufus genome comparison and variant discovery.'
    self.allowedToolCategories['Scripts']                 = 'Scripts for a variety of tasks.'
    self.allowedToolCategories['Short-variant-discovery'] = 'Detection of short variants.'
    self.allowedToolCategories['Simulation']              = 'Generation and processing simulated data.'
    self.allowedToolCategories['SV-discovery']            = 'Detection of structural variants.'
    self.allowedToolCategories['Tangram']                 = 'Tangram MEI detection package.'
    self.allowedToolCategories['Variant-discovery']       = 'Detection of all classes of variants.'
    self.allowedToolCategories['Variant-graph']           = 'Alignment and detection using a variant graph.'
    self.allowedToolCategories['vcflib'        ]          = 'vcflib VCF processing tool kit.',
    self.allowedToolCategories['VCF-processing']          = 'Tools used for processing VCF files.'
    self.allowedToolCategories['Visualisation']           = 'Visualisation and plotting tools.'

  # Define allowed pipeline categories.
  def definePipelineCategories(self):
    self.allowedPipelineCategories = {}

    self.allowedPipelineCategories['1000G-pipelines']   = 'Analyses performed similarly to 1000 Genomes project analyses.'
    self.allowedPipelineCategories['BAM-processing']    = 'Pipelines primarily focused on manipulating BAM files.'
    self.allowedPipelineCategories['Alignment']         = 'Read alignment tasks are performed as part of the pipeline.'
    self.allowedPipelineCategories['FASTA-processing']  = 'Pipelines involving manipulation of reference FASTA files.'
    self.allowedPipelineCategories['Reference-free']    = 'Analysis of genomes without use of the genome reference.'
    self.allowedPipelineCategories['Simulation']        = 'Simulation-based pipelines.'
    self.allowedPipelineCategories['SV-discovery']      = 'Pipelines including detection of structural variations.'
    self.allowedPipelineCategories['Variant-discovery'] = 'Pipelines including variant discovery tasks.'
    self.allowedPipelineCategories['Variant-graph']     = 'Alignments using a variant graph are incorporated.'
    self.allowedPipelineCategories['Visualisation']     = 'Visualisation and plotting pipelines.'

  # Check if help has been requested on the command line.  Search for the '--help'
  # or '-h' arguments on the command line.
  def checkForHelp(self, graph, config, gknoConfig, isPipeline, runName, admin, mode, toolConfigurationFilesPath, pipelineConfigurationFilesPath, parameterSetName):

    # Check if tool or pipeline categories should be displayed.
    for counter, argument in enumerate(sys.argv[1:]):

      # Check the next argument on the command line.
      try: nextArgument = sys.argv[counter + 2]
      except: nextArgument = None

      # Look to see if tool/pipeline categories are to be displayed.
      if argument == '--tool-categories' or argument == '-tcat':
        self.writeHelp         = True
        self.toolHelp          = True
        self.helpCategories    = True
        self.requestedCategory = nextArgument
      elif argument == '--pipeline-categories' or argument == '-pcat':
        self.writeHelp         = True
        self.pipelineHelp      = True
        self.helpCategories    = True
        self.requestedCategory = nextArgument
      elif argument == '--all-tools' or argument == '-ato':
        self.writeHelp = True
        self.toolHelp  = True
        self.allTools  = True
      elif argument == '--all-pipelines' or argument == '-apo':
        self.writeHelp    = True
        self.pipelineHelp = True
        self.allPipelines = True

    # If gkno is in pipeline mode, but no pipeline name was supplied, write out all pipeline 
    # categories.
    if isPipeline and (not runName or runName == '-h' or runName == '--help'):
      self.pipelineHelp   = True
      self.helpCategories = True

    # If gkno is in the help mode, set the writeHelp flag.
    if mode == 'help': self.writeHelp = True

    # Process the particular help required.
    if self.writeHelp:

      # If the help requires info from all tools or pipelines, get the necessary data.
      if self.toolHelp or mode == 'tool': self.getTools(config, gknoConfig, toolConfigurationFilesPath)
      if self.pipelineHelp and mode != 'pipeline': self.getPipelines(config, gknoConfig, pipelineConfigurationFilesPath)
  
      # If all tools or pipelines  are to written to screen.
      if self.allTools: self.writeToolModeUsage(config, admin)
      if self.allPipelines: self.writePipelineModeUsage(config)

      # Write out all available tool or pipeline categories.
      if self.helpCategories:
        if self.toolHelp and not self.requestedCategory: self.writeToolCategories()
        if self.pipelineHelp and not self.requestedCategory: self.writePipelineCategories()
  
        # Write out tools/pipelines within a category.
        if self.requestedCategory:
          if self.toolHelp: self.writeCategory(self.toolHelp, self.allowedToolCategories, self.requestedCategory)
          else: self.writeCategory(self.toolHelp, self.allowedPipelineCategories, self.requestedCategory)
        exit(0)

      # If the requested tool/pipeline is invalid.      
      if self.invalidPipeline:
        self.invalidPipelineMessage(runName)
        exit(0)
      if self.invalidTool:
        self.invalidToolMessage(runName)
        exit(0)

      # Write out help for a specific tool. If help on a specific pipeline is requested, this will be processed
      # after the pipeline has been built. Certain information (e.g. the workflow), need to be determined prior
      # to printing out help.
      if mode == 'tool':
        self.writeSpecificToolUsage(graph, config, gknoConfig, runName, toolConfigurationFilesPath, parameterSetName)
        exit(0)
      if isPipeline:
        self.specificPipelineHelp = True
        return

      # If general help is required, write out top level help.
      self.writeGeneral(admin)

  # Write general help.
  def writeGeneral(self, admin):
    print('The gkno package can be run in three different modes:', file=sys.stdout)
    print('     ADMIN mode:     lets you manage gkno itself', file = sys.stdout)
    print('     TOOL mode:      runs a single tool', file=sys.stdout)
    print('     PIPE mode:      runs a predetermined pipeline of tools', file=sys.stdout)
    print(file = sys.stdout)
    print('See below for usage instructions for each mode.', file = sys.stdout)
    print(file = sys.stdout)

    # Write out admin help.
    self.writeAdminModeUsage(admin)

    # Write out tool usage information.
    self.writeToolUsage()

    # Write out pipeline usage information.
    self.writePipelineUsage()

    # Terminate gkno.
    exit(0)

  # Get information on all avilable tools and pipelines.
  def getTools(self, config, gknoConfig, toolConfigurationFilesPath):

    # Some tools may have malformed configuration files. Instead of failing when those files are
    # processed, the failed tools are logged and are noted in the help.
    self.failedTools = {}

    # Open each tool file, check that it is a valid json file and get the tool description and
    # whether the tool is hidden.
    for filename in gknoConfig.jsonFiles['tools']:
      filePath           = toolConfigurationFilesPath + filename
      tool               = filename[:len(filename) - 5]

      # Open the tool configuration file and process the data.
      openFileSuccess = True
      try: configurationData = config.fileOperations.readConfigurationFile(filePath, allowTermination = False)
      except:
        openFileSuccess = False
        self.failedTools[tool] = 'Description could not be found'

      # If the configuration file is a valid json file, try and process the file.
      if not configurationData:
        openFileSuccess = False
        self.failedTools[tool] = 'Description could not be found'

      if openFileSuccess:
        try: success = config.tools.processConfigurationData(tool, configurationData, self.allowedToolCategories, allowTermination = False)
        except: success = False
        if success:
          description    = config.tools.getGeneralAttribute(tool, 'description')
          isHidden       = config.tools.getGeneralAttribute(tool, 'isHidden')
          isExperimental = config.tools.getGeneralAttribute(tool, 'isExperimental')
          categories     = config.tools.getGeneralAttribute(tool, 'categories')

          # Store information on categories and groups.
          for category in categories:
            if category not in self.availableToolCategories: self.availableToolCategories[category] = {}
            self.availableToolCategories[category][tool] = description

          # Store experimental tools separately from stable tools.
          if isExperimental: self.experimentalTools[tool] = (description, isHidden)
          else: self.availableTools[tool] = (description, isHidden)
        else:
          description = 'Configuration file could not be processed.'
          self.failedTools[tool] = description

      # For the purposes of formatting the screen output, find the longest tool
      # name and use this to define the format length.
      if len(tool) > self.toolLength: self.toolLength = len(tool)

  # Get information on pipelines.
  def getPipelines(self, config, gknoConfig, pipelineConfigurationFilesPath):

    # Some tools may have malformed configuration files. Instead of failing when those files are
    # processed, the failed tools are logged and are noted in the help.
    self.failedPipelines = {}

    # Open each pipeline file, check that it is a valid json file and get the pipeline description and
    # whether the tool is hidden.
    for filename in gknoConfig.jsonFiles['pipelines']:
      filePath = pipelineConfigurationFilesPath + filename
      pipeline = filename[:len(filename) - 5]

      # Open the pipeline configuration file and process the data.
      openFileSuccess = True
      try: configurationData = config.fileOperations.readConfigurationFile(filePath)
      except:
        openFileSuccess = False
        self.failedPipelines[pipeline] = 'Description could not be found.'

      if openFileSuccess:
        config.pipeline.clearPipeline()
        success = config.pipeline.processConfigurationData(configurationData, pipeline, gknoConfig.jsonFiles['tools'], self.allowedPipelineCategories, allowTermination = False)

        try: description = config.pipeline.getPipelineAttribute('description')
        except: description = 'Description could not be found.'
        if description == '' or description == None: description = 'Description could not be found.'

        # If the pipeline is listed as developmental, store the pipeline separately.
        if success:
          if not config.pipeline.getPipelineAttribute('isHiddenInHelp'):
            categories = config.pipeline.getPipelineAttribute('categories')
            if config.pipeline.getPipelineAttribute('isDevelopmental'): self.developmentalPipelines[pipeline] = description
            else: self.availablePipelines[pipeline] = (description, categories)

            # Store information on categories and groups.
            for category in categories:
              if category not in self.availablePipelineCategories: self.availablePipelineCategories[category] = {}
              self.availablePipelineCategories[category][pipeline] = description

        else: self.failedPipelines[pipeline] = description

      # For the purposes of formatting the screen output, find the longest tool
      # name and use this to define the format length.
      if len(pipeline) > self.pipelineLength: self.pipelineLength = len(pipeline)

  # Print usage information on the admin mode of operation.
  def writeAdminModeUsage(self, admin):
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

  # Print out tool usage.
  def writeToolUsage(self):
    print('===================', file = sys.stdout)
    print('  gkno tool usage', file = sys.stdout)
    print('===================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno [tool] [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    text = 'All tools in gkno are classified according to a category and a group. For example, tools that process a certain file format, e.g. BAM, ' + \
    'may be grouped into a category \'BAM-processing\'. Help groups are used to collect tools from a common library or source. To see a list of all ' + \
    'tool categories, use the command:'
    self.writeFormattedText('', text, 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --tool-categories (-tcat)', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'To see a list of all tools in a category, type:', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --tool-categories (-tcat) [category]', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'Similarly, replacing \'--tool-categories (-tcat)\' with \'--tool-groups (-tgr)\' will display the available groups.', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'To see all available tools, type:', 0, 1, '')
    self.writeFormattedText('', '\t', 0, 1, '')
    self.writeFormattedText('', 'gkno --all-tools (-ato)', 0, 2, '')
    self.writeFormattedText('', '\t', 0, 1, '')

  # Print out tool usage.
  def writePipelineUsage(self):
    print('=======================', file = sys.stdout)
    print('  gkno pipeline usage', file = sys.stdout)
    print('=======================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno pipe [pipeline] [options]', sep = '', file = sys.stdout)
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

  # Print out info on tool categories.
  def writeToolCategories(self):
    if not self.suppressHeader:
      print('====================', file = sys.stdout)
      print('gkno tool categories', file = sys.stdout)
      print('====================', file = sys.stdout)
      print(file = sys.stdout)
      text = 'Following is a list of tool categories. To see all of the tools in a specific category, use the command line: \'gkno -tool-categories ' + \
      ' <category>\''
      self.writeFormattedText('', text, 0, 1, '')
      self.writeFormattedText('', '\t', 0, 1, '')

    length = 0
    for category in self.allowedToolCategories.keys():
      if len(category) > length: length = len(category)

    for category in sorted(self.allowedToolCategories.keys()):
      description   = self.allowedToolCategories[category]
      printCategory = category + ": "
      self.writeFormattedText(printCategory, description, length + 2, 2, '')

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

    # Check that the requested category is valid.
    if category not in allowedCategories:
      self.invalidCategory(isToolHelp, allowedCategories, category)
      exit(0)

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

  # If the requested category is not available, write out the available categories.
  def invalidCategory(self, isToolHelp, allowedCategories, category):

    # Suppress writing the header when writing available categories.
    self.suppressHeader = True

    # Define text for the output message.
    runType         = 'tool' if isToolHelp else 'pipeline'
    self.writeFormattedText('', 'The requested category \'' + category + '\' is not valid. The available ' + runType + ' categories are:', 0, 1, '')
    print(file = sys.stdout)
    if isToolHelp: self.writeToolCategories()
    else: self.writePipelineCategories()

  # Print out tool usage.
  def writeSpecificToolUsage(self, graph, config, gknoConfig, tool, toolConfigurationFilesPath, parameterSetName):
    print('===================', file = sys.stdout)
    print('  gkno tool usage', file = sys.stdout)
    print('===================', file = sys.stdout)
    print(file = sys.stdout)
    print('Usage: gkno ', tool, ' [options]', sep = '', file = sys.stdout)
    print(file = sys.stdout)

    # Print out the tool description.
    print('     Description:', file = sys.stdout)
    try: self.writeFormattedText(self.availableTools[tool][0], ' ', 20, 2, ' ')
    except:
      try: self.writeFormattedText(self.experimentalTools[tool][0], ' ', 2, 2, ' ')
      except: self.errors.problemWithTool(tool)
    print(file = sys.stdout)
    sys.stdout.flush()

    # If this pipeline has different parameter sets, print them to screen.
    self.getParameterSets(config, gknoConfig, toolConfigurationFilesPath, '', 'tool', tool)
    if config.parameterSets.parameterSetAttributes[tool]:

      # Determine the longest parameter set name.
      parameterSetLength = 0
      for parameterSet in config.parameterSets.parameterSetAttributes[tool].keys():
        if len(parameterSet) > parameterSetLength: parameterSetLength = len(parameterSet)

      print('     Parameter sets:', file = sys.stdout)
      for parameterSet in sorted(config.parameterSets.parameterSetAttributes[tool].keys()):
        self.writeFormattedText(parameterSet + ":", config.parameterSets.parameterSetAttributes[tool][parameterSet].description, parameterSetLength + 4, 2, '')
      print(file = sys.stdout)

    # Write out all of the gkno options.
    self.gknoOptions(graph, config)

    # Sort the arguments by the argument group.
    arguments      = {}
    argumentLength = 0
    for longFormArgument in config.tools.argumentAttributes[tool].keys():
      if not config.tools.getArgumentAttribute(tool, longFormArgument, 'hideInHelp'):
        shortFormArgument = config.tools.getArgumentAttribute(tool, longFormArgument, 'shortFormArgument')
        argumentGroup     = config.tools.getArgumentAttribute(tool, longFormArgument, 'argumentGroup')
        isRequired        = config.tools.getArgumentAttribute(tool, longFormArgument, 'isRequired')

        # Check if this argument has construction instructions. If so, this does not need to be listed as
        # required.
        if config.tools.getArgumentAttribute(tool, longFormArgument, 'constructionInstructions'): isRequired = False
        if argumentGroup not in arguments: arguments[argumentGroup] = {}
        arguments[argumentGroup][longFormArgument] = (shortFormArgument, isRequired)

        # Compare the argument length to others in all groups.
        if (len(longFormArgument) + len(shortFormArgument)) > argumentLength: argumentLength = len(longFormArgument) + len(shortFormArgument)

    # Print out all the input files.
    if 'inputs' in arguments: self.writeToolArguments(config, tool, 'Input files', arguments.pop('inputs'), argumentLength)
    if 'outputs' in arguments: self.writeToolArguments(config, tool, 'Output files', arguments.pop('outputs'), argumentLength)
    for group in arguments: self.writeToolArguments(config, tool, group, arguments[group], argumentLength)

    # Write out all of the values included in the selected parameter set, if there are any.
    if config.parameterSets.getArguments(tool, parameterSetName, isPipeline = False): self.writeParameterSets(config, tool, parameterSetName)

  # Print out arguments.
  def writeToolArguments(self, config, tool, argumentGroup, arguments, length):
    print('     ', argumentGroup, ':', sep = '', file = sys.stdout)

    sortedArguments = sorted(arguments.keys())
    if sortedArguments:
      for longFormArgument in sortedArguments:
        shortFormArgument = arguments[longFormArgument][0]
        isRequired        = arguments[longFormArgument][1]
        argumentText      = longFormArgument + ' (' + shortFormArgument + '):'
        description       = config.tools.getArgumentAttribute(tool, longFormArgument, 'description')
        dataType          = config.tools.getArgumentAttribute(tool, longFormArgument, 'dataType')
        if isRequired: description += ' [REQUIRED]'
        self.writeFormattedText(argumentText, description, length + 5, 2, dataType)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Get parameter set information.
  def getParameterSets(self, config, gknoConfig, toolConfigurationFilesPath, pipelineConfigurationFilesPath, mode, name):

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
    config.parameterSets.checkParameterSets(name, configurationData['parameter sets'], isPipeline, isExternal = False)

    # Now get any external parameter sets.
    if externalFilename + '.json' in gknoConfig.jsonFiles[text]:
      configurationData = config.fileOperations.readConfigurationFile(externalFilePath)
      config.parameterSets.checkParameterSets(name, configurationData['parameter sets'], isPipeline, isExternal = True)

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
  def writeSpecificPipelineUsage(self, graph, config, gknoConfig, name, toolConfigurationFilesPath, parameterSetName):
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

    self.getTools(config, gknoConfig, toolConfigurationFilesPath)
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

    # Sort all of the pipelines into their groups.
    pipelineGroups = {}
    for pipeline in self.availablePipelines.keys():

      # Get the pipeline group to which this tool belongs.
      pipelineGroup = self.availablePipelines[pipeline][1]
      if pipelineGroup not in pipelineGroups: pipelineGroups[pipelineGroup] = []
      pipelineGroups[pipelineGroup].append(pipeline)
    sortedGroups = sorted(list(pipelineGroups.keys()))

    # Write the pipelines to screen.
    for pipelineGroup in sortedGroups:
      print('     ', pipelineGroup, ':', sep = '', file = sys.stdout)
      for pipeline in pipelineGroups[pipelineGroup]:
        self.writeFormattedText(pipeline + ':', self.availablePipelines[pipeline][0], self.pipelineLength + 5, 2, '')
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

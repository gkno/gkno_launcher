#!/usr/bin/python

from __future__ import print_function
from difflib import SequenceMatcher

import helpErrors as err
import stringOperations as so
import pipelineConfiguration as pc
import parameterSets as ps

import os
import sys
import textwrap

class helpInformation:
  def __init__(self, commitID, date, version):

    # Define the errors class.
    self.errors = err.helpErrors()

    # Store version information.
    self.commitID = commitID
    self.date     = date 
    self.version  = version

    # Define allowed help categories.
    self.helpCategories                      = {}
    self.helpCategories['1000G-pipelines']   = 'Analyses performed similarly to 1000 Genomes project analyses.'
    self.helpCategories['Alignment']         = 'Read alignment tasks are performed as part of the pipeline.'
    self.helpCategories['BAM-processing']    = 'Pipelines primarily focused on manipulating BAM files.'
    self.helpCategories['FASTA-processing']  = 'Pipelines involving manipulation of reference FASTA files.'
    self.helpCategories['kmer-processing']   = 'Perform analyses involving the processing of kmers.'
    self.helpCategories['Reference-free']    = 'Analysis of genomes without use of the genome reference.'
    self.helpCategories['R']                 = 'R scripts for all manner of statistical calculations.'
    self.helpCategories['Scripts']           = 'Scripts to perform many commonly performed tasks.'
    self.helpCategories['Simulation']        = 'Simulation-based pipelines.'
    self.helpCategories['SV-discovery']      = 'Pipelines including detection of structural variations.'
    self.helpCategories['Variant-discovery'] = 'Pipelines including variant discovery tasks.'
    self.helpCategories['Variant-graph']     = 'Alignments using a variant graph are incorporated.'
    self.helpCategories['VCF-processing']    = 'Process VCF files.'
    self.helpCategories['Visualisation']     = 'Visualisation and plotting pipelines.'

    # Create a text wrapper object to handle writing strings to a fixed width screen.
    self.wrap = textwrap.TextWrapper(initial_indent = '   ')

    # Define the maximum width of a line. THis will be modified by including tabs.
    self.width = 150

  # Provide general help.
  def generalHelp(self, mode, category, admin, path):

    # if information on help categories was requested, provide that information.
    if mode == 'categories':
      if category == None: self.writeHelpCategories()
      else: self.specificHelpCategory(category, path)

    elif mode == 'list-all': self.listAllPipelines(path)

    # Otherwise, provide general help.
    else:
      print(file = sys.stdout)
      self.writeSimpleLine('The gkno package can be run in the following modes:', isIndent = False, noLeadingTabs = 0)
      self.writeSimpleLine('ADMIN mode:    allows management of gkno and it\'s resources,', isIndent = False, noLeadingTabs = 1)
      self.writeSimpleLine('PIPELINE mode: executes a predetermined pipeline', isIndent = False, noLeadingTabs = 1)
      print(file = sys.stdout)
      self.writeSimpleLine('See below for usage instructions for each mode.', isIndent = False, noLeadingTabs = 0)
      print(file = sys.stdout)
  
      # Write out admin help.
      self.adminModeUsage(admin)
  
      # Write out pipeline usage information.
      self.pipelineUsage()

    # Terminate gkno.
    exit(0)

  # Write out the version number and date at the start of the message.
  def printHeader(self):
    print(file = sys.stdout)
    commitLength = len(self.commitID) + 18
    length       = max(commitLength, 29)
    self.writeSimpleLine('=' * length, isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('University of Utah gkno package', isIndent = True, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('version:    ' + self.version, isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('date:       ' + self.date, isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('git commit: ' + self.commitID, isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('=' * length, isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

  # Print out all of the available help categories.
  def writeHelpCategories(self):
    self.writeSimpleLine('==============================', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('gkno pipeline categories', isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('==============================', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('All available pipelines are organised into the following categories:', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

    # List all of the categories with their descriptions.
    length = len(max(self.helpCategories.keys(), key = len)) + 3
    for category in sorted(self.helpCategories.keys()):
      self.writeComplexLine([category + ':', self.helpCategories[category]], [length, 0], noLeadingTabs = 1)

    print(file = sys.stdout)
    self.writeSimpleLine('To see all of the pipelines in a specific category, use the command line:', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('gkno --categories <category>', isIndent = True, noLeadingTabs = 0)
    print(file = sys.stdout)

  # Print out informatino on a specific help category.
  def specificHelpCategory(self, providedCategory, path):
    self.writeSimpleLine('==========================', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('gkno help categories', isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('==========================', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

    # Check that the requested category is valid. If not, find the closest category to that written.
    category = providedCategory
    if providedCategory not in self.helpCategories:
      rankedList = so.rankListByString(self.helpCategories, category)
      category   = rankedList[0]

    # Open all the pipeline and determine the categories they fall into.
    categories, descriptions = self.findPipelinesInCategories(path)

    self.writeSimpleLine('Following is a list of pipelines in the category \'' + category + '\':', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

    # If there are no pipelines in the category, write this out.
    try: pipelines = categories[category]
    except:
      self.writeSimpleLine('The requested category (' + category + ') does not contain any pipelines.', isIndent = True, noLeadingTabs = 0)
      print(file = sys.stdout)

    # Write out the pipelines that fall into the category.
    else:

      # Get all the pipelines and their descriptions.
      length = len(max(pipelines, key = len)) + 3
      for pipeline in sorted(pipelines):
        self.writeComplexLine([pipeline + ':', descriptions[pipeline]], [length, 0], noLeadingTabs = 1)
      print(file = sys.stdout)

    # If the entered category did not exactly match one of the supplied categories, provide
    # a warning that the provided list was based on the assumed most likely category.
    if providedCategory not in self.helpCategories: self.invalidCategory(providedCategory, category)

  # Loop over all the pipeline and identify the categories they belong to.
  def findPipelinesInCategories(self, path):
    categories   = {}
    descriptions = {}
    for filename in os.listdir(path):
      if filename.endswith(".json"):
        pipeline = pc.pipelineConfiguration(allowTermination = False)
        success  = pipeline.getConfigurationData(path + '/' + filename)

        # Store the pipeline description if the pipeline is not developmental.
        if success and not pipeline.isDevelopment:
          descriptions[pipeline.name] = pipeline.description

          # Loop over the categories and populate the data structure.
          for category in pipeline.categories:

            # Check that the category is allowed.
            if category not in self.helpCategories: self.errors.invalidCategory(pipeline.name, category, self.helpCategories)
            if category not in categories: categories[str(category)] = [str(pipeline.name)]
            else: categories[str(category)].append(str(pipeline.name))

    # Return the dictionary containing all the tools connected to each category.
    return categories, descriptions

  # If the requested category is not available, write out the available categories.
  def invalidCategory(self, providedCategory, category):

    # Define text for the output message.
    self.writeSimpleLine('===============', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('    WARNING    ', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('===============', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('The requested category \'' + providedCategory + '\' is invalid. The pipelines shown are those available in the \'' + \
    category + '\' category. If this was not the desired category, please remove the category name from the command line to see a full list ' + \
    'of the available categories.', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

  # List all available pipelines.
  def listAllPipelines(self, path):
    self.writeSimpleLine('========================', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('all gkno pipelines', isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('========================', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('Following is a list of all of the pipelines currently available:', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

    # Get the names and descriptions for all the pipelines.
    descriptions    = {}
    failedPipelines = []
    for filename in os.listdir(path):
      if filename.endswith(".json"):
        pipeline                  = pc.pipelineConfiguration()
        pipeline.allowTermination = False
        success                   = pipeline.getConfigurationData(path + '/' + filename)

        # If the pipeline configuration was successfully parsed, get and store the description if the pipeline
        # is not developmental.
        if success:
          if not pipeline.isDevelopment: descriptions[pipeline.name] = pipeline.description

        # If there are errors with the pipeline configuration file, mark it as having errors.
        else: failedPipelines.append(pipeline.name)

    # Write out all the pipelines with their descriptions.
    length = len(max(descriptions.keys(), key = len)) + 3
    for pipeline in sorted(descriptions): self.writeComplexLine([pipeline + ':', descriptions[pipeline]], [length, 0], noLeadingTabs = 1)
    print(file = sys.stdout)

    # Now list all of the pipelines for which there exists a configuration file, but it has errors.
    if failedPipelines:
      self.writeSimpleLine('Following is a list of pipelines with malformed configuration files. These cannot be executed without first ' + \
      'fixing the files. The pipeilne can be run to give a detailed description of the errors:', isIndent = False, noLeadingTabs = 0)
      print(file = sys.stdout)
      length = len(max(failedPipelines, key = len)) + 3
      for pipeline in sorted(failedPipelines): self.writeComplexLine([pipeline], [length], noLeadingTabs = 1)
      #print(file = sys.stdout)

  # Print usage information on the admin mode of operation.
  def adminModeUsage(self, admin):
    self.writeSimpleLine('================', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('=  admin mode  =', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('================', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('Usage: gkno <admin operation> [options]', isIndent = True, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('<admin operation>:', isIndent = True, noLeadingTabs = 1)

    # For the purposes of formatting the screen output, find the longest admin
    # operation name and use this to define the format length.
    length = len(max(admin.allModes, key = len)) + 3

    # Loop over all modes, build each line to print and then print to screen..
    for mode in admin.allModes: self.writeComplexLine([mode + ':', admin.modeDescriptions[mode]], [length, -1], noLeadingTabs = 3)
    print(file = sys.stdout)

  # Print out how to use pipelines.
  def pipelineUsage(self):
    self.writeSimpleLine('=======================', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('= gkno pipeline usage =', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('=======================', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('Usage: gkno [pipeline] [options]', isIndent = True, noLeadingTabs = 0)
    print(file = sys.stdout)

    self.writeSimpleLine('All pipelines are classified by category. To see a list of the available categories, type:', isIndent = True, \
    noLeadingTabs = 1)
    self.writeSimpleLine('gkno --categories (-cat)', isIndent = False, noLeadingTabs = 4)
    print(file = sys.stdout)
    self.writeSimpleLine('To see a list of all pipelines contained in a category, type:', isIndent = False, noLeadingTabs = 2)
    self.writeSimpleLine('gkno --categories (-cat) [category]', isIndent = False, noLeadingTabs = 4)
    print(file = sys.stdout)
    self.writeSimpleLine('To see a list of all available pipelines, type:', isIndent = False, noLeadingTabs = 2)
    self.writeSimpleLine('gkno --all-pipelines (-api)', isIndent = False, noLeadingTabs = 4)
    print(file = sys.stdout)

  # Print out help on gkno arguments.
  def gknoArgumentHelp(self, arguments):
    print(file = sys.stdout)
    self.writeSimpleLine('==================', isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('= gkno arguments =', isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine('==================', isIndent = True, noLeadingTabs = 0)
    print(file = sys.stdout)
    text = 'There is a set of arguments that can be applied to all gkno pipelines. The operation of these arguments are explained below:'
    self.writeSimpleLine(text, isIndent = True, noLeadingTabs = 1)
    print(file = sys.stdout)

    # Loop over the arguments.
    argumentStrings = []
    dataTypes       = []
    descriptions    = []
    for argument in arguments:
      argumentStrings.append(argument + ' (' + arguments[argument].shortFormArgument + '):')
      dataTypes.append(arguments[argument].dataType)
      descriptions.append(arguments[argument].description)

    # Find the maximum length of an argument string.
    argumentStringLength = len(max(argumentStrings, key = len)) + 3
    dataTypeLength       = len(max(dataTypes, key = len)) + 3
    lengths              = [argumentStringLength, dataTypeLength, 0]

    # Print out the arguments.
    zipped = zip(argumentStrings, dataTypes, descriptions)
    zipped.sort()
    for argument, dataType, description in zipped: self.writeComplexLine([argument, dataType, description], lengths, noLeadingTabs = 3)

    # Terminate gkno.
    exit(0)

  # If help with a specific pipeline was requested, write out all of the commands available
  # for the requested pipeline.
  def pipelineHelp(self, superpipeline, graph, arguments):

    # Write out general header information.
    print(file = sys.stdout)
    self.writeSimpleLine((len(superpipeline.pipeline) + 28) * '=', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine('gkno pipeline usage - ' + superpipeline.pipeline, isIndent = True, noLeadingTabs = 0)
    self.writeSimpleLine((len(superpipeline.pipeline) + 28) * '=', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)
    self.writeSimpleLine('Usage: gkno ' + superpipeline.pipeline + ' [options]', isIndent = False, noLeadingTabs = 0)
    print(file = sys.stdout)

    # Print out the decription of the pipeline.
    self.writeSimpleLine('Description:', isIndent = False, noLeadingTabs = 0)
    self.writeSimpleLine(superpipeline.pipelineConfigurationData[superpipeline.pipeline].description, isIndent = False, noLeadingTabs = 1)
    print(file = sys.stdout)

    # Write out the pipeline workflow.
    self.writeSimpleLine('Workflow:', isIndent = False, noLeadingTabs = 0)
    length = len(max(graph.workflow, key = len)) + 3
    for task in graph.workflow:
      tool        = superpipeline.tasks[task]
      description = superpipeline.toolConfigurationData[tool].description
      self.writeComplexLine([task + ':', description + ' [Tool: ' + tool + ']'], [length, 0], noLeadingTabs = 1)
    print(file = sys.stdout)

    # List all the available parameter sets.
    parameterSets = superpipeline.pipelineConfigurationData[superpipeline.pipeline].getParameterSetNames()
    if parameterSets:
      self.writeSimpleLine('Parameter sets:', isIndent = False, noLeadingTabs = 0)

      # Loop over the parameter sets and get their descriptions.
      length = len(max(parameterSets, key = len)) + 3
      for parameterSet in parameterSets:
        description = superpipeline.pipelineConfigurationData[superpipeline.pipeline].getParameterSetDescription(parameterSet)
        self.writeComplexLine([parameterSet + ':', description], [length, 0], noLeadingTabs = 1)
      print(file = sys.stdout)

    # Loop over all of the available arguments.
    argumentHelp    = {}
    argumentLengths = {}
    for argument in arguments:

      # If this argument was imported from a constituent tool, check to see if the tool highlights this
      # argument as hidden from the user.
      hideInHelp = False
      if arguments[argument].isImported:
        task       = arguments[argument].importedFromTask
        tool       = graph.getGraphNodeAttribute(task, 'tool')
        toolData   = superpipeline.getToolData(tool)
        hideInHelp = toolData.getArgumentAttribute(argument, 'hideInHelp')

      # Only process arguments for the top level pipeline (e.g. not for arguments that include
      # the address of the tool/pipeline that they point to). Also, do not include arguments that
      # have been marked in the configuration file as not to be included in the help message.
      if '.' not in argument and not arguments[argument].hideInHelp and not hideInHelp:
        graphNodeIds      = arguments[argument].graphNodeIds
        category          = arguments[argument].category
        dataType          = arguments[argument].dataType
        description       = arguments[argument].description
        shortFormArgument = arguments[argument].shortFormArgument

        # Determine if any of the nodes connected with this argument list the argument as required. If the node
        # already has values, they are coming from a parameter set. If this is required, make it clear that it
        # isn't necessary to define the value.
        isRequired = False
        for graphNodeId in graphNodeIds:
          isRequired = True if (graph.getGraphNodeAttribute(graphNodeId, 'isRequired') or isRequired) else False
          hasValues  = True if graph.getGraphNodeAttribute(graphNodeId, 'values') else False

        # if the argument is required, add [REQUIRED] to the end of the description.
        if isRequired:
          if hasValues: description += ' [REQUIRED AND SET]'
          else: description += ' [REQUIRED]'

        # Build the argument string to write to the screen.
        argumentString = str(argument + ' (' + shortFormArgument + '):')

        # Add the information to a list.
        if category not in argumentHelp: argumentHelp[category] = []
        if category not in argumentLengths: argumentLengths[category] = [0, 0, 0]
        argumentHelp[category].append([argumentString, dataType, description])

        # Update the lengths of the longest argument string and data type.
        if len(argumentString) + 3 > argumentLengths[category][0]: argumentLengths[category][0] = len(argumentString) + 3
        if dataType:
          if len(dataType) + 3 > argumentLengths[category][1]: argumentLengths[category][1] = len(dataType) + 3

    # Print the arguments to screen, starting with the inputs.
    if 'Inputs' in argumentHelp:
      self.writeSimpleLine('Inputs', isIndent = False, noLeadingTabs = 0)
      for argumentInformation in sorted(argumentHelp['Inputs']):
        self.writeComplexLine(argumentInformation, argumentLengths['Inputs'], noLeadingTabs = 1)
      print(file = sys.stdout)

    # Then the outputs.
    if 'Outputs' in argumentHelp:
      self.writeSimpleLine('Outputs', isIndent = False, noLeadingTabs = 0)
      for argumentInformation in sorted(argumentHelp['Outputs']):
        self.writeComplexLine(argumentInformation, argumentLengths['Outputs'], noLeadingTabs = 1)
      print(file = sys.stdout)

    # Then all other categories.
    for category in argumentHelp:
      if category != 'Inputs' and category != 'Outputs':
        self.writeSimpleLine(category, isIndent = False, noLeadingTabs = 0)
        for argumentInformation in sorted(argumentHelp[category]):
          self.writeComplexLine(argumentInformation, argumentLengths[category], noLeadingTabs = 1)
        print(file = sys.stdout)

    # Write out all of the values included in the selected parameter set, if there are any.
    self.parameterSets(graph, superpipeline, arguments)

    # Terminate.
    exit(0)

  # Write out all arguments defined in the default parameter set as well values from a defined parameter set.
  def parameterSets(self, graph, superpipeline, arguments):

    # Store the values set by the parameter sets in the following dictionary.
    self.setArguments = {}

    # Start by getting information on the default parameter set, then the defined set.
    self.setParameterSetValues(graph, superpipeline, arguments, 'default')
    if graph.parameterSet: self.setParameterSetValues(graph, superpipeline, arguments, graph.parameterSet)

    # Set the parameter set name.
    setName = graph.parameterSet if graph.parameterSet else 'default'

    # Loop over all of the set arguments and write out the values.
    if len(self.setArguments) > 0:

      # Find the length of the longest argument.
      length = len(max(self.setArguments, key=len))

      # Write out general header information.
      self.writeSimpleLine('Parameter set information for parameter set: ' + setName, isIndent = False, noLeadingTabs = 0)
      for argument in sorted(self.setArguments):

        # Loop over all the values for the argument.
        for i, value in enumerate(self.setArguments[argument]):
          if i == 0: strings = [argument + ':', str(value)]
          else: strings = ['', str(value)]
          self.writeComplexLine(strings, [length + 5, 1], noLeadingTabs = 1)

  # Set parameter set values.
  def setParameterSetValues(self, graph, superpipeline, arguments, setName):
    parameterSet = superpipeline.getPipelineParameterSet(superpipeline.pipeline, setName)
    nodeIds      = ps.parameterSets.SM_getNodeIds(parameterSet)
    for nodeId in nodeIds:

      # Find the pipeline argument that corresponds to this node id.
      useArgument = None
      for argument in arguments.keys():
        if arguments[argument].nodeId == nodeId:
          useArgument = arguments[argument].longFormArgument
          break

      # For each node, determine if an argument exists for the node. Only show set arguments (rather than nodes
      # within the pipeline that are hidded).
      values = nodeIds[nodeId]
      if useArgument and values: self.setArguments[useArgument] = values

  ###############################################
  ##  Routines to write information to screen  ##
  ###############################################

  # Write a simple line of text.
  def writeSimpleLine(self, text, isIndent = True, noLeadingTabs = 0):

    # Set the indent for all lines of text.
    indent = ''.ljust(noLeadingTabs * 3)
    self.wrap.initial_indent    = indent
    self.wrap.subsequent_indent = indent
    if isIndent: self.wrap.initial_indent = indent + '   '

    # Set the width of the line. This depends of the number of tabs being prepended to each
    # line.
    self.wrap.width = self.width - ( noLeadingTabs * 3 )
    lines           = self.wrap.wrap(text)

    # Loop over the lines to print and print them.
    for line in lines: print(line, file = sys.stdout)

  # Given a list of strings and a corresponding list of lengths, construct a line to be
  # printed to screen.
  def writeComplexLine(self, strings, lengths, noLeadingTabs):
    lines = []

    # Check that each string is given a corresponding length.
    if len(strings) != len(lengths): self.errors.listsHaveDifferentLengths()

    # Construct the line by joining all the strings in the list according to their lengths.
    # The last element is not included, but returned as a separate string. Only this last
    # string can be be wrapped due to the maximum width of the screen.
    line = ''
    for counter in range(0, len(strings) - 1): line = line + strings[counter].ljust(lengths[counter])

    # Detemine the remaining width for the last column.
    lineWidth = len(line) + ( noLeadingTabs * 3 )
    width     = self.width - ( noLeadingTabs * 3 ) - len(line)

    # If the line is already longer than the width, just add the remaining string to the line.
    if width < 0: line = line + strings[-1]

    # Otherwise, split the last line.
    else:

      # Break the last line into pieces consistent with the remaining width.
      text = strings[-1]

      # If the final string can fit on the same line, add the string.
      if len(text) <= width: line = line + text

      # Otherwise, break the line into pieces.
      else:
        self.wrap.width             = self.width - ( noLeadingTabs * 3 ) - len(line)
        self.wrap.initial_indent    = ''
        self.wrap.subsequent_indent = ''
        lines                       = self.wrap.wrap(text)

    # If the lines list contains values, add the first value to the line.
    if lines: line = line + lines.pop(0)

    # Add leading spaces based on the number of requested tabs and write the first line.
    for count in range(0, noLeadingTabs): print('   ', end = '', file = sys.stdout)
    print(line, file = sys.stdout)

    # If there are still lines, print these to screen.
    if lines:
      for line in lines: print(''.ljust(lineWidth), line, sep = '', file = sys.stdout)












#######################
### REMOVE OR AMEND ###
#######################


  # If an admin mode's help was requested.
  def selectAdminModeUsage(self, admin):
    if   admin.mode == "build"          : self.buildUsage(admin)
    elif admin.mode == "update"         : self.updateUsage(admin)
    elif admin.mode == "add-resource"   : self.addResourceUsage(admin)
    elif admin.mode == "remove-resource": self.removeResourceUsage(admin)
    elif admin.mode == "update-resource": self.updateResourceUsage(admin)
  
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

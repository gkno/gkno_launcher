#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import json
import os
import sys

class pipeline:
  def __init__(self):
    self.addedToToolInfo               = {}
    self.deleteFiles                   = {}
    self.information                   = {}
    self.isPiped                       = False
    self.isPipeline                    = False
    self.finalOutputs                  = {}
    self.hasMultipleRuns               = False
    self.multipleRunsInputArguments    = []
    self.multipleRunsListFormat        = []
    self.multipleRunsNumberOfArguments = 0
    self.numberOfMultipleRuns          = 0
    self.resourcePath                  = ''
    self.streamedOutputs               = {}
    self.taskBlocks                    = []

  # After the json file has been parsed into the self.information structure, add some
  # pipeline specific values.
  def addPipelineSpecificOptions(self, tl):
    if 'arguments' not in self.information: self.information['arguments'] = {}

    if '--input-path' not in self.information:
      self.information['arguments']['--input-path']                        = {}
      self.information['arguments']['--input-path']['description']         = 'Path for input files if not defined.  Default: current directory'
      self.information['arguments']['--input-path']['link to this task']   = 'pipeline'
      self.information['arguments']['--input-path']['short form argument'] = '-ip'
      self.information['arguments']['--input-path']['type']                = 'string'
      self.information['arguments']['--input-path']['default']             = '$(PWD)'

    if '--output-path' not in self.information:
      self.information['arguments']['--output-path']                        = {}
      self.information['arguments']['--output-path']['description']         = 'Path for output files if not defined.  Default: current directory'
      self.information['arguments']['--output-path']['link to this task']   = 'pipeline'
      self.information['arguments']['--output-path']['short form argument'] = '-op'
      self.information['arguments']['--output-path']['type']                = 'string'
      self.information['arguments']['--output-path']['default']             = '$(PWD)'

    if '--resource-path' not in self.information:
      self.information['arguments']['--resource-path']                        = {}
      self.information['arguments']['--resource-path']['description']         = 'Path for resource files if not defined.  Default: gkno/resources'
      self.information['arguments']['--resource-path']['link to this task']   = 'pipeline'
      self.information['arguments']['--resource-path']['short form argument'] = '-rp'
      self.information['arguments']['--resource-path']['type']                = 'string'
      self.information['arguments']['--resource-path']['default']             = '$(RESOURCES)'

    self.information['resource path'] = '' if 'resource path' not in self.information else  self.information['resource path']

    if '--execute' not in self.information:
      self.information['arguments']['--execute']                        = {}
      self.information['arguments']['--execute']['description']         = 'Boolean to determine if the Makefile should be executed.  Default: True'
      self.information['arguments']['--execute']['link to this task']   = 'pipeline'
      self.information['arguments']['--execute']['short form argument'] = '-ex'
      self.information['arguments']['--execute']['type']                = 'bool'
      self.information['arguments']['--execute']['default']             = True

    if '--verbose' not in self.information:
      self.information['arguments']['--verbose']                        = {}
      self.information['arguments']['--verbose']['description']         = 'Boolean to determine if verbose information should be output.  Default: True'
      self.information['arguments']['--verbose']['link to this task']   = 'pipeline'
      self.information['arguments']['--verbose']['short form argument'] = '-vb'
      self.information['arguments']['--verbose']['type']                = 'bool'
      self.information['arguments']['--verbose']['default']             = True

    if '--export-config' not in self.information:
      self.information['arguments']['--export-config']                        = {}
      self.information['arguments']['--export-config']['description']         = 'Export information to a new configuration file of this name.'
      self.information['arguments']['--export-config']['link to this task']   = 'pipeline'
      self.information['arguments']['--export-config']['short form argument'] = '-ec'
      self.information['arguments']['--export-config']['type']                = 'string'
      self.information['arguments']['--export-config']['default']             = ''

    if '--multiple-runs' not in self.information:
      self.information['arguments']['--multiple-runs']                        = {}
      self.information['arguments']['--multiple-runs']['description']         = 'Run the pipeline multiple times using the inputs defined in this file.'
      self.information['arguments']['--multiple-runs']['link to this task']   = 'pipeline'
      self.information['arguments']['--multiple-runs']['short form argument'] = '-mr'
      self.information['arguments']['--multiple-runs']['type']                = 'string'
      self.information['arguments']['--multiple-runs']['default']             = ''

  # Print to screen information about the selected pipeline.
  def printPipelineInformation(self, tl):
    er = errors()

    if tl.toolArguments['pipeline']['--verbose']:

      # Determine the length of the longest tool name.
      length  = 0
      for task in self.information['workflow']:
        if task not in self.information['tools']:
          er.unknownToolName(task)
          er.terminate()
        tool = self.information['tools'][task]
        if tool not in tl.toolInfo:
          er.unknownTool(task, tool)
          er.terminate()
  
        text   = task + ' (' + tool + '):'
        length = len(text) if len(text) > length else length
      length += 5
  
      print('Workflow:', sep = '', file = sys.stdout)
      sys.stdout.flush()
      for task in self.information['workflow']:
        tool        = self.information['tools'][task]
        text        = task + ' (' + tool + '):'
        description = tl.toolInfo[tool]['description'] if 'description' in tl.toolInfo[tool] else 'No description'
        print("\t%-*s%-*s" % (length, text, 1, description), file = sys.stdout)
      print(file = sys.stdout)

  # Modify pipeline information to handle an individual tool.
  def setupIndividualTool(self, tool, verbose):
    self.information['tools']       = {}
    self.information['tools'][tool] = tool
    self.information['workflow']    = []
    self.information['workflow'].append(tool)
    text = '=' * (len(tool) + 20)
    if verbose:
      print(text, file = sys.stdout)
      print('Executing tool: ', tool, sep = '', file = sys.stdout)
      print(text, file = sys.stdout)
      print(file = sys.stdout)

    return 'tools/' + tool

  # Set up the pipeline specific options.
  def setupPipelineOptions(self, tl):
    er             = errors()
    linkToTask     = ''
    linkToArgument = ''
    if tl.toolArguments['pipeline']['--verbose']:
      print('Setting up pipeline defaults...', end = '', file = sys.stdout)
      sys.stdout.flush()

    for argument in self.information['arguments']:

      # The pipeline configuration file contains arguments for pipeline specific
      # options, as well as some for setting the options within individual tools
      # within the pipeline.  If the option is pipeline specific, the 'tool' value
      # will be 'pipeline', otherwise it will point to the individual tool.  For
      # tool commands, overwrite the current value stored.
      if 'link to this task' not in self.information['arguments'][argument]:
        er.optionAssociationError("\n\t\t", 'link to this task', argument, 'pipeline')
        er.terminate()
      else: task = self.information['arguments'][argument]['link to this task']
      default = ''
      if 'default' in self.information['arguments'][argument]: default = self.information['arguments'][argument]['default']

      # Set the defaults.
      # The arguments defined in the pipeline configuration file point to an argument
      # in one of the tools in the pipeline.  There are some pipeline specific options
      # that are given the tool name 'pipeline'.  For all tools that are not listed as
      # 'pipeline', check that the tool exists and that the argument that it points to
      # is valid.
      if (task != 'pipeline') and (task not in self.information['workflow']):
        er.associatedToolNotInPipeline("\n\t", task, argument)
        er.terminate()

      if task != 'pipeline':
        tool = self.information['tools'][task] if task != 'pipeline' else ''

        if 'link to this argument' not in self.information['arguments'][argument]:
          er.optionAssociationError('link to this argument', argument, 'pipeline')
          er.terminate()
        else: linkToArgument = self.information['arguments'][argument]['link to this argument']

        # Check that the argument is valid.
        if linkToArgument not in tl.toolArguments[task]:
          er.incorrectArgumentInPipelineConfigurationFile("\n\t", task, argument, linkToArgument)
          er.terminate()

        if default != '': tl.toolArguments[task][linkToArgument] = default
      else:
        default = self.information['arguments'][argument]['default']

        # The '--verbose' argument was set in the constructor for the command line object, so do
        # not reset this value.
        if argument == '--verbose': continue

        if 'pipeline' not in tl.toolArguments: tl.toolArguments['pipeline'] = {}
        tl.toolArguments['pipeline'][argument] = default

    if tl.toolArguments['pipeline']['--verbose']:
      print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

  # Construct filenames using the instructions in the pipeline configuration file.
  def constructFileNameFromJson(self, tl, task, tool, argument):
    er = errors()

    constructBlock = self.information['construct filenames'][task][argument]
    basename       = constructBlock['filename root'] if 'filename root' in constructBlock else ''
    linkedToolName = constructBlock['get root from task'] if 'get root from task' in constructBlock else ''
    linkedArgument = constructBlock['get root from argument'] if 'get root from argument' in constructBlock else ''
    removeExt      = constructBlock['remove input extension'] if 'remove input extension' in constructBlock else ''
    additionalText = constructBlock['additional text from parameters'] if 'additional text from parameters' in constructBlock else ''

    # If the basename is 'from argument', the 'tool', 'argument' and 'remove extension'
    # variables must be set.  Take the value from the specified tool/argument, remove
    # the extension if requested, then add the additional text if there is any to be
    # added.  Remove the path if one exists.
    if basename == 'from argument': basename = tl.toolArguments[linkedToolName][linkedArgument].split('/')[-1]
    if removeExt == 'true':
      linkedTool = self.information['tools'][linkedToolName]
      extension = ''
      if 'extension' in tl.toolInfo[linkedTool]['arguments'][linkedArgument]:
        extension = tl.toolInfo[linkedTool]['arguments'][linkedArgument]['extension']

      # If there is a '|' symbol in the extension, break up all the allowable extensions
      # and check if the name ends with any of them and if so, remove the extension.
      extensions = extension.split('|')
      for extension in extensions:
        if basename.endswith(extension):
          basename = basename[0:(len(basename) - len(extension) - 1)]
          break

    # If there is additional text to add to the name, the additionalText variable will have
    # a value.  If this is the case, a list of tool/argument pairs needs to be provided.  These
    # values will be added to the name separated by the separator variable.
    name = ''
    if not additionalText != '': name = basename
    else:

      # Determine the order of the variables to add.
      order = additionalText['order']

      # Determine the separator to be used when joining the values together.  If no separator
      # is provided, use '_'.
      separator = additionalText['separator'] if 'separator' in additionalText else '_'
      for text in order:
        if text == 'filename root': name += basename

        # If the text isn't 'filename root', then it refers to a variable used in the pipeline.
        # There must exist an entry in the json file that associates the text with a tool
        # and an argument.
        else:
          if text not in additionalText:
            er.noDescriptionOfVariable("\n\t\t\t", task, argument, text)
            er.terminate()
          addTaskName        = additionalText[text]['get parameter from task'] if 'get parameter from task' in additionalText[text] else ''
          addArgument        = additionalText[text]['get parameter from argument'] if 'get parameter from argument' in additionalText[text] else ''
          addRemoveExtension = additionalText[text]['remove extension'] if 'remove extension' in additionalText[text] else ''
          if (addTaskName == '') or (addArgument == ''):
            er.missingVariableForFilenameConstruction("\n\t", task, argument, text)
            er.terminate()

          # Now get the variable if it exist
          toolError     = False
          argumentError = False
          if addTaskName not in tl.toolArguments: toolError = True
          elif addArgument not in tl.toolArguments[addTaskName]: argumentError = True

          if toolError or argumentError:
            er.nonExistentTaskOrArgumentInConstruction(True, "\t\t\t", task, argument, text, addTaskName, addArgument, toolError)
            er.terminate()
          variable = tl.toolArguments[addTaskName][addArgument]

          # If the parameter being used in the output filename is itself a filename,
          # it should contain a path.  If this is the case, remove the path from the
          # name before using in the construction.
          variable = variable.split('/')[-1]

          # If the extension is to be removed, check that the input argument defines a file
          # with an extension and if so, remove the extension if requested.
          if addRemoveExtension == 'true':
            extension = tl.toolInfo[linkedTool]['arguments'][linkedArgument]['extension'] if 'extension' in \
            tl.toolInfo[linkedTool]['arguments'][linkedArgument] else ''

            # If there is a '|' symbol in the extension, break up all the allowable extensions
            # and check if the name ends with any of them and if so, remove the extension.
            if extension != '': 
              extensions = extension.split('|')
              for extension in extensions:
                if variable.endswith(extension):
                  variable = variable[0:(len(variable) - len(extension) - 1)]
                  break
          name += separator + str(variable)

    # Determine if the output file is a stub.  If not, add the extension to the output file.
    stub = tl.toolInfo[tool]['arguments'][argument]['stub'] if 'stub' in tl.toolInfo[tool]['arguments'][argument] else ''
    isStub = True if stub == 'true' else False
    if not isStub:
      if 'extension' not in tl.toolInfo[tool]['arguments'][argument]: extension = ''
      else: extension = tl.toolInfo[tool]['arguments'][argument]['extension']
      name += '.' + str(extension)

    # Having built the filename, set the value in the tl.toolArguments data structure.
    tl.toolArguments[task][argument] = name

  # Use the 'linkage' section of the pipeline configuration file to set all
  # parameters that depend on other tools.
  def toolLinkage(self, cl, tl, task, tool):
    er            = errors()
    linkArguments = {}
    if tl.toolArguments['pipeline']['--verbose']:
      print("\t\tChecking linkage to other tools in the pipeline...", end = '', file = sys.stdout)
      sys.stdout.flush()

    # Work through each argument in turn and identify all of the input and output files.
    # For non-input/output files, just check for links to other tools.
    hasLinkageInformation = True if 'linkage' in self.information else False
    if hasLinkageInformation: 
      taskLinkage = True if task in self.information['linkage'] else False

      if taskLinkage:

        # Populate the dictionary linkArguments with all of the arguments that
        # require linking.
        for argument in self.information['linkage'][task]:
          linkArguments[argument] = argument

        # Link together parameters.
        for argument in tl.toolArguments[task]:

          # Check that the option in the configuration file is valid.
          #if argument not in tl.toolInfo[tool]['arguments']:
          if (argument not in tl.toolInfo[tool]['arguments']) and (argument != 'json parameters'):
            er.invalidArgument(False, "\t\t\t", 'linkage', argument, task)
            er.terminate()

          # Check if this argument is linked to any other commands.
          argumentLinkage = True if argument in self.information['linkage'][task] else False
          if argumentLinkage:
            self.checkLinkage(tl, task, tool, argument)
            del linkArguments[argument]

      if tl.toolArguments['pipeline']['--verbose']:
        print("done.", file = sys.stdout)
        sys.stdout.flush()

    # Check the list of linked options and ensure that they have all been parsed.  Any
    # options that have not been handled are either special cases, or an error in the
    # configuration file.
    for argument in linkArguments:
      if argument == 'json parameters':
        self.checkLinkage(tl, task, tool, argument)
      else:
        er.invalidArgument(True, "\t\t\t", 'linkage', argument, task)
        er.terminate()

  # Check to see if a tool option is linked to another tool and modify the stored
  # value accordingly.
  def checkLinkage(self, tl, task, tool, argument):
    er = errors()

    targetToolName = ''
    try: targetToolName = self.information['linkage'][task][argument]['link to this task']
    except: er.optionAssociationError('link to this task', argument, tool)
    if er.error:
      print(file = sys.stdout)
      er.terminate()

    targetArgument = ''
    try: targetArgument = self.information['linkage'][task][argument]['link to this argument']
    except: er.optionAssociationError('link to this argument', argument, tool)
    if er.error:
      print(file = sys.stdout)
      er.terminate()

    # Check that the targetToolName and the targetOption are valid.
    if targetToolName not in tl.toolArguments:
      print(file = sys.stdout)
      er.invalidToolName('linkage', targetToolName)
      er.terminate()

    if targetArgument not in tl.toolArguments[targetToolName]:
      print(file = sys.stdout)
      er.invalidArgument('linkage', targetArgument, targetToolName)
      er.terminate()

    # If the linkage block contains 'extension', the linked value requires this
    # extension adding to the end of the value.
    extension = ''
    if 'extension' in self.information['linkage'][task][argument]:
      tl.toolArguments[task][argument] = tl.toolArguments[targetToolName][targetArgument] + self.information['linkage'][task][argument]['extension']
    else:
      tl.toolArguments[task][argument] = tl.toolArguments[targetToolName][targetArgument]

  # In the course of executing the pipeline, some of the intermediate files
  # generated along the way should be deleted.  The pipeline configuration
  # file segment 'delete files' identifies which files should be deleted and
  # when in the pipeline they can be removed.
  def determineFilesToDelete(self, tl):
    er = errors()

    if tl.toolArguments['pipeline']['--verbose']:
      print('Determining which intermediate files can be deleted...', end = '', file = sys.stdout)
      sys.stdout.flush()

    # Check to see if the configuration file has the 'delete files' section.
    if 'delete files' in self.information:
      for task in self.information['delete files']:

        # Check that the task is a valid task in the pipeline.
        if task not in self.information['tools']:
          er.invalidToolTaskName(True, "\t", 'delete files', True, task)
          er.terminate()

        for argument in self.information['delete files'][task]:

          # Check that the argument is a valid argument for the specified task.
          tool = self.information['tools'][task]
          if argument not in tl.toolInfo[tool]['arguments']:
            er.invalidArgument(True, "\t", 'delete files', argument, task)
            er.terminate()

          # Check if the argument is a filename stub.  If so, the 'extension' argument
          # must be provided in the configuration file listing which of the created files
          # should be deleted.
          isStub = False
          if 'stub' in tl.toolInfo[tool]['arguments'][argument]:
            if tl.toolInfo[tool]['arguments'][argument]['stub'] == 'true': isStub = True

          # If the filename is a stub, there can be a number of extensions that require
          # deleting, each of which can be deleted after a different task.  Loop over the
          # extensions and determine what needs to be deleted and when.
          if isStub:
            for extension in self.information['delete files'][task][argument]:

              # Check that the extension is valid.
              if extension not in tl.toolInfo[tool]['arguments'][argument]['outputs']:
                er.invalidStubExtension(True, "\t", task, argument, extension)
                er.terminate()

              if 'delete after task' in self.information['delete files'][task][argument][extension]:
                deleteAfterTask = self.information['delete files'][task][argument][extension]['delete after task']

              # Check that the task after which the file is to be deleted is valid.
              if deleteAfterTask not in self.information['tools']:
                er.invalidToolTaskName(True, "\t", 'delete files', True, deleteAfterTask)
                er.terminate()

              if deleteAfterTask not in self.deleteFiles: self.deleteFiles[deleteAfterTask] = {}
              if argument not in self.deleteFiles[deleteAfterTask]: self.deleteFiles[deleteAfterTask][argument] = []
              self.deleteFiles[deleteAfterTask][argument].append(tl.toolArguments[task][argument] + extension)

          # If not a stub, then there is only a single file to deal with.
          else:
            if 'delete after task' in self.information['delete files'][task][argument]:
              deleteAfterTask = self.information['delete files'][task][argument]['delete after task']

            # Check that the task after which the file is to be deleted is valid.
            if deleteAfterTask not in self.information['tools']:
              er.invalidToolTaskName(True, "\t", 'delete files', True, deleteAfterTask)
              er.terminate()

            if deleteAfterTask not in self.deleteFiles: self.deleteFiles[deleteAfterTask] = {}
            if argument not in self.deleteFiles[deleteAfterTask]: self.deleteFiles[deleteAfterTask][argument] = []
            self.deleteFiles[deleteAfterTask][argument].append(tl.toolArguments[task][argument])

    if tl.toolArguments['pipeline']['--verbose']:
      print('done.', file = sys.stdout)
      print(file = sys.stdout)
      sys.stdout.flush()

  # The list of files to be produced by the script is all of the files created
  # by each individual task in the pipeline.  However, if some of the files
  # are deleted along the way, the final list of files should not include these
  # deleted files.
  def determineFinalOutputs(self, tl):

    # Put all of the files to be deleted in a dictionary.
    deletedFiles = {}
    for task in self.deleteFiles:
      for argument in self.deleteFiles[task]:
        for output in self.deleteFiles[task][argument]:
          deletedFiles[output] = True

    for task in tl.outputs:
      if task not in self.finalOutputs: self.finalOutputs[task] = []
      for output in tl.outputs[task]:
        if output not in deletedFiles: self.finalOutputs[task].append(output)

  # Determine if any of the tools are being piped together and check if the
  # tools involved can use the stream for input and output.
  def determinePiping(self, tl):
    er           = errors()
    addArguments = {}

    if 'tools outputting to stream' in self.information:
      if tl.toolArguments['pipeline']['--verbose']:
        print('Checking integrity of piped tools...', end = '', file = sys.stdout)
        sys.stdout.flush()
      self.isPiped = True
      for taskCounter, task in enumerate(self.information['workflow']):
        if task in self.information['tools outputting to stream']:
          self.streamedOutputs[task] = True
          tool                       = self.information['tools'][task]
          canOutputToStream          = False

          # If the tool only deals with the stream for inputs and outputs, skip the
          # following search.  There is no input or output commands as the tool is
          # expecting to be receiving and outputting to the stream.
          if tl.toolsDemandingOutputStream[tool]: canOutputToStream = True

          # Check if the tool allows the output to be sent to a stream.
          for argument in tl.toolInfo[tool]['arguments']:
            isOutput = True if tl.toolInfo[tool]['arguments'][argument]['output'] == 'true' else False
            if isOutput:
              if 'if output to stream' in tl.toolInfo[tool]['arguments'][argument]:
                if canOutputToStream:
                  er.multipleOutputsToStream(True, "\t", task, tool)
                  er.terminate()
                canOutputToStream = True

                # If the entry in the configuration file is 'do not include', just
                # remove this argument from the toolArguments structure.
                if tl.toolInfo[tool]['arguments'][argument]['if output to stream'] == 'do not include':
                  del(tl.toolArguments[task][argument])

                # Otherwise, handle as appropriate.
                else:
                  print('NOT YET HANDLED THIS STREAM OPTION', task, argument, file = sys.stdout)
                  er.terminate()

          # Now check that the subsequent tool can accept the stream as an input.  If
          # this was the last task in the pipeline, fail as the output needs to pipe
          # somewhere.
          if (taskCounter + 1) == len(self.information['workflow']):
            er.lastTaskOutputsToPipe(True, "\t", task)
            er.terminate()

          nextTask        = self.information['workflow'][taskCounter + 1]
          nextTool        = self.information['tools'][nextTask]
          canAcceptStream = False

          # If the current tool outputs to the stream, we need to check that the following
          # tool is set up to handle the stream.  This information is contained in the
          # information for one of the input files in the next tool.  If the next tool
          # demands the stream, then there are no input or output command line arguments as
          # the stream is assumed and so this check is unnecessary.
          if tl.toolsDemandingInputStream[nextTool]: canAcceptStream = True

          for argument in tl.toolInfo[nextTool]['arguments']:
            isInput = True if tl.toolInfo[nextTool]['arguments'][argument]['input'] == 'true' else False
            if isInput:
              if 'if input is stream' in tl.toolInfo[nextTool]['arguments'][argument]:
                if canAcceptStream:
                  er.multipleInputsAcceptStream(True, "\t", task, tool)
                  er.terminate()
                canAcceptStream = True

                # If the entry in the configuration file is 'do not include', just
                # remove this argument from the toolArguments structure.
                if tl.toolInfo[nextTool]['arguments'][argument]['if input is stream'] == 'do not include':
                  del(tl.toolArguments[nextTask][argument])

                # If the entry is 'replace', then the argument needs to be removed and
                # replaced with that provided.  When the Makefile is generated, the
                # tl.toolInfo structure is interogated.  This replacement value should
                # not be present in the structure, so a value needs to be input.
                elif tl.toolInfo[nextTool]['arguments'][argument]['if input is stream'] == 'replace':
                  if 'replace argument with' not in tl.toolInfo[nextTool]['arguments'][argument]:
                    er.noReplacementFoundWhenStreaming(True, "\t", nextTask, nextTool, argument)
                    er.terminate()

                  if ('argument' not in tl.toolInfo[nextTool]['arguments'][argument]['replace argument with']) or \
                  ('value' not in tl.toolInfo[nextTool]['arguments'][argument]['replace argument with']):
                    er.noReplacementFoundWhenStreaming(True, "\t", nextTask, nextTool, argument)
                    er.terminate()

                  del(tl.toolArguments[nextTask][argument])
                  replacementArgument = tl.toolInfo[nextTool]['arguments'][argument]['replace argument with']['argument']
                  replacementValue    = tl.toolInfo[nextTool]['arguments'][argument]['replace argument with']['value']
                  if replacementArgument not in tl.toolArguments[nextTask]:
                    tl.toolArguments[nextTask][replacementArgument] = replacementValue
                    if replacementArgument in tl.toolInfo[nextTool]['arguments']:
                      er.replacementArgumentAlreadyPresent(True, "\t", nextTask, tool, replacementArgument)
                      er.terminate()
                    else:
                      if nextTool not in addArguments: addArguments[nextTool] = {}
                      addArguments[nextTool] = replacementArgument

                # If the entry is neither 'do not include' or 'replace', just use this value
                # as the value for the argument.
                else:  
                  tl.toolArguments[nextTask][argument] = tl.toolInfo[nextTool]['arguments'][argument]['if input is stream']

          # If no instructions are provided on how to handle a streaming input, terminate.
          if not canOutputToStream:
            er.noOutputStreamInstructions(True, "\t", task, tool)
            er.terminate()

          if not canAcceptStream:
            er.noInputStreamInstructions(True, "\t", nextTask, nextTool)
            er.terminate()

      # Having determined all arguments that are modified, add the necessary arguments to the
      # tl.toolInfo structure (these weren't added before as the dictionary cannot be modified
      # while it was being used).  Keep track of added arguments as they need to be removed
      # once the makefile has been created, to reset the toolInfo structure back to its original
      # form before rerunning the pipeline if multiple runs are being performed.
      for task in addArguments:
        tl.toolInfo[nextTool]['arguments'][replacementArgument] = 'replacement'
        if nextTool not in self.addedToToolInfo: self.addedToToolInfo[nextTool] = []
        self.addedToToolInfo[nextTool].append(replacementArgument)

      if tl.toolArguments['pipeline']['--verbose']:
        print('done.', file = sys.stdout)
        print(file = sys.stdout)

  # Determine the order in which to write out the tasks.
  def determineToolWriteOrder(self):
    taskBlock = []
    for task in self.information['workflow']:

      # Add the task to a task block.
      taskBlock.append(task)

      # If the task outputs to a file (i.e. it is not listed as outputting to a stream,
      # the block of piped tasks is complete, so add the task to the list of task
      # blocks and reset the block.
      if self.isPiped: 
        if task not in self.information['tools outputting to stream']:
          self.taskBlocks.append(taskBlock)
          taskBlock = []
      else:
        self.taskBlocks.append(taskBlock)
        taskBlock = []

#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import json
import os
import sys

class pipeline:
  def __init__(self):
    self.isPipeline  = False
    self.information = {}

  # After the json file has been parsed into the self.information structure, add some
  # pipeline specific values.
  def addPipelineSpecificOptions(self, tl):
    if 'arguments' not in self.information: self.information['arguments'] = {}

    if '--input-path' not in self.information:
      self.information['arguments']['--input-path']                = {}
      self.information['arguments']['--input-path']['description'] = 'Path for input files if not defined.  Default: current directory'
      self.information['arguments']['--input-path']['tool']        = 'pipeline'
      self.information['arguments']['--input-path']['alternative'] = '-ip'
      self.information['arguments']['--input-path']['type']        = 'string'
      self.information['arguments']['--input-path']['default']     = '$(PWD)'

    if '--output-path' not in self.information:
      self.information['arguments']['--output-path']                = {}
      self.information['arguments']['--output-path']['description'] = 'Path for output files if not defined.  Default: current directory'
      self.information['arguments']['--output-path']['tool']        = 'pipeline'
      self.information['arguments']['--output-path']['alternative'] = '-op'
      self.information['arguments']['--output-path']['type']        = 'string'
      self.information['arguments']['--output-path']['default']     = '$(PWD)'

    if '--resource-path' not in self.information:
      self.information['arguments']['--resource-path']                = {}
      self.information['arguments']['--resource-path']['description'] = 'Path for resource files if not defined.  Default: gkno/resources'
      self.information['arguments']['--resource-path']['tool']        = 'pipeline'
      self.information['arguments']['--resource-path']['alternative'] = '-rp'
      self.information['arguments']['--resource-path']['type']        = 'string'
      self.information['arguments']['--resource-path']['default']     = '$(RESOURCES)'

    if '--execute' not in self.information:
      self.information['arguments']['--execute']                = {}
      self.information['arguments']['--execute']['description'] = 'Boolean to determine if the Makefile should be executed.  Default: True'
      self.information['arguments']['--execute']['tool']        = 'pipeline'
      self.information['arguments']['--execute']['alternative'] = '-ex'
      self.information['arguments']['--execute']['type']        = 'bool'
      self.information['arguments']['--execute']['default']     = True

    if '--verbose' not in self.information:
      self.information['arguments']['--verbose']                = {}
      self.information['arguments']['--verbose']['description'] = 'Boolean to determine if verbose information should be output.  Default: False'
      self.information['arguments']['--verbose']['tool']        = 'pipeline'
      self.information['arguments']['--verbose']['alternative'] = '-vb'
      self.information['arguments']['--verbose']['type']        = 'bool'
      self.information['arguments']['--verbose']['default']     = False

  # Print to screen information about the selected pipeline.
  def printPipelineInformation(self, tl):
    er = errors()

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

    print('Workflow:', sep = '', file = sys.stderr)
    for task in self.information['workflow']:
      tool        = self.information['tools'][task]
      text        = task + ' (' + tool + '):'
      description = tl.toolInfo[tool]['description'] if 'description' in tl.toolInfo[tool] else 'No description'
      print("\t%-*s%-*s" % (length, text, 1, description), file = sys.stderr)
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
    er      = errors()
    command = ''
    tool    = ''
    print('Setting up pipeline defaults...', end = '', file = sys.stdout)
    sys.stdout.flush()

    for argument in self.information['arguments']:

      # The pipeline configuration file contains arguments for pipeline specific
      # options, as well as some for setting the options within individual tools
      # within the pipeline.  If the option is pipeline specific, the 'tool' value
      # will be 'pipeline', otherwise it will point to the individual tool.  For
      # tool commands, overwrite the current value stored.
      if 'tool' not in self.information['arguments'][argument]:
        er.optionAssociationError("\n\t\t", 'tool', argument, 'pipeline')
        er.terminate()
      else: task = self.information['arguments'][argument]['tool']
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

        if 'command' not in self.information['arguments'][argument]:
          er.optionAssociationError('command', argument, 'pipeline')
          er.terminate()
        else: command = self.information['arguments'][argument]['command']

        # Check that the argument is valid.
        if command not in tl.toolArguments[task]:
          er.incorrectArgumentInPipelineConfigurationFile("\n\t", task, argument, command)
          er.terminate()

        if default != '': tl.toolArguments[task][command] = default
      else:
        default = self.information['arguments'][argument]['default']
        if 'pipeline' not in tl.toolArguments: tl.toolArguments['pipeline'] = {}
        tl.toolArguments['pipeline'][argument] = default

    print('done.', file = sys.stdout)
    print(file = sys.stdout)

  # Construct filenames using the instructions in the pipeline configuration file.
  def constructFileNameFromJson(self, tl, task, tool, argument):
    constructBlock = self.information['construct filenames'][task][argument]
    basename       = constructBlock['base name'] if 'base name' in constructBlock else ''
    linkedToolName = constructBlock['tool'] if 'tool' in constructBlock else ''
    linkedArgument = constructBlock['argument'] if 'argument' in constructBlock else ''
    removeExt      = constructBlock['remove extension'] if 'remove extension' in constructBlock else ''
    additionalText = constructBlock['additional text from variables'] if 'additional text from variables' in constructBlock else ''

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
        if text == 'base name': name += basename

        # If the text isn't 'base name', then it refers to a variable used in the pipeline.
        # There must exist an entry in the json file that associates the text with a tool
        # and an argument.
        else:
          if text not in additionalText:
            er.noDescriptionOfVariable("\n\t", task, argument, text)
            er.terminate()
          addToolName = additionalText[text]['tool'] if 'tool' in additionalText[text] else ''
          addArgument = additionalText[text]['argument'] if 'argument' in additionalText[text] else ''
          if (addToolName == '') or (addArgument == ''):
            er.missingVariableForFilenameConstruction("\n\t", task, argument, text)
            er.terminate()

          # Now get the variable if it exists.
          toolError     = False
          argumentError = False
          if addToolName not in tl.toolArguments: toolError = True
          elif addArgument not in tl.toolArguments[addToolName]: argumentError = True

          if toolError or argumentError:
            er.nonExistentToolOrArgumentInConstruction("\n\t", task, argument, text, addToolName, addArgument, toolError)
            er.terminate()
          variable = tl.toolArguments[addToolName][addArgument]
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
    print("\t\tChecking linkage to other tools in the pipeline...", end = '', file = sys.stdout)

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
          if argument not in tl.toolInfo[tool]['arguments']:
            print(file = sys.stdout)
            er.invalidOption('linkage', argument, task)
            er.terminate()

          # Check if this argument is linked to any other commands.
          argumentLinkage = True if argument in self.information['linkage'][task] else False
          if argumentLinkage:
            self.checkLinkage(tl, task, tool, argument)
            del linkArguments[argument]

      print("done.", file = sys.stdout)
      sys.stdout.flush()

    # Check the list of linked options and ensure that they have all been parsed.  Any
    # options that have not been handled are either special cases, or an error in the
    # configuration file.
    for argument in linkArguments:
      if argument == 'json parameters':
        self.checkLinkage(tl, task, tool, argument)
      else:
        er.invalidOption(True, "\t\t\t", 'linkage', argument, task)
        er.terminate()

  # Check to see if a tool option is linked to another tool and modify the stored
  # value accordingly.
  def checkLinkage(self, tl, task, tool, argument):
    er = errors()

    targetToolName = ''
    try: targetToolName = self.information['linkage'][task][argument]['tool']
    except: er.optionAssociationError('tool', argument, tool)
    if er.error:
      print(file = sys.stdout)
      er.terminate()

    targetArgument = ''
    try: targetArgument = self.information['linkage'][task][argument]['command']
    except: er.optionAssociationError('command', argument, tool)
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
      er.invalidOption('linkage', targetArgument, targetToolName)
      er.terminate()

    # If the linkage block contains 'extension', the linked value requires this
    # extension adding to the end of the value.
    extension = ''
    if 'extension' in self.information['linkage'][task][argument]:
      tl.toolArguments[task][argument] = tl.toolArguments[targetToolName][targetArgument] + self.information['linkage'][task][argument]['extension']
    else:
      tl.toolArguments[task][argument] = tl.toolArguments[targetToolName][targetArgument]

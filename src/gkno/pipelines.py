#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import os
import sys

class pipeline:
  def __init__(self):
    self.options = {}

  # Print to screen information about the selected pipeline.
  def printPipelineInformation(self, tl):
    er = errors()

    print("Workflow:", sep = "", file = sys.stderr)
    for toolName in self.information['workflow']:
      if toolName not in self.information['tools']:
        er.unknownToolName(toolName)
        er.terminate()
      else:
        tool = self.information['tools'][toolName]
        if tool not in tl.toolInfo:
          er.unknownTool(toolName, tool)
          er.terminate()
        else:
          print("\t", toolName, " (", tool, "):\t", tl.toolInfo[tool]['description'], sep = "", file = sys.stdout)
    print(file = sys.stdout)

  # Modify pipeline information to handle an individual tool.
  def setupIndividualTool(self, tool):
    self.information                = {}
    self.information['tools']       = {}
    self.information['tools'][tool] = tool
    self.information['workflow']    = []
    self.information['workflow'].append(tool)
    print("-------------------------------------", file = sys.stdout)
    print("Executing tool: ", tool, sep = '', file = sys.stdout)
    print("-------------------------------------", file = sys.stdout)
    print(file = sys.stdout)

    return 'tools/' + tool

  # Set up a dictionary containing the pipeline specific options.
  def setupPipelineOptions(self, tl):
    er = errors()
    print("Setting up pipeline defaults...", file = sys.stdout)

    if 'arguments' not in self.information: self.information['arguments'] = {}

    # Set up the default pipeline options.
    if '--name' not in self.information:
      self.information['arguments']['--name']                = {}
      self.information['arguments']['--name']['description'] = 'name to use for constructing undefined filenames'
      self.information['arguments']['--name']['tool']        = 'pipeline'
      self.information['arguments']['--name']['alternative'] = '-n'
      self.information['arguments']['--name']['type']        = 'string'
      self.information['arguments']['--name']['default']     = 'gkno_temp'

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
      self.information['arguments']['--execute']['alternative'] = '-e'
      self.information['arguments']['--execute']['type']        = 'bool'
      self.information['arguments']['--execute']['default']     = True

    for option in self.information['arguments']:

      # The pipeline configuration file contains arguments for pipeline specific
      # options, as well as some for setting the options within individual tools
      # within the pipeline.  If the option is pipeline specific, the 'tool' value
      # will be 'pipeline', otherwise it will point to the individual tool.  For
      # tool commands, overwrite the current value stored.
      if 'tool' not in self.information['arguments'][option]:
        er.optionAssociationError('tool', option, 'pipeline')
        er.terminate()
      else: toolName = self.information['arguments'][option]['tool']
      default = ""
      if 'default' in self.information['arguments'][option]: default = self.information['arguments'][option]['default']

      # Set the defaults.
      if toolName == 'pipeline': self.options[option] = default
      else:

        # Check that the tool and option in the configuration are valid.
        if toolName not in self.information['workflow']:
          er.invalidToolName('arguments', toolName)
          er.terminate()
        tool = self.information['tools'][toolName]

        if 'command' not in self.information['arguments'][option]:
          er.optionAssociationError('command', option, 'pipeline')
          er.terminate()
        else: command = self.information['arguments'][option]['command']
        if default != "": tl.toolOptions[toolName][command] = default
    print(file = sys.stdout)

  # Use the 'linkage' section of the pipeline configuration file to set all
  # parameters that depend on other tools.
  def toolLinkage(self, cl, tl):
    er = errors()
    print("Determining linkage between tools in the pipeline...", file = sys.stdout)

    hasLinkageInformation = False
    if 'linkage' in self.information: hasLinkageInformation = True

    # Generate a list of all of the options that have linkage information.
    linkedOptions = {}
    if hasLinkageInformation:
      for toolName in self.information['linkage']:
        if toolName not in self.information['workflow']:
          er.invalidToolName('linkage', toolName)
          if er.error: er.terminate()

        tool = self.information['tools'][toolName] 
        if toolName not in linkedOptions: linkedOptions[toolName] = {}
        for option in self.information['linkage'][toolName]: linkedOptions[toolName][option] = True

    # Work through each tool in turn and identify all of the input and output files.
    # If required input files are unset and are not linked to another tool, terminate
    # the script as the individual tools cannot run without knowledge of the input
    # files. For unset output files, use the pl.name property to determine names.
    for toolName in self.information['workflow']:
      tool = self.information['tools'][toolName]
      print("\t", toolName, " (", tool, ")...", sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()

      # Loop over each of the options.  If it is an input, check that it is defined or
      # that it can be defined by being linked to a previous tool.  Set outputs and
      # check input/output paths.  For non-input/output files, just check for links to
      # other tools.
      if toolName in tl.toolOptions:
        toolLinkage = False
        if hasLinkageInformation: 
          if toolName in self.information['linkage']: toolLinkage = True

        for option in tl.toolOptions[toolName]:

          # Check that the option in the configuration file is valid.
          if option not in tl.toolInfo[tool]['options']:
            print(file = sys.stdout)
            er.invalidOption('linkage', option, toolName)
            er.terminate()

          isInput    = False
          isOutput   = False
          isResource = False
          if tl.toolInfo[tool]['options'][option]['input'] == 'true': isInput = True
          if tl.toolInfo[tool]['options'][option]['output'] == 'true': isOutput = True

          # Check if this option is linked to any other commands.
          optionLinkage = False
          if toolLinkage:
            if option in self.information['linkage'][toolName]: optionLinkage = True

          # Perform necessary tasks for input and output files.
          if isInput or isOutput:
            try:
              if tl.toolInfo[tool]['options'][option]['resource'] == 'true': isResource = True
            except: er.optionAssociationError('resource', option, tool)
            if er.error:
              print(file = sys.stdout)
              er.terminate()

            # First, check for linkage to another tool.
            self.checkLinkage(tl, optionLinkage, toolName, tool, option)

          # Deal with input files.
          if isInput:

            # If the input file is required and undefined, terminate the script.
            required = 'true'
            try: required = tl.toolInfo[tool]['options'][option]['required']
            except: er.optionAssociationError('required', option, tool)
            if er.error:
              print(file = sys.stdout)
              er.terminate()

            if (required == 'true') and (tl.toolOptions[toolName][option] == ''):

              # Before writing the error to screen, check if this input has a pipeline command.
              # For example, a tool may require option -A as an input, but the pipeline has a
              # command --input which links to -A in the tool.  The error message is of more use
              # to the user if the stated missing command is --input as the -A option would need
              # to be set in context of the tool.
              hasPipelineOption = False
              linkedOption      = ""
              altOption         = ""
              for pipelineOption in self.information['arguments']:
                if 'tool' in self.information['arguments'][pipelineOption]: linkedTool = self.information['arguments'][pipelineOption]['tool']
                if 'command' in self.information['arguments'][pipelineOption]: linkedOption = self.information['arguments'][pipelineOption]['command']
                if linkedOption == option:
                  hasPipelineOption = True
                  if 'alternative' in self.information['arguments'][pipelineOption]:
                    altOption = self.information['arguments'][pipelineOption]['alternative']
                  break
              print(file = sys.stdout)
              er.inputFileError(tool, option)
              if hasPipelineOption: er.pipelineOption(linkedTool, pipelineOption, altOption)
              er.terminate()

          # and output files.
          elif isOutput:

            # If the output is not defined (and linkage has already been checked), set the
            # output file name based on the pl.name value and the output extension.
            if tl.toolOptions[toolName][option] == '':

              # Determine if the output is a stub.  If so, no extension is required.
              isStub = False
              if 'stub' in tl.toolInfo[tool]['options'][option]:
                if tl.toolInfo[tool]['options'][option]['stub'] == 'true': isStub = True

              if isStub: extension = ''
              else:
                try:
                  extension = tl.toolInfo[tool]['options'][option]['extension']
                except:
                  er.optionAssociationError('extension', option, tool)
                if er.error:
                  print(file = sys.stdout)
                  er.terminate()
                extension = '.' + extension

              # Check that the --name option has a value.
              if self.options['--name'] == '': er.blankName()
              tl.toolOptions[toolName][option] = self.options['--name'] + extension

          # Perform tasks for non-input and output files.
          else: self.checkLinkage(tl, optionLinkage, toolName, tool, option)

          # Remove this linked option from the list.
          if toolName in linkedOptions:
            if option in linkedOptions[toolName]: linkedOptions[toolName][option] = False

      print("done.", file = sys.stdout)

    # Check the list of linked options and ensure that they have all been parsed.  Any
    # options that have not been handled are either special cases, or an error in the
    # configuration file.
    for toolName in linkedOptions:
      for option in linkedOptions[toolName]:
        if linkedOptions[toolName][option]:
          if option == 'json parameters':
            self.checkLinkage(tl, True, toolName, tool, option)
          else:
            er.invalidOption('linkage', option, toolName)
            er.terminate()
    print(file = sys.stdout)

  # Check to see if a tool option is linked to another tool and modify the stored
  # value accordingly.
  def checkLinkage(self, tl, optionLinkage, toolName, tool, option):
    er = errors()

    if optionLinkage:
      targetToolName = ''
      try: targetToolName = self.information['linkage'][toolName][option]['tool']
      except: er.optionAssociationError('tool', option, tool)
      if er.error:
        print(file = sys.stdout)
        er.terminate()

      targetOption   = ''
      try: targetOption   = self.information['linkage'][toolName][option]['command']
      except: er.optionAssociationError('command', option, tool)
      if er.error:
        print(file = sys.stdout)
        er.terminate()

      # Check that the targetToolName and the targetOption are valid.
      if targetToolName not in tl.toolOptions:
        print(file = sys.stdout)
        er.invalidToolName('linkage', targetToolName)
        er.terminate()

      if targetOption not in tl.toolOptions[targetToolName]:
        print(file = sys.stdout)
        er.invalidOption('linkage', targetOption, targetToolName)
        er.terminate()

      # If the linkage block contains 'extension', the linked value requires this
      # extension adding to the end of the value.
      extension = ''
      if 'extension' in self.information['linkage'][toolName][option]:
        tl.toolOptions[toolName][option] = tl.toolOptions[targetToolName][targetOption] + self.information['linkage'][toolName][option]['extension']
      else:
        tl.toolOptions[toolName][option] = tl.toolOptions[targetToolName][targetOption]

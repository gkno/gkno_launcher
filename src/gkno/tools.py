#!/usr/bin/python

from __future__ import print_function
import os
import sys

import errors
from errors import *

class tools:

  # Initialise the tools class.
  def __init__(self):

    # Set up a list of top level fields that must be present for all tools.
    self.requiredFields = []
    self.requiredFields.append('description')
    self.requiredFields.append('help')
    self.requiredFields.append('path')
    self.requiredFields.append('executable')
    self.requiredFields.append('arguments')
    self.requiredFields.append('instances')

    # The configuration file contains arguments for each tool.  Each argument also has a
    # set of required fields that must be checked.
    self.requiredArgumentFields = []
    self.requiredArgumentFields.append('description')
    self.requiredArgumentFields.append('dependent')
    self.requiredArgumentFields.append('extension')
    self.requiredArgumentFields.append('input')
    self.requiredArgumentFields.append('output')
    self.requiredArgumentFields.append('required')
    self.requiredArgumentFields.append('resource')
    self.requiredArgumentFields.append('type')

    # Setup some structures to hold information on each of the tools.
    self.additionalFiles            = {}
    self.arguments                  = {}
    self.argumentInformation        = {}
    self.argumentDelimiters         = {}
    self.argumentOrder              = {}
    self.availableTools             = []
    self.descriptions               = {}
    self.executables                = {}
    self.instances                  = {}
    self.modifiers                  = {}
    self.paths                      = {}
    self.precommands                = {}
    self.shortForms                 = {}
    self.hiddenTools                = {}
    self.toolsDemandingInputStream  = {}
    self.toolsDemandingOutputStream = {}

    #TODO Remove these when the new system is implemented.
    self.dependencies               = {}
    self.originalToolArguments      = {}
    self.outputs                    = {}
    self.tool                       = ''
    self.toolInfo                   = {}
    self.toolArguments              = {}

  # Given JSON data from a tool configuration file, check that everything contained within.
  # the file is allowed.  The allowed values for the configuration file are defined in the
  # initialisation of the tools object.
  def checkToolConfigurationFile(self, data, filename, verbose):
    er = errors()

    # Ensure that the configuration file contains tools.
    if 'tools' not in data:
      er.missingToolsBlockInConfig(False, filename)
      er.terminate()

    # Loop over all of the tools contained in the configuration file.
    for tool in data['tools']:

      # Store the name of the tools.
      self.availableTools.append(tool)
      self.observedFields = {}
      hasArgumentOrder    = False

      for  field in data['tools'][tool]:

        # Following is a list of all the allowed blocks in the configuration file.  Each is checked
        # for errors before proceeding.
        if field == 'additional files': self.checkAdditionalFiles(tool, data['tools'][tool][field], filename)
        elif field == 'arguments': self.checkArguments(tool, data['tools'][tool][field], filename)
        elif field == 'argument delimiter': self.checkArgumentDelimiter(tool, data['tools'][tool][field], filename)
        elif field == 'description': self.checkDescription(tool, data['tools'][tool][field], filename)
        elif field == 'executable': self.checkExecutable(tool, data['tools'][tool][field], filename)
        elif field == 'help': self.checkHelp(tool, data['tools'][tool][field], filename)
        elif field == 'hide tool': self.checkHideTool(tool, data['tools'][tool][field], filename)
        elif field == 'input is stream': self.checkInputStream(tool, data['tools'][tool][field], filename)
        elif field == 'instances': self.checkInstances(tool, data['tools'][tool][field], filename)
        elif field == 'modifier': self.checkModifier(tool, data['tools'][tool][field], filename)
        elif field == 'output is stream': self.checkOutputStream(tool, data['tools'][tool][field], filename)
        elif field == 'path': self.checkPath(tool, data['tools'][tool][field], filename)
        elif field == 'precommand': self.checkPrecommand(tool, data['tools'][tool][field], filename)

        # The argument order needs to be checked against the tool arguments.  This is deferred until the
        # end of this step to ensure that the arguments have been processed prior to performing the checks.
        elif field == 'argument order': hasArgumentOrder = True

        # If the field is anything other than those objects listed above, this is an
        # unrecognised field and gkno will terminate citing problems with the configuration file.
        else:
          er.undefinedFieldInConfig(False, filename, tool, field)
          er.terminate()

      # Now check the argument order field, if this was present.
      if hasArgumentOrder: self.checkArgumentOrder(tool, data['tools'][tool]['argument order'], filename)

      # Having checked that everything present in the configuration file is valid, ensure that
      # there are no omissions of required fields.  The dictionary requiredFields contains the
      # required top level fields for checking.
      missingVariables = []
      for field in self.requiredFields:
        if field not in self.observedFields: missingVariables.append(field)

      if len(missingVariables) > 0:
        er.missingRequiredFieldInConfig(False, filename, tool, missingVariables)
        er.terminate()

  # Check the validity of the configuration file block by block.  Start with the description.
  def checkDescription(self, tool, description, filename):
    er            = errors()
    givenType     = type(description)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'description', givenType, str)
      er.terminate()
    self.observedFields['description'] = True
    self.descriptions[tool]            = description

  # ...executable...
  def checkExecutable(self, tool, executable, filename):
    er            = errors()
    givenType     = type(executable)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'executable', givenType, str)
      er.terminate()
    self.observedFields['executable'] = True
    self.executables[tool]            = executable

  # ...help...
  def checkHelp(self, tool, helpMessage, filename):
    er            = errors()
    givenType     = type(helpMessage)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'help', givenType, str)
      er.terminate()
    self.observedFields['help'] = True

  # ...path...
  def checkPath(self, tool, path, filename):
    er            = errors()
    givenType     = type(path)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'path', givenType, str)
      er.terminate()
    self.observedFields['path'] = True
    self.paths[tool]            = path

  # ...precommand...
  def checkPrecommand(self, tool, precommand, filename):
    er            = errors()
    givenType     = type(precommand)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'precommand', givenType, str)
      er.terminate()
    self.observedFields['precommand'] = True
    self.precommands[tool]            = precommand

  # ...modifier...
  def checkModifier(self, tool, modifier, filename):
    er            = errors()
    givenType     = type(modifier)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'modifier', givenType, str)
      er.terminate()
    self.observedFields['modifier'] = True
    self.modifiers[tool]            = modifier

  # ...argument delimiter...
  def checkArgumentDelimiter(self, tool, delimiter, filename):
    er            = errors()
    givenType     = type(delimiter)
    if givenType != str:
      er.differentDataTypeInConfig(False, filename, tool, 'delimiter', givenType, str)
      er.terminate()
    self.observedFields['argument delimiter'] = True
    self.argumentDelimiters[tool]             = delimiter

  # ...arguments...
  def checkArguments(self, tool, arguments, filename):
    er            = errors()
    givenType     = type(arguments)
    if givenType != dict:
      er.differentDataTypeInConfig(False, filename, tool, 'arguments', givenType, dict)
      er.terminate()

    # Now parse through all of the arguments and check the contents of each entry in the
    # arguments field.  Any string is allowed as an argument, but each argument must contain
    # some fields.  Optional fields are also checked and unknown fields will call gkno to
    # terminate.
    for argument in arguments:
      givenType     = type(arguments[argument])
      if givenType != dict:
        er.differentDataTypeInConfig(False, filename, tool, 'arguments -> ' + str(argument), givenType, dict)
        er.terminate()

      # Parse through all entries for this argument.
      self.observedArgumentFields = {}
      for field in arguments[argument]:
        if field == 'allow multiple definitions': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'apply by repeating this argument': self.checkRepeatArgument(tool, arguments, argument, field, str, filename)
        elif field == 'default': self.checkGeneralField(tool, arguments[argument][field], field, list, filename)
        elif field == 'dependent': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'description': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'do not construct filename from input': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'extension': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'if input is stream': self.checkArgumentInputStream(tool, arguments[argument], argument, field, arguments[argument][field], filename)
        elif field == 'if output is stream': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'if output to stream': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'input': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'list of input files': self.checkInputList(tool, argument, arguments[argument], field, filename)
        elif field == 'modify argument name on command line': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'output': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'outputs': self.checkArgumentOutputs(tool, argument, arguments[argument][field], filename)
        elif field == 'required': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'resource': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'replace argument with': pass
        elif field == 'short form argument': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'stub': self.checkArgumentStub(tool, arguments[argument], argument, arguments[argument][field], filename)
        elif field == 'type': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'use for filenames': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)

        # If the field is unknown, terminate.
        else:
          er.undefinedFieldInConfig(False, filename, tool, 'arguments -> ' + str(argument) + ' -> ' + str(field))
          er.terminate()

      # Now check that all of the required fields for this argument were present.
      missingVariables = []
      for field in self.requiredArgumentFields:
        if field not in self.observedArgumentFields: missingVariables.append('arguments -> ' + argument + ' -> ' + field)

      if len(missingVariables) > 0:
        er.missingRequiredFieldInConfig(False, filename, tool, missingVariables)
        er.terminate()

    # Update the self.argumentInformation structure to include the arguments for this tool.
    self.argumentInformation[tool] = arguments
    self.observedFields['arguments'] = True

  # ...hide tool...
  def checkHideTool(self, tool, hiddenTool, filename):
    er            = errors()
    givenType     = type(hiddenTool)
    if givenType != bool:
      er.differentDataTypeInConfig(False, filename, tool, 'hidden tools', givenType, bool)
      er.terminate()
    self.observedFields['hide tool'] = True
    self.hiddenTools[tool] = hiddenTool

  # ...argument order...
  def checkArgumentOrder(self, tool, argumentOrder, filename):
    er            = errors()
    givenType     = type(argumentOrder)
    if givenType != list:
      er.differentDataTypeInConfig(False, filename, tool, 'argument order', givenType, list)
      er.terminate()

    # Parse through the contents of the list and ensure that the list is a complete list of all
    # the arguments for this tool and no more.
    for argument in argumentOrder:
      if argument not in self.argumentInformation[tool]:
        er.unknownArgumentInArgumentOrder(False, filename, tool, argument)
        er.terminate()

    # Then parse through the arguments for the tools and ensure that the argument order list
    # is exhaustive.
    for argument in self.argumentInformation[tool]:
      if argument not in argumentOrder:
        er.argumentMissingFromArgumentOrder(False, filename, tool, argument)
        er.terminate()

    self.argumentOrder[tool]              = argumentOrder
    self.observedFields['argument order'] = True

  # ...output is stream...
  def checkOutputStream(self, tool, outputStream, filename):
    er            = errors()
    givenType     = type(outputStream)
    if givenType != bool:
      er.differentDataTypeInConfig(False, filename, tool, 'output is stream', givenType, bool)
      er.terminate()
    self.observedFields['output is stream'] = True
    self.toolsDemandingOutputStream[tool] = outputStream

  # ...input is stream...
  def checkInputStream(self, tool, inputStream, filename):
    er            = errors()
    givenType     = type(inputStream)
    if givenType != bool:
      er.differentDataTypeInConfig(False, filename, tool, 'input is stream', givenType, bool)
      er.terminate()
    self.observedFields['input is stream'] = True
    self.toolsDemandingInputStream[tool] = inputStream

  # ...additional files...
  def checkAdditionalFiles(self, tool, arguments, filename):
    er       = errors()
    required = []
    required.append('type')
    required.append('link to this argument')
    required.append('remove extension')
    required.append('add extension')
    required.append('output extension')
    required.append('stub')

    # The only allowed fields within the 'additional fields' section are:
    #   1. from input argument.
    #
    # Check that these are the only observed fields, and that their contents are as expected.
    for field in arguments:
      if field == 'from input arguments':

        if type(arguments[field]) != list:
          er.differentDataTypeInConfig(False, filename, tool, field, type(arguments[field]), list)
          er.terminate()

        # Check that the field is a list and that the list contents are dictionaries and that their
        # contents are as expected.
        for entry in arguments[field]:
          if type(entry) != dict:
            er.differentDataTypeInConfig(False, filename, tool, field + ' -> ' + entry, type(entry), dict)
            er.terminate()

          # Check the contents of each of the dictionaries.
          for information in entry:

            # The 'type' field can take the values "output" or "dependency".
            if information == 'type':
              if entry[information] != 'output' and entry[information] != 'dependency':
                er.typeInAdditionalFieldsError(False, filename, tool, entry[information])
                er.terminate()

            # The "link to his argument field must link to an argument for this tool.
            elif information == 'link to this argument':
              if entry[information] not in self.argumentInformation[tool]:
                er.unknownArgumentInAdditionalFiles(False, filename, tool, entry[information])
                er.terminate()

            # Check that the remove/add extension field is a Boolean.
            elif information == 'remove extension':
              if type(entry[information]) != bool:
                er.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                er.terminate()

            elif information == 'add extension':
              if type(entry[information]) != bool:
                er.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                er.terminate()

            elif information == 'output extension': pass

            # Check that the stub field is a Boolean.
            elif information == 'stub':
              if type(entry[information]) != bool:
                er.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                er.terminate()

            else:
              er.unknownFieldInAdditionalFilesDictionary(False, filename, tool, information)
              er.terminate()
          

          # Check that all of the required fields are present.
          for information in required:
            if information not in entry:
              er.missingFieldInAdditionalFiles(False, filename, tool, information, required)
              er.terminate()

      # If the field is not known.
      else:
        er.unknownFieldInAdditionalFiles(False, filename, tool, field)
        er.terminate()

    self.additionalFiles[tool]              = arguments
    self.observedFields['additional files'] = True

  # ...instances...
  def checkInstances(self, tool, instances, filename):
    er            = errors()
    givenType     = type(instances)
    if givenType != dict:
      er.differentDataTypeInConfig(False, filename, tool, 'instances', givenType, dict)
      er.terminate()
    self.observedFields['instances'] = True
    for instance in instances: self.instances[instance] = instances[instance]

  # If the field for an argument is expected to be of a specific type, check that it is.
  def checkGeneralField(self, tool, value, text, expectedType, filename):
    er            = errors()
    givenType     = type(value)
    if givenType != expectedType:
      er.differentDataTypeInConfig(False, filename, tool, text, givenType, expectedType)
      er.terminate()
    self.observedArgumentFields[text] = True

  def checkRepeatArgument(self, tool, arguments, argument, field, expectedType, filename):
    er            = errors()
    value         = arguments[argument][field]
    givenType     = type(value)
    if givenType != expectedType:
      er.differentDataTypeInConfig(False, filename, tool, field, givenType, expectedType)
      er.terminate()

    # Now check that the value is an argument for this tool.
    if value not in arguments:
      text = 'arguments -> ' + argument + ' -> ' + field
      er.invalidArgumentInRepeat(False, filename, tool, argument, text, value)
      er.terminate()
    self.observedArgumentFields[field] = True

  # If the argument input is the stream, there are a number of ways that gkno can be instructed
  # to modify the command line.  Check that the value given is valid and that any further information
  # required is present.
  def checkArgumentInputStream(self, tool, arguments, argument, field, value, filename):
    er = errors()
    if value == 'do not include': self.checkGeneralField(tool, value, field, str, filename)
    elif value == 'replace':
      if 'replace argument with' not in arguments:
        er.replaceArgumentMissing(False, filename, tool, field)
        er.terminate()

      # If the "replace argument with" field is present, check that it is a dictionary containing an alternative
      # argument and value to use.
      givenType = type(arguments['replace argument with'])
      text = 'arguments -> ' + argument + ' -> replace argument with'
      if givenType != dict:
        er.differentDataTypeInConfig(False, filename, tool, text, givenType, dict)
        er.terminate()

      # Check the contents.
      if 'argument' not in arguments['replace argument with']:
        er.missingFieldInReplace(False, filename, tool, text, 'argument')
        er.terminate()
      if 'value' not in arguments['replace argument with']:
        er.missingFieldInReplace(False, filename, tool, text, 'value')
        er.terminate()

      # and finally check that the "argument" and "value" fields are strings.
      givenType = type(arguments['replace argument with']['argument'])
      if givenType != str:
        er.differentDataTypeInConfig(False, filename, tool, text + ' -> argument', givenType, str)
        er.terminate()

      givenType = type(arguments['replace argument with']['value'])
      if givenType != str:
        er.differentDataTypeInConfig(False, filename, tool, text + ' -> value', givenType, str)
        er.terminate()

    # If the value is unknown to gkno, terminate.
    else:
      text = 'arguments -> ' + argument + ' -> if input is stream' + ' -> ' + value
      er.undefinedFieldInConfig(False, filename, tool, text)
      er.terminate()

  # If the argument contains the 'outputs' field, this needs to be a list of outputs outputted by
  # the tool.  Check that is is a list of strings.
  def checkArgumentOutputs(self, tool, argument, value, filename):
    er = errors()

    # First check that the value for the 'outputs' argument is a list.
    givenType = type(value)
    text      = 'arguments -> ' + argument + ' -> outputs'
    if givenType != list:
      er.differentDataTypeInConfig(False, filename, tool, text, givenType, list)
      er.terminate()

    # Now check that the list contains strings only.
    for field in value:
      givenType = type(field)
      text      = 'arguments -> ' + argument + ' -> outputs'
      if givenType != str:
        er.differentDataTypeInConfig(False, filename, tool, text, givenType, str)
        er.terminate()

  # If the 'stub' field is present, ensure that the value is a Boolean and that the outputs field is
  # also present.
  def checkArgumentStub(self, tool, arguments, argument, value, filename):
    er = errors()

    # First check that the value is a Boolean.
    givenType = type(value)
    if givenType != bool:
      text = 'arguments -> ' + argument + ' -> stub'
      er.differentDataTypeInConfig(False, filename, tool, text, givenType, bool)
      er.terminate()

    # ...then check that the 'outputs' field is also present.  It's contents are checked elsewhere
    # if it is present, so only its presence is checked for here.
    if 'outputs' not in arguments:
      text = 'arguments -> ' + argument + ' -> outputs'
      er.missingOutputsForStub(False, filename, tool, argument, text)
      er.terminate()

  # If the 'input is list' field is present, ensure that the accompanying value is a 
  # Boolean and that the "apply by repeating this argument" is also present.
  def checkInputList(self, tool, argument, arguments, field, filename):
    er            = errors()
    value         = arguments[field]
    givenType     = type(value)
    if givenType != bool:
      er.differentDataTypeInConfig(False, filename, tool, 'list of input files', givenType, bool)
      er.terminate()
    self.observedArgumentFields['list of input files'] = True

    # Check that the "apply by repeating this argument" is also present.
    if value and 'apply by repeating this argument' not in arguments:
      text = 'arguments -> ' + argument + ' -> apply by repeating this argument'
      er.missingArgumentToRepeat(False, filename, tool, argument, text)
      er.terminate()

  # Parse through the allowed arguments for each tool and check if they have a short form
  # equivalent.  If so, add them to the shortForms dictionary.
  def setupShortFormArguments(self):
    for tool in self.argumentInformation:
      self.shortForms[tool] = {}
      for argument in self.argumentInformation[tool]:
        if 'short form argument' in self.argumentInformation[tool][argument]:
          shortForm = self.argumentInformation[tool][argument]['short form argument']
          self.shortForms[tool][shortForm] = argument

  # If gkno is being run in the single tool mode, check that the specified tool
  # exists.
  def checkTool(self, gknoHelp):
    if self.tool not in self.availableTools:
      gknoHelp.toolHelp    = True
      gknoHelp.printHelp   = True
      gknoHelp.unknownTool = True

  # Loop over all of the allowed arguments for each tool and build up the arguments structure
  # containing all of the defaults from the configuration file.
  def getDefaults(self, workflow, tools, arguments, shortForms, verbose):
    er = errors()

    for task in workflow:
      tool = tools[task]
      self.arguments[task] = {}
      for argument in arguments[tool]:

        # Check if the argument has a default value.
        if 'default' in arguments[tool][argument]:
          self.arguments[task][argument] = arguments[tool][argument]['default']
          shortForm                      = shortForms[argument] if argument in shortForms else ''

          # Check that the given values are valid.
          for value in self.arguments[task][argument]:
            givenType = type(value)
            dataType  = arguments[tool][argument]['type']

            # If the argument expects a Boolean, check that the given value is either 'true', 'True', 'false' or
            # 'False'.
            if dataType == 'bool':

              # Ensure that a valid argument has been provided.
              if (value == 'true') or (value == 'True'): value = True
              elif (value == 'false') or (value == 'False'): value = False
              else:
                er.incorrectDefaultBooleanValue(verbose, task, argument, shortForm, value)
                er.terminate()
          
            # If the argument demands a string, no checks are required.
            elif dataType == 'string': pass
          
            # If the argument demands an integer, check that the supplied value is an integer.
            elif (dataType == 'integer'):
              try: value = int(value)
              except: er.incorrectDefaultDataType(verbose, task, argument, shortForm, value, 'integer')
              if er.error: er.terminate()
          
            # If the argument demands a floating point...
            elif dataType == 'float':
              try: value = float(value)
              except: er.incorrectDefaultDataType(verbose, task, argument, shortForm, value, 'float')
              if er.error: er.terminate()





















  # Reset the tl.toolArguments structure.
  def resetDataStructures(self, pl):
    self.toolArguments = {}
    for task in self.originalToolArguments:
      if task not in self.toolArguments: self.toolArguments[task] = {}
      for argument in self.originalToolArguments[task]:
        if argument not in self.toolArguments[task]: self.toolArguments[task][argument] = {}
        self.toolArguments[task][argument] = self.originalToolArguments[task][argument]

    # Also reset the toolInfo structure.  If tools were streamed together, some
    # additional options have been added to toolInfo, but the added options were
    # tracked in the pl.addedToToolInfo structure.
    #TODO pl.addedToToolInfo has been modified to make.addedInformation.
    for task in pl.addedToToolInfo:
      for argument in pl.addedToToolInfo[task]:
        if argument in self.toolInfo[task]['arguments']: del(self.toolInfo[task]['arguments'][argument])

    # Reset other data structures.
    self.dependencies  = {}
    self.outputs       = {}
    pl.deleteFiles     = {}
    pl.finalOutputs    = {}
    pl.streamedOutputs = {}
    pl.taskBlocks      = []

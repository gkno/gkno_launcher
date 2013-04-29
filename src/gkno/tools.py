#!/usr/bin/python

from __future__ import print_function
import os
import sys

import errors
from errors import *

class tools:

  # Initialise the tools class.
  def __init__(self):
    self.errors = errors()

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
    self.generatedFiles             = {}
    self.instances                  = {}
    self.modifiers                  = {}
    self.paths                      = {}
    self.precommands                = {}
    self.shortForms                 = {}
    self.hiddenTools                = {}
    self.tool                       = ''
    self.toolsDemandingInputStream  = {}
    self.toolsDemandingOutputStream = {}

  # Given JSON data from a tool configuration file, check that everything contained within.
  # the file is allowed.  The allowed values for the configuration file are defined in the
  # initialisation of the tools object.
  def checkToolConfigurationFile(self, data, filename, verbose):

    # Ensure that the configuration file contains tools.
    if 'tools' not in data:
      self.errors.missingToolsBlockInConfig(False, filename)
      self.errors.terminate()

    # Loop over all of the tools contained in the configuration file.
    for tool in data['tools']:

      # Store the name of the tools.
      self.availableTools.append(tool)
      self.observedFields = {}
      hasArgumentOrder    = False

      for field in data['tools'][tool]:

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
          self.errors.undefinedFieldInConfig(False, filename, tool, field)
          self.errors.terminate()

      # Now check the argument order field, if this was present.
      if hasArgumentOrder: self.checkArgumentOrder(tool, data['tools'][tool]['argument order'], filename)

      # Having checked that everything present in the configuration file is valid, ensure that
      # there are no omissions of required fields.  The dictionary requiredFields contains the
      # required top level fields for checking.
      missingVariables = []
      for field in self.requiredFields:
        if field not in self.observedFields: missingVariables.append(field)

      if len(missingVariables) > 0:
        self.errors.missingRequiredFieldInConfig(False, filename, tool, missingVariables)
        self.errors.terminate()

  # Check the validity of the configuration file block by block.  Start with the description.
  def checkDescription(self, tool, description, filename):
    givenType     = type(description)
    if not isinstance(description, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'description', givenType, str)
      self.errors.terminate()
    self.observedFields['description'] = True
    self.descriptions[tool]            = description

  # ...executable...
  def checkExecutable(self, tool, executable, filename):
    givenType     = type(executable)
    if not isinstance(executable, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'executable', givenType, str)
      self.errors.terminate()
    self.observedFields['executable'] = True
    self.executables[tool]            = executable

  # ...help...
  def checkHelp(self, tool, helpMessage, filename):
    givenType     = type(helpMessage)
    if not isinstance(helpMessage, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'help', givenType, str)
      self.errors.terminate()
    self.observedFields['help'] = True

  # ...path...
  def checkPath(self, tool, path, filename):
    givenType     = type(path)
    if not isinstance(path, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'path', givenType, str)
      self.errors.terminate()
    self.observedFields['path'] = True
    self.paths[tool]            = path

  # ...precommand...
  def checkPrecommand(self, tool, precommand, filename):
    givenType     = type(precommand)
    if not isinstance(precommand, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'precommand', givenType, str)
      self.errors.terminate()
    self.observedFields['precommand'] = True
    self.precommands[tool]            = precommand

  # ...modifiself.errors...
  def checkModifier(self, tool, modifier, filename):
    givenType     = type(modifier)
    if not isinstance(modifier, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'modifier', givenType, str)
      self.errors.terminate()
    self.observedFields['modifier'] = True
    self.modifiers[tool]            = modifier

  # ...argument delimitself.errors...
  def checkArgumentDelimiter(self, tool, delimiter, filename):
    givenType     = type(delimiter)
    if not isinstance(delimiter, basestring):
      self.errors.differentDataTypeInConfig(False, filename, tool, 'delimiter', givenType, str)
      self.errors.terminate()
    self.observedFields['argument delimiter'] = True
    self.argumentDelimiters[tool]             = delimiter

  # ...arguments...
  def checkArguments(self, tool, arguments, filename):
    givenType     = type(arguments)
    if givenType != dict:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'arguments', givenType, dict)
      self.errors.terminate()

    # Now parse through all of the arguments and check the contents of each entry in the
    # arguments field.  Any string is allowed as an argument, but each argument must contain
    # some fields.  Optional fields are also checked and unknown fields will call gkno to
    # terminate.
    for argument in arguments:
      givenType     = type(arguments[argument])
      if givenType != dict:
        self.errors.differentDataTypeInConfig(False, filename, tool, 'arguments -> ' + str(argument), givenType, dict)
        self.errors.terminate()

      # Parse through all entries for this argument.
      self.observedArgumentFields = {}
      for field in arguments[argument]:
        if field == 'allow multiple definitions': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'apply by repeating this argument': self.checkRepeatArgument(tool, arguments, argument, field, str, filename)
        elif field == 'default': self.checkGeneralField(tool, arguments[argument][field], field, list, filename)
        elif field == 'dependent': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'description': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'directory': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'do not construct filename from input': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'extension': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'generated files': self.checkGeneratedFiles(tool, argument, arguments[argument][field], field, list, filename)
        elif field == 'if input is stream': self.checkArgumentInputStream(tool, arguments[argument], argument, field, arguments[argument][field], filename)
        elif field == 'if output is stream': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'if output to stream': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'input': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'list of input files': self.checkInputList(tool, argument, arguments[argument], field, filename)
        elif field == 'modify argument name on command line': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'output': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'outputs': self.checkArgumentOutputs(tool, argument, arguments[argument][field], filename)
        elif field == 'required': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)
        elif field == 'replace argument with': pass
        elif field == 'short form argument': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'stub': self.checkArgumentStub(tool, arguments[argument], argument, arguments[argument][field], filename)
        elif field == 'type': self.checkGeneralField(tool, arguments[argument][field], field, str, filename)
        elif field == 'use for filenames': self.checkGeneralField(tool, arguments[argument][field], field, bool, filename)

        # If the field is unknown, terminate.
        else:
          self.errors.undefinedFieldInConfig(False, filename, tool, 'arguments -> ' + str(argument) + ' -> ' + str(field))
          self.errors.terminate()

      # Now check that all of the required fields for this argument were present.
      missingVariables = []
      for field in self.requiredArgumentFields:
        if field not in self.observedArgumentFields: missingVariables.append('arguments -> ' + argument + ' -> ' + field)

      if len(missingVariables) > 0:
        self.errors.missingRequiredFieldInConfig(False, filename, tool, missingVariables)
        self.errors.terminate()

    # Update the self.argumentInformation structure to include the arguments for this tool.
    self.argumentInformation[tool] = arguments
    self.observedFields['arguments'] = True

  # ...hide tool...
  def checkHideTool(self, tool, hiddenTool, filename):
    givenType     = type(hiddenTool)
    if givenType != bool:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'hidden tools', givenType, bool)
      self.errors.terminate()
    self.observedFields['hide tool'] = True
    self.hiddenTools[tool] = hiddenTool

  # ...argument ordself.errors...
  def checkArgumentOrder(self, tool, argumentOrder, filename):
    givenType     = type(argumentOrder)
    if givenType != list:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'argument order', givenType, list)
      self.errors.terminate()

    # Parse through the contents of the list and ensure that the list is a complete list of all
    # the arguments for this tool and no more.
    for argument in argumentOrder:
      if argument not in self.argumentInformation[tool]:
        self.errors.unknownArgumentInArgumentOrder(False, filename, tool, argument)
        self.errors.terminate()

    # Then parse through the arguments for the tools and ensure that the argument order list
    # is exhaustive.
    for argument in self.argumentInformation[tool]:
      if argument not in argumentOrder:
        self.errors.argumentMissingFromArgumentOrder(False, filename, tool, argument)
        self.errors.terminate()

    self.argumentOrder[tool]              = argumentOrder
    self.observedFields['argument order'] = True

  # ...output is stream...
  def checkOutputStream(self, tool, outputStream, filename):
    givenType     = type(outputStream)
    if givenType != bool:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'output is stream', givenType, bool)
      self.errors.terminate()
    self.observedFields['output is stream'] = True
    self.toolsDemandingOutputStream[tool] = outputStream

  # ...input is stream...
  def checkInputStream(self, tool, inputStream, filename):
    givenType     = type(inputStream)
    if givenType != bool:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'input is stream', givenType, bool)
      self.errors.terminate()
    self.observedFields['input is stream'] = True
    self.toolsDemandingInputStream[tool] = inputStream

  # ...additional files...
  def checkAdditionalFiles(self, tool, arguments, filename):
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
          self.errors.differentDataTypeInConfig(False, filename, tool, field, type(arguments[field]), list)
          self.errors.terminate()

        # Check that the field is a list and that the list contents are dictionaries and that their
        # contents are as expected.
        for entry in arguments[field]:
          if type(entry) != dict:
            self.errors.differentDataTypeInConfig(False, filename, tool, field + ' -> ' + entry, type(entry), dict)
            self.errors.terminate()

          # Check the contents of each of the dictionaries.
          for information in entry:

            # The 'type' field can take the values "output" or "dependency".
            if information == 'type':
              if entry[information] != 'output' and entry[information] != 'dependency':
                self.errors.typeInAdditionalFieldsError(False, filename, tool, entry[information])
                self.errors.terminate()

            # The "link to his argument field must link to an argument for this tool.
            elif information == 'link to this argument':
              if entry[information] not in self.argumentInformation[tool]:
                self.errors.unknownArgumentInAdditionalFiles(False, filename, tool, entry[information])
                self.errors.terminate()

            # Check that the remove/add extension field is a Boolean.
            elif information == 'remove extension':
              if type(entry[information]) != bool:
                self.errors.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                self.errors.terminate()

            elif information == 'add extension':
              if type(entry[information]) != bool:
                self.errors.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                self.errors.terminate()

            elif information == 'output extension': pass

            # Check that the stub field is a Boolean.
            elif information == 'stub':
              if type(entry[information]) != bool:
                self.errors.incorrectBooleanInAdditionalFiles(False, filename, tool, information, entry[information])
                self.errors.terminate()

            else:
              self.errors.unknownFieldInAdditionalFilesDictionary(False, filename, tool, information)
              self.errors.terminate()


          # Check that all of the required fields are present.
          for information in required:
            if information not in entry:
              self.errors.missingFieldInAdditionalFiles(False, filename, tool, information, required)
              self.errors.terminate()

      # If the field is not known.
      else:
        self.errors.unknownFieldInAdditionalFiles(False, filename, tool, field)
        self.errors.terminate()

    self.additionalFiles[tool]              = arguments
    self.observedFields['additional files'] = True

  # ...instances...
  def checkInstances(self, tool, instances, filename):
    givenType     = type(instances)
    if givenType != dict:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'instances', givenType, dict)
      self.errors.terminate()
    self.observedFields['instances'] = True
    self.instances[tool]             = {}
    for instance in instances: self.instances[tool][instance] = instances[instance]

  # If the field for an argument is expected to be of a specific type, check that it is.
  def checkGeneralField(self, tool, value, text, expectedType, filename):
    givenType     = type(value)
    print('CHECK', tool, value, expectedType, givenType, givenType == expectedType)
    if ((givenType != expectedType) or
        (givenType == str and not isinstance(value, basestring))):
      self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, expectedType)
      self.errors.terminate()
    self.observedArgumentFields[text] = True

  def checkRepeatArgument(self, tool, arguments, argument, field, expectedType, filename):
    value         = arguments[argument][field]
    givenType     = type(value)
    if (givenType != expectedType and
        (givenType == str and not isinstance(value, basestring))):
      self.errors.differentDataTypeInConfig(False, filename, tool, field, givenType, expectedType)
      self.errors.terminate()

    # Now check that the value is an argument for this tool.
    if value not in arguments:
      text = 'arguments -> ' + argument + ' -> ' + field
      self.errors.invalidArgumentInRepeat(False, filename, tool, argument, text, value)
      self.errors.terminate()
    self.observedArgumentFields[field] = True

  def checkGeneratedFiles(self, tool, argument, arguments, field, expectedType, filename):
    givenType = type(arguments)
    if givenType != expectedType:
      text = 'arguments -> ' + argument + ' -> generated files'
      self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, list)
      self.errors.terminate()

    self.generatedFiles[tool] = arguments

  # If the argument input is the stream, there are a number of ways that gkno can be instructed
  # to modify the command line.  Check that the value given is valid and that any further information
  # required is present.
  def checkArgumentInputStream(self, tool, arguments, argument, field, value, filename):
    if value == 'do not include': self.checkGeneralField(tool, value, field, str, filename)
    elif value == 'replace':
      if 'replace argument with' not in arguments:
        self.errors.replaceArgumentMissing(False, filename, tool, field)
        self.errors.terminate()

      # If the "replace argument with" field is present, check that it is a dictionary containing an alternative
      # argument and value to use.
      givenType = type(arguments['replace argument with'])
      text = 'arguments -> ' + argument + ' -> replace argument with'
      if givenType != dict:
        self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, dict)
        self.errors.terminate()

      # Check the contents.
      if 'argument' not in arguments['replace argument with']:
        self.errors.missingFieldInReplace(False, filename, tool, text, 'argument')
        self.errors.terminate()
      if 'value' not in arguments['replace argument with']:
        self.errors.missingFieldInReplace(False, filename, tool, text, 'value')
        self.errors.terminate()

      # and finally check that the "argument" and "value" fields are strings.
      givenType = type(arguments['replace argument with']['argument'])
      if not isinstance(arguments['replace argument with']['argument'], basestring):
        self.errors.differentDataTypeInConfig(False, filename, tool, text + ' -> argument', givenType, str)
        self.errors.terminate()

      givenType = type(arguments['replace argument with']['value'])
      if not isinstance(arguments['replace argument with']['value'], basestring):
        self.errors.differentDataTypeInConfig(False, filename, tool, text + ' -> value', givenType, str)
        self.errors.terminate()

    # If the value is unknown to gkno, terminate.
    else:
      text = 'arguments -> ' + argument + ' -> if input is stream' + ' -> ' + value
      self.errors.undefinedFieldInConfig(False, filename, tool, text)
      self.errors.terminate()

  # If the argument contains the 'outputs' field, this needs to be a list of outputs outputted by
  # the tool.  Check that is is a list of strings.
  def checkArgumentOutputs(self, tool, argument, value, filename):

    # First check that the value for the 'outputs' argument is a list.
    givenType = type(value)
    text      = 'arguments -> ' + argument + ' -> outputs'
    if givenType != list:
      self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, list)
      self.errors.terminate()

    # Now check that the list contains strings only.
    for field in value:
      givenType = type(field)
      text      = 'arguments -> ' + argument + ' -> outputs'
      if not isinstance(field, basestring):
        self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, str)
        self.errors.terminate()

  # If the 'stub' field is present, ensure that the value is a Boolean and that the outputs field is
  # also present.
  def checkArgumentStub(self, tool, arguments, argument, value, filename):

    # First check that the value is a Boolean.
    givenType = type(value)
    if givenType != bool:
      text = 'arguments -> ' + argument + ' -> stub'
      self.errors.differentDataTypeInConfig(False, filename, tool, text, givenType, bool)
      self.errors.terminate()

    # ...then check that the 'outputs' field is also present.  It's contents are checked elsewhere
    # if it is present, so only its presence is checked for here.
    if 'outputs' not in arguments:
      text = 'arguments -> ' + argument + ' -> outputs'
      self.errors.missingOutputsForStub(False, filename, tool, argument, text)
      self.errors.terminate()

  # If the 'input is list' field is present, ensure that the accompanying value is a
  # Boolean and that the "apply by repeating this argument" is also present.
  def checkInputList(self, tool, argument, arguments, field, filename):
    value         = arguments[field]
    givenType     = type(value)
    if givenType != bool:
      self.errors.differentDataTypeInConfig(False, filename, tool, 'list of input files', givenType, bool)
      self.errors.terminate()
    self.observedArgumentFields['list of input files'] = True

    # Check that the "apply by repeating this argument" is also present.
    if value and 'apply by repeating this argument' not in arguments:
      text = 'arguments -> ' + argument + ' -> apply by repeating this argument'
      self.errors.missingArgumentToRepeat(False, filename, tool, argument, text)
      self.errors.terminate()

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
                self.errors.incorrectDefaultBooleanValue(verbose, task, argument, shortForm, value)
                self.errors.terminate()

            # If the argument demands a string, no checks are required.
            elif dataType == 'string': pass

            # If the argument demands an integer, check that the supplied value is an integself.errors.
            elif (dataType == 'integer'):
              try: value = int(value)
              except: self.errors.incorrectDefaultDataType(verbose, task, argument, shortForm, value, 'integer')
              if self.errors.hasError: self.errors.terminate()

            # If the argument demands a floating point...
            elif dataType == 'float':
              try: value = float(value)
              except: self.errors.incorrectDefaultDataType(verbose, task, argument, shortForm, value, 'float')
              if self.errors.hasError: self.errors.terminate()

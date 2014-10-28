#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import fileOperations

import json
import os
import sys

class argumentAttributes:
  def __init__(self):

    # If an argument is allowed to be set multiple times.
    self.allowMultipleValues      = False

    # Store the defined long and short form of the argument recognised as well
    # as the argument expected by the tool.
    self.commandLineArgument = None
    self.longFormArgument    = None
    self.shortFormArgument   = None

    # Define the extensions allowed for the argument.
    self.extensions = []

    # Store instructions on how to construct the filename.
    self.constructionInstructions = None

    # Record the argument description.
    self.description = None

    # Store the data type of the value supplied with this argument.
    self.dataType = None

    # Record id the argument points to a filename stub and store the 
    # associated extensions.
    self.filenameExtensions = None
    self.isFilenameStub     = False

    # Record if this argument should be hidden in the help.
    self.hideInHelp = False

    # Record the argument group to which the argument belongs.
    self.argumentGroup = None

    # If the values are to be written as a comma separated list.
    self.isCommaSeparatedList = False

    # Record if the argument is for an input or output file.
    self.isInput     = False
    self.isOutput    = False
    self.isTemporary = False

    # Store whether the argument can be suggested as a possible tool to use in a
    # pipeline builder.
    self.isSuggestible = False

    # Handle streaming inputs. inputStream is used to describe how to modify the command
    # line argument in the event that a stream is piped to the tool. isStream identifies
    # the argument which accepts the stream. If the tool is used in isolation (no pipe),
    # the tool can still be run, but the file associated with the argument identified with
    # isStream will be streamed to the tool.
    self.inputStream = False
    self.isStream    = False

    # If the argument is an inputList, it must also include information on the tool argument
    # that is set using all the values in the list.
    self.isRepeatedArgumentList = False
    self.isArgumentList         = False
    self.listValues             = None
    self.listArgument           = None
    self.listMode               = None

    # For some inputs, the path should not be included on the command line. The path is still
    # required for the dependency list, however. Store those files/directories listed as not
    # requiring the path on the command line. Also store the path to use if another command
    # provides the path.
    self.includePathOnCommandLine = True
    self.pathArgument             = None

    # Keep track of argument pointing to input or output directories.
    self.isDirectory = False

    # Keep track of required arguments.
    self.isRequired          = False
    self.isRequiredIfStream  = None

    # Some argument require the values to be in quotation marks on the command line. Store if this
    # is the case.
    self.inQuotations = False

    # Some arguments require that spaces are placed around mathematical operators. Record if this is
    # the case.
    self.inSpaces = False

    # gkno can modify hopw the argument is written on the command line, depending on the extension
    # provided. Store this information in the modifyValues structure.
    self.modifyValues = {}

    self.modifyArgument           = None
    self.outputStream             = False
    self.replaceArgument          = None

    # Record if the presence of the specified file/directory is not allowed prior
    # to execution.
    self.terminateIfPresent = False

    # If the argument has an argument to evaluate, store the instructions.
    self.commandToEvaluate = None
    self.commandEvaluation = commandEvaluation()

    # If another argument can be used to set this argument, store the argument. For example,
    # the argument may require an input file, but another tool argument defines a list of
    # input files that will use this argument.
    self.canBeSetByArgument = []

class commandEvaluation:
  def __init__(self):

    # If the command being evaluated is a replacement command line argument, the command
    # does not need to be included in '`' in the makefile. Record if the command is just
    # a replacement command line argument.
    self.isCommandLineArgument = False

    # Store the command.
    self.command = None

    # Store the values included in the command.
    self.values = {}

class toolConfiguration:
  def __init__(self):

    # Record the tool ID.
    self.id = None

    # Define the arguments associated with the tool.
    self.arguments = {}

    # Define the order in which the argument should be written.
    self.argumentOrder = []

    # Define the delimiter between the argument and the value on the
    # tool commmand line. This is usually a space.
    self.delimiter = ' '

    # A description of the tool.
    self.description = None

    # The categories to which the tool belongs.
    self.categories = ['General']

    # The tool executable and its path and any modifiers.
    self.executable = None
    self.modifier   = None
    self.path       = None
    self.precommand = None

    # Record if the input to this tool needs to be a stream.
    self.inputIsStream = False

    # Record if this tool is hidden in the help.
    self.isHidden = False

    # Some tools do not produce any outputs. If this is the case, the tool has to
    # be marked.
    self.noOutput = False

    # Store the tools that need to be compiled for this tool to be available.
    self.requiredCompiledTools = []

    # Store the URL for the tool.
    self.url = None

    # If the tool is untested, but available, the isExperimental flag can be set. This
    # will ensure that the tool is listed as experimental and urge caution in its use.
    self.isExperimental = False

    # If the tool has any arguments with commands to evaluate, record them.
    self.argumentsWithCommands = []

    # Define a structure to hold all the information about a tools arguments.
    self.argumentAttributes = {}

    # Define dictionaries to store the long and short form arguments.
    self.longFormArguments  = {}
    self.shortFormArguments = {}

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

  # Process the tool data.
  def getConfigurationData(self, filename):

    # Get the configuration file data.
    data = fileOperations.readConfigurationFile(filename, True)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

  # Process the configuration file data.
  def processConfigurationFile(self, data):

    # Parse the tool configuration file and check that all fields are valid. Ensure that there are
    # no errors, omissions or inconsistencies. Store the information in the relevant data structures
    # as the checks are performed.
    #
    # Check the general tool information.
    success = self.checkTopLevelInformation(data)

    # Check the validity of all of the supplied arguments.
    if success: success = self.checkToolArguments(data['arguments'])

    # Check general and argument attribute dependencies.
    #if success: success = self.checkAttributeDependencies(tool)

    # Generate a dictionary that links the long and short form arguments with each other..
    #if success: success = self.consolidateArguments(tool)

    # Check if a tool argument includes the pathArgument. If so, ensure that the supplied argument
    # is valid.
    #if success: success = self.checkPathArguments(tool)

    # Look to see if the 'argument order' section is present and check its validity.
    #if success: success = self.checkArgumentOrder(tool, self.attributes[tool])

    # If filename constuction instructions are provided, check that all is provided.
    #if success: success = self.checkConstructionInstructions(tool)

    # If any of the argument values can be modified on the command line, chcck that the
    # instructiobns are valid.
    #if success: success = self.checkModifyValues(tool)

    # If any arguments have the 'if input is stream' or the 'output to stream' fields, check that
    # all accompanying data is valid.
    #if success: success = self.checkStreams(tool)

    # If any argument lists were provided, check the values.
    #if success: success = self.checkListValues(tool)

    # If any of the arguments require the evaluation of a command, check the command is
    # correctly set up.
    #if success: success = self.checkCommands(tool)

    # Check if any of the arguments are input lists. If so, connect these to the arguments
    # that they use.
    #if success: success = self.connectArguments(tool)

    # Check that the category to which the tool is assigned is valid.
    #if success: success = self.checkCategory(tool, allowedCategories)

    return success

  # Check and store the top level tool attibutes.
  def checkTopLevelInformation(self, data):

    # Define the allowed values. The tuple contains the expected type and whether the
    # value is required, whether the value should be stored and finally the name in the
    # attributes data structure under which it should be stored..
    allowedAttributes                       = {}
    allowedAttributes['arguments']          = (dict, True, False, None)
    allowedAttributes['argument delimiter'] = (str, False, True, 'delimiter')
    allowedAttributes['argument order']     = (list, False, True, 'argumentOrder')
    allowedAttributes['categories']         = (list, True, True, 'categories')
    allowedAttributes['description']        = (str, True, True, 'description')
    allowedAttributes['executable']         = (str, True, True, 'executable')
    allowedAttributes['experimental']       = (bool, False, True, 'isExperimental')
    allowedAttributes['help']               = (str, True, False, None)
    allowedAttributes['hide tool']          = (bool, False, True, 'isHidden')
    allowedAttributes['id']                 = (str, True, True, 'id')
    allowedAttributes['input is stream']    = (bool, False, True, 'inputIsStream')
    allowedAttributes['parameter sets']     = (list, True, False, None)
    allowedAttributes['modifier']           = (str, False, True, 'modifier')
    allowedAttributes['path']               = (str, True, True, 'path')
    allowedAttributes['precommand']         = (str, False, True, 'precommand')
    allowedAttributes['no output']          = (bool, False, True, 'noOutput')
    allowedAttributes['tools']              = (list, True, True, 'requiredCompiledTools')
    allowedAttributes['url']                = (str, False, True, 'url')

    # Keep track of the observed required values.
    observedAttributes = {}

    # Loop over all of the attributes in the configuration file.
    for attribute in data:

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if attribute not in allowedAttributes:
        #TODO ERROR
        if self.allowTermination: print('tool.checkGeneralAttributes - 1'); exit(0) #invalidGeneralAttributeInConfigurationFile
        else: return False

      # Mark this values as having been observed,
      observedAttributes[attribute] = True

      # Check that the value given to the attribute is of the correct type. If the value is unicode,
      # convert to a string first.
      value = str(data[attribute]) if isinstance(data[attribute], unicode) else data[attribute]
      if allowedAttributes[attribute][0] != type(value):
        #TODO ERROR
        if self.allowTermination: print('tool.checkGeneralAttributes - 2'); exit(0) # incorrectTypeInToolConfigurationFile
        else: return False

      # At this point, the attribute in the configuration file is allowed and of valid type. Check that 
      # the value itself is valid (if necessary) and store the value.
      if allowedAttributes[attribute][2]: setattr(self, attribute, value)

    # Having parsed all of the general attributes attributes, check that all those that are required
    # are present.
    for attribute in allowedAttributes:
      if allowedAttributes[attribute][1] and attribute not in observedAttributes:
        #TODO ERROR
        if self.allowTermination: print('tool.checkGeneralAttributes - 3'); exit(0) #missingGeneralAttributeInConfigurationFile
        else: return False

    return True

  # Check that all the supplied arguments are valid and complete.
  def checkToolArguments(self, arguments):

    # Keep track of the short from arguments for this tool.
    observedShortForms = {}

    # The arguments are organised in named groups. The 'inputs' and 'outputs' groups, but then the configuration
    # file author is free to title any other groups as they see fit.

    # Start by checking the 'inputs'.
    #TODO ERROR
    try: validateArguments = arguments.pop('inputs')
    except: print('tool.checkToolArguments - 1'); exit(0) #self.errors.missingRequiredArgumentGroup(tool, True)

    # Set any additional fields that are valid for this group.
    allowedAttributes = self.setAllowedArgumentAttributes('inputs')
    success           = self.checkArgumentGroup('inputs', validateArguments, allowedAttributes, observedShortForms)

    # Next check the 'outputs'.
    #TODO ERROR
    try: validateArguments = arguments.pop('outputs')
    except: print('tool.checkToolArguments - 2'); exit(0) #self.errors.missingRequiredArgumentGroup(tool, True)

    # Set any additional fields that are valid for this group.
    allowedAttributes = self.setAllowedArgumentAttributes('outputs')
    sucess            = self.checkArgumentGroup('outputs', validateArguments, allowedAttributes, observedShortForms)

    # Now set all of the other arguments from user defined argument groups.
    for argumentGroup in arguments.keys():
      allowedAttributes = self.setAllowedArgumentAttributes(str(argumentGroup))
      success           = self.checkArgumentGroup(argumentGroup, arguments.pop(argumentGroup), allowedAttributes, observedShortForms)

    return success

  # Validate the argument group.
  def checkArgumentGroup(self, group, arguments, allowedAttributes, observedShortForms):
    for argumentDescription in arguments:

      # Keep track of the observed attributes.
      observedAttributes = {}

      # First check that the argument defines a dictionary of values.
      #TODO ERROR
      if not isinstance(argumentDescription, dict): print('tool.checkArgumentGroup - 1'); exit(0) #self.errors.toolArgumentHasNoDictionary(tool)

      # First get the 'long form' for this argument. This will be used to identify the argument in error messages and
      # will be used as the key when storing attributes in a dictionary.
      try: longFormArgument = argumentDescription['long form argument']
      except:
        #TODO ERROR
        if self.allowTermination: print('tool.checkArgumentGroup - 2'); exit(0) #self.errors.noLongFormForToolArgument(tool, group)
        else: return False

      # Check that this argument is unique.
      if longFormArgument in self.argumentAttributes:
        if self.allowTermination: print('tool.checkArgumentGroup - 3'); exit(0) #self.errors.repeatedToolArgumentInToolConfigurationFile(tool, longFormArgument, isLongForm = True)
        else: return False

      # Initialise the data structure for holding the argument information.
      attributes = argumentAttributes()

      # Store the long and short form arguments. If these aren't included, the routine will fail at the final check
      # since these are required argument. If the value is already included, fail.
      if 'short form argument' in argumentDescription:
        shortFormArgument = argumentDescription['short form argument']
        if shortFormArgument in observedShortForms:
          #TODO ERROR
          if self.allowTermination: print('tool.checkArgumentGroup - 4'); exit(0) #self.errors.repeatedToolArgumentInToolConfigurationFile(tool, shortFormArgument, isLongForm = False)
          else: return False
        else: observedShortForms[shortFormArgument] = True

      # Loop over all entries in the argument description, checking that the attributes are allowed and valid.
      for attribute in argumentDescription:
        if attribute not in allowedAttributes:
          if self.allowTermination: print('tool.checkArgumentGroup - 5'); exit(0) #self.errors.invalidArgumentAttributeInToolConfigurationFile(tool, group, longFormArgument, attribute, allowedAttributes)
          else: return False

        # Mark the attribute as observed.
        observedAttributes[attribute] = True

        # Check that the value given to the attribute is of the correct type. If the value is unicode,
        # convert to a string first.
        value = str(argumentDescription[attribute]) if isinstance(argumentDescription[attribute], unicode) else argumentDescription[attribute]
        if allowedAttributes[attribute][0] != type(value):
          if self.allowTermination:
            #TODO ERROR
            print('tool.checkArgumentGroup - 6'); exit(0)
            #self.errors.incorrectTypeInToolConfigurationFile(tool, group, attribute, longFormArgument, value, allowedAttributes[attribute][0])
          else: return False

        # Store the information in the attributes structure.
        self.setAttribute(attributes, allowedAttributes[attribute][2], value)

      # Set additional attributes depending on the argument group.
      attributes = self.setAdditionalArgumentAttributes(group, attributes)

      # Check if any required arguments are missing.
      for attribute in allowedAttributes:
        if allowedAttributes[attribute][1] and attribute not in observedAttributes:
          #TODO ERROR
          if self.allowTermination: print('tooo.checkArgumentGroup - 7'); exit(0) #self.errors.missingArgumentAttributeInToolConfigurationFile(tool, group, longFormArgument, attribute, allowedAttributes)
          else: return False

      # Store the attributes.
      self.argumentAttributes[longFormArgument] = attributes

    return True

  # Set the attributes allowed in the argument block. The structure describes the expected data type, 
  # whether the attribute is requred and finally, the name of the attribute in the data structure storing
  # the values.
  def setAllowedArgumentAttributes(self, groupName):
    allowedAttributes = {}

    # Set attributes that are available to all groups.
    allowedAttributes['allow multiple values']                = (bool, False, 'allowMultipleValues')
    allowedAttributes['allow list']                           = (bool, False, 'isArgumentList')
    allowedAttributes['allow list of repeated arguments']     = (bool, False, 'isRepeatedArgumentList')
    allowedAttributes['argument list']                        = (dict, False, 'listValues')
    allowedAttributes['command line argument']                = (str, True, 'commandLineArgument')
    allowedAttributes['comma separated list']                 = (bool, False, 'isCommaSeparatedList')
    allowedAttributes['data type']                            = (str, True, 'dataType')
    allowedAttributes['description']                          = (str, True, 'description')
    allowedAttributes['directory']                            = (bool, False, 'isDirectory')
    allowedAttributes['evaluate command']                     = (dict, False, 'commandToEvaluate')
    allowedAttributes['extensions']                           = (list, True, 'extensions')
    allowedAttributes['hide in help']                         = (bool, False, 'hideInHelp')
    allowedAttributes['include value in quotations']          = (bool, False, 'inQuotations')
    allowedAttributes['long form argument']                   = (str, True, 'longFormArgument')
    allowedAttributes['modify argument name on command line'] = (str, False, 'modifyArgument')
    allowedAttributes['modify argument values']               = (dict, False, 'modifyValues')
    allowedAttributes['place spaces around operator']         = (bool, False, 'inSpaces')
    allowedAttributes['required']                             = (bool, False, 'isRequired')
    allowedAttributes['required if stream']                   = (bool, False, 'isRequiredIfStream')
    allowedAttributes['short form argument']                  = (str, False, 'shortFormArgument')
    allowedAttributes['terminate if present']                 = (bool, False, 'terminateIfPresent')
    allowedAttributes['include path from argument']           = (str, False, 'pathArgument')

    # Set attributes that are specific to particular groups.
    if groupName == 'inputs' or groupName == 'outputs':
      allowedAttributes['construct filename']               = (dict, False, 'constructionInstructions')
      allowedAttributes['filename extensions']              = (list, False, 'filenameExtensions')
      allowedAttributes['is filename stub']                 = (bool, False, 'isFilenameStub')
      allowedAttributes['replace argument with']            = (dict, False, 'replaceArgument')
      allowedAttributes['temporary']                        = (bool, False, 'isTemporary')

    # Attributes specific to input files.
    if groupName == 'inputs':
      allowedAttributes['if input is stream']           = (str, False, 'inputStream')
      allowedAttributes['is stream']                    = (bool, False, 'isStream')
      allowedAttributes['suggestible']                  = (bool, False, 'isSuggestible')
      allowedAttributes['include path on command line'] = (bool, False, 'includePathOnCommandLine')

    # Attributes specific to output files.
    if groupName == 'outputs':
      allowedAttributes['if output to stream'] = (str, False, 'outputStream')

    return allowedAttributes

  # Set additional argument attributes depending on the argument group.
  def setAdditionalArgumentAttributes(self, group, attributes):

    # Set the argument group.
    self.setAttribute(attributes, 'argumentGroup', group)

    # Set attributes for inputs.
    if group == 'inputs': self.setAttribute(attributes, 'isInput', True)

    # Set attributes for required outputs.
    if group == 'outputs': self.setAttribute(attributes, 'isOutput', True)

    return attributes

  # Check if an argument includes a path supplied from a different argument. If so, ensure that the
  # supplied argument is valid.
  def checkPathArguments(self, tool):
    for longFormArgument in self.argumentAttributes[tool]:
      pathArgument = self.argumentAttributes[tool][longFormArgument].pathArgument
      if pathArgument:
        longFormPathArgument = self.getLongFormArgument(tool, pathArgument, False)
        if longFormPathArgument not in self.argumentAttributes[tool]:
          if self.allowTermination: self.errors.invalidArgumentInPathArgument(tool, longFormArgument, pathArgument)
          return False

        # Replace the provided argument with the long form.
        else:
          self.argumentAttributes[tool][longFormArgument].pathArgument = longFormPathArgument

    return True

  # Check all argument attribute dependencies.
  def checkAttributeDependencies(self, tool):

    # Define any dependencies. For each attribute, a list is provided allowing for different values associated
    # with the attribute being defined. It may be that there are different dependencies depending on the value
    # that the attribute takes. The format of the dictionary is as follows:
    #
    # (A, B, [])
    #
    # A: Is the value a general or argument attribute.
    # B: If defined, does the attribute require a value or just needs to be present. This takes the values 'present' or
    # the value that is being checked.
    dependencies = {}
    dependencies['inputIsStream'] = [('general', 'present', 'any', [('argument', 'includeOnCommandLine', False)])]
    dependencies['inputStream']   = [('argument', True)]

    return True

  # Generate a dictionary that links the long and short form arguments with each other.
  def consolidateArguments(self, tool):
    self.longFormArguments[tool]  = {}
    self.shortFormArguments[tool] = {}
    for longForm in self.argumentAttributes[tool]:
      shortForm = self.getArgumentAttribute(tool, longForm, 'shortFormArgument')
      self.longFormArguments[tool][longForm]   = shortForm
      self.shortFormArguments[tool][shortForm] = longForm

    return True

  # If the order in which the arguments should be used is included, check that all of the arguments are
  # included in the list and no invalid arguments are present.
  def checkArgumentOrder(self, tool, attributes):

    # If this tool does not include an argument order, the following checks are not required.
    if not attributes.argumentOrder: return True

    # Loop over all of the arguments and check that they are represented in the argument order.
    for argument in self.argumentAttributes[tool]:
      if argument not in attributes.argumentOrder:
        if self.allowTermination: self.errors.missingArgumentInArgumentOrder(tool, argument)
        else: return False

    # Loop over all of the arguments in the argument order and check that no arguments are invalid or repeated.
    observedArguments = []
    for argument in attributes.argumentOrder:
      if argument not in self.argumentAttributes[tool]:
        if self.allowTermination: self.errors.invalidArgumentInArgumentOrder(tool, argument)
      if argument in observedArguments:
        if self.allowTermination: self.errors.repeatedArgumentInArgumentOrder(tool, argument)
        else: return False
      observedArguments.append(argument)

    return True

  # Check that filename constructions are valid and complete.
  def checkConstructionInstructions(self, tool):
    allowedMethods = []
    allowedMethods.append('define name')
    allowedMethods.append('from tool argument')

    for argument in self.argumentAttributes[tool]:
      if self.argumentAttributes[tool][argument].constructionInstructions:

        # For each allowed method, check that everything required is present. First get the method.
        instructions = self.argumentAttributes[tool][argument].constructionInstructions
        if 'method' not in instructions: 
          if self.allowTermination: self.errors.noConstructionMethod(tool, argument, allowedMethods)
          else: return False

        # Now check the specifics of each method.
        method = self.argumentAttributes[tool][argument].constructionInstructions['method']
        if method == 'define name': success = self.checkDefineName(tool, argument)
        elif method == 'from tool argument': success = self.checkFromToolArgument(tool, argument)
        else:
          if self.allowTermination: self.errors.unknownConstructionMethod(tool, argument, method, allowedMethods)
          else: return False

    return True

  # If argument values are to be modified on the command line, check that the instructions are correct.
  def checkModifyValues(self, tool):

    # Loop over all arguments in the configuration file.
    for argument in self.argumentAttributes[tool]:
      if self.argumentAttributes[tool][argument].modifyValues:

        # For each allowed method, check that everything required is present. First get the method.
        instructions = self.argumentAttributes[tool][argument].modifyValues
        if 'command' not in instructions:
          if self.allowTermination: self.errors.noCommandInModifyValues(tool, argument)
          else: return False

        # Now check to see if the modification should only take place for specific extensions. If so
        # check that the specified extensions are valid
        if 'extensions' in instructions:
          allowedExtensions = self.argumentAttributes[tool][argument].extensions
          for extension in instructions['extensions']:
            if extension not in allowedExtensions:
              if self.allowTermination: self.errors.invalidExtensionInModifyValues(tool, argument, extension, allowedExtensions)
              else: return False

    return True

  # Check constructions instructions for the 'define name' method.
  def checkDefineName(self, tool, argument):
    allowedAttributes                                 = {}
    allowedAttributes['add extension']                = (bool, True)
    allowedAttributes['directory argument']           = (str, False)
    allowedAttributes['filename']                     = (str, True)
    allowedAttributes['for multiple runs connect to'] = (str, True)
    allowedAttributes['method']                       = (str, True)

    # Keep track of the observed required values.
    observedAttributes = {}

    # Loop over all of the attributes in the configuration file.
    for attribute in self.argumentAttributes[tool][argument].constructionInstructions:

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if attribute not in allowedAttributes:
        if self.allowTermination: self.errors.invalidAttributeInConstruction(tool, argument, attribute, 'define name', allowedAttributes)
        else: return False

      # Mark this values as having been observed,
      observedAttributes[attribute] = True

      # Check that the value given to the attribute is of the correct type. If the value is unicode,
      # convert to a string first.
      value = self.argumentAttributes[tool][argument].constructionInstructions[attribute]
      value = str(value) if isinstance(value, unicode) else value
      if allowedAttributes[attribute][0] != type(value):
        if self.allowTermination:
          self.errors.incorrectTypeInConstruction(tool, argument, attribute, 'define name', value, allowedAttributes[attribute][0])
        else: return False

    # Having parsed all of the general attributes attributes, check that all those that are required
    # are present.
    for attribute in allowedAttributes:
      if allowedAttributes[attribute][1] and attribute not in observedAttributes and self.allowTermination: 
        self.errors.missingAttributeInConstruction(tool, argument, attribute, 'define name', allowedAttributes)

    # If the 'directory argument' was present, check that this is a valid  argument for this tool. Being
    # valid means that the argument exists and is a directory argument.
    if 'directory argument' in self.argumentAttributes[tool][argument].constructionInstructions:

      # Get all directory arguments for this tool.
      directoryArguments = []
      for addArgument in self.argumentAttributes[tool].keys():
        if self.argumentAttributes[tool][addArgument].isDirectory: directoryArguments.append(addArgument)

      # Check the validity of the entry in the configuration file.
      addArgument = self.argumentAttributes[tool][argument].constructionInstructions['directory argument']
      if addArgument not in directoryArguments:
        if self.allowTermination: self.errors.invalidArgumentInConstruction(tool, argument, addArgument, directoryArguments, 'directory argument')
        else: return False

    return True

  # Check constructions instructions for the 'from tool argument' method.
  def checkFromToolArgument(self, tool, argument):

    # Define the allowed attributes.
    allowedAttributes                             = {}
    allowedAttributes['add path']                 = (str, False)
    allowedAttributes['fail if cannot construct'] = (bool, False)
    allowedAttributes['method']                   = (str, True)
    allowedAttributes['modify extension']         = (str, True)
    allowedAttributes['modify text']              = (list, False)
    allowedAttributes['use argument']             = (str, True)
    allowedAttributes['use path']                 = (bool, False)

    # Keep track of the observed required values.
    observedAttributes = {}

    # Loop over all of the attributes in the configuration file.
    for attribute in self.argumentAttributes[tool][argument].constructionInstructions:

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if attribute not in allowedAttributes:
        if self.allowTermination: self.errors.invalidAttributeInConstruction(tool, argument, attribute, 'from tool argument', allowedAttributes)
        else: return False

      # Mark this values as having been observed,
      observedAttributes[attribute] = True

      # Check that the value given to the attribute is of the correct type. If the value is unicode,
      # convert to a string first.
      value = self.argumentAttributes[tool][argument].constructionInstructions[attribute]
      value = str(value) if isinstance(value, unicode) else value
      if allowedAttributes[attribute][0] != type(value):
        if self.allowTermination:
          self.errors.incorrectTypeInConstruction(tool, argument, attribute, 'from tool argument', value, allowedAttributes[attribute][0])
        else: return False

    # Having parsed all of the general attributes attributes, check that all those that are required
    # are present.
    for attribute in allowedAttributes:
      if allowedAttributes[attribute][1] and attribute not in observedAttributes:
        if self.allowTermination: self.errors.missingAttributeInConstruction(tool, argument, attribute, 'from tool argument', allowedAttributes)
        else: return False

    # If the 'modify text' field was present, check its contents.
    if 'modify text' in self.argumentAttributes[tool][argument].constructionInstructions: self.checkModifyText(tool, argument)

  # Check the contents of the 'modify values' field.
  def checkModifyText(self, tool, argument):
    success = True

    # Define the allowed attributes.
    allowedInstructions                        = {}
    allowedInstructions['add argument values'] = (list, True)
    allowedInstructions['add text'] = (list, True)
    allowedInstructions['remove text']         = (list, True)

    # Loop over the instructions.
    for instructionDict in self.argumentAttributes[tool][argument].constructionInstructions['modify text']:
      if not isinstance(instructionDict, dict): self.errors.notDictionaryInModifyText(tool, argument)

      # Each dictionary can only contain one instruction. This preserves the order in which to make the filename
      # construction.
      if len(instructionDict) != 1:
        if self.allowTermination: self.errors.multipleInstructionsInModifyTextDictionary(tool, argument)
        else: return False

      instruction = instructionDict.iterkeys().next()
      value       = instructionDict[instruction]

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if instruction not in allowedInstructions:
        if self.allowTermination: self.errors.invalidAttributeInConstruction(tool, argument, instruction, 'from tool argument', allowedInstructions)
        else: return False

      # Check the individual instructions.
      if instruction == 'add text':
        success, instructionDict[instruction] = self.checkConstructionStrings(tool, argument, value, 'add text')

      # Check fields associated with 'add argument values'.
      elif instruction == 'add argument values':
        success, instructionDict[instruction] = self.checkConstructionStrings(tool, argument, value, 'add argument values')

        # Check that the values are all arguments associated with this tool.
        for addArgument in instructionDict[instruction]:
          if addArgument not in self.argumentAttributes[tool]:
            if self.allowTermination:
              self.errors.invalidArgumentInConstruction(tool, argument, addArgument, self.argumentAttributes[tool].keys(), 'add argument values')
            else: return False

      # Check fields associated with 'remove text'.
      elif instruction == 'remove text': 
        success, instructionDict[instruction] = self.checkConstructionStrings(tool, argument, value, 'remove text')

    return success

  # Check the field is a list of strings.
  def checkConstructionStrings(self, tool, argument, valueList, field):
    strings = []

    # Check that the value is a list.
    if not isinstance(valueList, list):
      if self.allowTermination: self.errors.nonListInConstruction(tool, argument, field)
      else: return False, strings

    # Loop over all values in the list and check that they are strings.
    for value in valueList:
      if isinstance(value, list) or isinstance(value, dict):
        if self.allowTermination: self.errors.invalidStringInConstruction(tool, argument, field)
        else: return False, strings
      strings.append(str(value))

    # Return the original list with unicodes and integers etc converted to strings.
    return True, strings

  # Check arguments that describe how to handle input or output streams.
  def checkStreams(self, tool):
    for longFormArgument in self.argumentAttributes[tool]:

      # Check to see if the argument has the 'if input is stream' field ot the 'if output to
      # stream' field..
      inputStream  = self.argumentAttributes[tool][longFormArgument].inputStream
      outputStream = self.argumentAttributes[tool][longFormArgument].outputStream

      # If this has details on how to proceed if the input is a stream, ensure that the accompanying
      # data is valid.
      if inputStream:
        allowedValues = ['do not include', 'replace', 'omit']

        # If the instructions are 'replace', further information is required.
        if inputStream == 'replace': self.checkStreamReplace(tool, longFormArgument, isInput = True)

        # No other values are allowed.
        elif inputStream not in allowedValues:
          self.errors.invalidValueArgumentStream(tool, longFormArgument, inputStream, allowedValues, isInput = True)

      # If this has details on how to proceed if the output is a stream, ensure that the accompanying
      # data is valid.
      if outputStream:
        allowedValues = ['do not include', 'replace']

        # If the instructions are 'do not include', no further information is required
        if outputStream == 'do not include': pass

        # If the instructions are 'replace', further information is required.
        elif outputStream == 'replace': self.checkStreamReplace(tool, longFormArgument, isInput = False)

        # No other values are allowed.
        else: self.errors.invalidValueArgumentStream(tool, longFormArgument, outputStream, allowedValues, isInput = False)

    return True

  # Check instructions on replacing arguments in the event of an input/output stream.
  def checkStreamReplace(self, tool, longFormArgument, isInput):

    # Check that the 'replace argument' field is present.
    replaceArgument = self.argumentAttributes[tool][longFormArgument].replaceArgument
    if not replaceArgument: self.errors.noReplace(tool, longFormArgument, isInput = isInput)

    # If present, the replaceArgument field has already been checked to ensure that it is a dictionary.
    # Now check that the 'argument' field is present and has a valid value and that the value field is
    # present.
    if 'argument' not in self.argumentAttributes[tool][longFormArgument].replaceArgument:
      self.errors.missingAttributeInReplace(tool, longFormArgument, 'argument', isInput = isInput)
    if 'value' not in self.argumentAttributes[tool][longFormArgument].replaceArgument:
      self.errors.missingAttributeInReplace(tool, longFormArgument, 'value', isInput = isInput)

  # TODO
  # IS THIS STILL REQUIRED AFTER LIST UPDATE?
  # Check if there are any list values specified. If so, check the contents.
  def checkListValues(self, tool):
    allowedAttributes                 = {}
    allowedAttributes['use argument'] = (str, True)
    allowedAttributes['mode']         = (str, True)

    # Define the allowed modes.
    allowedModes = []
    allowedModes.append('multiple makefiles')
    allowedModes.append('repeat argument')
    allowedModes.append('single makefile')

    # Record the observed attributes.
    observedAttributes = []

    # Check the values.
    for longFormArgument in self.argumentAttributes[tool]:
      if self.argumentAttributes[tool][longFormArgument].listValues:
        for attribute in self.argumentAttributes[tool][longFormArgument].listValues:
          value = self.argumentAttributes[tool][longFormArgument].listValues[attribute]

          # Check that the attribute is valid.
          if attribute not in allowedAttributes: self.errors.invalidAttributeInList(tool, longFormArgument, attribute, allowedAttributes)

          # If the attribute is 'use argument', check that the argument is valid.
          if attribute == 'use argument':
            if value not in self.argumentAttributes[tool]:

              # Check to see if the value is a short form of a valid argument.
              longFormValue = self.shortFormArguments[tool][value] if value in self.shortFormArguments[tool] else None
              if longFormValue not in self.argumentAttributes[tool]: self.errors.invalidArgumentInList(tool, longFormArgument, value)
              value = longFormValue
            self.argumentAttributes[tool][longFormArgument].listArgument = value

            # This argument can be used to set the argument defined in 'use argument'. Store this fact.
            self.argumentAttributes[tool][value].canBeSetByArgument.append(str(longFormArgument))

          # If the attribute is 'mode', check that the supplied value is allowed.
          if attribute == 'mode':
            if value not in allowedModes: self.errors.invalidModeInList(tool, longFormArgument, value, allowedModes)
            self.argumentAttributes[tool][longFormArgument].listMode = value

          # Record that this attribute was observed.
          observedAttributes.append(attribute)

    return True

  # Check the instructions on evaluating a command.
  def checkCommands(self, tool):
    allowedAttributes                          = {}
    allowedAttributes['command']               = (str, True)
    allowedAttributes['command line argument'] = (bool, False)
    allowedAttributes['add values']            = (list, False)

    # Keep track of the observed attributes.
    observedAttributes = []

    for longFormArgument in self.argumentAttributes[tool]:
      if self.argumentAttributes[tool][longFormArgument].commandToEvaluate:

        # Loop over the evaluate command attributes.
        commandInformation = self.argumentAttributes[tool][longFormArgument].commandToEvaluate
        for attribute in commandInformation:
          if attribute not in allowedAttributes: self.errors.invalidAttributeInEvaluate(tool, longFormArgument, attribute, allowedAttributes)

          # Convert unicode values to strings.
          if isinstance(commandInformation[attribute], unicode): commandInformation[attribute] = str(commandInformation[attribute])

          # Check that the attribute has the correct type.
          if not isinstance(commandInformation[attribute], allowedAttributes[attribute][0]):
            self.errors.invalidTypeEvaluate(tool, longFormArgument, attribute, allowedAttributes[attribute][0])

          # Store this attribute as observed.
          observedAttributes.append(attribute)

        # Check that all required attributes were present.
        for attribute in allowedAttributes:
          if allowedAttributes[attribute][1] and attribute not in observedAttributes:
            self.errors.missingAttributeInEvaluate(tool, longFormArgument, attribute)

        # Record if this is a command line argument replacement.
        if 'command line argument' in commandInformation: 
          self.argumentAttributes[tool][longFormArgument].commandEvaluation.isCommandLineArgument = True

        # Set the command and store this argument in the tool attributes.
        self.argumentAttributes[tool][longFormArgument].commandEvaluation.command = commandInformation['command']
        self.attributes[tool].argumentsWithCommands.append(longFormArgument)

        # Loop over the values, check that they appear in he command and store them.
        if 'add values' in commandInformation:

          # Keep track of the observed IDs. Each ID can only be defined once.
          observedIDs = []
          for valueDict in commandInformation['add values']:

            # Get the ID that should appear in the command.
            if 'ID' not in valueDict: self.errors.errorInEvaluateValues(tool, longFormArgument, 'ID')
            if valueDict['ID'] not in commandInformation['command']: self.errors.invalidIDInEvaluate(tool, longFormArgument, valueDict['ID'])
            if valueDict['ID'] in observedIDs: self.errors.IDDefinedMultipleTimesInEvaluate(tool, longFormArgument, valueDict['ID'])
            observedIDs.append(valueDict['ID'])

            # Get the argument (or tool) which this ID should be replaced by.
            if 'argument' not in valueDict: self.errors.errorInEvaluateValues(tool, longFormArgument, 'argument')

            # Check that the argument is a valid argument for this tool (or takes the value tool).
            if valueDict['argument'] != 'tool':
              if valueDict['argument'] not in self.argumentAttributes[tool]:
                if valueDict['argument'] not in self.shortFormArguments[tool]:
                  self.errors.invalidArgumentInEvaluate(tool, longFormArgument, valueDict['ID'], valueDict['argument'])
                valueDict['argument'] = self.shortFormArguments[tool][valueDict['argument']]

            self.argumentAttributes[tool][longFormArgument].commandEvaluation.values[valueDict['ID']] = valueDict['argument']

    return True

  # Set a value in the toolAttributes.
  def setAttribute(self, attributes, attribute, value):
    try: test = getattr(attributes, attribute)

    # If the attribute can't be set, determine the source of the problem and provide an
    # error message.
    except:

      # If the tool is not available.
      #TODO ERROR
      print('tool.setAttribute - 1'); exit(0)
      #self.errors.invalidAttributeInSetAttribute(attribute, False)
      #self.errors.terminate()

    # Set the attribute.
    setattr(attributes, attribute, value)

    return attributes

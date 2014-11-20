#!/bin/bash/python

from __future__ import print_function

import fileHandling
import generalConfigurationFileMethods as methods
import parameterSets
import toolConfigurationErrors as errors

import json
import os
import sys

# Define a class to hold information on the arguments.
class argumentAttributes:
  def __init__(self):
    
    # If an argument is allowed to be set multiple times.
    self.allowMultipleValues = False

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

    # Keep track of required arguments.
    self.isRequired = False

    # Record id the argument points to a filename stub and store the 
    # associated extensions.
    self.isStub = False
    self.stubExtensions = []

    # Record if this argument should be hidden in the help.
    self.hideInHelp = False

    # Record the argument group to which the argument belongs.
    self.argumentGroup = None

    # Record if the argument is for an input or output file.
    self.isInput  = False
    self.isOutput = False

    # Store whether the argument can be suggested as a possible tool to use in a
    # pipeline builder.
    self.isSuggestible = False

# Define a class to hold information about the tool.
class toolAttributes:
  def __init_(self):
    pass

# Define a class to store general pipeline attributes,
class toolConfiguration:
  def __init__(self):

    # Define error handling.
    self.errors = errors.toolErrors()

    # Record the name of the tool.
    self.name = None

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

    # The tool executable, its path and any modifiers.
    self.executable = None
    self.modifier   = None
    self.path       = None
    self.precommand = None

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
    self.isDevelopmental = False

    # The parameter set information for this pipeline.
    self.parameterSets = parameterSets.parameterSets()

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

    # As pipeline configuration files are processed, success will identify whether a problem was
    # encountered.
    self.success = True

  # Open a configuration file, process the data and return.
  def getConfigurationData(self, tool, filename):

    # Store the name of the tool.
    self.name = tool

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

  # Process the configuration file.
  def processConfigurationFile(self, data):

    # Check the top level information, e.g. pipeline description.
    self.checkTopLevelInformation(data)

    # Validate input arguments.
    if self.success: self.checkInputArguments(data['arguments'])

    # Validate output arguments.
    if self.success: self.checkOutputArguments(data['arguments'])

    # Validate all other arguments.
    if self.success: self.checkRemainingArguments(data['arguments'])

    # Check that certain required combinations of attributes are adhered to.
    if self.success: self.checkAttributeCombinations()

    # Check the parameter set information and store.
    if self.success: self.success = self.parameterSets.checkParameterSets(data['parameter sets'], self.allowTermination, self.name)

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                       = {}
    allowedAttributes['arguments']          = (dict, True, False, None)
    allowedAttributes['argument delimiter'] = (str, False, True, 'delimiter')
    allowedAttributes['argument order']     = (list, False, True, 'argumentOrder')
    allowedAttributes['categories']         = (list, True, True, 'categories')
    allowedAttributes['description']        = (str, True, True, 'description')
    allowedAttributes['developmental']      = (bool, False, True, 'isDevelopmental')
    allowedAttributes['executable']         = (str, True, True, 'executable')
    allowedAttributes['hide tool']          = (bool, False, True, 'isHidden')
    allowedAttributes['id']                 = (str, True, True, 'id')
    allowedAttributes['parameter sets']     = (list, True, False, None)
    allowedAttributes['modifier']           = (str, False, True, 'modifier')
    allowedAttributes['path']               = (str, True, True, 'path')
    allowedAttributes['precommand']         = (str, False, True, 'precommand')
    allowedAttributes['tools']              = (list, True, True, 'requiredCompiledTools')
    allowedAttributes['url']                = (str, False, True, 'url')

    # Define a set of information to be used in help messages.
    helpInfo = (self.name, None, None)

    # Check the attributes against the allowed attributes and make sure everything is ok.
    self = methods.checkAttributes(data, allowedAttributes, self, self.allowTermination, helpInfo)

  # Validate the contents of all input arguments.
  def checkInputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values'] = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument'] = (str, True, True, 'commandLineArgument')
    allowedAttributes['data type']             = (str, True, True, 'dataType')
    allowedAttributes['description']           = (str, True, True, 'description')
    allowedAttributes['extensions']            = (list, False, True, 'extensions')
    allowedAttributes['stub extensions']       = (list, False, True, 'stubExtensions')
    allowedAttributes['hide in help']          = (bool, False, True, 'hideInHelp')
    allowedAttributes['long form argument']    = (str, True, True, 'longFormArgument')
    allowedAttributes['required']              = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']   = (str, False, True, 'shortFormArgument')
    allowedAttributes['construct filename']    = (dict, False, True, 'constructionInstructions')
    allowedAttributes['is filename stub']      = (bool, False, True, 'isStub')
    allowedAttributes['suggestible']           = (bool, False, True, 'isSuggestible')

    # Return if there are no input arguments.
    if 'inputs' not in arguments: return

    # Check the arguments.
    self.checkArguments(arguments['inputs'], allowedAttributes, isInput = True, isOutput = False)

  # Validate the contents of all input arguments.
  def checkOutputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values'] = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument'] = (str, True, True, 'commandLineArgument')
    allowedAttributes['data type']             = (str, True, True, 'dataType')
    allowedAttributes['description']           = (str, True, True, 'description')
    allowedAttributes['extensions']            = (list, False, True, 'extensions')
    allowedAttributes['stub extensions']       = (list, False, True, 'stubExtensions')
    allowedAttributes['hide in help']          = (bool, False, True, 'hideInHelp')
    allowedAttributes['long form argument']    = (str, True, True, 'longFormArgument')
    allowedAttributes['required']              = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']   = (str, False, True, 'shortFormArgument')
    allowedAttributes['construct filename']    = (dict, False, True, 'constructionInstructions')
    allowedAttributes['is filename stub']      = (bool, False, True, 'isStub')

    # Return if there are no input arguments.
    if 'outputs' not in arguments: return

    # Check the arguments.
    self.checkArguments(arguments['outputs'], allowedAttributes, isInput = False, isOutput = True)

  # Validate the contents of all input arguments.
  def checkRemainingArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values'] = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument'] = (str, True, True, 'commandLineArgument')
    allowedAttributes['data type']             = (str, True, True, 'dataType')
    allowedAttributes['description']           = (str, True, True, 'description')
    allowedAttributes['extensions']            = (list, False, True, 'extensions')
    allowedAttributes['hide in help']          = (bool, False, True, 'hideInHelp')
    allowedAttributes['long form argument']    = (str, True, True, 'longFormArgument')
    allowedAttributes['required']              = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']   = (str, False, True, 'shortFormArgument')

    # Loop over all the other categories of arguments.
    for category in arguments:
      if category != 'inputs' and category != 'outputs':

        # Check the arguments.
        self.checkArguments(arguments[category], allowedAttributes, isInput = False, isOutput = False)

  # Check the contents of the arguments.
  def checkArguments(self, arguments, allowedAttributes, isInput, isOutput):

    # Loop over all of the input arguments and check their validity.
    for argumentInformation in arguments:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'arguments', None)

      # Define a class to store task attribtues.
      attributes = argumentAttributes()

      # Check all the supplied attributes.
      self.success, attributes = methods.checkAttributes(argumentInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Check that the argument name is unique.
      if attributes.longFormArgument in self.arguments:
        #TODO ERROR
        if self.allowTermination: print('tools.checkArguments - 1', attributes.longFormArgument); exit(0)
        else:
          self.success = False
          return

      # Store the attributes for the task.
      if isInput: attributes.isInput = True
      elif isOutput: attributes.isOutput = True
      self.arguments[attributes.longFormArgument] = attributes

  # Check that required attributes combinations are available. For example, if the 'is filename stub'
  # attribute is set, the stub extensions field must also be present.
  def checkAttributeCombinations(self):

    # Loop over all the arguments.
    for argument in self.arguments:

      # If isStub is set, 
      if self.getArgumentAttribute(argument, 'isStub') and not self.getArgumentAttribute(argument, 'stubExtensions'):
        if self.allowTermination: self.errors.noExtensionsForStub(self.name, argument)
        else:
          self.success = False
          return

  # Get an argument attribute.
  def getArgumentAttribute(self, argument, attribute):
    try: return getattr(self.arguments[argument], attribute)
    except: return None

  # Return the long form version of an argument.
  def getLongFormArgument(self, argument):

    # Loop over all the arguments and see if the argument corresponds to a long
    # or short form version.
    for longFormArgument in self.arguments.keys():
      if argument == longFormArgument: return longFormArgument

      # Get the short form version of the argument and check if the argument matches this.
      shortFormArgument = self.getArgumentAttribute(longFormArgument, 'shortFormArgument')
      if argument == shortFormArgument: return longFormArgument

    # If no match was found, return None.
    return None

  # Return the data structure containing all the information on the requested argument.
  def getArgumentData(self, argument):
    try: return self.arguments[argument]
    except: return None

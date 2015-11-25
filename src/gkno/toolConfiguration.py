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

    # Instructions on how to modify the argument and the value to be used on
    # the command line in the makefile.
    self.modifyArgument = None
    self.modifyValue    = None

    # If there are instructions on supplying a command to use in place of the value,
    # store the instructions.
    self.valueCommand = {}

    # Mark the edge as a stream if necessary.
    self.isStream = False

    # Store instructions on how to modify the argument and the value if the tool is
    # accepting a stream as input or is outputting to a stream.
    self.inputStreamInstructions  = {}
    self.outputStreamInstructions = {}

    # Define the extensions allowed for the argument.
    self.extensions = []

    # The 'location' field can be used to specifiy a location for the file specified. This
    # location is stored in the fileLocation attribute.
    self.fileLocation = None

    # An argument can be defined as being linked to another argument for the tool. Linked
    # arguments can be used to make sure that lists of values are ordered such that each
    # value for the argument is most similar to the value for the linked argument. For
    # example, paired end fastq files. The argument for the second mate is linked to the
    # argument for the first mate to ensure that the correct values go together.
    self.linkedArgument = None
    
    # Store instructions on how to construct the filename.
    self.constructionInstructions = None

    # Record the argument description.
    self.description = None

    # Store the data type of the value supplied with this argument.
    self.dataType = None

    # Keep track of required arguments.
    self.isRequired = False

    # If an argument accepts a string, the configuration file can contain information
    # on replacing substrings within the string. Store this information.
    self.isReplaceSubstring = False
    self.replaceSubstring   = []

    # Record id the argument points to a filename stub and store the 
    # associated extensions. Also, store the extension for this specific node.
    self.isStub            = False
    self.isPrimaryStubNode = False
    self.stubExtension     = None
    self.stubExtensions    = []
    self.includeStubDot    = True

    # Record the category to which the argument belongs.
    self.category = None

    # If the argument should be hidden from the user in help messages.
    self.hideInHelp = False

    # Record if the argument is for an input or output file.
    self.isInput  = False
    self.isOutput = False

    # Store if the argument is greedy (e.g. uses all values associated with the node).
    self.isGreedy = False

    # Store whether the argument can be suggested as a possible tool to use in a
    # pipeline builder.
    self.isSuggestible = False

    # Record if the value supplied on the command line should be included in quotations when included
    # in the command line in the makefile.
    self.includeInQuotations = False

    # Record whether the node associated with this argument should be included in a reduced plot.
    self.includeInReducedPlot = True

    # Some argument values are commands that are to be evaluated at run time and these commands may require
    # information from other nodes in the pipeline. When this is the case, an edge is included in the graph
    # in order to account for the dependency, but there is no argument associated with the edge. In these
    # cases, the following flag will be set.
    self.isLinkOnly = False

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
    self.arguments          = {}
    self.shortFormArguments = []

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
    self.modifier   = ''
    self.path       = None
    self.precommand = ''

    # Record if this tool is hidden in the help.
    self.isHidden = False

    # Some tools do not produce any outputs. If this is the case, the tool has to
    # be marked.
    self.noOutput = False

    # Store the tools that need to be compiled for this tool to be available.
    self.requiredCompiledTools = []

    # Keep track of any R packages that are required by the tool.
    self.rPackages = []

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

    # Store information about the tool for display on the web page.
    self.webPage = {}

    # As pipeline configuration files are processed, success will identify whether a problem was
    # encountered.
    self.success = True

  # Check that a supplied configuration file is a tool configuration file.
  def checkConfigurationFile(self, filename):

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Check that the configuration file is for a pipeline.
    try: configurationType = data['configuration type']
    except: return False
    if configurationType != 'tool': return False
    return True

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

    # Check that the configuration file is a pipeline configuration file.
    self.success = self.checkIsTool(data)

    # Check the top level information, e.g. pipeline description.
    if self.success: self.checkTopLevelInformation(data)

    # Validate input arguments.
    if self.success: self.checkInputArguments(data['arguments'])

    # Validate output arguments.
    if self.success: self.checkOutputArguments(data['arguments'])

    # Validate all other arguments.
    if self.success: self.checkRemainingArguments(data['arguments'])

    # Check the information supplied for display on the web page.
    if self.success: self.success = self.checkWeb()

    # Check that certain required combinations of attributes are adhered to.
    if self.success: self.checkAttributeCombinations()

    # There are occasions where a particular attribute value can force the value of
    # another. Check for these cases and force the values as required. As an example,
    # if the 'command line argument' attribute is set to 'none', then the argument
    # will not be written to the command line. If the 'modify argument' attribute is
    # unset, it can be set to 'omit' in this instance
    if self.success: self.forceAttributes()

    # Check the values supplied to attributes.
    if self.success: self.checkAttributeValues()

    # Check that input and output stream instructions are correct.
    if self.success: self.checkStreamInstructions()

    # If any of the arguments have instructions on how to construct filenames, check
    # that the values are valid.
    if self.success: self.checkConstructionInstructions()

    # Check replace substring commands.
    if self.success: self.checkReplaceSubstring(data['arguments'])

    # If instructtions have been provided on replacing a value with a command, check that the
    # instructions are valid.
    if self.success: self.checkValueCommand()

    # If the configuration file includes the 'argument order' list, check that all the arguments
    # for the tool are included and no others.
    if self.success: self.success = self.checkArgumentOrder()

    # Check the parameter set information and store.
    if self.success: self.success = self.parameterSets.checkParameterSets(data['parameter sets'], self.allowTermination, self.name, isTool = True)

  # Check that the configuration file is for a tool.
  def checkIsTool(self, data):

    # Get the configuration type field. If this is not present, terminate, since this is the field that
    # defines if the configuration file is for a tool or for a pipeline.
    try: configurationType = data['configuration type']
    except:
      if self.allowTermination: self.errors.noConfigurationType(self.name)
      else: return False

    if configurationType != 'tool':
      if self.allowTermination: self.errors.invalidConfigurationType(self.name, configurationType)
      else: return False

    # Return true if this was completed succesfully.
    return True

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                       = {}
    allowedAttributes['arguments']          = (dict, True, False, None)
    allowedAttributes['argument delimiter'] = (str, False, True, 'delimiter')
    allowedAttributes['argument order']     = (list, False, True, 'argumentOrder')
    allowedAttributes['categories']         = (list, True, True, 'categories')
    allowedAttributes['configuration type'] = (str, True, False, None)
    allowedAttributes['description']        = (str, True, True, 'description')
    allowedAttributes['developmental']      = (bool, False, True, 'isDevelopmental')
    allowedAttributes['executable']         = (str, True, True, 'executable')
    allowedAttributes['hide tool']          = (bool, False, True, 'isHidden')
    allowedAttributes['id']                 = (str, True, True, 'id')
    allowedAttributes['parameter sets']     = (list, True, False, None)
    allowedAttributes['modifier']           = (str, False, True, 'modifier')
    allowedAttributes['path']               = (str, True, True, 'path')
    allowedAttributes['precommand']         = (str, False, True, 'precommand')
    allowedAttributes['R packages']         = (list, False, True, 'rPackages')
    allowedAttributes['tools']              = (list, True, True, 'requiredCompiledTools')
    allowedAttributes['url']                = (str, False, True, 'url')
    allowedAttributes['web page']           = (dict, False, True, 'webPage')

    # Define a set of information to be used in help messages.
    helpInfo = (self.name, None, None)

    # Check the attributes against the allowed attributes and make sure everything is ok.
    self = methods.checkAttributes(data, allowedAttributes, self, self.allowTermination, helpInfo)

  # Validate the contents of all input arguments.
  def checkInputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']         = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']         = (str, True, True, 'commandLineArgument')
    allowedAttributes['construct filename']            = (dict, False, True, 'constructionInstructions')
    allowedAttributes['data type']                     = (str, True, True, 'dataType')
    allowedAttributes['description']                   = (str, True, True, 'description')
    allowedAttributes['extensions']                    = (list, False, True, 'extensions')
    allowedAttributes['hide argument in help']         = (bool, False, True, 'hideInHelp')
    allowedAttributes['if input is stream']            = (dict, False, True, 'inputStreamInstructions')
    allowedAttributes['include dot in stub extension'] = (bool, False, True, 'includeStubDot')
    allowedAttributes['include in reduced plot']       = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations']   = (bool, False, True, 'includeInQuotations')
    allowedAttributes['is filename stub']              = (bool, False, True, 'isStub')
    allowedAttributes['linked argument']               = (str, False, True, 'linkedArgument')
    allowedAttributes['location']                      = (str, False, True, 'fileLocation')
    allowedAttributes['long form argument']            = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']               = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                  = (str, False, True, 'modifyValue')
    allowedAttributes['replace substring']             = (list, False, False, None)
    allowedAttributes['required']                      = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']           = (str, False, True, 'shortFormArgument')
    allowedAttributes['stub extensions']               = (list, False, True, 'stubExtensions')
    allowedAttributes['suggestible']                   = (bool, False, True, 'isSuggestible')
    allowedAttributes['value command']                 = (dict, False, True, 'valueCommand')

    # Fail if there is no input arguments section. This is included since all input arguments
    # are included in the 'Inputs' section and, if by mistake, the section is named 'inputs' (no
    # capitalisation), input arguments will be miscategorised.
    if 'Inputs' not in arguments: self.errors.missingArgumentSection(self.name, 'Inputs')

    # Check the arguments.
    self.checkArguments('Inputs', arguments['Inputs'], allowedAttributes, isInput = True, isOutput = False)

  # Validate the contents of all input arguments.
  def checkOutputArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']         = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']         = (str, True, True, 'commandLineArgument')
    allowedAttributes['construct filename']            = (dict, False, True, 'constructionInstructions')
    allowedAttributes['data type']                     = (str, True, True, 'dataType')
    allowedAttributes['description']                   = (str, True, True, 'description')
    allowedAttributes['extensions']                    = (list, False, True, 'extensions')
    allowedAttributes['hide argument in help']         = (bool, False, True, 'hideInHelp')
    allowedAttributes['include dot in stub extension'] = (bool, False, True, 'includeStubDot')
    allowedAttributes['include in reduced plot']       = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations']   = (bool, False, True, 'includeInQuotations')
    allowedAttributes['is filename stub']              = (bool, False, True, 'isStub')
    allowedAttributes['if output to stream']           = (dict, False, True, 'outputStreamInstructions')
    allowedAttributes['long form argument']            = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']               = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                  = (str, False, True, 'modifyValue')
    allowedAttributes['replace substring']             = (list, False, False, None)
    allowedAttributes['required']                      = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']           = (str, False, True, 'shortFormArgument')
    allowedAttributes['stub extensions']               = (list, False, True, 'stubExtensions')
    allowedAttributes['value command']                 = (dict, False, True, 'valueCommand')

    # Fail if there is no output arguments section. This is included since all output arguments
    # are included in the 'Outputs' section and, if by mistake, the section is named 'outputs' (no
    # capitalisation), output arguments will be miscategorised.
    if 'Outputs' not in arguments: self.errors.missingArgumentSection(self.name, 'Outputs')

    # Check the arguments.
    self.checkArguments('Outputs', arguments['Outputs'], allowedAttributes, isInput = False, isOutput = True)

  # Validate the contents of all input arguments.
  def checkRemainingArguments(self, arguments):

    # Define the allowed input argument attributes.
    allowedAttributes = {}
    allowedAttributes['allow multiple values']       = (bool, False, True, 'allowMultipleValues')
    allowedAttributes['command line argument']       = (str, True, True, 'commandLineArgument')
    allowedAttributes['construct filename']          = (dict, False, True, 'constructionInstructions')
    allowedAttributes['data type']                   = (str, True, True, 'dataType')
    allowedAttributes['description']                 = (str, True, True, 'description')
    allowedAttributes['extensions']                  = (list, False, True, 'extensions')
    allowedAttributes['hide argument in help']       = (bool, False, True, 'hideInHelp')
    allowedAttributes['include in reduced plot']     = (bool, False, True, 'includeInReducedPlot')
    allowedAttributes['include value in quotations'] = (bool, False, True, 'includeInQuotations')
    allowedAttributes['long form argument']          = (str, True, True, 'longFormArgument')
    allowedAttributes['modify argument']             = (str, False, True, 'modifyArgument')
    allowedAttributes['modify value']                = (str, False, True, 'modifyValue')
    allowedAttributes['replace substring']           = (list, False, False, None)
    allowedAttributes['required']                    = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument']         = (str, False, True, 'shortFormArgument')
    allowedAttributes['value command']               = (dict, False, True, 'valueCommand')

    # Loop over all the other categories of arguments.
    for category in arguments:
      if category != 'Inputs' and category != 'Outputs':

        # Check the arguments.
        self.checkArguments(category, arguments[category], allowedAttributes, isInput = False, isOutput = False)

  # Check the contents of the arguments.
  def checkArguments(self, category, arguments, allowedAttributes, isInput, isOutput):

    # Loop over all of the input arguments and check their validity.
    for argumentInformation in arguments:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'arguments', category)

      # Define a class to store task attribtues.
      attributes = argumentAttributes()

      # Check all the supplied attributes.
      self.success, attributes = methods.checkAttributes(argumentInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Check that the argument name is unique.
      if attributes.longFormArgument in self.arguments:
        if self.allowTermination: self.errors.repeatedLongFormArgument(helpInfo, attributes.longFormArgument)
        else:
          self.success = False
          return

      if attributes.shortFormArgument in self.shortFormArguments:
        if self.allowTermination: self.errors.repeatedShortFormArgument(helpInfo, attributes.longFormArgument, attributes.shortFormArgument)
        else:
          self.success = False
          return

      # Define the argument category.
      attributes.category = category

      # Store the attributes for the argument.
      if isInput: attributes.isInput = True
      elif isOutput: attributes.isOutput = True
      self.arguments[attributes.longFormArgument] = attributes
      self.shortFormArguments.append(attributes.shortFormArgument)

  # Check the contents of the information supplied for the web page.
  def checkWeb(self):
    allowedAttributes              = {}
    allowedAttributes['authors']   = (list, False)
    allowedAttributes['citations'] = (list, False)
    allowedAttributes['emails']    = (list, False)
    allowedAttributes['papers']    = (list, False)
    allowedAttributes['tool']      = (list, False)
    allowedAttributes['web_pages'] = (list, False)

    # If web information was provided, ensure that only valid fields were provided
    for field in self.webPage:
      if field not in allowedAttributes:
        if self.allowTermination: print('ERROR - toolConfiguration - checkWeb', field); exit(1)
        else: return False

    # Return True if this was successfully parsed.
    return True

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

  # Force attribute values based on set values.
  def forceAttributes(self):
    for argument in self.arguments:

      # If the 'command line argument' is set to none and 'modify argument' is unset, force 'modify
      # argument' to be set to 'omit'.
      if self.getArgumentAttribute(argument, 'commandLineArgument') == 'none' and not self.getArgumentAttribute(argument, 'modifyArgument'):
        self.setArgumentAttribute(argument, 'modifyArgument', 'omit')

  # Check that the values given to certain attributes are valid.
  def checkAttributeValues(self):

    # Loop over all the arguments.
    for argument in self.arguments:

      # If modify argument is populated, check that the supplied value is valid.
      value = self.getArgumentAttribute(argument, 'modifyArgument')
      if value:
  
        # Define the valid values.
        validValues = [
                        'omit',
                        'stdout'
                      ]
  
        # Check that the supplied value is valid.
        #TODO ERROR
        if value not in validValues:
          if self.allowTermination: self.errors.invalidValues(self.name, argument, 'modifyArgument', value, validValues)
          else:
            self.success = False
            return False

  # Check that instructions for handling an input stream are correct.
  def checkStreamInstructions(self):

    # Loop over all of the tools arguments.
    for argument in self.arguments:

      # Find arguments with input stream instructions.
      inputInstructions  = self.arguments[argument].inputStreamInstructions
      outputInstructions = self.arguments[argument].outputStreamInstructions
      if inputInstructions: self.checkStreamInstructionsSets(argument, inputInstructions, isInput = True) 
      if outputInstructions: self.checkStreamInstructionsSets(argument, outputInstructions, isInput = False) 


  # Check the streaming instructions.
  def checkStreamInstructionsSets(self, argument, instructions, isInput):

     # Check that the 'default' instructions are present.
     if 'default' not in instructions.keys(): self.errors.noDefaultStream(self.name, argument, isInput)

     # Loop over each of the sets of instructions and check they are valid.
     for setName in instructions.keys():

       # Check that there is a valid argument.
       if 'argument' not in instructions[setName]: self.errors.noArgumentInStreamInstructions(self.name, argument, setName, isInput, 'argument')
       if 'value' not in instructions[setName]: self.errors.noArgumentInStreamInstructions(self.name, argument, setName, isInput, 'value')

  # Check values supplied to construction instructions.
  def checkConstructionInstructions(self):
    success = True

    # Define a list of allowed construction methods.
    allowedMethods = []
    allowedMethods.append('from tool argument')
    allowedMethods.append('define name')

    # Loop over all the arguments set for the pipeline and find ones with construction instructions.
    for argument in self.arguments:
      instructions = self.getArgumentAttribute(argument, 'constructionInstructions')
      category     = self.getArgumentAttribute(argument, 'category')
      if instructions:

        # Check that there is a method described and if so, that it is valid.
        if 'method' not in instructions: self.errors.missingMethod(self.name, category, argument, allowedMethods)
        elif instructions['method'] not in allowedMethods:
          self.errors.invalidMethod(self.name, category, argument, instructions['method'], allowedMethods)

        # Depending on the selected method, check that all accompanying values are valid.
        if instructions['method'] == 'from tool argument': success = self.checkFromArgument(category, argument, instructions)
        elif instructions['method'] == 'define name': success = self.checkDefineName(category, argument, instructions)

    return success

  # Check 'from tool argument' construction instructions.
  def checkFromArgument(self, category, argument, instructions):
    allowedFields = []
    allowedFields.append('method')
    allowedFields.append('modify extension')
    allowedFields.append('modify text')
    allowedFields.append('no temp string')
    allowedFields.append('use argument')

    # Loop over the arguments and check if there are any invalid fields supplied.
    for field in instructions:
      if field not in allowedFields: self.errors.invalidConstructionField(self.name, category, argument, 'from tool argument', field, allowedFields)

  # Check 'define name' construction instructions.
  def checkDefineName(self, category, argument, instructions):
    allowedFields = []
    allowedFields.append('filename')
    allowedFields.append('method')
    allowedFields.append('modify text')
    allowedFields.append('path argument')

    # Loop over the arguments and check if there are any invalid fields supplied.
    for field in instructions:
      if field not in allowedFields: self.errors.invalidConstructionField(self.name, category, argument, 'define name', field, allowedFields)

    # Check for required fields.
    if 'filename' not in instructions: self.errors.missingConstructionField(self.name, category, argument, 'filename', 'define name')

    # If a path argument is supplied, ensure that the supplied argument is valid for the tool.
    if 'path argument' in instructions:
      pathArgument = instructions['path argument']
      if pathArgument not in self.arguments: self.errors.invalidPathArgument(self.name, category, argument, pathArgument, 'define name')

  # Check that substring replacement is valid.
  def checkReplaceSubstring(self, arguments):
    allowedFields = {}
    allowedFields['replace'] = (str, True)
    allowedFields['with']    = (str, True)

    # Loop over all the arguments.
    for category in arguments.keys():
      for argumentAttributes in arguments[category]:

        # Check if the argument has instructions on replacing substrings.
        if 'replace substring' in argumentAttributes:

          # Get the long form argument.
          argument = argumentAttributes['long form argument']
          replace  = argumentAttributes['replace substring']

          # Loop over the list and check that each entry is a dictionary with the correct attributes.
          for data in replace:
            if not methods.checkIsDictionary(data, self.allowTermination):
              if self.allowTermination: self.errors.invalidReplaceSubstring(self.name, category, argument)
              else: return False

            # Check the contained values.
            observedFields = []
            toReplace      = None
            replaceWith    = None
            for key in data:
              value = data[key]
              if key not in allowedFields:
                if self.allowTermination: self.errors.invalidReplaceSubstring(self.name, category, argument)
                else: return False
  
              # Store the value.
              if key == 'replace': toReplace = value
              elif key == 'with': replaceWith = value

              # Record the field as having been observed.
              observedFields.append(key)

            # Store the values.
            self.arguments[argument].isReplaceSubstring    = True
            self.arguments[argument].replaceSubstring.append((str(toReplace), str(replaceWith)))

            # Check that all required fields have been set.
            for field in allowedFields.keys():
              if allowedFields[field][1] and field not in observedFields:
                if self.allowTermination: self.errors.invalidReplaceSubstring(self.name, category, argument)
                else: return False

    # Return success.
    return True

  # Check that instructions on replacing a value with a command are valid.
  def checkValueCommand(self):
    allowedFields = {}
    allowedFields['command']             = (str, True)
    allowedFields['apply to extensions'] = (list, False)

    # Loop over all the tool arguments looking for any with instructions on replacing a value with a command.
    for argument in self.arguments:
      observedFields = []

      # Loop over all fields in the instructions and check that they are valid.
      if self.arguments[argument].valueCommand:
        for field in self.arguments[argument].valueCommand:
  
          # If the field is invalid, terminate.
          if field not in allowedFields: print('ERROR - checkValueCommand'); exit(1)
  
          # Check that the field has the correct type.
          setValue = self.arguments[argument].valueCommand[field]
          value    = str(setValue) if isinstance(setValue, unicode) else setValue
          if allowedFields[field][0] != type(value): print('ERROR - checkValueCommand - type', field); exit(1)
  
          # Record the field as having been observed.
          observedFields.append(field)
  
          # If the field 'apply to extensions' is set, check that all supplied extensions are valid for the argument.
          if field == 'apply to extensions':
            for extension in self.arguments[argument].valueCommand[field]:
              if extension not in self.arguments[argument].extensions: print('ERROR - checkValueCommand - invalid extension'); exit(1)
  
        # Check that all required fields have been set.
        for field in allowedFields.keys():
          if allowedFields[field][1] and field not in observedFields: print('ERROR - checkValueCommand - missing', field); exit(1)

    return True

  # Check that the 'argument order' list is complete and valid.
  def checkArgumentOrder(self):
    observedArguments = []
    if len(self.argumentOrder) != 0:

      # Loop over the arguments in the list.
      for argument in self.argumentOrder:

        # Get the long form of the argument.
        longFormArgument = self.getLongFormArgument(argument)
        if longFormArgument == None: self.errors.invalidArgumentInArgumentOrder(self.name, argument)

        # Check that the argument is a valid argument for the tool.
        observedArguments.append(longFormArgument)

      # Loop over all the defined tool arguments and ensure that they have been defined in the argument order list.
      missingArguments = []
      for argument in self.arguments:
        if argument not in observedArguments: missingArguments.append(argument)
      if len(missingArguments) > 0: self.errors.incompleteArgumentOrder(self.name, missingArguments)

    return True

  ##############################
  ### Get and set attributes ###
  ##############################

  # Get an argument attribute.
  def getArgumentAttribute(self, argument, attribute):
    try: return getattr(self.arguments[argument], attribute)
    except: return None

  # Set an argument attribute.
  def setArgumentAttribute(self, argument, attribute, value):
    setattr(self.arguments[argument], attribute, value)

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

  ######################
  ### Static methods ###
  ######################

  # Get an argument attribute from supplied attributes
  def getArgumentAttributeFromSupplied(attributes, attribute):
    try: return getattr(attributes.arguments[argument], attribute)
    except: return False


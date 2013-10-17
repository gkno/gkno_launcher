#!/usr/bin/python

from __future__ import print_function
import sys

import configurationClass
from configurationClass import *

import dataChecking
from dataChecking import *

import gknoErrors
from gknoErrors import *

import files
from files import *

import gknoConfigurationFiles
from gknoConfigurationFiles import *

import gknoErrors
from gknoErrors import *

class instances:

  # Constructor.
  def __init__(self):
    self.arguments         = {}
    self.errors            = gknoErrors()
    self.externalInstance  = False
    self.externalInstances = []
    self.hasInstance       = False
    self.instanceData      = {}

  # Check for and read in instances from separate instance files.
  def checkInstanceFile(self, sourcePath, directory, filename, instances):
    instanceFilename = filename + '_instances.json'
    if instanceFilename in instances.keys():
      config = configurationClass()
      data   = config.fileOperations.readConfigurationFile(sourcePath + '/config_files/' + directory + '/' + instanceFilename)
      return data
    else: return ''

  # Check the contents of the external instance file.
  def checkInstanceInformation(self, instances, storedInstances, filename):
    if 'instances' not in instances:
      self.errors.instancesFileHasNoInstances(False, filename)
      self.errors.terminate()

    instances = instances['instances']
    givenType = type(instances)
    if givenType != dict:
      self.errors.differentDataTypeInConfig(False, filename, '', 'instances', givenType, dict)
      self.errors.terminate()

    # Loop over the instances and add them to the storedInstances structure.
    for instance in instances:

      # Check that the instances in the instances file do not have the same name as any in the
      # configuration file.
      if instance in storedInstances:
        self.errors.instanceNameAlreadyExists(False, instance, filename)
        self.errors.terminate()
      storedInstances[instance] = instances[instance]

      # Also store the instance name in the externalInstances structure.  This keeps track of
      # the instances in the instances file (and not in the configuration file), if the instances
      # file gets modified (using the export instance functionality).
      self.externalInstances.append(instance)

  # Check if an instance was requested and find the information for it if so.
  def getInstanceName(self, graph, config, verbose):
 
    # If multiple instances have been requested, fail.
    if len(config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-INSTANCE', 'values')[1]) != 1:
      self.errors.multipleInstances(verbose)
      self.errors.terminate()

    # Check the '--instance' node value.  Since the value is a list in a dictionary, allowing
    # for loops, the name of the instance corresponds to element '1' in the dictionary and is
    # the only value in the list.
    self.instanceName = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-INSTANCE', 'values')[1][0]

  # If an instance was requested, get the information from the configuration file, or the
  # instance file.
  def getInstanceArguments(self, path, name, instances, verbose):
    if self.instanceName not in instances:
      self.errors.noInstanceInformation(verbose, path, name, self.instanceName)
      self.errors.terminate()
    else: self.instanceData = instances[self.instanceName]

  # Attach the values supplied on the command line to the nodes.
  def attachPipelineArgumentsToNodes(self, graph, config, gknoConfig):
    for node in self.instanceData['nodes']:

      # Get the ID of the node in the graph that this argument points to.  Since nodes were merged in
      # the generation of the pipeline graph, the dictionary config.nodeIDs retains information about
      # which node this value refers to.
      nodeID = config.nodeIDs[node['id']]

      # All of the values extracted from the instance json file are unicode.  Convert them to strings.
      for counter, value in enumerate(node['values']): node['values'][counter] = str(value)

      config.nodeMethods.addValuestoGraphNodeAttribute(graph, nodeID, node['values'], overwrite = False)

  # If the instance is for a pipeline, all of the commands appearing in the instance will be pipeline commands.
  # These need to be converted to command line arguments for the individual tools.
  def convertPipeArgumentsToToolArguments(self, arguments, shortForms, pipelineArguments, verbose):
    er        = errors()
    shortForm = ''
    value     = ''

    for argument in self.instanceData:
      if argument == 'description': self.description = self.instanceData[argument]
      else:
        if argument in arguments:
          shortForm = arguments[argument]['short form argument']
          value     = self.instanceData[argument]
        elif argument in shortForms:
          shortForm = argument
          argument  = shortForms[argument]
          value     = self.instanceData[shortForm]
        else:
          er.invalidArgumentInInstance(verbose, self.instanceName, argument)
          er.terminate()

        # Determine the tool and argument to which the pipeline argument points.
        tool = arguments[argument]['link to this task']
        if tool == 'pipeline':
          pipelineArguments[argument] = value
        else:
          toolArgument = arguments[argument]['link to this argument']
          if tool not in self.arguments: self.arguments[tool] = {}
          if toolArgument not in self.arguments[tool]: self.arguments[tool][toolArgument] = []
          if type(value) == list:
            for entry in value: self.arguments[tool][toolArgument].append(entry)
          else: self.arguments[tool][toolArgument].append(value)

  # If the instance is for a tool, set the self.arguments structure in the same format as the other
  # arguments structures.
  def setToolArguments(self, tool, verbose):
    self.arguments[tool] = {}
    for argument in self.instanceData:
      if argument == 'description': self.description = self.instanceData[argument]
      else:
        if argument not in self.arguments[tool]: self.arguments[tool][argument] = []
        self.arguments[tool][argument].append(self.instanceData[argument])

  # Now that all of the arguments contained in the instance have been associated with the relevant tool, check
  # that all of the supplied values are valid.
  def checkInstanceArguments(self, taskToTool, arguments, shortForms, verbose):
    er                = errors()
    shortForm         = ''
    value             = ''
    modifiedArguments = {}

    # Clear the instanceData structure as it is no longer required.
    self.instanceData = {}
    for task in self.arguments:
      modifiedArguments[task] = {}
      tool                    = taskToTool[task]
      for argument in self.arguments[task]:
        for value in self.arguments[task][argument]:

          # Ensure that the argument is in the long form.
          if argument in arguments[tool]:
            shortForm = arguments[tool][argument]['short form argument'] if 'short form argument' in arguments[tool][argument] else ''
          elif argument in shortForms[tool]:
            shortForm = argument
            argument  = shortForms[tool][argument]
          else:
            er.unknownArgumentInInstance(verbose, self.instanceName, argument)
            er.terminate()
  
          # Check the data type.
          dataType = arguments[tool][argument]['type']
          success  = checkDataType(dataType, value)
          if not success:
            if dataType == 'flag': er.flagGivenInvalidValueInstance(verbose, argument, shortForm, value)
            elif dataType == 'bool': er.incorrectBooleanValueInInstance(verbose, self.instanceName, argument, shortForm, value)
            elif dataType == 'integer': er.incorrectDataTypeInInstance(verbose, self.instanceName, task, argument, shortForm, value, dataType)
            elif dataType == 'float': er.incorrectDataTypeInInstance(verbose, self.instanceName, task, argument, shortForm, value, dataType)
            elif dataType == 'string': er.incorrectDataTypeInInstance(verbose, self.instanceName, task, argument, shortForm, value, dataType)
            else: print('error with data type 1', givenType)
            er.terminate()
          else:
            if argument not in modifiedArguments[task]: modifiedArguments[task][argument] = []
            modifiedArguments[task][argument].append(value)

    # Update the arguments structrue to contain the modifiedArguments (where all arguments are in their long forms).
    self.arguments = modifiedArguments

  # Check if a different instance of the pipeline was requested and if so, set the parameters.
  def checkToolInstance(self, sourcePath, uniqueArguments, argumentList, tool, arguments, shortForms, instances, instanceFiles, verbose):

    if verbose:
      if externalInstance:
        print('Setting parameters for requested (external) instance: \'', instance, '\'...', sep = '', end = '', file = sys.stdout)
      else:
        print('Setting parameters for requested instance: \'', instance, '\'...', sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()

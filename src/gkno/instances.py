#!/usr/bin/python

from __future__ import print_function
import sys

import dataChecking
from dataChecking import *

import errors
from errors import *

import files
from files import *

class instances:

  # Constructor.
  def __init__(self):
    self.arguments         = {}
    self.externalInstance  = False
    self.externalInstances = []
    self.hasInstance       = False
    self.instanceData      = {}

  # Check for and read in instances from separate instance files.
  def checkInstanceFile(self, sourcePath, directory, filename, instances):
    instanceFilename = filename + '_instances.json'
    if instanceFilename in instances.keys():
      io   = files()
      data = io.getJsonData(sourcePath + '/config_files/' + directory + '/' + instanceFilename, True)
      return data
    else: return ''

  # Check the contents of the external instance file.
  def checkInstanceInformation(self, instances, storedInstances, filename):
    er = errors()

    if 'instances' not in instances:
      er.instancesFileHasNoInstances(False, filename)
      er.terminate()

    instances = instances['instances']
    givenType     = type(instances)
    if givenType != dict:
      er.differentDataTypeInConfig(False, filename, '', 'instances', givenType, dict)
      er.terminate()

    # Loop over the instances and add them to the storedInstances structure.
    for instance in instances:

      # Check that the instances in the instances file do not have the same name as any in the
      # configuration file.
      if instance in storedInstances:
        er.instanceNameAlreadyExists(False, instance, filename)
        er.terminate()
      storedInstances[instance] = instances[instance]

      # Also store the instance name in the externalInstances structure.  This keeps track of
      # the instances in the instances file (and not in the configuration file), if the instances
      # file gets modified (using the export instance functionality).
      self.externalInstances.append(instance)

  # Check if an instance was requested and find the information for it if so.
  def getInstanceName(self, uniqueArguments, argumentList, verbose):
    er = errors()
 
    # Check if the --instance (-is) command appears on the command line.
    if '--instance' in uniqueArguments:

      # If multiple instances have been requested, fail.
      if uniqueArguments['--instance'] != 1:
        er.multipleInstances(verbose)
        er.terminate()
  
      # Find the name of the requested instance and check that it is valid.
      for argument, instance in argumentList:
        if argument == '--instance':
          self.instanceName = instance
          break
    else: self.instanceName = 'default'

  # If an instance was requested, get the information from the configuration file, or the
  # instance file.
  def getInstanceArguments(self, path, name, instances, verbose):
    er = errors()

    if self.instanceName not in instances:
      externalInstancesFilename = name + '_instances.json'
      io = files()
      data = io.getJsonData(path + externalInstancesFilename, False)
      if data == '':
        er.noInstanceInformation(verbose, path, name, self.instanceName)
        er.terminate()
      self.externalInstance = True
      self.instanceData     = data['instances'][self.instanceName]
    else: self.instanceData = instances[self.instanceName]

  # If the instance is for a pipeline, all of the commands appearing in the instance will be pipeline commands.
  # These need to be converted to command line arguments for the individual tools.
  def convertPipeArgumentsToToolArguments(self, arguments, shortForms, verbose):
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
        tool         = arguments[argument]['link to this task']
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

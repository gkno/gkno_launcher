#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import json
import os
import sys

class toolAttributes:
  def __init__(self):
    self.description = ''
    self.executable  = ''
    self.modifier    = ''
    self.path        = ''
    self.precommand  = ''

class toolArguments:
  def __init__(self):
    self.allowedExtensions        = []
    self.allowMultipleDefinitions = False
    self.description              = ''
    self.hasType                  = None
    self.isInput                  = False
    self.isOutput                 = False
    self.isRequired               = False
    self.shortForm                = ''

class toolConfiguration:
  def __init__(self):
    self.arguments            = {}
    self.filename             = ''
    self.jsonError            = ''
    self.setRequiredArguments = False

  # Open a configuration file and store the contents of the file in the
  # configuration dictionary.
  def readConfiguration(self, filename):
    try: jsonData = open(filename)
    except: return False
    self.filename = filename

    try: self.configuration = json.load(jsonData)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.jsonError = exc_value
      return False

    return True

  # Validate the data from the tools configuration file and assuming that everything is valid,
  # put all the data in the tools data structures.
  def getConfigurationData(self, toolName):

    # TODO Validate the data.  This includes checking that information for the specific tool
    # exists in the supplied configuration file.
    success = self.validateConfiguration()

    # Populate the data structures.
    self.setDataStructures(toolName)

  #TODO
  # Validate the contents of the tool configuration file.
  def validateConfiguration(self):
    return True

  # Populate the tool specific data structures.
  def setDataStructures(self, toolName):

    # Set the general tool attributes.
    self.attributes             = toolAttributes()
    self.attributes.description = self.configuration['tools'][toolName]['description']
    self.attributes.executable  = self.configuration['tools'][toolName]['executable']
    self.attributes.modifier    = self.configuration['tools'][toolName]['modifier'] if 'modifier' in self.configuration['tools'][toolName] else ''
    self.attributes.path        = self.configuration['tools'][toolName]['path']
    self.attributes.precommand  = self.configuration['tools'][toolName]['precommand'] if 'precommand' in self.configuration['tools'][toolName] else ''

    # Set the tool argument information.
    for argument in self.configuration['tools'][toolName]['arguments']:
      if argument not in self.arguments: self.arguments[argument] = toolArguments()
      contents   = self.configuration['tools'][toolName]['arguments'][argument]

      # If multiple extensions are allowed, they will be separated by pipes in the configuration
      # file.  Add all allowed extensions to the list.
      extension = contents['extension']
      if '|' in extension:
        extensions = extension.split('|')
        for extension in extensions: self.arguments[argument].allowedExtensions.append(extension)
      else: self.arguments[argument].allowedExtensions.append(extension)

      if 'allow multiple definitions' in contents: self.arguments[argument].allowMultipleDefinitions = contents['allow multiple definitions']
      self.arguments[argument].description              = contents['description']
      self.arguments[argument].hasType                  = contents['type']
      self.arguments[argument].isInput                  = contents['input']
      self.arguments[argument].isOutput                 = contents['output']
      self.arguments[argument].isRequired               = contents['required']
      if 'short form' in contents: self.arguments[argument].shortForm = contents['short form']

    self.configuration = {}

  # Extract and return a list of all of the arguments required by a tool.
  def getRequiredArguments(self):
    requiredArguments         = []
    self.setRequiredArguments = True
    for argument in self.arguments:
      if self.arguments[argument].isRequired: requiredArguments.append(argument)

    return requiredArguments

#!/bin/bash/python

from __future__ import print_function
from subprocess import Popen, PIPE

import json
import os
import subprocess
import sys

import toolConfiguration as tc

# Define a class for holding information for web content..
class webContent:
  def __init__(self):

    # Define a dictionary to hold all the categories to which pipelines belong.
    self.categories = {}

    # Define a dictionary to hold pipeline information.
    self.pipelineInformation = {}

    # Define a dictionary to hold tool information.
    self.toolInformation = {}

    # Define a dictionary to hold resources information.
    self.resourcesInformation = {}

    # Store information on gkno specific arguments.
    self.gknoArguments = {}

  # Update the categories.
  def updateCategories(self, pipelineData):

    # Loop over all the categories with which the tool is associated.
    for category in pipelineData.categories:
      if category not in self.categories: self.categories[str(category)] = [str(pipelineData.name)]
      else: self.categories[category].append(str(pipelineData.name))

  # Update the structures holding pipeline information.
  def updatePipelineInformation(self, pipelineData, arguments):

    # Get the pipeline name.
    pipeline = str(pipelineData.name)

    # Create the object to hold the content for this pipeline.
    self.pipelineInformation[pipeline] = {}
 
    # Add the pipeline description.
    self.pipelineInformation[pipeline]['description'] = str(pipelineData.description)

    # Loop over all of the arguments associated with the pipeline.
    self.pipelineInformation[pipeline]['arguments'] = []
    for argument in arguments:

      # Only deal with top level arguments (e.g. not those that can address child pipelines).
      if '.' not in argument and not arguments[argument].hideInHelp:

        # Update the necessary information for the pipeline.
        information                        = {}
        information['long form argument']  = str(arguments[argument].longFormArgument)
        information['short form argument'] = str(arguments[argument].shortFormArgument)
        information['data type']           = str(arguments[argument].dataType)
        information['description']         = str(arguments[argument].description)

        # Add the information to the pipeline information.
        self.pipelineInformation[pipeline]['arguments'].append(information)

  # Get web site information for all tools.
  def updateTools(self, files, path):

    # Loop over all tools.
    for tool in files.tools:

      # Do not attempt to parse the gknoConfiguration configuration file, since this does not represent a tool.
      if tool != 'gknoConfiguration':
        toolData                  = tc.toolConfiguration()
        toolData.allowTermination = False
  
        # Get the filename of the tool.
        filename = str(path + '/' + tool + '.json')
  
        # Get the configuration file data.
        toolData.getConfigurationData(tool, filename)
        if not toolData.success:
          print('Tool:', tool, 'could not be parsed.')
          sys.stdout.flush()

        # Get all required information.
        elif toolData.webPage:
          webInfo = toolData.webPage
          lower   = str(webInfo['tool']).lower()

          # If this is the first time the tool is observed, add it to the self.toolInformation information.
          if str(lower) not in self.toolInformation: self.toolInformation[lower] = {}

          # Add information to the tool.
          for attribute in webInfo:
            if attribute != 'tool':
              if attribute not in self.toolInformation[lower]: self.toolInformation[lower][str(attribute)] = []

              # Loop over all entries in the list.
              for value in webInfo[attribute]: self.toolInformation[lower][attribute].append(value)

  # Store information on the gkno specific arguments.
  def getGknoArguments(self, arguments):
    for argument in arguments:

      # Get the long and short form arguments, the data type and description.
      dataType    = arguments[argument].dataType
      description = arguments[argument].description
      shortForm   = arguments[argument].shortFormArgument

      # Store the information.
      self.gknoArguments[argument] = {}
      self.gknoArguments[argument]['dataType']    = arguments[argument].dataType
      self.gknoArguments[argument]['description'] = arguments[argument].description
      self.gknoArguments[argument]['shortForm']   = arguments[argument].shortFormArgument

  # Write out the web content and terminate.
  def writeContent(self, commitId, version, date):
    webContent = {}

    # Define the names of the files to output.
    filename = 'gkno-web-content.json'

    # Open the files..
    fileHandle = open(filename, 'w')

    # Include the current version of gkno.
    webContent['__gkno__']            = {}
    webContent['__gkno__']['version'] = version
    webContent['__gkno__']['commit']  = commitId
    webContent['__gkno__']['date']    = date

    # Get the commit ids for all tools.
    execute       = Popen(['git', 'submodule'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, error = execute.communicate()
    success       = execute.returncode

    # Loop over the submodules and extract those associated with tools.
    for line in output.split('\n'):
      lineList = line.split(' ')
      if len(lineList) > 2:
        commit = lineList[1]
        name   = lineList[2]
        name   = name.replace('../', '')

        # Extract resource information.
        if name.startswith('resources'):
          name = name.replace('resources/', '').lower()
          self.resourcesInformation[name] = {}
          self.resourcesInformation[name]['commit'] = commit

        # Extract tool information.
        elif name.startswith('tools'):
          name = name.replace('tools/', '').lower()

          # Check if the tool has information for display on the webpage.
          if name in self.toolInformation: self.toolInformation[name]['commit'] = commit

    # Merge the content into a single structure.
    webContent['categories']    = self.categories
    webContent['tools']         = self.toolInformation
    webContent['pipelines']     = self.pipelineInformation
    webContent['resources']     = self.resourcesInformation
    webContent['gknoArguments'] = self.gknoArguments

    # Dump the information in json format.
    json.dump(webContent, fileHandle, sort_keys = True, indent = 2)

    # Close the files.
    fileHandle.close()

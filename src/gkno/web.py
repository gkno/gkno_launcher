#!/bin/bash/python

from __future__ import print_function

import json
import os
import sys

# Define a class for holding information for web content..
class webContent:
  def __init__(self):

    # Define a dictionary to hold all the categories to which pipelines belong.
    self.categories = {}

    # Define a dictionary to hold pipeline information.
    self.pipelineInformation = {}

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
      if '.' not in argument:

        # Update the necessary information for the pipeline.
        information                        = {}
        information['long form argument']  = str(arguments[argument].longFormArgument)
        information['short form argument'] = str(arguments[argument].shortFormArgument)
        information['data type']           = str(arguments[argument].dataType)
        information['description']         = str(arguments[argument].description)

        # Add the information to the pipeline information.
        self.pipelineInformation[pipeline]['arguments'].append(information)

  # Write out the web content and terminate.
  def writeContent(self):

    # Define the names of the files to output.
    filename = 'gkno-web-content.json'

    # Open the files..
    fileHandle = open(filename, 'w')

    # Merge the content into a single structure.
    webContent = {}
    webContent['categories'] = self.categories
    webContent['pipelines']  = self.pipelineInformation

    # Dump the information in json format.
    json.dump(webContent, fileHandle, sort_keys = True, indent = 2)

    # Close the files.
    fileHandle.close()

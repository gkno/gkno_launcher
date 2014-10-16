#!/bin/bash/python

from __future__ import print_function
from difflib import SequenceMatcher

import gknoErrors
from gknoErrors import *

import json
import os
import subprocess
from subprocess import PIPE
import sys
import traceback

class files:

  # Initiate data structures.
  def __init__(self):

    # Define the errors class.
    self.errors = gknoErrors()

    # Define a dictionary that holds the names of all json files. These are separated into
    # tools and pipelines and json files holding parameter sets only.
    self.jsonFiles                            = {}
    self.jsonFiles['tools']                   = {}
    self.jsonFiles['tool parameter sets']     = {}
    self.jsonFiles['pipelines']               = {}
    self.jsonFiles['pipeline parameter sets'] = {}

    #TODO ARE THESE USED?
    self.dependenciesList      = []
    self.makeFilehandle        = ''
    self.outputsList           = []

  # Search a directory for json files and return a reference to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_parameterSets.json' seperately.  These files contain additional parameter set information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_parameterSets.json'): self.jsonFiles['tool parameter sets'][files] = True
      elif files.endswith('.json'): self.jsonFiles['tools'][files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_parameterSets.json'): self.jsonFiles['pipeline parameter sets'][files] = True
      if files.endswith('.json'): self.jsonFiles['pipelines'][files] = True

    return self.jsonFiles

  # Check if the pipeline/tool name is valid.
  def checkPipelineName(self, mode, name):
    invalidName = False

    # If this is a tool, check against the available tools.
    if mode == 'tool':
      if name + '.json' not in self.jsonFiles['tools']: invalidName = True

    # Now check for pipelines.
    elif mode == 'pipeline':
      if name + '.json' not in self.jsonFiles['pipelines']: invalidName = True

    # If the provided name is not recognised, try to find the most likely name.
    if invalidName:

      # Define variables for use in determining the most likely tool or pipeline if the provided
      # name is invalid.
      mostLikelyPipeline = ''
      mostLikelyTool     = ''
      maxPipelineRatio   = 0.
      maxToolRatio       = 0.

      # Find the closest pipeline name.
      maxToolRatio, mostLikelyTool = self.compareNames(self.jsonFiles['tools'], name)

      # Find the closest pipeline name.
      maxPipelineRatio, mostLikelyPipeline = self.compareNames(self.jsonFiles['pipelines'], name)

      # If the mode is 'tool' and the name given is a pipeline, or vice versa, provide an error
      # suggesting the mode should be changed.
      if mode == 'tool' and maxPipelineRatio == 1.0: self.errors.suggestMode(name, mostLikelyPipeline, 'tool')
      elif mode == 'pipeline' and maxToolRatio == 1.0: self.errors.suggestMode(name, mostLikelyTool, 'pipeline')
      else:
        if maxToolRatio > maxPipelineRatio:
          mostLikelyMode = 'tool'
          mostLikelyName = mostLikelyTool
        else:
          mostLikelyMode = 'pipeline'
          mostLikelyName = mostLikelyPipeline
        self.errors.suggestMostLikely(mode, name, mostLikelyMode, mostLikelyName)

  # Compare the given name with all the pipelines or tools and find the closest match.
  def compareNames(self, names, providedName):
    maxRatio = 0
    for json in names:
      name  = json.replace('.json', '', -1)
      match = SequenceMatcher(None, providedName, name)
      ratio = match.ratio()
      if ratio > maxRatio:
        maxRatio       = ratio
        mostLikelyName = name

    return maxRatio, mostLikelyName

  # Get json data from a file.
  def getJsonData(self, filename, fail):
    errors    = gknoErrors()
    inputData = ''

    # Check that the file exists.
    try: jsonData = open(filename)
    except: errors.hasError = True
    if errors.hasError and fail:
      errors.missingFile(True, filename)
      errors.terminate()

    if not errors.hasError:
      try: inputData = json.load(jsonData)
      except:
        errors.hasError = True
        exc_type, exc_value, exc_traceback = sys.exc_info()

      # If the json file has a problem, terminate the script with an error.
      if errors.hasError:
        errors.jsonOpenError(True, exc_value, filename)
        errors.terminate()

    return inputData

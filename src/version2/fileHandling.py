#!/bin/bash/python

from __future__ import print_function

import fileErrors
from fileErrors import *

import stringComparisons

import json
import os
import sys

# Define a class for handling all file operations.
class fileHandling:
  def __init__(self, toolsPath, pipelinesPath):

    # Define error handling for file errors.
    self.errors = fileErrors()

    # Get the names of all available tools and pipelines.
    self.pipelines = self.getValidJsonFiles(os.listdir(pipelinesPath))
    self.tools     = self.getValidJsonFiles(os.listdir(toolsPath))

  # Given the name of the pipeline, determine if the configuration file exists and if the
  # pipeline is a tool.
  def checkPipeline(self, toolsPath, pipelinesPath, pipeline):
                                                                             
    # If the requested pipeline is valid, return the path to the configuration file.
    if pipeline in  self.pipelines: return pipelinesPath + pipeline + '.json'

    # If the requested pipeline is invalid, terminate.
    else:
      closestPipelines = stringComparisons.findClosestPipelines(self.pipelines, pipeline)
      self.errors.invalidPipelineName(closestPipelines, pipeline)
  
  ######################
  ### Static methods ###
  ######################
  
  # Return a list of json files excluding parameterSet json files.
  @staticmethod
  def getValidJsonFiles(files):
    validFiles = []
    for filename in files:
      if filename.endswith('json') and not filename.endswith('_parameterSets.json'): validFiles.append(filename.rstrip('json')[:-1])

    return validFiles

  # Open a file and return the contents.
  @staticmethod
  def openFile(filename):
    try: return open(filename)
    except: return False

  # Open a configuration file and return the contents.
  @staticmethod
  def readConfigurationFile(filename, allowTermination = True):
    try: jsonData = open(filename)
    except:
      # TODO ERROR
      if allowTermination: print('ERROR - failed to open json file - ' + str(filename)); exit(0)
      else: return False
  
    try: data = json.load(jsonData)
    except:
      if allowTermination:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print('ERROR - failed to extract json information - ' + str(filename))
        print(exc_type, exc_value, exc_traceback)
        exit(0)
      else: return False
  
    return data

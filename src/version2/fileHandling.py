#!/bin/bash/python

from __future__ import print_function

import fileErrors
from fileErrors import *

import stringOperations

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
    if pipeline in self.pipelines: return pipelinesPath + '/' + pipeline + '.json'

    # If the requested pipeline is invalid, terminate.
    else:
      rankedPipelines = stringOperations.rankListByString(self.pipelines, pipeline)
      self.errors.invalidPipelineName(rankedPipelines, pipeline)

  # Check that all the files in the provided list exist.
  def checkFileExistence(self, fileList, resourcesPath, toolsPath):
    missingFiles = []
    for filename in fileList:

      # If the filename starts with a link to a directory, replace it with the absolute path of
      # the directory for this test.
      if filename.startswith('$(PWD)'): updatedFilename = filename.replace('$(PWD)', '.')
      elif filename.startswith('$(RESOURCES)'): updatedFilename = filename.replace('$(RESOURCES)', resourcesPath)
      elif filename.startswith('$(TOOL_BIN)'): updatedFilename = filename.replace('$(TOOL_BIN)', toolsPath)
      else: updatedFilename = filename

      # If the file does not exist, add it to a list of missing files.
      if not os.path.exists(updatedFilename): missingFiles.append(filename)

    # If there are missing files, write out a warning and return False.
    if missingFiles:
      self.errors.missingFiles(missingFiles)
      return False

    # If all required files are present, return True.
    else: return True

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
  def openFileForReading(filename):
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

  # Open all files in a list and return a list of filehandles.
  @staticmethod
  def openFileForWriting(filename):
    return open(filename, 'w')
  
  # Close all the files provided.
  @staticmethod
  def closeFile(filehandle):
    filehandle.close()

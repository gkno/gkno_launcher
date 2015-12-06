#!/bin/bash/python

from __future__ import print_function

import fileErrors as errors

import stringOperations

import json
import os
import sys

# Define a class for handling all file operations.
class fileHandling:
  def __init__(self, toolsPath, pipelinesPath, definedPath):

    # Define error handling for file errors.
    self.errors = errors.fileErrors()

    # If a path to configuration files was defined by the used, find the available configuration
    # files in this directory.
    self.userConfigurationFiles = self.getValidJsonFiles(os.listdir(definedPath)) if definedPath else []

    # Get the names of all available tools and pipelines.
    self.pipelines = self.getValidJsonFiles(os.listdir(pipelinesPath))
    self.tools     = self.getValidJsonFiles(os.listdir(toolsPath))

  # Given the name of the pipeline, determine if the configuration file exists and if the
  # pipeline is a tool.
  def checkPipeline(self, toolsPath, pipelinesPath, definedPath, pipeline):

    # First check to see if the pipeline is available in the user defined configuration files path (if defined).
    if pipeline in self.userConfigurationFiles: return definedPath + '/' + pipeline + '.json'

    # If the requested pipeline is valid, return the path to the configuration file.
    elif pipeline in self.pipelines: return pipelinesPath + '/' + pipeline + '.json'

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

  # Look for a file of the form PIPELINE.RANDOM_STRING.make. If there exists only one such
  # file, return the RANDOM_STRING.
  def getRandomString(self, pipeline):

    # Find all files that fit the description.
    files = []
    for filename in os.listdir("./"):
      if filename.startswith(pipeline) and filename.endswith('.make'): files.append(filename)

    # If there are no files that fit the bill, or too many files, return False.
    if len(files) != 1: return False

    # If there is only a single file, return the random string.
    randomString = files[0].replace(pipeline + '.', '')
    return randomString.replace('.make', '')

  ######################
  ### Static methods ###
  ######################
  
  # Return a list of json files excluding parameterSet json files.
  @staticmethod
  def getValidJsonFiles(files):
    validFiles = []
    for filename in files:
      if filename.endswith('json') and not filename.endswith('-parameter-sets.json'): validFiles.append(filename.rstrip('json')[:-1])

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
      if allowTermination: errors.fileErrors().noFile(filename)
      else: return False
  
    try: data = json.load(jsonData)
    except:
      if allowTermination: errors.fileErrors().notJson(filename, sys.exc_info)
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

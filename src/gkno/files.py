#!/bin/bash/python

from __future__ import print_function

import gknoErrors
from gknoErrors import *

import json
import os
import subprocess
from subprocess import PIPE
import sys
import traceback

class files:
  def __init__(self):
    self.dependenciesList      = []
    self.jsonToolFiles         = {}
    self.jsonToolParameterSets     = {}
    self.jsonPipelineFiles     = {}
    self.jsonPipelineParameterSets = {}
    self.makeFilehandle        = ''
    self.outputsList           = []

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_parameterSets.json' seperately.  These files contain additional parameter set information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_parameterSets.json'): self.jsonToolParameterSets[files] = True
      elif files.endswith('.json'): self.jsonToolFiles[files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_parameterSets.json'): self.jsonPipelineParameterSets[files] = True
      if files.endswith('.json'): self.jsonPipelineFiles[files] = True

  # Get json data from a file.
  def getJsonData(self, filename, fail):
    er        = gknoErrors()
    inputData = ''

    # Check that the file exists.
    try: jsonData = open(filename)
    except: er.hasError = True
    if er.hasError and fail:
      er.missingFile(True, filename)
      er.terminate()

    if not er.hasError:
      try: inputData = json.load(jsonData)
      except:
        er.hasError = True
        exc_type, exc_value, exc_traceback = sys.exc_info()

      # If the json file has a problem, terminate the script with an error.
      if er.hasError:
        er.jsonOpenError(True, exc_value, filename)
        er.terminate()

    return inputData

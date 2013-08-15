#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataChecking
from dataChecking import checkDataType

import errors
from errors import *

import helpClass
from helpClass import *

import json
import os
import sys

class gknoConfigurationFiles:
  def __init__(self):
    pass

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):
    toolFiles     = {}
    pipelineFiles = {}

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_instances.json' seperately.  These files contain additional instance information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_instances.json'): toolFiles[files] = False
      elif files.endswith('.json'): toolFiles[files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_instances.json'): pipelineFiles[files] = False
      elif files.endswith('.json'): pipelineFiles[files] = True

    return toolFiles, pipelineFiles

#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import json
import os
import shutil
import subprocess
import sys
import traceback

class exportJson:
  def __init__(self):
    pass

  # If a configuration file is being exported, check that the configuration filename
  # provided does not already exist.
  def checkExportName(self, tl, io):
    er = errors()

    self.outputName = tl.toolArguments['pipeline']['--export-config']

    # Check that the filename ends with '.json'.
    if self.outputName[-5:len(self.outputName)] != '.json': self.outputName += '.json'

    # Check that the configuration file does not already exist.
    for json in io.jsonPipelineFiles:
      if self.outputName == json:
        er.outputJsonExists(True, "\t", io, self.outputName)
        er.terminate()

  # Step through all of the set values and modify the pipeline information
  # data structure.  If no default was originally given, set the given
  # value as the default
  def modifyPipelineInformation(self, tl, pl):
    print('Setting up new defaults...', end = '', file = sys.stdout)
    sys.stdout.flush()
    for argument in pl.information['arguments']:
      tool         = pl.information['arguments'][argument]['tool']
      if tool == 'pipeline':
        pass
      else:
        toolArgument = pl.information['arguments'][argument]['command']
        pl.information['arguments'][argument]['default'] = tl.toolArguments[tool][toolArgument]
    print('done.', file = sys.stdout)

  # Write out the new configuration file and move to the config_files/pipes directory.
  def writeNewConfigurationFile(self, pl, sourcePath):

    # Open the new file.
    filehandle = open(self.outputName, 'w')
    json.dump(pl.information, filehandle, indent = 2)
    filehandle.close()

    # Move the configuration file.
    destinationPath = sourcePath + '/config_files/pipes/'
    shutil.move(self.outputName, destinationPath)

    print(file = sys.stdout)
    print('=' * 84, file = sys.stdout)
    print('gkno configuration file generation complete.', file = sys.stdout)
    print('It is recommended that the new configuration is tested to ensure expected behaviour.', file = sys.stdout)
    print('=' * 84, file = sys.stdout)
    sys.stdout.flush()

  # Get the data for the new configuration file.
  def getData(self, tl, pl, gknoHelp):

    # Set the paths for all of the inputted files and check that all set parameters
    # are valid.
    for task in pl.information['workflow']:
      tool = pl.information['tools'][task]
      if tl.toolArguments['pipeline']['--verbose']:
        print("\t", task, ' (', tool, ')...', sep = '', file = sys.stdout)
        sys.stdout.flush()
      cl.setPaths(tl, pl, task, tool)
      cl.checkParameters(tl, pl, gknoHelp, task, tool, False)
      if tl.toolArguments['pipeline']['--verbose']:
        print(file = sys.stdout)
        sys.stdout.flush()

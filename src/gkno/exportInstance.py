#!/bin/bash/python

from __future__ import print_function

import dataChecking
from dataChecking import *

import errors
from errors import *

import json
import os
import shutil
import subprocess
import sys
import traceback

class exportInstance:
  def __init__(self):
    self.filename = ''
    self.name     = ''

  # The instance information will be written out to a file defined by the name of the tool or
  # pipeline being run.  If this is called X, the file to export to will be X_instances.json.
  # If this file already exists, read in the information present.
  def checkInstanceFile(self, argumentList, filename, instances, verbose):#, toolFiles, pipelineFiles, verbose):
    er = errors()
    for argument, value in argumentList:
      if argument == '--export-instance':
        self.name = value
        break

    # Set the filename.
    self.filename = filename + '_instances.json'

    # If no filename was supplied for the output configuration file, terminate.
    if self.name == '':
      er.noInstanceNameInExport(verbose, instanceName, self.filename)
      er.terminate()

    # Check that an instance of the given name doesn't already exist.
    for instance in instances:
      if self.name == instance:
        er.instanceNameExists(verbose, self.name)
        er.terminate()

  # Get the data for the new configuration file.
  def getData(self, gknoHelp, argumentInformation, shortForms, isPipeline, workflow, taskToTool, pipelineArgumentInformation, pipelineArguments, toolsOutputtingToStream, links, linkage, arguments, verbose):

    # Set the paths for all of the inputted files and check that all set parameters are valid.
    for task in workflow:
      tool = taskToTool[task]
      setPaths(task, tool, argumentInformation, shortForms, pipelineArgumentInformation, pipelineArguments, links, arguments, verbose)
      checkParameters(gknoHelp, task, tool, argumentInformation, arguments, isPipeline, workflow, pipelineArgumentInformation, toolsOutputtingToStream, links, linkage, False, verbose)

  # Write out the new configuration file and move to the config_files/pipes directory.
  def writeNewConfigurationFile(self, sourcePath, directory, external, instances, arguments):

    # Open the new file.
    filehandle = open(self.filename, 'w')

    # Loop over the instances in the externalInstances structure and store these in the output
    # dictionary.
    output = {}
    output['instances'] = {}
    for instance in external: output['instances'][instance] = instances[instance]

    # Now add the new instance information.
    output['instances'][self.name] = {}
    output['instances'][self.name]['description'] = 'User specified instance'
    for task in arguments:
      for argumentType, pipelineArgument, argument, value in arguments[task]:
        output['instances'][self.name][pipelineArgument] = value

    # Dump all the instances to file.
    json.dump(output, filehandle, indent = 2)
    filehandle.close()

    # Move the configuration file.
    destinationPath = sourcePath + '/config_files/' + directory + '/'
    shutil.copy(self.filename, destinationPath)
    os.remove(self.filename)

    print(file = sys.stdout)
    print('=' * 84, file = sys.stdout)
    print('gkno configuration file generation complete.', file = sys.stdout)
    print('It is recommended that the new configuration is tested to ensure expected behaviour.', file = sys.stdout)
    print('=' * 84, file = sys.stdout)
    sys.stdout.flush()

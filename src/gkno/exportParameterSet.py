#!/bin/bash/python

from __future__ import print_function

import gknoErrors
from gknoErrors import *

import json
import os
import shutil
import subprocess
import sys
import traceback

class exportInstance:


  # Write out the new configuration file and move to the config_files/pipes directory.
  def writeNewConfigurationFile(self, sourcePath, directory, external, parameterSets, arguments):

    # Open the new file.
    filehandle = open(self.filename, 'w')

    # Loop over the parameter sets in the externalInstances structure and store these in the output
    # dictionary.
    output = {}
    output['parameter sets'] = {}
    for parameterSet in external: output['parameter sets'][parameterSet] = parameterSets[parameterSet]

    # Now add the new parameter set information.
    output['parameter sets'][self.name] = {}
    output['parameter sets'][self.name]['description'] = 'User specified parameter set'
    for task in arguments:
      for argumentType, pipelineArgument, argument, value in arguments[task]:
        output['parameter sets'][self.name][pipelineArgument] = value

    # Dump all the parameter sets to file.
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

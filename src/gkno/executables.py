#!/bin/bash/python

from __future__ import print_function
from subprocess import Popen, PIPE

import json
import os
import subprocess
import sys

# Define a class for handling executable files.
class executables:
  def __init__(self):

    # Store a list of missing executables.
    self.missingExecutables = []

  # Check that all required executables exist.
  def checkExecutables(self, toolPath, superpipeline, builtTools):

    print('TEST')
    print(builtTools)
    print()

    # Loop over all tools used in the pipeline.
    for tool in superpipeline.getTools():
      toolData = superpipeline.getToolData(tool)

      # Get the list of equired compiled tools.
      tools = toolData.requiredCompiledTools

      # Get a list of required R packages.
      rPackages = toolData.rPackages

      # Get the exectuable for the tool.
      path       = toolData.path
      executable = toolData.executable

      # If there is no executable or path, this does not need to be checked.
      if path == 'none': executable = None
      elif executable == 'none': executable = None
      else:
        executable = str(toolPath + '/' + path + '/' + toolData.executable)
        if not os.path.exists(executable): self.missingExecutables.append(executable)

    print('Missing executables:')
    for tool in self.missingExecutables: print('\t', tool)
    exit(0)

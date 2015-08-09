#!/bin/bash/python

from __future__ import print_function
from subprocess import Popen, PIPE

import json
import os
import subprocess
import sys

import errors as er
import adminErrors as ae
import fileHandling as fh

# Define a class for handling executable files.
class executables:
  def __init__(self):

    # Define the errors class for use in writing out error messages.
    self.errors = er.errors()

  # Check that all required executables exist.
  def checkExecutables(self, toolPath, superpipeline, builtTools):
    missingCompiledTools = []
    missingExecutables   = []
    missingRPackages     = []
    success              = True

    # Loop over all tools used in the pipeline.
    for tool in superpipeline.getTools():

      # Get the configuration file information for this tool.
      toolData = superpipeline.getToolData(tool)

      # Get the list of equired compiled tools.
      tools = toolData.requiredCompiledTools

      # Get a list of required R packages.
      rPackages = toolData.rPackages

      # Get the exectuable for the tool.
      path       = toolData.path
      executable = toolData.executable

      # Check that all of the tools listed as being required have been successfully compiled.
      for requiredTool in tools:
        if (requiredTool not in builtTools) and (requiredTool not in missingCompiledTools) and (requiredTool != ''):
          missingCompiledTools.append((str(requiredTool), str(tool)))
          success = False

      # If there is no executable or path, this does not need to be checked.
      if path == 'none': executable = None
      elif executable == 'none': executable = None
      else:
        executable = str(toolPath + '/' + path + '/' + toolData.executable)
        if not os.path.exists(executable):
          missingExecutables.append((str(executable), str(tool)))
          success = False

      # If thie pipeline requires any R packages to be installed, ensure that they are.
      for package in rPackages:
        if not self.checkRPackage(package) and (package not in missingRPackages) and (package != ''):
          missingRPackages.append(str(package))
          success = False

    # If any required tools, executables or R packages are missing, output a warning.
    if not success:
      isMissingCompiledTools = True if len(missingCompiledTools) > 0 else False
      isMissingExecutables   = True if len(missingExecutables) > 0 else False
      isMissingRPackages     = True if len(missingRPackages) > 0 else False
      text = ['Missing executable files, compiled tools or R packages.']
      text.append('In order for this pipeline to execute, a number of requirements need to be met. These are not ' + \
      'met for this pipeline. The following requirements are listed below:')
      text.append('\t')
      text.append('\tAll required tools must be compiled:        ' + str(not isMissingCompiledTools))
      text.append('\tAll executable files must be present:       ' + str(not isMissingExecutables))
      text.append('\tAll required R packages must be installed:  ' + str(not isMissingRPackages))
      text.append('\t')

      # Print additional information about missing compiled tools.
      if isMissingCompiledTools:
        text.append('The following tools are listed as needing to have been successfully compiled in order for some of ' + \
        'the tools in this pipeline to run. NOTE: If any of these tools have been included in gkno manually (e.g. the ' + \
        'software is not a part of gkno and was not compiled as part of gkno), please ensure that the \'tools\' list ' + \
        'in the corresponding tool configuration files do not include this software. The list below gives the name ' + \
        'of the missing compiled tool with a tool configuration file calling for it in parentheses.')
        text.append('\t')
        for requiredTool, tool in missingCompiledTools: text.append('\t' + requiredTool + ' (' + tool + ')')
        text.append('\t')

      # Print out the missing executables.
      if isMissingExecutables:
        text.append('The following executable files are required in order for this pipeline to execute. Please ensure that ' + \
        'all software has been succesfully built, or for executable not included in the gkno distribution, the configuration ' + \
        'files point to a valid version of this executable. Each of the missing files is accompanied by the name of a tool ' + \
        'that requires the file in parentheses.')
        text.append('\t')
        for executable, tool in missingExecutables: text.append('\t' + executable + ' (' + tool + ')')
        text.append('\t')

      # If any R packages are missing, provide instructions on how to include them.
      if isMissingRPackages:
        text.append('This pipeline uses R to perform some tasks and not all of the required R packages are available in the ' + \
        'local R installation. Use the following instructions to install the packages listed at the end of this message.')
        text.append('\tFrom the command line, enter R with the command \'R\'. From the R command line, install the packages ' + \
        'with the command \'install.packages(PACKAGE)\', replacing PACKAGE with the name of a package from the following list. ' + \
        'Select a mirror to download from and wait for installation to complete. Repeat this procedure for each of the missing ' + \
        'packages. When complete, use the command \'q()\' to exit R (type \'n\' to exit without saving).')
        text.append('\t')
        for package in missingRPackages: text.append('\t' + package)
        text.append('\t')

      # Write the error message and terminate.
      self.errors.writeFormattedText(text, errorType = 'error')
      self.errors.terminate(1)

  # Check for existence of R packages.
  def checkRPackage(self, package):

    # Define the name of a file for testing.
    filename = str('test-R-package.XGU382HD2.r')

    # Open the file.
    filehandle = fh.fileHandling.openFileForWriting('test-R-package.XGU382HD2.r')

    # Insert the library command with the name of the required package.
    print('library(' + str(package) + ')', sep = '', file = filehandle)
    filehandle.flush()

    # Check if Rscript can be executed.
    try: p = subprocess.Popen('Rscript'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError: ae.adminErrors().noRscript()

    # Execute the r script and retrieve the error code. If the package exists, this will be zero, otherwise 1.
    execute       = Popen(['Rscript', 'test-R-package.XGU382HD2.r'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, error = execute.communicate()

    # Remove the testing file.
    os.remove(filename)

    # Return the error code.
    if execute.returncode != 0: return False
    else: return True

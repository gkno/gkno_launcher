#!/usr/bin/python

from __future__ import print_function

import errors
import inspect
from inspect import currentframe, getframeinfo

import os
import sys

class adminErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors.errors()

    # The error messages are stored in the following list.
    self.text = []

    # Errors encountered with the admin portion of gkno generate an error code of '2'.
    # The error codes associated with other aspects of the code are as follows:
    #
    # Admin errors generate an error code of '2'.
    # Command line errors generate an error code of '3'.
    # File handling errors generate an error code of '4'.
    # General configuration file errors generate an error code of '5'.
    # Tool configuration file errors generate an error code of '6'.
    # Pipeline configuration file errors generate an error code of '7'.
    # Errors associated with the graph construction generate an error code of '8'.
    # Errors associated with handling arguments generate an error code of '9'.
    # Data consistency errors generate an error code of '10'.
    # Errors coming from help requests generate an error code of '11'.
    # Errors with plotting the pipeline graph generate an error code of '12'.
    # Errors with makefile generation generate an error code of '13'.
    # Errors with parameter sets generate an error code of '14'.
    # Errors associated with constructing filenames generate an error code of '15'.
    self.errorCode = '2'

  #####################
  # Admin mode errors
  #####################
  
  def attemptingRemoveUnknownResource(self, resourceName, dest=sys.stderr):
    self.errorType = 'WARNING'
    print("WARNING: Resource '" + resourceName + "' was not removed because it is unknown", file=dest)

  def extractTarballFailed(self, filename, dest=sys.stderr):
    print("ERROR: Could not extract contents of"+filename, file=dest)

  def gitSubmoduleUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/submodule_update.* files for more details.", file=dest)

  def gitUpdateFailed(self, dest=sys.stderr):
    print("ERROR: See logs/gkno_update.* files for more details.", file=dest)

  # If the specified file containing the list of files to skip is missing.
  def cannotSkipAndCompile(self, dest=sys.stderr):
    self.text.append('Invalid arguments for gkno build.')
    self.text.append('The \'--skip-tools (-st)\' argument was set in conjuction with the \'--compile-tools (-ct)\'. These arguments cannot ' + \
    'set simultaneously. Please provide either a list of tools to skip or to compile, but not both')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The user requested that not all tools be built, but failed to provide a list of tools to skip.
  def missingSkipList(self, dest=sys.stderr):
    self.text.append('Missing list of tools to skip.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a json format file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. Please either build all tools using \'gkno build\' or remove tools by using the ' + \
    'command \'gkno build --skip-list list.json\'.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the specified file containing the list of files to skip is missing.
  def missingSkipListFile(self, filename, dest=sys.stderr):
    self.text.append('Missing file containing list of tools to skip.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a json format file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. The specified file \'' + filename + '\' cannot be found. Please check the name of ' + \
    'the supplied file.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool listed as a tool to skip is not a tool in gkno.
  def invalidToolToSkip(self, filename, tool, availableTools, dest=sys.stdout):
    self.text.append('Invalid tool in list of tools to not compile.')
    self.text.append('The \'--skip-tools (-st)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be skipped needs to be supplied. The specified file \'' + filename + '\' contains the tool \'' + tool + '\' which ' + \
    'is not a tool in gkno. Please ensure that all of the tools listed in the file are present in the following list of available tools:')
    self.text.append('\t')
    for tool in availableTools: self.text.append(tool)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The user requested that not all tools be built, but failed to provide a list of tools to skip.
  def missingCompileList(self, dest=sys.stderr):
    self.text.append('Missing list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. Please either build all tools using \'gkno build\' or select the tools to compile ' + \
    'by using the command \'gkno build --compile-list list.json\'.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the specified file containing the list of files to skip is missing.
  def missingCompileListFile(self, filename, dest=sys.stderr):
    self.text.append('Missing file containing list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. The specified file \'' + filename + '\' cannot be found. Please check the name of ' + \
    'the supplied file.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool listed as a tool to skip is not a tool in gkno.
  def invalidToolToCompile(self, filename, tool, availableTools, dest=sys.stdout):
    self.text.append('Invalid tool in list of tools to compile.')
    self.text.append('The \'--compile-tools (-ct)\' argument was set when attempting to build gkno. If set, a text file containing a list ' + \
    'of all the tools to be compiled needs to be supplied. The specified file \'' + filename + '\' contains the tool \'' + tool + '\' which ' + \
    'is not a tool in gkno. Please ensure that all of the tools listed in the file are present in the following list of available tools:')
    self.text.append('\t')
    for tool in availableTools: self.text.append(tool)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  def gknoAlreadyBuilt(self):
    print("Already built.", file=sys.stdout)

  def gknoNotBuilt(self, dest=sys.stderr):
    print("ERROR: 'gkno build' must be run before performing this operation", file=dest)

  def invalidResourceArgs(self, mode, dest=sys.stderr):
    print("ERROR: Invalid arguments or order used. Type 'gkno", mode, "--help' for a usage example.", file=dest)
    
  def noCurrentReleaseAvailable(self, resourceName, dest=sys.stderr):
    print("ERROR: Resource: " + resourceName + " has no release marked as 'current'. Cannot fetch.", file=dest)

  def noReleaseUrlFound(self, resourceName, releaseName, dest=sys.stderr):
    print("ERROR: Could not fetch files for resource: "+resourceName+", release: "+releaseName+" - URL not found", file=dest)

  def requestedUnknownResource(self, resourceName, dest=sys.stderr):
    print("ERROR: Requested resource '" + resourceName + "' is not recognized", file=dest)

  def resourceAlreadyAdded(self, resourceName, dest=sys.stderr):
    print("WARNING: Requested resource '" + resourceName + "' has already been added to gkno", file=dest)

  def resourceFetchFailed(self, resourceName, dest=sys.stderr):
    print("ERROR:  See logs/build_"+resourceName+".* files for more details.", file=dest)
  
  def toolBuildFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/build_"+toolName+".* files for more details.", file=dest)

  def toolUpdateFailed(self, toolName, dest=sys.stderr):
    print("ERROR: See logs/update_"+toolName+".* files for more details.", file=dest)

  def urlRetrieveFailed(self, url, dest=sys.stderr):
    print("ERROR: Could not retrieve file at "+url, file=dest)
    
  def dependencyCheckFailed(self, missing, unknown, incompatible, dest=sys.stderr):
    if len(missing) > 0:
      print("    Missing:", file=dest)
      for dep in missing:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
    if len(incompatible) > 0:
      print("    Not up-to-date:", file=dest)
      for dep in incompatible:
        print("        ", dep.name, 
              "    minimum version: ", dep.minimumVersion, 
              "    found version: "  , dep.currentVersion, sep="", file=dest)
      print("", file=dest)
    if len(missing) > 0 or len(incompatible) > 0:
      print("", file=dest)
      print("gkno (and its components) require a few 3rd-party utilities", file=dest)
      print("to either build or run properly.  To obtain/update the utilities ", file=dest)
      print("listed above, check your system's package manager or search the ", file=dest)
      print("web for download instructions.", file=dest)
      print("", file=dest)

    # ODD CASE
    if len(unknown) > 0:
      print("----------------------------------------", file=dest)
      print("The following utilities have version numbers that could not be ", file=dest)
      print("determined by gkno:", file=dest)
      for dep in unknown:
        print("        ",dep.name, sep="", file=dest)
      print("", file=dest)
      print("This indicates a likely bug or as-yet-unseen oddity.", file=dest)
      print("Please contact the gkno development team to report this issue.  Thanks.", file=dest)
      print("", file=dest)
      print("----------------------------------------", file=dest)
      print("", file=dest)

  # If some of the tools failed to build, write a warning.
  def failedToolBuilds(self, tools):
    self.text.append('Not all tools were built successfully.')
    self.text.append('While building gkno, some of the tools failed to compile successfully. Please check the log files to determine the ' + \
    'cause of the failures and rebuild. In the meantime, all other tools and pipelines not containing the failed tools can be used. The ' + \
    'tools that failed to build are:')
    self.text.append('\t')
    for tool in tools:
      if not tools[tool]: self.text.append('\t' + str(tool))
    self.text.append('\t')
    self.errors.writeFormattedText(self.text, errorType = 'warning')
    self.errors.terminate(self.errorCode)

  # If a tool is added, but the tool name is not provided.
  def noToolNameProvided(self, tools):
    self.text.append('No tool name provided.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but no tool name was provided. If adding a tools, the syntax \'' + \
    './gkno add-tool <tool name> miust be used, where <tool name> is one of the following tools:')
    for tool in tools: self.text.append('\t' + tool.name)
    self.text.append('\t')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool is added, but the tool added is invalid.
  def invalidToolAdded(self, tools):
    self.text.append('Attempt to add an invalid tool.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but the requested tool is not available in gkno. The tool ' + \
    'added must be one of the following:')
    for tool in tools: self.text.append('\t' + tool.name)
    self.text.append('\t')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool is added, but the tool is already available.
  def toolAlreadyBuilt(self):
    self.text.append('Attempt to add a tool that is already present.')
    self.text.append('An attempt to add a tool to the gkno distribution was made, but the requested tool is already available. Only tools that ' + \
    'have previously been omitted from the build can be added.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

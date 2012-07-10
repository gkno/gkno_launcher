#!/usr/bin/python

from __future__ import print_function
import os
import sys

import errors
from errors import *

class tools:

  # Initialise the tools class.
  def __init__(self):
    self.toolInfo     = {}
    self.toolOptions  = {}
    self.dependencies = {}
    self.outputs      = {}

  # Loop over each tool in the pipeline and set up a hash of hashes.
  # For each tool, the set of allowed options along with default values
  # if defined.
  def setupToolOptions(self, cl, pl):
    er = errors()

    print("Setting up tool defaults...", file = sys.stdout)
    for toolName in pl.information['workflow']:

      # Check if this tool name has already been used.  It is required that 
      # the names describing the order of the tools in the pipeline are unique.
      # This ensures that all tools can be anambiguously linked with any of the
      # others.
      if toolName in self.toolOptions:
        er.repeatedTool(toolName)
        er.terminate()
      else:
        tool = pl.information['tools'][toolName]
        print("\t", tool, " (", toolName, ")...", sep = '', end = '', file = sys.stdout)
        self.toolOptions[toolName] = {}
        for option in self.toolInfo[tool]['options']:

          # If a default value for the argument is assigned, set this value in the data structure.
          default = ''
          if 'default' in self.toolInfo[tool]['options'][option]: default = self.toolInfo[tool]['options'][option]['default']

          # Determined the required data type.
          if 'type' not in self.toolInfo[tool]['options'][option]:
            er.toolOptionsError('type', tool, option)
            er.terminate()
          else:
            dataType = self.toolInfo[tool]['options'][option]['type']
            if dataType == 'flag':
              if default == "": default = 'unset'
              if (default != 'set') and (default != 'unset'):
                er.unknownFlagDefault(toolName, option, default)
                er.terminate()
            else:
              if default != "": default = cl.checkDataType(self, pl, toolName, option, default, dataType)

          # Check if a value for this particular option is required.
          if 'required' not in self.toolInfo[tool]['options'][option]:
            er.toolOptionsError('required', tool, option)
            er.terminate()
          self.toolOptions[toolName][option] = default
        print("done.", file = sys.stdout)
    print(file = sys.stdout)

  # Check extensions, paths and output/dependent file strings.
  def determineDependencies(self, cl, pl):
    er = errors()

    print("Checking file extensions and paths...", file = sys.stdout)
    for toolName in pl.information['workflow']:
      tool = pl.information['tools'][toolName]
      print("\t", toolName, '...', sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()

      for option in self.toolOptions[toolName]:
        if option == 'json parameters':
          isInput = True
          cl.setPath(pl, self, toolName, tool, option, isInput, isOutput, isResource)
          value = self.toolOptions[toolName][option]
          self.dependencies[toolName] += value + ' '
        else:
          isInput     = False
          isOutput    = False
          isDependent = False
          isResource  = False

          # Check if the file is an input or an output file, or is listed as a dependent
          # file.  If it is an output, the file should be added to the string containing
          # all outputs from this tool.  If it is an input or dependent file, this will
          # be added to the string containing all files required for this tool to run.
          try: operation = self.toolInfo[tool]['options'][option]['input']
          except: er.error = True
          if er.error:
            print(file = sys.stdout)
            er.toolOptionsError('input', tool, option)
            er.terminate()
          if operation == 'true': isInput = True
  
          try: operation = self.toolInfo[tool]['options'][option]['output']
          except: er.error = True
          if er.error:
            print(file = sys.stdout)
            er.toolOptionsError('output', tool, option)
            er.terminate()
          if operation == 'true': isOutput = True
  
          try: operation = self.toolInfo[tool]['options'][option]['dependent']
          except: er.error = True
          if er.error:
            print(file = sys.stdout)
            er.toolOptionsError('dependent', tool, option)
            er.terminate()
          if operation == 'true': isDependent = True
  
          try: operation = self.toolInfo[tool]['options'][option]['resource']
          except: er.error = True
          if er.error:
            print(file = sys.stdout)
            er.toolOptionsError('resource', tool, option)
            er.terminate()
          if operation == 'true': isResource = True

          if isInput or isDependent or isOutput or isResource:
  
            # If the input/output file is defined, check that the extension is as expected.
            if self.toolOptions[toolName][option] != '':
              cl.checkExtension(self, toolName, tool, option)
              cl.setPath(pl, self, toolName, tool, option, isInput, isOutput, isResource)
              value = self.toolOptions[toolName][option]
  
            # If this file needs to be added to one of the string, check to see if it is a stub
            # or not.  If so, all of the files associated with the stub need to be added to the
            # string.
            string = ''
            isStub = False
            if 'stub' in self.toolInfo[tool]['options'][option]:
              if self.toolInfo[tool]['options'][option]['stub'] == 'true': isStub = True
  
            # If this is a stub, create the string containing all of the files.
            if isStub:
  
              # If the file that the tool requires for successful execution is a stub,
              # make sure that all of the required files are listed in the list of
              # dependencies.
              if 'outputs' not in self.toolInfo[tool]['options'][option]:
                print(file = sys.stdout)
                sys.stdout.flush()
                er.stubNoOutputs(tool, option)
                er.terminate()
              else:
                for name in self.toolInfo[tool]['options'][option]['outputs']: string += value + name + ' '
  
            # If the filename is not a stub, just include the value.
            else: string += value + ' '
  
            if isOutput: self.outputs[toolName] += string
            else: self.dependencies[toolName] += string
      print("done.", file = sys.stdout)
    print(file = sys.stdout)

  # Determine additional dependencies that are not associated with an input
  # command line argument.
  #
  # All of the included output files have already been added to the outputs
  # string for each tool if they appear on the command line.  There are some
  # programs that generate output files, however, without specifying the output
  # file.  In these instances, the additional output files for the tool are
  # included at the beginning of the tools configuration files.  Parse these
  # additional output files (if there are any) and add to the outputs string.
  def determineAdditionalFiles(self, pl):
    er = errors()
    print('Determining additional dependencies and output files...', file = sys.stdout)

    # Loop over each tool in turn and check for additional output files.
    for toolName in pl.information['workflow']:
      if toolName not in self.outputs: self.outputs[toolName] = ''
      tool = pl.information['tools'][toolName]
      print("\t", toolName, " (", tool, ")...", sep = '', end = '', file = sys.stdout)
      if 'additional files' in self.toolInfo[tool]:

        # There are different formats for building up output files.  Each of these can
        # be dealt with separately.
        #
        # 1. If the output file can be constructed from a value given to one of the
        # tools command line arguments.
        if 'from input arguments' in self.toolInfo[tool]['additional files']:
          for argument in self.toolInfo[tool]['additional files']['from input arguments']:

            # Check that the command which should be used to determine the file name exists
            # and has a value defined.
            fileType = ''
            command  = ''
            filename = ''
            try: fileType = argument['type']
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.optionAssociationError('type', 'additional files\' -> \'from input arguments', toolName)
              er.terminate()

            try: command = argument['command']
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.optionAssociationError('command', 'additional files\' -> \'from input arguments', toolName)
              er.terminate()

            try: filename = self.toolOptions[toolName][command]
            except: er.error = True
            if er.error:
              print(file = sys.stdout)
              sys.stdout.flush()
              er.missingCommand(toolName, tool, command)
              er.terminate()
              
            # In constructing the output file name, the extension associated with the associated
            # file name can be stripped off and a new extension can be appended if requested.
            # Determine and enact the appropriate steps.
            if 'remove extension' in argument:
              if argument['remove extension'] == 'true':
                filename = filename.rpartition('.')[0]
            if 'add extension' in argument:
              if argument['add extension'] == 'true':
                try: extension = argument['output extension']
                except: er.error = True
                if er.error:
                  print(file = sys.stdout)
                  sys.stdout.flush()
                  er.optionAssociationError('output extension', 'additional files\' -> \'from input arguments', toolName)
                  er.terminate()
                filename += '.' + extension

            # If the file is a dependency, add to the dependency string, otherwise add to the
            # output string.
            if fileType == 'dependency': self.dependencies[toolName] += filename + ' '
            elif fileType == 'output': self.outputs[toolName] += filename + ' '
            else:
              er.unknownDependencyOrOutput(toolName, fileType)
              er.terminate()
           
      # Strip lagging spaces from the self.outputs string.
      self.dependencies[toolName] = self.dependencies[toolName].rstrip()
      self.outputs[toolName]      = self.outputs[toolName].rstrip()

      print("done.", file = sys.stdout)
    print(file = sys.stdout)

#!/bin/bash/python

from __future__ import print_function

import errors
from errors import *

import json
import os
import subprocess
from subprocess import PIPE
import sys
import traceback

class files:
  def __init__(self):
    self.jsonToolFiles      = {}
    self.jsonPipelineFiles  = {}
    self.makeFilehandle     = ''
    self.phoneHomeID        = ''

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):
      if files.endswith('.json'): self.jsonToolFiles[files] = 1

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('.json'): self.jsonPipelineFiles[files] = 1

  # From the list of json files, popluate a hash table with the names
  # and descriptions of the tools.
  def getToolDescriptions(self, tl, sourcePath):
    er = errors()

    print("Reading in tool configuration files...", file = sys.stdout)
    for toolFile in self.jsonToolFiles:
      print("\t", toolFile, '...', sep = '', end = '', file = sys.stdout)
      sys.stdout.flush()
      jsonData = open(sourcePath + '/' + toolFile)
      try: toolData = json.load(jsonData)
      except:
        er.error = True
        exc_type, exc_value, exc_traceback = sys.exc_info()

      # If the json file has a problem, terminate the script with an error.
      if er.error:
        print(file = sys.stdout)
        er.jsonOpenError("\t\t", exc_value)
        er.terminate()
      else:
        for tool in toolData['tools']:
          tl.toolInfo[tool] = toolData['tools'][tool]
        print("done.", file = sys.stdout)

    print(file = sys.stdout)

  # If a pipeline is being run, search for the corresponding config file.
  def getPipelineConfigurationFile(self, path):
    er = errors()

    # If the pipeline name was not given, throw an error.
    try: pipelineName = sys.argv[2]

    # If no pipeline name was given, throw an error.
    except:
      er.pipelineUsage(self.jsonPipelineFiles)
      exit(1)

    if (pipelineName == '--help') or (pipelineName == '-h'):
      er.pipelineUsage(self.jsonPipelineFiles)
      exit(0)
    self.jsonPipelineFile = path + "/" + sys.argv[2] + '.json'
    if pipelineName + '.json' not in self.jsonPipelineFiles.keys():
      er.missingPipelineJsonFile(self.jsonPipelineFile)
      er.pipelineUsage(self.jsonPipelineFiles)
      exit(1)

# Open the pipeline configuration file and put the information into memory.
  def getPipelineDescription(self, pl):
    er = errors()

    print("-------------------------------------", file = sys.stdout)
    print("Executing pipeline: ", sys.argv[2], sep = "", file = sys.stdout)
    print("-------------------------------------\n", file = sys.stdout)
    print("Reading in pipeline configuration file...", end = '', file = sys.stdout)
    sys.stdout.flush()
    jsonData = open(self.jsonPipelineFile)
    try: pl.information = json.load(jsonData)
    except:
      print(file = sys.stdout)
      er.error = True
      exc_type, exc_value, exc_traceback = sys.exc_info()

    # If the json file has a problem, terminate the script with an error.
    if er.error:
      er.jsonOpenError("\t", exc_value)
      er.terminate()
    else: print("done\n", file = sys.stdout)

    return 'pipe/' + sys.argv[2]

  # The set of tools and the associated parameters are set
  # in the config file, so build up the scripts to run the
  # pipeline.
  def generateMakefile(self, tl, pl, sourcePath):
    er = errors()

    # Open a script file.
    self.makeFilehandle = open('Makefile', 'w')
    self.filename       = os.path.abspath('Makefile')
  
    print("Generating Makefile...", file = sys.stdout)
    print("### gkno Makefile\n", file = self.makeFilehandle)
    print("GKNO_PATH=", sourcePath, "/src/gkno", sep = "", file = self.makeFilehandle)
    print("TOOL_BIN=", sourcePath, "/tools", sep = "", file = self.makeFilehandle)
    print("RESOURCES=", sourcePath, "/resources\n", sep = "", file = self.makeFilehandle)
  
    # Loop over each tool in the work flow and generate the command lines
    # for each.  Work in reverse order building up the dependencies.
    for counter in reversed(range(0, len(pl.information['workflow']))):
      toolName = pl.information['workflow'][counter]
      tool     = pl.information['tools'][toolName]

    # Having established all the dependencies and the output files for each
    # tool, write out the commands for the Makefile.
    print(".DELETE_ON_ERROR:", file = self.makeFilehandle)
    print(".PHONY: all", file = self.makeFilehandle)
    print("all:", end = "", file = self.makeFilehandle)
    for counter in reversed(range(0, len(pl.information['workflow']))):
      toolName = pl.information['workflow'][counter]
      tool     = pl.information['tools'][toolName]
      if toolName in tl.outputs: print(tl.outputs[toolName], end = ' ', file = self.makeFilehandle)

      # If the tool doesn't generate an output, set the target of the recipe in the
      # Makefile as a phony target.  Define the name of the phony target as the tool
      # name appended with phony.
      else:
        phonyTarget = toolName.replace(' ', '_') + '_phony'
        tl.outputs[toolName] = ''
        tl.outputs[toolName] = phonyTarget
        print(" ", phonyTarget, sep = "", end = "", file = self.makeFilehandle)

    print(file = self.makeFilehandle)
    print(file = self.makeFilehandle)
    for counter in reversed(range(0, len(pl.information['workflow']))):
      toolName     = pl.information['workflow'][counter]
      tool         = pl.information['tools'][toolName]
      pathVariable = self.writeInitialInformation(tl, toolName, tool)
      self.generateCommand(tl, pl, pathVariable, toolName, tool)

    # Close the Makefile.
    self.makeFilehandle.close()
    print(file = sys.stdout)

  # Write initial information to the Makefile.
  def writeInitialInformation(self, tl, toolName, tool):
    er = errors()
    print("\t", toolName, " (", tool, ")...", sep = "", file = sys.stdout)
    print("### Information for ", toolName, " (", tool, ")", sep = "", file = self.makeFilehandle)
    try: path = tl.toolInfo[tool]['path']
    except: er.error = True
    if er.error:
      er.missingJsonEntry('path', tool)
      er.terminate()

    # Only print out the path if it isn't defined as 'null'.  Unix commands will
    # be defined as 'null' as they do not need to include a path, for example.
    pathVariable = ''
    if path != 'null':
      pathVariable = (tool.replace(" ", "_")  + '_PATH').upper()
      print(pathVariable, "=$(TOOL_BIN)/", path, sep = "" , file = self.makeFilehandle)
  
    return pathVariable

  # Generate commands for the makefile
  def generateCommand(self, tl, pl, pathVariable, toolName, tool):
    er = errors()

    # Check if the target is a phony target.  If so, define the phony target.
    if tl.outputs[toolName].endswith('_phony'): print(".PHONY: ", tl.outputs[toolName], sep = '', file = self.makeFilehandle)

    # Print out the output file and the list of dependencies.
    else: print(tl.outputs[toolName], ": ", tl.dependencies[toolName], sep = '', file = self.makeFilehandle)
  
    # Print out the command line.
    print("\t", end = '', file = self.makeFilehandle)
    if 'precommand' in tl.toolInfo[tool]:
      print(tl.toolInfo[tool]['precommand'], ' ', sep = '', end = '', file = self.makeFilehandle)
    if pathVariable == '': print(tl.toolInfo[tool]['executable'], sep = '', end = '', file = self.makeFilehandle)
    else: print("$(", pathVariable, ")/", tl.toolInfo[tool]['executable'], sep = '', end = '', file = self.makeFilehandle)
    if 'modifier' in tl.toolInfo[tool]:
      print(" ", tl.toolInfo[tool]['modifier'], sep = '', end = '', file = self.makeFilehandle)
  
    # Check if the order in which the parameters appear matters.  For certain
    # tools, the command line is built up of a list of arguments, but each
    # argument isn't given an option.  For example, renaming a file has a 
    # command line 'mv A B', where A and B are filenames that have to appear
    # in the correct order.
    if 'ordered' in tl.toolInfo[tool]:
      optionList = {}
      if tl.toolInfo[tool]['ordered'] == 'true':
        for option in tl.toolOptions[toolName]:
          try: order = tl.toolInfo[tool]['options'][option]['order']
          except: er.error = True
          if er.error:
            er.missingOrderID(toolName, tool, option)
            er.terminate()

          if order in optionList:
            er.optionIDExists(toolName, tool, option)
            er.terminate()

          # Only include the option, if it is required.
          if tl.toolOptions[toolName][option] == 'set': optionList[order] = option
          elif (tl.toolOptions[toolName][option] != 'unset') and (tl.toolOptions[toolName][option] != ''):
            optionList[order] = option + ' ' + tl.toolOptions[toolName][option]

      orderList = sorted(optionList.iteritems())
      start     = int(orderList[0][0])
      end       = int(orderList[-1][0])
      while start <= end:
        if str(start) not in optionList: er.orderWarning(toolName, tool, start)
        else: print(" \\\n\t", optionList[str(start)], sep = "", end = "", file = self.makeFilehandle)
        start += 1
    else:

      # Include all of the set options.
      for option in tl.toolOptions[toolName]:

        # Check if the option is a flag.
        isFlag = False
        if option == 'json parameters':

          # If a json file is being used to generate parameters, the configuration file
          # needs to contain a 'json block' argument.  This tells the script the name of
          # the block in the json file from which to extract parameters.
          if 'json block' not in pl.information['linkage'][toolName]['json parameters']:
            er.optionAssociationError('json block', 'json parameters', 'pipeline')
            er.terminate()
          else:
            jsonBlock = pl.information['linkage'][toolName]['json parameters']['json block']
            print(" \\\n\t`python $(GKNO_PATH)/getParameters.py ", end = "", file = self.makeFilehandle)
            print(tl.toolOptions[toolName][option], " ", jsonBlock, "`", sep = "", end = "", file = self.makeFilehandle)
        else:
          if tl.toolInfo[tool]['options'][option]['type'] == 'flag': isFlag = True

          # If the command is a flag, check if the value is 'set' or 'unset'.  If 'set',
          # write out the command.
          if isFlag:
            if tl.toolOptions[toolName][option] == 'set': print(" \\\n\t", option, sep = "", end = "", file = self.makeFilehandle)
          else:

            # Some command lines allow multiple options to be set and the command line can
            # therefore be repeated multiple times.  If the defined value is a list, this
            # is the case and the command should be written out once for each value in the
            # list.
            isList = isinstance(tl.toolOptions[toolName][option], list)
            if isList:
              for value in tl.toolOptions[toolName][option]:
                print(" \\\n\t", option, " ", value, sep = "", end = "", file = self.makeFilehandle)

            # If the option is given a value, print it out.
            elif tl.toolOptions[toolName][option] != '':
              print(" \\\n\t", option, " ", tl.toolOptions[toolName][option], sep = "", end = "", file = self.makeFilehandle)

    print(file = self.makeFilehandle)
    print(file = self.makeFilehandle)

  # Ping the website with usage information.
  def phoneHome(self, sourcePath):
    print("Logging gkno usage with ID: ", self.phoneHomeID, "...", sep = '', end = '', file = sys.stdout)
    executable = sourcePath + '/src/gkno/ga.sh'
    subprocess.call([executable, self.phoneHomeID], stdout=PIPE, stderr=PIPE)
    print("done.", file = sys.stdout)

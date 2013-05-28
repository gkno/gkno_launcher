#!/usr/bin/python

from __future__ import print_function
from copy import deepcopy
import os
import sys

import errors
from errors import *

import files
from files import *

# Check if data types agree.
def checkDataType(expectedType, value):
  success = True

  # Check that flags have the value "set" or "unset".
  if expectedType == 'flag':
    if value != 'set' and value != 'unset': success = False

  # Boolean values should be set to 'true', 'True', 'false' or 'False'.
  elif expectedType == 'bool':
    if value != 'true' and value != 'True' and value != 'false' and value != 'False': success = False

  # Check integers...
  elif expectedType == 'integer':
    try: test = int(value)
    except: success = False

  # Check floats...
  elif expectedType == 'float':
    try: test = float(value)
    except: success = False

  # and strings.
  elif expectedType == 'string':
    try: test = str(value)
    except: success = False

  # If the data type is unknown.
  else:
    success = False

  return success

# Some of the tools included in gkno can have multiple input files set on the
# command line.  When many files are to be included, it can be more convenient
# to allow a file including a list of files to be included.  Check if any of the
# tools have input lists specified and if so, add these to the actual command line
# argument list that should be used.
def checkInputLists(argumentInformation, workflow, taskToTool, arguments, verbose):
  er                = errors()
  modifiedArguments = deepcopy(arguments)
  argumentsToRemove = []

  for task in workflow:
    tool = taskToTool[task]
    if task not in modifiedArguments: modifiedArguments[task] = {}
    for argument in arguments[task]:
      isList = False
      if argument != 'json parameters':
        if 'list of input files' in argumentInformation[tool][argument]:
          if argumentInformation[tool][argument]['list of input files'] == True: isList = True

      if isList:
        repeatArgument = argumentInformation[tool][argument]['apply by repeating this argument']

        # Check that the file exists, open and read the contents.  The file should
        # be a simple json list.  Only do this is a file is given.
        filename = arguments[task][argument][0]
        io       = files()
        data     = io.getJsonData(filename, False)
        if data == '':
          er.noInputFileList(verbose, filename)
          er.terminate()
        if 'filename list' not in data: er.hasError = True
        else:
          if not isinstance(data['filename list'], list): er.hasError = True
        if er.hasError:
          er.malformedFilenameList(verbose, filename, task, tool, argument)
          er.terminate()

        # All of the data has been read in and is valid, so can be added to the
        # lists of values for the specified argument.
        if repeatArgument not in modifiedArguments[task]: modifiedArguments[task][repeatArgument] = []
        for inputFile in data['filename list']:
          modifiedArguments[task][repeatArgument].append(inputFile)

        # Having accounted for all the files in the list, this option can be removed
        # from the tools data structure.
        argumentsToRemove.append((task, argument))

  for task, argument in argumentsToRemove:
    del modifiedArguments[task][argument]

  return modifiedArguments

# Some of the variables use the value MAKEFILE_ID in their names.  This is often used in
# the names of temporary files etc and is intended to ensure that if multiple scripts are
# generated, these values are all different in each script.  If there are parameters in the
# internal loop that use this value, then they need to be modified to include the iteration
# number to ensure that the values are still unique.
def checkMakefileID(arguments, iTasks, numberOfIterations):
  for task in arguments:

    # Determine if this task is in an internal loop.  If so, loop over each iteration and
    # check if any of the argument values contain 'MAKEFILE_ID'.
    if task in iTasks:
      for iterationCounter, iterationArguments in enumerate(arguments[task]):
        for argument in iterationArguments:
          for argumentCounter, value in enumerate(iterationArguments[argument]):
            if 'MAKEFILE_ID' in value:
              tempString  = arguments[task][iterationCounter][argument][argumentCounter]
              replacement = 'MAKEFILE_ID)_' + str(iterationCounter + 1)
              arguments[task][iterationCounter][argument][argumentCounter] = tempString.replace('MAKEFILE_ID)', replacement)

# For each tool, find the output files.  If these haven't already been given a
# value, then a value needs to be assigned.  First check if there is a 'construct
# filenames' block in the json file with instructions on how to build the filename
# (this applies to pipelines only).  If there are no explicit instructions, check
# if any of the input files have 'use for filenames' set to true.  If so, use this
# filename to build the output (changing the extension as required).
def constructFilenames(task, tool, arguments, argumentInformation, constructFilenames, links, taskToTool, verbose):
  er = errors()

  # Each task has a set of arguments depending on whether the task is involved in an internal loop
  # and the number of loops over the task need to be performed.  When constructing the filenames,
  # consider each set of argument in turn.
  for counter, iteration in enumerate(arguments[task]):

    # First identify the input and output files and how their names should be constructed.
    filenameConstructor = ''
    inputFiles          = []
    outputFiles         = {}

    for argument in arguments[task][counter]:
      if argument != 'json parameters':
        isInput  = argumentInformation[tool][argument]['input']
        isOutput = argumentInformation[tool][argument]['output']

        # If this is an input file, check to see if it is to be used for building filenames.
        if isInput:

          # Check if this input file is itself to be created.  If so, create it now.  If the
          # information is not yet available, terminate.
          construct = False
          if task in constructFilenames:
            for constructArgument in constructFilenames[task]:
              if constructArgument == argument:
                construct = True
                break
          if construct:
            construction = constructFilename(task, tool, counter, argument, constructFilenames, arguments, argumentInformation, taskToTool, verbose)
            arguments[task][counter][argument].append(construction)

          inputFiles.append(argument)
          if 'use for filenames' in argumentInformation[tool][argument]:
            if argumentInformation[tool][argument]['use for filenames']:
  
              # If there was an input file previous designated as the file to use for
              # constructing output filenames for this tool, gkno cannot determine which
              # file to use and so terminates.
              if filenameConstructor != '':
                er.multipleFilenameConstructors(verbose, task, tool, argument, filenameConstructor)
                er.terminate()
              else: filenameConstructor = argument

        # If the argument is an output, check to see if it has already been defined.  If
        # not, store this as a filename to be constructed.
        if isOutput:
          if len(arguments[task][counter][argument]) == 0:
  
            # For pipelines, check if the 'construct filenames' block exists and describes
            # how to build this filename.
            if task in constructFilenames:
              for constructArgument in constructFilenames[task]:
                if constructArgument == argument: outputFiles[argument] = 'construct'
                break

            # If the argument to be built has no instructions on how to construct the filename.
            if argument not in outputFiles:
  
              # If the configuration file specifically states not to construct the filename from
              # the input file, terminate as the user needs to input the output filename.  Otherwise
              # use the input file.
              if 'do not construct filename from input' in argumentInformation[tool][argument]:
                shortForm = argumentInformation[tool][argument]['short form argument'] if 'short form argument' in \
                argumentInformation[tool][argument] else ''
                pipelineArgument  = ''
                pipelineShortForm = ''
                if task in links:
                  if argument in links[task]:
                    pipelineArgument  = links[task][argument][0]
                    pipelineShortForm = links[task][argument][1]
                er.missingFilenameNotToBeConstructed(verbose, task, tool, argument, shortForm, pipelineArgument, pipelineShortForm)
                er.terminate()
              else: outputFiles[argument] = 'from input'
  
    # Now all of the output files have been identified and the method of filename generation
    # determined, build the filenames.
    for outputFile in outputFiles:

      # If to be constructed using information from the configuration file, construct.
      if outputFiles[outputFile] == 'construct':
        construction = constructFilename(task, tool, counter, outputFile, constructFilenames, arguments, argumentInformation, taskToTool, verbose)
        arguments[task][counter][outputFile].append(construction)

      elif outputFiles[outputFile] == 'from input':

        # If the output filename is to be generated using an input file from this task and there
        # are no input files designated as to be used for generating the filename, check what
        # input files there are.  If there is only one input for this task, use this file to
        # generate the filenames.  If there are multiple or no input file arguments, terminate.
        if filenameConstructor == '':
          if len(inputFiles) == 1:
            constructFilenameFromInput(task, tool, counter, argumentInformation, arguments, outputFile, inputFiles[0], verbose)
          #else:
          #  er.unknownFilenameConstructor(verbose, task, tool, outputFile)
          #  er.terminate()

        else:
          constructFilenameFromInput(task, tool, counter, argumentInformation, arguments, outputFile, filenameConstructor, verbose)

# Construct filenames using the instructions in the pipeline configuration file.
def constructFilename(task, tool, iteration, argument, constructFilenames, arguments, argumentInformation, taskToTool, verbose):
  er           = errors()
  basename     = ''
  construction = ''
  separator    = '_'

  filenameRoot             = constructFilenames[task][argument]['filename root']
  additionalText           = constructFilenames[task][argument]['additional text'] if 'additional text' in constructFilenames[task][argument] else ''
  additionalTextParameters = constructFilenames[task][argument]['additional text from parameters'] if 'additional text from parameters' in \
  constructFilenames[task][argument] else ''

  # If the basename is 'from argument', the 'tool', 'argument' and 'remove extension'
  # variables must be set.  Take the value from the specified tool/argument, remove
  # the extension if requested, then add the additional text if there is any to be
  # added.  Remove the path if one exists.
  if filenameRoot == 'from argument':
    linkedTask      = constructFilenames[task][argument]['get root from task']
    linkedArgument  = constructFilenames[task][argument]['get root from argument']
    removeExtension = constructFilenames[task][argument]['remove input extension']

    # If the argument for the linked task is unset, the filename cannot be constructed, so return from
    # the routine without having constructed the new filename.  The unset filenames will be caught later
    # and gkno terminated if they were required.
    if len(arguments[linkedTask][iteration][linkedArgument]) != 1:
      return

    # If the linked argument is set (and has only one name), construct the new filename.
    construction = arguments[linkedTask][iteration][linkedArgument][0].split('/')[-1]
    if removeExtension:
      linkedTool = taskToTool[linkedTask]
      extension  = argumentInformation[linkedTool][linkedArgument]['extension']

      # If there is a '|' symbol in the extension, break up all the allowable extensions
      # and check if the name ends with any of them and if so, remove the extension.
      extensions = extension.split('|')
      for extension in extensions:
        if construction.endswith(extension):
          construction = construction[0:(len(construction) - len(extension) - 1)]
          break

  elif filenameRoot == 'from text':
    construction = constructFilenames[task][argument]['filename root text']

  # If there is additional text to add to the name, the additionalTextParameters variable will have
  # a value.  If this is the case, a list of tool/argument pairs needs to be provided.  These
  # values will be added to the name separated by the separator variable.
  if len(additionalTextParameters) != 0:

    # Determine the separator to be used when joining the values together.  If no separator
    # is provided, use '_'.
    if 'separator' in additionalTextParameters: separator = additionalTextParameters['separator']

   # Determine the order of the variables to add.
    order = additionalTextParameters['order']

    for field in order:
      if field != 'filename root' and field != 'separator':

        # If the text isn't 'filename root' or 'separator', then it refers to a variable used in the pipeline.
        additionalTask            = additionalTextParameters[field]['get parameter from task']
        additionalArgument        = additionalTextParameters[field]['get parameter from argument']
        additionalRemoveExtension = additionalTextParameters[field]['remove extension']
        additionalTool            = taskToTool[additionalTask]

        # Now get the variable if it exists.
        value = ''
        if additionalArgument in arguments[additionalTask][iteration]: value = arguments[additionalTask][iteration][additionalArgument][0]

        # If the parameter being used in the output filename is itself a filename,
        # it should contain a path.  If this is the case, remove the path from the
        # name before using in the construction.
        try: value = value.split('/')[-1]
        except: pass

        # If the extension is to be removed, check that the input argument defines a file
        # with an extension and if so, remove the extension if requested.
        if additionalRemoveExtension:
          extension = argumentInformation[additionalTool][additionalArgument]['extension']

          # If there is a '|' symbol in the extension, break up all the allowable extensions
          # and check if the name ends with any of them and if so, remove the extension.
          if extension != '' and extension != 'no extension':
            extensions = extension.split('|')
            for extension in extensions:
              if value.endswith(extension):
                value = value[0:(len(value) - len(extension) - 1)]
                break
        if value != '': construction += separator + str(value)

  # If there is additional text to add to the filename (not from a parameter), add it here.
  if len(additionalText) != 0: construction += additionalText

  # Determine if the output file is a stub.  If not, add the extension to the output file.
  isStub = argumentInformation[tool][argument]['stub'] if 'stub' in argumentInformation[tool][argument] else False
  if not isStub:
    extension = argumentInformation[tool][argument]['extension']

    # Some tools can operate on any file (e.g. gzip) and so have the extension listed as
    # 'no extension'.  If this is the case, check if the output extension is given in the
    # pipeline configuration file.  If so, use this extension, if not, do not add an
    # extension.
    if extension == 'no extension':
      outputExtension = constructFilenames[task][argument]['output extension'] if 'output extension' in constructFilenames[task][argument] else ''
      if outputExtension != '': construction += '.' + str(outputExtension)

    else:

      # Check if the extension is already in place.  If not add it.
      if not construction.endswith('.' + extension): construction += '.' + str(extension)

  return construction

# If the output filename is to be constructed from an input filename, take the
# requested input filename, remove the extension and replace with the required
# extension for this output file.
def constructFilenameFromInput(task, tool, iteration, argumentInformation, arguments, outputFile, inputArgument, verbose):
  er = errors()
  
  # Check if the input file that is to be used for constructing the output filename is
  # blank.  If so, terminate gkno as the output filename cannot be determined.
  if len(arguments[task][iteration][inputArgument]) == 0: return

  # If the output filename is to be generated from an input file, but there are
  # multiple files, use the first file in the list for generating the output
  # filename.
  inputFile      = arguments[task][iteration][inputArgument][0].split('/')[-1]
  inputExtension = ''
  for extension in argumentInformation[tool][inputArgument]['extension'].split('|'):
    if inputFile.endswith(extension):
      inputExtension = extension
      break

  # Strip off the extension.
  if inputExtension != '': inputFile = inputFile[0:(len(inputFile) - len(extension) - 1)]

  # Add the output extension unless the output is a stub.
  isStub = argumentInformation[tool][outputFile]['stub'] if 'stub' in argumentInformation[tool][outputFile] else False
  if isStub: arguments[task][iteration][outputFile].append(inputFile)
  else: arguments[task][iteration][outputFile].append(inputFile + '.' + argumentInformation[tool][outputFile]['extension'].split('|')[0])

# Check to see if the input file has a path or not.  If not, set it to the
# input or the output path.
def setPaths(task, tool, argumentInformation, shortForms, pipelineArgumentInformation, pipelineArguments, links, arguments, verbose):

  # Loop over all the tool arguments and check if the argument is for an input or output
  # file.
  for counter, iteration in enumerate(arguments[task]):
    for argument in arguments[task][counter]:

      # If the value is blank, prior to constructing the Makefiles, each
      # argument is checked and if the argument is not set and is required, gkno 
      # will catch the omission.
      if (len(arguments[task][counter][argument]) == 0) or (argument == 'json parameters'): continue
  
      # Check if an input or an output file.
      isInput    = argumentInformation[tool][argument]['input']
      isOutput   = argumentInformation[tool][argument]['output']
  
      if isInput or isOutput:
  
        # Check the paths and the extension.
        files = []
        for filename in arguments[task][counter][argument]:
          intermediateFilename = setFile(pipelineArgumentInformation, pipelineArguments, arguments, filename, isInput, isOutput)
          finalFilename        = checkExtension(argumentInformation, shortForms, links, task, tool, argument, isOutput, intermediateFilename, verbose)
          files.append(finalFilename)
        arguments[task][counter][argument] = deepcopy(files)

# Provided the filename, check if input or output and set the file accordingly.
def setFile(pipelineArgumentInformation, pipelineArguments, arguments, filename, isInput, isOutput):

  # Check if the file already contains a path (e.g. already contains the
  # '/' character.
  filePath = ''
  if '/' not in filename:
    if isInput:  filePath = pipelineArguments['--input-path'] + '/' + filename
    elif isOutput: filePath = pipelineArguments['--output-path'] + '/' + filename

  # If the file path is given, ensure that the full path is given. For example,
  # if './file' is specified, modify the './' to the full path of the current
  # directory.  If the path specified is a parameter and as such begins with '$(',
  # do not modify the path.
  else:
    if not filename.startswith('$('):
      givenPath = filename.split('/')
      filename  = givenPath.pop()
      givenPath = '/'.join(givenPath)
      filePath  = os.path.abspath(givenPath) + '/' + filename
    else: filePath = filename

  return filePath

# Check the filename extension.  If the filename is not a stub and the
# name soesn't end with the expected extension, throw an error.
def checkExtension(argumentInformation, shortForms, links, task, tool, argument, isOutput, filename, verbose):
  er      = errors()
  correct = False

  # First check if the filename is a stub.
  isStub = argumentInformation[tool][argument]['stub'] if 'stub' in argumentInformation[tool][argument] else False

  # Only find the extension and check the files if the filename isn't a stub.
  if not isStub:

    # The extension could be a list of allowable extensions separated by pipes.
    # Split the extension on the pipes and check the files extension against
    # all the allowed extensions.
    extensions = argumentInformation[tool][argument]['extension'].split('|')

    # If the extension is listed as null, do not check the extension as it is
    # permitted to be anything.
    if (len(extensions) == 1) and (extensions[0] == 'no extension'): next
    else:
      for extension in extensions:
        extension = '.' + extension
        if filename.endswith(extension):
          correct = True
          break

      # If all the extensions have been checked and the files extension did not
      # match any of them, throw an error.
      if not correct and isOutput: filename += '.' + extensions[0]
      elif not correct:

        # Find the short form of the argument, as well as the pipeline version of the argument if one exists.
        shortForm    = shortForms[argument] if argument in shortForms else ''
        pipelineLink = ''
        if task in links:
          if argument in links[task]: pipelineLink = links[task][argument]
        er.fileExtensionError(verbose, task, argument, shortForm, pipelineLink, filename, argumentInformation[tool][argument]['extension'])
        er.terminate()

  return filename

# Loop over the tools and check that all required information has been set.
def checkParameters(gknoHelp, task, tool, argumentInformation, arguments, isPipeline, workflow, toolsOutputtingToStream, links, checkRequired, verbose):
  er = errors()

  for counter, iteration in enumerate(arguments[task]):
    for argument in iteration:
      if argument == 'json parameters': continue
  
      # Check if the argument has been given a value.
      isArgumentSet = False if len(arguments[task][counter][argument]) == 0 else True
  
      # If the argument is an input file (not from the stream) or an output file,
      # check that it does not contain the ':' character as this is a special
      # character in the Makefile.  If it does, replace the ':' with a '_'.
      isInput  = argumentInformation[tool][argument]['input']
      isOutput = argumentInformation[tool][argument]['output']
      if isInput or isOutput:
        modifiedList = []
        for value in arguments[task][counter][argument]:
          if ':' in value: modifiedList.append(value.replace(':', '_'))
          else: modifiedList.append(value)
        arguments[task][counter][argument] = deepcopy(modifiedList)
  
      # If the value is required and no value has been provided, terminate.
      if checkRequired and not isArgumentSet:
  
        # Check if the argument is an input file and if so, if the input is coming from
        # the stream.  If so, this does not need to be set.
        inputIsStream = False
        if isInput:
          previousTask = ''
          for currentTask in workflow:
            if currentTask == task: break
            else: previousTask = currentTask
          if previousTask in toolsOutputtingToStream: inputIsStream = True
  
        # Find the short form of the argument if one exists.
        shortForm = argumentInformation[tool][argument]['short form argument'] if 'short form argument' in argumentInformation[tool][argument] else ''
  
        # If the input to task is not a stream and the input is not set,
        # terminate with an error.
        if not inputIsStream:
          pipelineArgument  = ''
          pipelineShortForm = ''
          if task in links:
            if argument in links[task]:
              pipelineArgument  = links[task][argument][0]
              pipelineShortForm = links[task][argument][1]
          er.missingRequiredValue(verbose, task, argument, shortForm, isPipeline, pipelineArgument, pipelineShortForm)
          er.terminate()
  
        # If the input to this task is a stream, check if this particular argument has
        # instructions on how to handle the stream.  If it doesn't have any, then this
        # input still needs to be set.
        else:
          ignoreInput = True if 'input is stream' in argumentInformation[tool][argument] else False
          if not ignoreInput:
            pipelineArgument  = ''
            pipelineShortForm = ''
            if task in links:
              if argument in links[task]:
                pipelineArgument  = links[task][argument][0]
                pipelineShortForm = links[task][argument][1]
            er.missingRequiredValue(verbose, task, argument, shortForm, isPipeline, pipelineArgument, pipelineShortForm)
            er.terminate()

# Determine which files are required for each tool to run.  For each tool, these files
# are stored in a list and are used to define the dependencies in the Makefile.
def determineDependencies(argumentInformation, generatedFiles, workflow, taskToTool, toolsOutputtingToStream, arguments):
  er           = errors()
  previousTask = ''
  dependencies = {}
  outputs      = {}

  for task in workflow:
    tool               = taskToTool[task]
    dependencies[task] = []
    outputs[task]      = []

    for counter, iteration in enumerate(arguments[task]):
      dependencies[task].append([])
      outputs[task].append([])
      for argument in iteration:
        if argument == 'json parameters':
          value      = iteration[argument][0]
          dependencies[task][counter].append(value)
        else:
  
          # Check if the file is an input or an output file, or is listed as a dependent
          # file.  If it is an output, the file should be added to the string containing
          # all outputs from this tool.  If it is an input or dependent file, this will
          # be added to the string containing all files required for this tool to run.
          hasGeneratedFiles = True if 'generated files' in argumentInformation[tool][argument] else False
          isInput           = argumentInformation[tool][argument]['input']
          isOutput          = argumentInformation[tool][argument]['output']
          isDependent       = argumentInformation[tool][argument]['dependent']
          isFlag            = True if argumentInformation[tool][argument]['type'] == 'flag' else False
  
          # Determine if the input and output from this task are the stream.  If so, the
          # dependencies and outputs structures do not need to be updated to include these
          # arguments
          outputToStream = True if task in toolsOutputtingToStream else False
          inputIsStream  = True if (previousTask != '') and (previousTask in toolsOutputtingToStream) else False

          # If the files generated by this task are defined, use them to define the outputs.
          if hasGeneratedFiles:

            # If the argument specified a directory, include the directory name in the filename.
            isDirectory = True if 'directory' in argumentInformation[tool][argument] else False
            directory = arguments[task][counter][argument][0] + '/' if isDirectory else ''
            for filename in generatedFiles[tool]: outputs[task][counter].append(directory + filename)

          if isInput or isDependent or isOutput and not hasGeneratedFiles:
  
            # If the input/output file is defined, check that the extension is as expected.
            for value in arguments[task][counter][argument]:
  
              # If this file needs to be added to one of the string, check to see if it is a stub
              # or not.  If so, all of the files associated with the stub need to be added to the
              # string.
              isStub = argumentInformation[tool][argument]['stub'] if 'stub' in argumentInformation[tool][argument] else False
    
              # If this is a stub, create the string containing all of the files.
              if isStub:
    
                # Do not add the output to the self.outputs structure if the task is outputting
                # to the stream.  Only add these values if it has been defined (i.e. value is not
                # and empty string).
                if value != '':
                  for name in argumentInformation[tool][argument]['outputs']:
                    if isOutput:
                      if not outputToStream: outputs[task][counter].append(value + name)
                    elif isInput:
                      if not inputIsStream: dependencies[task][counter].append(value + name)
    
              # If the filename is not a stub, just include the value.
              else:
                if (value != '') and not isFlag:
                  if isOutput:
                    if not outputToStream: outputs[task][counter].append(value)
                  elif isInput:
                   if not inputIsStream: dependencies[task][counter].append(value)

    # Update the previous task and previous tool to be the task and tool just evaluated.
    previousTask = task
    previousTool = tool

  return dependencies, outputs

# Determine additional dependencies that are not associated with an input
# command line argument.
#
# All of the included output files have already been added to the outputs
# string for each tool if they appear on the command line.  There are some
# programs that generate output files, however, without specifying the output
# file.  In these instances, the additional output files for the tool are
# included at the beginning of the tools configuration files.  Parse these
# additional output files (if there are any) and add to the outputs string.
def determineAdditionalFiles(additionalFiles, workflow, taskToTool, pipelineDependencies, arguments, dependencies, outputs, verbose):
  er = errors()

  # Loop over each tool in turn and check for additional output files.
  for task in workflow:
    if task not in outputs: outputs[task] = []
    tool = taskToTool[task]
    if tool in additionalFiles:

      # There are different formats for building up output files.  Each of these can
      # be dealt with separately.
      #
      # 1. If the output file can be constructed from a value given to one of the
      # tools command line arguments.
      if 'from input arguments' in additionalFiles[tool]:
        for field in additionalFiles[tool]['from input arguments']:

          # Check that the command which should be used to determine the file name exists
          # and has a value defined.
          fileType = field['type']
          argument = field['link to this argument']

          # Loop over all the values for this argument (if there is an internal loop, there
          # could be multiple values for this).
          for counter, iteration in enumerate(arguments[task]):
            filename = arguments[task][counter][argument][0]

            # In constructing the output file name, the extension associated with the associated
            # file name can be stripped off and a new extension can be appended if requested.
            # Determine and enact the appropriate steps.
            if field['remove extension']: filename = filename.rpartition('.')[0]
            if field['add extension']:
              extension = field['output extension']
              filename += '.' + extension

            # Check if any of the other tasks in the pipeline demand this output as a dependency.
            for pipelineTask in pipelineDependencies:
              if task in pipelineDependencies[pipelineTask]:
                if len(dependencies[pipelineTask]) == 1: dependencies[pipelineTask][0].append(filename)
                else: dependencies[pipelineTask][counter].append(filename)

            # If the file is a dependency, add to the dependency string, otherwise add to the
            # output string.
            if fileType == 'dependency': dependencies[task][counter].append(filename)
            elif fileType == 'output': outputs[task][counter].append(filename)

      # If there are defined files that are created by a particular tool, add these to the
      # outputs.
      elif 'defined filenames':
        for filename in additionalFiles[tool]['defined filenames']:
          for counter, iteration in enumerate(arguments[task]):
            outputs[task][counter].append(filename)

# In the course of executing the pipeline, some of the intermediate files
# generated along the way should be deleted.  The pipeline configuration
# file segment 'delete files' identifies which files should be deleted and
# when in the pipeline they can be removed.
def determineFilesToDelete(arguments, deleteFiles, iTasks, numberOfIterations, verbose):
  er     = errors()
  output = {}

  # Check to see if the configuration file has the 'delete files' section.
  if len(deleteFiles) != 0:
    for task in deleteFiles:
      for information in deleteFiles[task]:
        argument        = information[0]
        deleteAfterTask = information[1]
        extension       = information[2]
        if deleteAfterTask not in output: output[deleteAfterTask] = []

        # Check if task and/or the deleteAfterTask appear in the tasks in the internal loop.
        # Depending on the result handle them appropriately.
        #
        # If both tasks appear in the internal loop, then loop over the sets of contained
        # parameters and add the files to delete to the output structure in a straight
        # mapping.
        if task in iTasks and deleteAfterTask in iTasks:
          for counter in range(0, numberOfIterations):
            if counter not in output[deleteAfterTask]: output[deleteAfterTask].append([])
            for value in arguments[task][counter][argument]: 
              if extension != '': value += extension
              output[deleteAfterTask][counter].append(value)

        # If task appears in the internal loop, but deleteAfterTask does not, there are (potentially)
        # multiple iterations of task and the defined outputs from each of these are to be deleted
        # after the single iteration of the task defined by deleteAfterTask.
        elif task in iTasks and deleteAfterTask not in iTasks:
          if len(output[deleteAfterTask]) == 0: output[deleteAfterTask].append([])
          for value in arguments[task][counter][argument]:
            if extension != '': value += extension
            output[deleteAfterTask][0].append(value)

        # If task is not in the internal loop, but deleteAfterTask is, terminate the script with an
        # error.  In this case, there can be multiple iterations of the task defined by deleteAfterTask
        # to be run.  After completion of this task, the defined output from task can be deleted, but
        # since these jobs will be running in parallel, gkno cannot guarantee that the file being
        # deleted has been used in all of the parallel tasks that may need it.  If the outputs from task
        # are to be deleted, they should be deleted after a task not appearing in the internal loop.
        elif task not in iTasks and deleteAfterTask in iTasks:
          er.deleteFileInLoop(verbose, task, deleteAfterTask)
          er.terminate()

        # Finally, if neither task or deleteAfterTask appear in iTasks, then both of them fall outside
        # of any internal loops and so have only one iteration of parameters.  This can be treated in
        # the same way as if they were both in iTasks.
        elif task not in iTasks and deleteAfterTask not in iTasks:
          if len(output[deleteAfterTask]) == 0: output[deleteAfterTask].append([])
          for value in arguments[task][0][argument]:
            if extension != '': value += extension
            output[deleteAfterTask][0].append(value)

  return output

# The list of files to be produced by the script is all of the files created
# by each individual task in the pipeline.  However, if some of the files
# are deleted along the way, the final list of files should not include these
# deleted files.
def determineFinalOutputs(deleteFiles, outputs):

  # Put all of the files to be deleted in a dictionary.
  deletedFiles = {}
  for task in deleteFiles:
    for internalLoopIteration in deleteFiles[task]:
      for output in internalLoopIteration:
        deletedFiles[output] = True

  finalOutputs = {}
  for task in outputs:
    if task not in finalOutputs: finalOutputs[task] = []
    for internalLoopIteration in outputs[task]:
      for output in internalLoopIteration:
        if output not in deletedFiles: finalOutputs[task].append(output)

  outputs = deepcopy(finalOutputs)

# Determine if any of the tools are being piped together and check if the
# tools involved can use the stream for input and output.
def determinePiping(arguments, argumentInformation, toolsDemandingInputStream, toolsDemandingOutputStream, workflow, taskToTool, toolsOutputtingToStream, verbose):
  er               = errors()
  addArguments     = {}
  addedInformation = {}
  hasPipes         = False
  streamedOutputs  = {}

  if len(toolsOutputtingToStream) != 0:
    hasPipes = True
    for taskCounter, task in enumerate(workflow):
      if task in toolsOutputtingToStream:
        streamedOutputs[task] = True
        tool                  = taskToTool[task]
        canOutputToStream     = False

        # If the tool only deals with the stream for inputs and outputs, skip the
        # following search.  There is no input or output commands as the tool is
        # expecting to be receiving and outputting to the stream.
        if tool in toolsDemandingOutputStream: canOutputToStream = True
        if not canOutputToStream:

          # Check if the tool allows the output to be sent to a stream.
          for argument in argumentInformation[tool]:
            isOutput = argumentInformation[tool][argument]['output']
            if isOutput:
              if 'if output to stream' in argumentInformation[tool][argument]:
                if canOutputToStream:
                  er.multipleOutputsToStream(True, "\t", task, tool)
                  er.terminate()
                canOutputToStream = True

                # If the entry in the configuration file is 'do not include', just
                # remove this argument from the toolArguments structure.
                if argumentInformation[tool][argument]['if output to stream'] == 'do not include':
                  for iterationCounter, value in enumerate(arguments[task]): del(arguments[task][iterationCounter][argument])

                # Otherwise, handle as appropriate.
                else:
                  print('NOT YET HANDLED THIS STREAM OPTION', task, argument, file = sys.stdout)
                  er.terminate()

        # Now check that the subsequent tool can accept the stream as an input.  If
        # this was the last task in the pipeline, fail as the output needs to pipe
        # somewhere.
        if (taskCounter + 1) == len(workflow):
          er.lastTaskOutputsToPipe(True, "\t", task)
          er.terminate()

        nextTask        = workflow[taskCounter + 1]
        nextTool        = taskToTool[nextTask]
        canAcceptStream = False

        # If the current tool outputs to the stream, we need to check that the following
        # tool is set up to handle the stream.  This information is contained in the
        # information for one of the input files in the next tool.  If the next tool
        # demands the stream, then there are no input or output command line arguments as
        # the stream is assumed and so this check is unnecessary.
        if nextTool in toolsDemandingInputStream: canAcceptStream = True

        for argument in argumentInformation[nextTool]:
          isInput = argumentInformation[nextTool][argument]['input']
          if isInput:
            if 'if input is stream' in argumentInformation[nextTool][argument]:
              if canAcceptStream:
                er.multipleInputsAcceptStream(True, "\t", task, tool)
                er.terminate()
              canAcceptStream = True

              # If the entry in the configuration file is 'do not include', just
              # remove this argument from the arguments structure.
              if argumentInformation[nextTool][argument]['if input is stream'] == 'do not include':
                for iterationCounter, value in enumerate(arguments[nextTask]): del(arguments[nextTask][iterationCounter][argument])

              # If the entry is 'replace', then the argument needs to be removed and
              # replaced with that provided.  When the Makefile is generated, the
              # tl.toolInfo structure is interogated.  This replacement value should
              # not be present in the structure, so a value needs to be input.
              elif argumentInformation[nextTool][argument]['if input is stream'] == 'replace':
                for iterationCounter, value in enumerate(arguments[nextTask]): del(arguments[nextTask][iterationCounter][argument])
                replacementArgument = argumentInformation[nextTool][argument]['replace argument with']['argument']
                replacementValue    = argumentInformation[nextTool][argument]['replace argument with']['value']
                for iterationCounter, value in enumerate(arguments[nextTask]):
                  if replacementArgument not in arguments[nextTask][iterationCounter]:
                    arguments[nextTask][iterationCounter][replacementArgument] = []
                    arguments[nextTask][iterationCounter][replacementArgument].append(replacementValue)
                    if replacementArgument in argumentInformation[nextTool]:
                      er.replacementArgumentAlreadyPresent(True, "\t", nextTask, tool, replacementArgument)
                      er.terminate()
                    else:
                      if nextTool not in addArguments: addArguments[nextTool] = {}
                      addArguments[nextTool] = replacementArgument

              # If the entry is neither 'do not include' or 'replace', just use this value
              # as the value for the argument.
              else:
                for iterationCounter, value in enumerate(arguments[nextTask]):
                  arguments[nextTask][iterationCounter][argument] = []
                  arguments[nextTask][iterationCounter][argument].append(argumentInformation[nextTool][argument]['if input is stream'])

        # If no instructions are provided on how to handle a streaming input, terminate.
        if not canOutputToStream:
          er.noOutputStreamInstructions(True, task, tool)
          er.terminate()

        if not canAcceptStream:
          er.noInputStreamInstructions(True, nextTask, nextTool)
          er.terminate()

    # Having determined all arguments that are modified, add the necessary arguments to the
    # tl.toolInfo structure (these weren't added before as the dictionary cannot be modified
    # while it was being used).  Keep track of added arguments as they need to be removed
    # once the makefile has been created, to reset the toolInfo structure back to its original
    # form before rerunning the pipeline if multiple runs are being performed.
    for task in addArguments:
      if task not in addedInformation: addedInformation[task] = []
      addedInformation[task].append(addArguments[task])

  return hasPipes, addedInformation

# Determine the order in which to write out the tasks.
def determineToolWriteOrder(workflow, toolsOutputtingToStream, hasPipes):
  taskBlock  = []
  taskBlocks = []
  for task in workflow:

    # Add the task to a task block.
    taskBlock.append(task)

    # If the task outputs to a file (i.e. it is not listed as outputting to a stream,
    # the block of piped tasks is complete, so add the task to the list of task
    # blocks and reset the block.
    if hasPipes:
      if task not in toolsOutputtingToStream:
        taskBlocks.append(taskBlock)
        taskBlock = []
    else:
      taskBlocks.append(taskBlock)
      taskBlock = []

  return taskBlocks

# Determine the outputs and dependencies for each block of tasks
# linked together by pipes.  If the block is a single task, then the outputs
# and dependencies are just those of the tool.  If the block is a set of
# linked tasks, we need only the outputs and dependent files that are not
# linked between the tools.
def getTaskBlockOutputsAndDependencies(taskBlocks, outputs, dependencies, iTasks, numberOfIterations):
  outputsList      = []
  dependenciesList = []

  for taskBlock in taskBlocks:
      
    # If the task block contains a single task, update the outputs and dependency lists
    # to include all listed files for this block.
    if len(taskBlock) == 1:
      outputsList.append(outputs[taskBlock[0]])
      dependenciesList.append(dependencies[taskBlock[0]])
    else:

      # Determine if the set of piped tasks are also in an internal loop and so, how
      # many parameter iterations there are.
      if taskBlock[0] not in iTasks: numberOfIterations = 1
      
      # Generate a list of all outputs and all dependencies, then check if any of the
      # outputs from any task in this block appear as dependencies for other tasks in
      # this block.  These should all be omitted as they are internal to the stream.
      tempOutputs      = []
      tempDependencies = []
      for task in taskBlock:
        for counter, internalLoopIteration in enumerate(outputs[task]):
          tempOutputs.append({})
          for output in internalLoopIteration: tempOutputs[counter][output] = True

        for counter, internalLoopIteration in enumerate(dependencies[task]):
          tempDependencies.append({})
          for dependent in internalLoopIteration: tempDependencies[counter][dependent] = True

      # Check if dependency is an output in the streamed tasks.
      for counter, internalLoopIteration in enumerate(tempDependencies):
        for dependent in internalLoopIteration:
          if dependent in tempOutputs[counter]:
            tempOutputs[counter][dependent]      = False
            tempDependencies[counter][dependent] = False

      tempList = []
      for counter in range(0, numberOfIterations):
        tempList.append([])
        for output in tempOutputs[counter]:
          if tempOutputs[counter][output]: tempList[counter].append(output)
      outputsList.append(tempList)

      tempList = []
      for counter in range(0, numberOfIterations):
        tempList.append([])
        for dependent in tempDependencies[counter]:
          if tempDependencies[counter][dependent]: tempList[counter].append(dependent)
      dependenciesList.append(tempList)

  return outputsList, dependenciesList

# Check that all of the executables required exist.
def checkExecutables(sourcePath, paths, executables, workflow, taskToTool, verbose):
  er                    = errors()
  executablesList       = []
  missingExecutableList = []
  for task in workflow:
    tool = taskToTool[task]
    if paths[tool] != 'no path':
      executable = sourcePath + '/tools/' + paths[tool] + '/' + executables[tool]
      if executable not in executablesList: executablesList.append(executable)

  # Having identified all of the unique programmes, check that they exist.
  for executable in executablesList:
    try:
      with open(executable): pass
    except IOError:
      missingExecutableList.append(executable)

  # If there are any executable files that don't exist, print them out and fail.
  if len(missingExecutableList) != 0:
    er.missingExecutables(verbose, missingExecutableList)
    er.terminate()

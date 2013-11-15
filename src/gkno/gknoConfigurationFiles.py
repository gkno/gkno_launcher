#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import dataChecking
from dataChecking import checkDataType

import gknoErrors
from gknoErrors import *

import helpClass
from helpClass import *

import json
import os
import sys

# Define a data structure for holding information about multiple runs/internal loops.
class loopData:
  def __init__(self):

    # Define a list of arguments. The order is important since the values in the loop file are
    # in the same order as the arguments.
    self.arguments = []

    # Define the number of data sets in the file.
    self.numberOfDataSets = 0

    # Define a dictionary that will hold the values.
    self.values = {}

class gknoConfigurationFiles:
  def __init__(self):
    self.jsonFiles                       = {}
    self.jsonFiles['tools']              = {}
    self.jsonFiles['tool instances']     = {}
    self.jsonFiles['pipelines']          = {}
    self.jsonFiles['pipeline instances'] = {}

    # Errors class.
    self.errors = gknoErrors()

    # Define a dictionary to hold information contained in the gkno configuration file.
    self.gknoConfigurationData = {}

    #TODO FILL IN TEXT
    self.delimiter = '_'

    # Define the data structure for loop data.
    self.loopData = loopData()

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_instances.json' seperately.  These files contain additional instance information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_instances.json'): self.jsonFiles['tool instances'][files] = False
      elif files.endswith('.json'): self.jsonFiles['tools'][files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_instances.json'): self.jsonFiles['pipeline instances'][files] = False
      elif files.endswith('.json'): self.jsonFiles['pipelines'][files] = True

  # Check if the pipeline/tool name is valid.
  def checkPipelineName(self, gknoHelp, isPipeline, name):

    # If this is a tool, check against the available tools.
    if (not isPipeline) and name:
      if name + '.json' not in self.jsonFiles['tools']:
        gknoHelp.printHelp   = True
        gknoHelp.toolHelp    = True
        gknoHelp.invalidTool = True

    # Now check for pipelines.
    else:
      if not name:
        gknoHelp.printHelp       = True
        gknoHelp.pipelineHelp    = True
      elif name + '.json' not in self.jsonFiles['pipelines']:
        gknoHelp.printHelp       = True
        gknoHelp.pipelineHelp    = True
        gknoHelp.invalidPipeline = True

  #TODO SORT THIS OUT
  # Validate the gkno configuration file.
  def validateConfigurationFile(self):
    pass

  # Add the nodes from the gkno configuration file to the graph.  These nodes will not be conected to any
  # other nodes.
  def addGknoSpecificNodes(self, graph, config):

    # Add a task node representing gkno.
    attributes = taskNodeAttributes()
    attributes.description = 'gkno task'
    attributes.tool        = 'gkno'
    attributes.nodeType    = 'gkno'
    graph.add_node('gkno', attributes = attributes)

    for nodeID in self.gknoConfigurationData['gkno options']:

      # Generate a node.
      graph.add_node(nodeID, attributes = optionNodeAttributes())
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'nodeType', 'general')
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'dataType', self.gknoConfigurationData['gkno options'][nodeID]['data type'])
      config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'description', self.gknoConfigurationData['gkno options'][nodeID]['description'])
      if 'value' in self.gknoConfigurationData['gkno options'][nodeID]:

        # Convert unicode values from the configuration file into strings.
        for counter, value in enumerate(self.gknoConfigurationData['gkno options'][nodeID]['value']):
          if type(value) != bool: self.gknoConfigurationData['gkno options'][nodeID]['value'][counter] = str(value)

        config.nodeMethods.addValuesToGraphNode(graph, nodeID, self.gknoConfigurationData['gkno options'][nodeID]['value'], write = 'replace')
        config.nodeMethods.setGraphNodeAttribute(graph, nodeID, 'hasValue', True)
    
      # Join the option node to the gkno task node.
      attributes = edgeAttributes()
      attributes.argument  = self.gknoConfigurationData['gkno options'][nodeID]['argument']
      attributes.shortForm = self.gknoConfigurationData['gkno options'][nodeID]['short form']
      graph.add_edge(nodeID, 'gkno', attributes = attributes)

  # Check if a command line argument is a gkno specific argument.
  def checkPipelineArgument(self, graph, config, argument):

    # Next, check if the argument is a gkno specific pipeline argument.
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':
        edgeArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'argument')
        shortForm    = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'shortForm')
        if edgeArgument == argument: return edgeArgument
        elif shortForm == argument: return edgeArgument

    return None

  # Clear the data structure holding the gkno specific data.
  def eraseConfigurationData(self):
    self.gknoConfigurationData = {}

  # Check if multiple runs or internal loops have been requested. If so, check that only one file
  # has been provided.
  def hasLoop(self, graph, config):
    multipleRuns = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-MULTIPLE-RUNS', 'values')
    internalLoop = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-LOOP', 'values')

    # Either multiple runs or internal loops are allowed, but not both.
    if multipleRuns and internalLoop:
      #TODO ERROR
      print('CANNOT DEFINE MULTIPLE RUN AND INTERNAL LOOP SIMULTANEOUSLY - hasMultipleRunsOrLoop')
      self.errors.terminate()

    # If no multiple runs or internal loops are requested, return.
    if not multipleRuns and not internalLoop: return False, False

    # If a file is provided, check the format.
    hasMultipleRuns = False
    hasInternalLoop = False
    if multipleRuns:
      files           = multipleRuns[1]
      hasMultipleRuns = True
    elif internalLoop:
      files = internalLoop[1]
      hasInternalLoop = True

    # There can only be a single file specified
    if len(files) != 1:
      # TODO ERROR
      print('ONLY A SINGLE FILE CAN BE SPECIFIED FOR MULTIPLE RUN/INTERNAL LOOP - hasMultipleRunsOrLoop')
      self.errors.terminate()

    # TODO IMPLEMENT
    # Validate the file and import the information into a data structure.
    data = config.fileOperations.readConfigurationFile(files[0])
    self.validateMultipleRunsFiles(data)
    self.processMultipleRunFileData(data)
    return hasMultipleRuns, hasInternalLoop

  # TODO
  # Validate the contents of a multiple run or internal loop file.
  def validateMultipleRunsFiles(self, data):
    pass

  # Parse the information from the multiple runs/internal loop file into data structures.
  def processMultipleRunFileData(self, data):
 
    # Store the arguments contained in the loop file in the correct order.
    for argument in data['arguments']: self.loopData.arguments.append(argument)

    # Loop over the sets of values and add to the data structure. Keep track of the number of
    # data sets.
    for iteration in data['values']:
      self.loopData.numberOfDataSets += 1
      self.loopData.values[iteration] = []
      for value in data['values'][iteration]: self.loopData.values[iteration].append(value)

  # Assign loop values to the graph.
  def addLoopValuesToGraph(self, graph, config):

    # TODO EXPLAIN
    for iteration in range(1, self.loopData.numberOfDataSets + 1):
      for argument, values in zip(self.loopData.arguments, self.loopData.values[str(iteration)]):

        # Find the node for this argument.
        nodeID = config.pipeline.argumentData[argument].nodeID

        # TODO Check if a node has been deleted as part of the merge process, that the pipeline
        # has the argumentData updated to reflect the change.
        if nodeID not in graph.nodes():
          print('ERROR - node not in graph - addLoopValuesToGraph')
          self.errors.terminate()

        if iteration == 1: config.nodeMethods.addValuesToGraphNode(graph, nodeID, values, write = 'replace')
        else: config.nodeMethods.addValuesToGraphNode(graph, nodeID, values, write = 'iteration', iteration = str(iteration))

  # Return the node for a gkno argument contained in the gkno configuration file.
  def getNodeForGknoArgument(self, graph, config, argument):
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].argument: return nodeID

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].shortForm: return nodeID

    return None

  # Construct all filenames.  Some output files from a single tool or a pipeline do not need to be
  # defined by the user.  If there is a required input or output file and it does not have its value set, 
  # determine how to construct the filename and populate the node with the value.
  def constructFilenames(self, pipelineGraph, config, workflow):
    for task in workflow:
                                 
      # Input files are predecessor nodes to the task.  Deal with the input files first.
      fileNodeIDs = config.nodeMethods.getPredecessorFileNodes(pipelineGraph, task)
      for fileNodeID in fileNodeIDs:
        argument     = config.edgeMethods.getEdgeAttribute(pipelineGraph, fileNodeID, task, 'argument')
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
                                 
        # Use the argument to get information about the argument.
        isRequired = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, optionNodeID, 'isRequired')
        isSet      = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, optionNodeID, 'hasValue')
                                 
        # If input files aren't set, gkno should terminate.  If the input is linked to the output of
        # another task, the nodes are merged and so the input is set.  Thus, an empty value cannot be
        # filled without command line (or instance) information.
        if isRequired and not isSet:
          print('MISSING INPUT FILE:', task, argument)
          self.errors.terminate()
                                 
      # Now deal with output files,  These are all successor nodes.
      fileNodeIDs = config.nodeMethods.getSuccessorFileNodes(pipelineGraph, task)
      for fileNodeID in fileNodeIDs:
        argument     = config.edgeMethods.getEdgeAttribute(pipelineGraph, task, fileNodeID, 'argument')
        optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
                                 
        isRequired = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, optionNodeID, 'isRequired')
        isSet      = config.nodeMethods.getGraphNodeAttribute(pipelineGraph, optionNodeID, 'hasValue')
        if isRequired and not isSet:
          method = self.constructionInstructions(pipelineGraph, config, task, argument, fileNodeID)
          if method == None:     
  
            # TODO ERROR MESSAGE
            print('\tMISSING OUTPUT:', fileNodeID, task, config.pipeline.tasks[task], argument)
            self.errors.terminate()
  
          # If the tool configuration file has instructions on how to construct the filename,
          # built it using these instructions.
          else: self.constructFilename(pipelineGraph, config, method, task, fileNodeID)

  # If a filename is not defined, check to see if there are instructions on how to 
  # construct the filename.
  def constructionInstructions(self, graph, config, task, argument, fileNodeID):
    instructions = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    if instructions == None: return None
    else: return instructions['ID']

  # Construct a filename from instructions.
  def constructFilename(self, graph, config, method, task, fileNodeID):
    if method == 'from tool argument':
      self.constructFilenameFromToolArgument(graph, config, task, fileNodeID)

    # TODO ERRORS
    else:
      print('UNKNOWN CONSTRUCTION METHOD: gknoConfig.constructFilename')
      self.errors.terminate()

  # Construct a filename using another tool argument.
  def constructFilenameFromToolArgument(self, graph, config, task, fileNodeID):
    optionNodeID   = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)

    # Check if the filename is a filename stub.
    isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isFilenameStub')
    if isFilenameStub: self.constructFilenameFromToolArgumentStub(graph, config, task, fileNodeID)
    else: self.constructFilenameFromToolArgumentNotStub(graph, config, task, fileNodeID)

  # Construct the filenames for filename stub arguments.
  def constructFilenameFromToolArgumentStub(self, graph, config, task, fileNodeID):
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'argument')
    instructions     = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    baseArgument     = instructions['use argument']
    replaceExtension = instructions['replace extension']

    # Get the ID of the node corresponding to the baseArgument.
    # TODO SORT OUT THE CASE WHERE THERE ARE MULTIPLE VALUES
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument)
    if len(baseNodeIDs) != 1:
      print('Not yet handled constructFilenameFromToolArgumentStub')
      self.errors.terminate()
    else: baseNodeID = baseNodeIDs[0]
    values = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')

    # Generate the filename for the option node.  Since this is a filename stub, this will not have any
    # extension.
    originalExtension = config.tools.getArgumentData(config.pipeline.tasks[task], baseArgument, 'extension')
    modifiedValues    = self.modifyExtensions(values, originalExtension, '')

    # If the construction instructions indicate that values from another argument should be included
    # in the filename, include them here.
    if 'add argument values' in instructions: modifiedValues = self.addArgumentValues(graph, config, instructions, task, modifiedValues, hasExtension = False)

    # If the instructions indicate that additional text should be added to the filename, add it.
    if 'add additional text' in instructions: modifiedValues = self.addAdditionalText(instructions, modifiedValues, hasExtension = False)

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)

    # Set all of the file nodes with their values.
    fileNodeIDs = config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID)
    extensions  = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'filename extensions')

    # If the number of file nodes is not equal to the number of extensions, there is a problem.
    if len(fileNodeIDs) != len(extensions):
      #TODO SORT ERROR
      print('Number of file nodes != number of extensions - gknoConfigurationFiles.constructFilenameFromToolArgumentStub')
      self.errors.terminate()

    for nodeID in fileNodeIDs:
      fileValues = {}
      extension  = extensions.pop(0)
      for iteration in modifiedValues:
        fileValues[iteration] = []
        for value in modifiedValues[iteration]: fileValues[iteration].append(value + extension)
      config.nodeMethods.replaceGraphNodeValues(graph, nodeID, fileValues)

  # Add additional argument values to the filename.
  def addArgumentValues(self, graph, config, instructions, task, modifiedValues, hasExtension):
    numberOfValues = len(modifiedValues)

    # The modifiedValues structure is a dictionary.  This contains values for each iteration of the
    # pipeline to be executed.  It must be the case that the modifiedValues dictionary has the same
    # number of iterations as the values structure associated with the node for the argument from
    # which the filenames are to be constructed, or one of the structured must have only one iteration.
    additionalArguments = []
    for taskArgument in instructions['add argument values']:

      # Find the option node that provides information for this argument.
      # TODO HANDLE THE CASE OF MULTIPLE VALUES
      argumentNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, taskArgument)
      if len(argumentNodeIDs) != 1:
        print('not yet handled - constructFilenameFromToolArgumentStub mark2')
        self.errors.terminate()
      else: argumentNodeID = argumentNodeIDs[0]

      argumentNodeValues = config.nodeMethods.getGraphNodeAttribute(graph, argumentNodeID, 'values')
      numberOfNodeValues = len(argumentNodeValues)

      # If both data structures have the same number of values, or one list is larger than the other,
      # update the modifiedValues dictionary accordingly.
      if numberOfValues == numberOfNodeValues: self.setModifiedValuesA(modifiedValues, argumentNodeValues)
      elif numberOfValues == 1 and numberOfNodeValues > 1: self.setModifiedValuesB(modifiedValues, argumentNodeValues)
      elif numberOfValues > 1 and numberOfNodeValues == 1: self.setModifiedValuesC(modifiedValues, argumentNodeValues)
      else:
        print('NOT HANDLED VALUES - constructFilenameFromToolArgumentStub')
        print(taskArgument, modifiedValues)
        self.errors.terminate()

    return modifiedValues

  # Update the modifiedValues dictionary.
  def setModifiedValuesA(self, modifiedValues, argumentNodeValues):
    for iteration in modifiedValues:

      # Check that there is only a single value in the list for this iteration in 'argumentNodeValues'.
      if len(argumentNodeValues[iteration]) != 1:
        print('CANNOT CONSTRUCT FILENAMES IF THERE IS MORE THAN ONE PARAMETER VALUE.')
        print('constructFilenameFromToolArgumentStub')
        self.errors.terminate()

      else:
        modifiedList = []
        for value in modifiedValues[iteration]: modifiedList.append(value + self.delimiter + argumentNodeValues[iteration][0])
        modifiedValues[iteration] = modifiedList

  def setModifiedValuesB(self, modifiedValues, argumentNodeValues):
    numberOfValues     = len(modifiedValues)
    numberOfNodeValues = len(argumentNodeValues)
    values             = modifiedValues[1]

    for iteration in range(1, numberOfNodeValues + 1):
      modifiedList = []
      for value in values: modifiedList.append(value + self.delimiter + argumentNodeValues[iteration][0])
      modifiedValues[iteration] = modifiedList

  def setModifiedValuesC(self, modifiedValues, argumentNodeValues):
    numberOfValues     = len(modifiedValues)
    numberOfNodeValues = len(argumentNodeValues)
    values             = modifiedValues

    for iteration in range(1, numberOfValues + 1):
      modifiedList = []
      for value in values[iteration]: modifiedList.append(value + self.delimiter + argumentNodeValues[1][0])
      modifiedValues[iteration] = modifiedList

  # Add additional text to the constructed filename.
  def addAdditionalText(self, instructions, values, hasExtension = False, extension = ''):
    text = instructions['add additional text']
    for iteration in values:
      modifiedValues = []
      for value in values[iteration]:

        # If the value has an extension, remove it, then replace it.
        if hasExtension:

          # The supplied extension can be a list of extensions separated by a '|'. Check
          # if the file finishes with any of these extensions. Store the specific extension.
          if '|' in extension:
            extensions = extension.split('|')
            fileHasExtension = False
            for specificExtension in extensions:
              if value.endswith('.' + specificExtension):
                fileHasExtension = True
                break
            extension = specificExtension

            if not fileHasExtension:
              #TODO ERROR
              print('Unexpected extension - addAdditionalText')
              self.errors.terminate()

          newValue = str(value.split('.' + extension)[0] + '.' + str(text) + '.' + extension)
          modifiedValues.append(newValue)

        else: modifiedValues.append(value + str(text))
      values[iteration] = modifiedValues

    return values

  # Construct the filenames for non-filename stub arguments.
  def constructFilenameFromToolArgumentNotStub(self, graph, config, task, fileNodeID):
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'argument')
    instructions     = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'construct filename')
    baseArgument     = instructions['use argument']
    replaceExtension = instructions['replace extension']

    # Get the ID of the node corresponding to the baseArgument. If there are multiple nodes
    # available, pick one that has a predecessor node itself. TODO SORT THIS OUT
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument)
    if len(baseNodeIDs) == 1: baseNodeID = baseNodeIDs[0]
    elif len(baseNodeIDs) == 0:
      #TODO Sort error
      print('No basenode - constructFilenameFromToolArgumentNotStub')
      self.errors.terminate()
    else: baseNodeID = config.nodeMethods.getNodeIDWithPredecessor(graph, baseNodeIDs, task)

    # Find all predecessor file nodes and then identify the file associated with the baseNodeID.
    # Get the values from this file node.  Some of the values associated with option nodes are
    # for filename stubs, but those attached to file nodes will always be a full file name as
    # required here.
    predecessorFileNodeIDs = config.nodeMethods.getPredecessorFileNodes(graph, task)
    fileNodeExists         = False
    for nodeID in predecessorFileNodeIDs:
      if nodeID.startswith(baseNodeID + '_'):
        values         = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        fileNodeExists = True
        break

    # If no file node was found, terminate.
    if not fileNodeExists:
      #TODO ERROR
      print('constructFilenameFromToolArgumentNotStub')
      self.errors.terminate()

    # Determine if the baseArgument is greedy. If so, the values associated with each iteration
    # will be used as input for a single iteration of this task. In this case, even if the values
    # have multiple iterations, this argument should only have one iteration of values.
    isBaseGreedy = config.edgeMethods.getEdgeAttribute(graph, baseNodeID, task, 'isGreedy')
    if isBaseGreedy:
      for i in range(2, len(values) + 1): del values[i]

    # Check if the argument being created allowed to have multiple values. If not, check each iteration
    # and ensure that the modifiedValues dictionary only has one entry per iteration.
    if not config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowMultipleValues'):
      modifiedValues = {}
      for iteration in values: modifiedValues[iteration] = [values[iteration][0]]
    else: modifiedValues = values

    # If the extension is to be replaced, do that here.
    originalExtension = config.tools.getArgumentData(config.pipeline.tasks[task], baseArgument, 'extension')
    if replaceExtension:
      newExtension      = config.tools.getArgumentData(config.pipeline.tasks[task], argument, 'extension')
      modifiedValues    = self.modifyExtensions(modifiedValues, originalExtension, newExtension)

    # If the construction instructions indicate that values from another argument should be included
    # in the filename, include them here.
    #modifiedValues = deepcopy(values)
    if 'add argument values' in instructions:
      modifiedValues = self.addArgumentValues(graph, config, instructions, task, modifiedValues, hasExtension = True, extension = originalExtension)

    # If the instructions indicate that additional text should be added to the filename, add it.
    if 'add additional text' in instructions:
      modifiedValues = self.addAdditionalText(instructions, modifiedValues, hasExtension = True, extension = originalExtension)

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

  # Modify the extensions for files.
  def modifyExtensions(self, values, extA, extB):
    modifiedValues = {}

    # The extensions may be a list of allowed extension separated by '|'.  Break the extensions
    # into lists of allowed extensions.
    extAList = extA.split('|')

    # The replacement extension may also be a list of allowed values.  Choose the first value in
    # this list as the extension to use.
    if extB == '': replaceExtension = ''
    else: replaceExtension = '.' + str(extB.split('|')[0])

    # Loop over all values and change the extension.
    for valueID in values:
      newValuesList = []
      for value in values[valueID]:
        for extension in extAList:
          if value.endswith(extension):
            string  = '.' + str(extension)
            newValuesList.append(value.replace(string, replaceExtension))
            break

      # Update the modifiedValues dictionary to reflect the modified extensions.
      modifiedValues[valueID] = newValuesList

    return modifiedValues

  # Set file paths for all of the files.
  def setFilePaths(self, graph, config):

    # Get the path of the input and the output directories.
    inputPath  = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-INPUT-PATH', 'values')
    outputPath = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-OUTPUT-PATH', 'values')

    # Make sure the path is well formed.
    if not inputPath: inputPath = '$(PWD)'
    else: inputPath = inputPath[1][0]
    if not inputPath.endswith('/'): inputPath += '/'

    if not outputPath: outputPath = '$(PWD)'
    else: outputPath = outputPath[1][0]
    if not outputPath.endswith('/'): outputPath += '/'

    # Parse all of the option nodes.
    for optionNodeID in config.nodeMethods.getNodes(graph, 'option'):
      if config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFile'):

        # Loop over each iteration of lists of files.
        values = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
        for iteration in values:
          modifiedValues = []
          for filename in values[iteration]:

            # If the filename already has a '/' in it, assume that the path is already defined.
            # In this case, leave the path as defined.
            if '/' not in filename:

              # Determine if the file is an input or output file. Since the node could be feeding
              # into or from multiple tasks, a file is an input, if and only if, the file nodes
              # associated with the option node have no predecessors.
              fileNodeIDs = config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID)
              isInput     = True
              for fileNodeID in fileNodeIDs:
                if graph.predecessors(fileNodeID): isInput = False
              if isInput: filename = inputPath + filename
              else: filename = outputPath + filename

              modifiedValues.append(filename)

            else: modifiedValues.append(filename)

          # Reset the stored values.
          values[iteration] = modifiedValues

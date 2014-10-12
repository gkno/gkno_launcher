#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import configurationClass.configurationClass
from configurationClass.configurationClass import *

import constructFilenames
from constructFilenames import *

import gknoErrors
from gknoErrors import *

import loops
from loops import *

import helpClass
from helpClass import *

import json
import os
import sys

class gknoConfigurationFiles:
  def __init__(self):
    self.jsonFiles                            = {}
    self.jsonFiles['tools']                   = {}
    self.jsonFiles['tool parameter sets']     = {}
    self.jsonFiles['pipelines']               = {}
    self.jsonFiles['pipeline parameter sets'] = {}

    # Errors class.
    self.errors = gknoErrors()

    # Define a dictionary to hold information contained in the gkno configuration file.
    self.gknoConfigurationData = {}

    # Define the data structure for loop data.
    self.loopData = loops()

    # Define methods for constructing filenames.
    self.construct = constructFilenames()

    # Define dictionaries to hold argument information.
    self.validLongFormArguments  = {}
    self.validShortFormArguments = {}

    # Define a structure to hold missing files and one for files that need to be
    # removed prior to execution.
    self.filesToRemove = []

    # Keep track of missing files.
    self.hasMissingFiles = False

  # Search a directory for json files and return a reference
  # to a list.
  def getJsonFiles(self, path):

    # Find configuration files for individual tools.
    for files in os.listdir(path + "tools"):

      # Store files ending with '_parameterSets.json' seperately.  These files contain additional parameter set information, are modifiable
      # by the user (modifying the configuration files is discouraged) and do not contain information on a tool, so would
      # fail the checks performed on the tool configuration files.
      if files.endswith('_parameterSets.json'): self.jsonFiles['tool parmeter sets'][files] = False
      elif files.endswith('.json'): self.jsonFiles['tools'][files] = True

    # Find configuration files for pipelines.
    for files in os.listdir(path + "pipes"):
      if files.endswith('_parameterSets.json'): self.jsonFiles['pipeline parameter sets'][files] = False
      elif files.endswith('.json'): self.jsonFiles['pipelines'][files] = True

  # Check if the pipeline/tool name is valid.
  def checkPipelineName(self, gknoHelp, isPipeline, name, mode):

    # If this is a tool, check against the available tools.
    if mode == 'tool':
      if name + '.json' not in self.jsonFiles['tools']:
        gknoHelp.writeHelp   = True
        gknoHelp.toolHelp    = True
        gknoHelp.invalidTool = True

    # Now check for pipelines.
    elif mode == 'pipeline':
      if name + '.json' not in self.jsonFiles['pipelines']:
        gknoHelp.writeHelp       = True
        gknoHelp.pipelineHelp    = True
        gknoHelp.invalidPipeline = True

  #TODO SORT THIS OUT
  # Validate the gkno configuration file.
  def validateConfigurationFile(self):
    pass

  # Add the nodes from the gkno configuration file to the graph.  These nodes will not be conected to any
  # other nodes.
  def addGknoSpecificNodes(self, graph, config, isPipeline):

    # Add a task node representing gkno.
    attributes             = taskNodeAttributes()
    attributes.description = 'gkno task'
    attributes.tool        = 'pipeline' if isPipeline else 'tool'
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
      attributes.longFormArgument  = self.gknoConfigurationData['gkno options'][nodeID]['argument']
      attributes.shortFormArgument = self.gknoConfigurationData['gkno options'][nodeID]['short form']
      graph.add_edge(nodeID, 'gkno', attributes = attributes)

      # Add the arguments to the list of valid gkno specific arguments.
      self.validLongFormArguments[attributes.longFormArgument]   = attributes.shortFormArgument
      self.validShortFormArguments[attributes.shortFormArgument] = attributes.longFormArgument

  # Check that there are no conflicts between gkno arguments and any of the tool arguments.
  def checkToolArguments(self, config, graph):
    for task in config.pipeline.workflow:
      tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      for longFormArgument in config.tools.argumentAttributes[tool].keys():
        shortFormArgument = config.tools.getArgumentAttribute(tool, longFormArgument, 'shortFormArgument')
        isPipeline        = config.isPipeline
        if longFormArgument in self.validLongFormArguments:
          gknoArgument = longFormArgument + ' (' + self.validLongFormArguments[longFormArgument] + ')'
          self.errors.gknoToolError(config, graph, task, tool, longFormArgument, shortFormArgument, gknoArgument, isLongFormConflict = True)
        if shortFormArgument in self.validShortFormArguments:
          gknoArgument = self.validShortFormArguments[shortFormArgument] + ' (' + shortFormArgument + ')'
          self.errors.gknoToolError(config, graph, task, tool, longFormArgument, shortFormArgument, gknoArgument, isLongFormConflict = False)

  # Attach the gkno specific parameter set arguments to the relevant nodes.
  def attachParameterSetArgumentsToNodes(self, config, graph, runName, parameterSet):
    for counter in range(len(config.parameterSets.parameterSetAttributes[runName][parameterSet].nodes) - 1, -1, -1):
      argument = config.parameterSets.parameterSetAttributes[runName][parameterSet].nodes[counter].argument
      values   = config.parameterSets.parameterSetAttributes[runName][parameterSet].nodes[counter].values

      # If the argument is a gkno specific argument, check if it is in the short form. If so, convert it to the
      # long form.
      if argument in self.validShortFormArguments: argument = self.validShortFormArguments[argument]

      # Check to see if the argument is a gkno specific argument.
      if argument in self.validLongFormArguments:

        # Get the nodeID, for this argument.
        for nodeID in config.nodeMethods.getNodes(graph, 'general'):
          nodeArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, graph.successors(nodeID)[0], 'longFormArgument')
          if argument == nodeArgument: break

        # Update the values in the node.
        config.nodeMethods.addValuesToGraphNode(graph, nodeID, values, write = 'replace')

        # Remove the information from the parameter set data.
        config.parameterSets.parameterSetAttributes[runName][parameterSet].nodes.pop(counter)

  # Check if a command line argument is a gkno specific argument.
  def checkPipelineArgument(self, graph, config, argument):

    # Next, check if the argument is a gkno specific pipeline argument.
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':
        edgeArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'longFormArgument')
        shortForm    = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'shortFormArgument')
        if edgeArgument == argument: return edgeArgument
        elif shortForm == argument: return edgeArgument

    return None

  # Clear the data structure holding the gkno specific data.
  def eraseConfigurationData(self):
    self.gknoConfigurationData = {}

  # Return the node for a gkno argument contained in the gkno configuration file.
  def getNodeForGknoArgument(self, graph, config, argument):
    for nodeID in graph.nodes(data = False):
      if config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'nodeType') == 'general':

        # Check if the supplied argument is the same as the argument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].longFormArgument: return nodeID

        # Check if the supplied argument is the same as the short formargument given for this node.
        if argument == graph[nodeID]['gkno']['attributes'].shortFormArgument: return nodeID

    return None

  # Construct all filenames.  Some output files from a single tool or a pipeline do not need to be
  # defined by the user.  If there is a required input or output file and it does not have its value set, 
  # determine how to construct the filename and populate the node with the value.
  def constructFilenames(self, graph, config, isPipeline):
    for task in config.pipeline.workflow:
      numberOfIterations = 0
      tool               = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')

      # Input files are predecessor nodes to the task.  Deal with the input files first.
      for fileNodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
        longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'longFormArgument')
        shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'shortFormArgument')
        optionNodeID      = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
                                 
        # Use the argument to get information about the argument.
        isRequired = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
        isSet      = True if config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values') else False

        # If input files aren't set, gkno should terminate.  If the input is linked to the output of
        # another task, the nodes are merged and so the input is set.  Thus, an empty value cannot be
        # filled without command line (or parameter set) information.
        if isRequired and not isSet:
          method = self.constructionInstructions(graph, config, task, longFormArgument, fileNodeID)

          # Build the input filename using the described method.
          if method != None: self.constructFilename(graph, config, method, task, fileNodeID, isInput = True)

        # Keep track of the maximum number of iterations for any of the input files.
        iterations         = len(config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values'))
        numberOfIterations = iterations if iterations > numberOfIterations else numberOfIterations
        config.nodeMethods.setGraphNodeAttribute(graph, task, 'numberOfDataSets', numberOfIterations)

        # If the input file has been set, check that it has the correct extension. This file may be used
        # for constructing an output filename, so errors in the extension should be caught here.
        values = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')
        if values:
          for iteration in values:
            for counter, value in enumerate(values[iteration]):
              if not config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFilenameStub'):
      
                # Loop over the file names contained in the file nodes.
                for fileValue in config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')[iteration]:
                  if not self.checkFileExtension(graph, config, optionNodeID, fileValue):
                    extensions = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowedExtensions')
      
                    # Check if the extension is listed as 'no extension'. If so, any extension is allowed, so do not fail.
                    if extensions[0] != 'no extension':
            
                      # If gkno is being run in tool mode, get the arguments.
                      if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'tool':
                        self.errors.invalidExtension(fileValue, extensions, longFormArgument, shortFormArgument, task, '', '')
              
                      # If gkno is being run in pipeline, mode, determine if the argument with the
                      # incorrect extension is a pipeline argument.
                      else:
                        longForm, shortForm = config.pipeline.getPipelineArgument(task, longFormArgument)
                        self.errors.invalidExtension(fileValue, extensions, longForm, shortForm, task, longFormArgument, shortFormArgument)

      # Now deal with output files,  These are all successor nodes.
      for fileNodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, task, fileNodeID, 'longFormArgument')
        shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, task, fileNodeID, 'shortFormArgument')
        optionNodeID      = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
        isRequired        = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
        isSet             = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'hasValue')
        if isRequired and not isSet:
          method = self.constructionInstructions(graph, config, task, longFormArgument, fileNodeID)

          # If an output file does not exist and has no instructions on how to be generated, terminate.
          if method == None:
            if isPipeline:
              tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
              pipelineArgument = config.pipeline.getPipelineArgument(task, longFormArgument)
              self.errors.noOutputFilename(task, tool, longFormArgument, shortFormArgument, pipelineArgument)

            else: self.errors.noToolOutputFilename(task, longFormArgument, shortFormArgument)
  
          # If the tool configuration file has instructions on how to construct the filename,
          # built it using these instructions.
          else: self.constructFilename(graph, config, method, task, fileNodeID, isInput = False)

        # Check that there are as many interations in the generated values as there are in the inputs. If the
        # values were defined on the command line, it is possible that this is not the case.
        if numberOfIterations != 0 and len(config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')) != 0:
          if len(config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')) != numberOfIterations:
            self.modifyNumberOfOutputIterations(graph, config, fileNodeID, numberOfIterations, task, longFormArgument, shortFormArgument)

  # If a filename is not defined, check to see if there are instructions on how to 
  # construct the filename.
  def constructionInstructions(self, graph, config, task, argument, fileNodeID):
    return config.tools.getConstructionMethod(config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool'), argument)

  # Construct a filename from instructions.
  def constructFilename(self, graph, config, method, task, fileNodeID, isInput):
    if method == 'from tool argument': self.constructFilenameFromToolArgument(graph, config, task, fileNodeID, isInput)

    # If a known file is being constructed, set the name here.
    elif method == 'define name': self.constructKnownFilename(graph, config, task, fileNodeID)

    # TODO ERRORS
    else:
      print('UNKNOWN CONSTRUCTION METHOD: gknoConfig.constructFilename')
      self.errors.terminate()

  # Construct a filename using another tool argument.
  def constructFilenameFromToolArgument(self, graph, config, task, fileNodeID, isInput):
    optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)

    # Check if the filename is a filename stub.
    isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isFilenameStub')
    if isFilenameStub: self.constructFilenameFromToolArgumentStub(graph, config, task, fileNodeID, isInput)
    else: self.constructFilenameFromToolArgumentNotStub(graph, config, task, fileNodeID, isInput)

  # Construct the filenames for filename stub arguments.
  def constructFilenameFromToolArgumentStub(self, graph, config, task, fileNodeID, isInput):
    tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    longFormArgument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
    instructions     = config.tools.getArgumentAttribute(tool, longFormArgument, 'constructionInstructions')
    baseArgument     = instructions['use argument']

    # Get the ID of the node corresponding to the baseArgument.
    # TODO SORT OUT THE CASE WHERE THERE ARE MULTIPLE VALUES
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument, 'option')
    if len(baseNodeIDs) != 1:
      print('Not yet handled constructFilenameFromToolArgumentStub')
      self.errors.terminate()
    else: baseNodeID = baseNodeIDs[0]
    values = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')

    # Generate the filename for the option node.  Since this is a filename stub, this will not have any
    # extension.
    originalExtensions        = config.tools.getArgumentAttribute(tool, baseArgument, 'extensions')
    modifiedValues, extension, success = self.modifyExtensions(values, originalExtensions, '', replace = True)
    for iteration in modifiedValues: modifiedValues[iteration] = [value.split('/')[-1] for value in modifiedValues[iteration]]

    # If the construction instructions indicate that values from another argument should be included
    # in the filename, include them here.
    if 'modify text' in instructions:
      for instructionDict in instructions['modify text']:
        instruction = instructionDict.iterkeys().next()
        valueList   = instructionDict[instruction]

        # If values attributed to other tool arguments are to be included in the filename, or text is to
        # added or removed.
        if instruction == 'add text': modifiedValues = self.addAdditionalText(valueList, modifiedValues, isBefore = False)
        if instruction == 'add argument values': modifiedValues = self.addArgumentValues(graph, config, valueList, task, modifiedValues)
        if instruction == 'remove text': modifiedValues = self.removeAdditionalText(config, task, tool, longFormArgument, valueList, modifiedValues)

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)

    # Mark this node as having had its values constructed, rather than set by the user.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isConstructed', True)

    # Set all of the file nodes with their values.
    fileNodeIDs = config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID)
    extensions  = config.tools.getArgumentAttribute(tool, longFormArgument, 'filenameExtensions')

    # If the number of file nodes is not equal to the number of extensions, there is a problem.
    if len(fileNodeIDs) != len(extensions):
      #TODO SORT ERROR
      print('Number of file nodes != number of extensions - gknoConfigurationFiles.constructFilenameFromToolArgumentStub')
      self.errors.terminate()

    # Loop over all of the file nodes and set the values.
    for fileNodeID in fileNodeIDs:
      fileValues = {}
      extension  = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'allowedExtensions')[0]
      for iteration in modifiedValues:
        fileValues[iteration] = []
        for value in modifiedValues[iteration]: fileValues[iteration].append(value + extension)
      config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, fileValues)

  # Add additional argument values to the filename.
  def addArgumentValues(self, graph, config, arguments, task, modifiedValues):
    numberOfValues = len(modifiedValues)
    if numberOfValues == 0: return modifiedValues

    # The modifiedValues structure is a dictionary.  This contains values for each iteration of the
    # pipeline to be executed.  It must be the case that the modifiedValues dictionary has the same
    # number of iterations as the values structure associated with the node for the argument from
    # which the filenames are to be constructed, or one of the structured must have only one iteration.
    additionalArguments = []
    for taskArgument in arguments:

      # Find the option node that provides information for this argument.
      argumentNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, taskArgument, 'option')

      # If there is no node defined, the argument required to construct the filename has not been
      # defined. As such, it is impossible to construct the filename, so terminate gkno with an error
      # message.
      #TODO FORCE A VALUE TO BE REQUIRED
      if len(argumentNodeIDs) == 0:
        return modifiedValues
        #if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'pipeline':
        #  self.errors.missingArgumentInFilenameConstructionNotPipelineArgument(graph, config, task, taskArgument)
        #self.errors.missingArgumentInFilenameConstruction(graph, config, task, taskArgument, '', config.isPipeline)

      # TODO HANDLE THE CASE OF MULTIPLE VALUES
      elif len(argumentNodeIDs) != 1:
        print(taskArgument, numberOfValues, len(argumentNodeIDs))
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

      # If the values aren't set, nothing is added.
      #TODO Determine if this is desired behaviour. Force user to supply a value or include in configuration
      # file that this doesn't need to be set?
      elif numberOfNodeValues == 0:
        pass
        # If gkno is being run in pipeline mode, check if this argument is a pipeline argument.
        #if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'pipeline':
        #  longFormArgument, shortFormArgument = config.pipeline.getPipelineArgument(task, taskArgument)
        #  if longFormArgument != None:
        #    self.errors.missingArgumentInFilenameConstruction(graph, config, task, longFormArgument, shortFormArgument, True)

          # Running in pipeline mode, but the argument required for filename construction is not a
          # pipeline argument. Fail, but recommend that the pipeline configurtaion file be modified
          # to include this argument.
        #  else: self.errors.missingArgumentInFilenameConstructionNotPipelineArgument(graph, config, task, taskArgument)

        # If gkno is being run in tool mode, write the correct error message.
        #self.errors.missingArgumentInFilenameConstruction(graph, config, task, taskArgument, '', False)
      else:
        print('NOT HANDLED VALUES - gknoConfig.addArgumentValues')
        print(task, taskArgument, modifiedValues)
        self.errors.terminate()

    return modifiedValues

  # Update the modifiedValues dictionary.
  def setModifiedValuesA(self, modifiedValues, argumentNodeValues):
    for iteration in modifiedValues:

      # Check that there is only a single value in the list for this iteration in 'argumentNodeValues'.
      if len(argumentNodeValues[iteration]) != 1:
        print('CANNOT CONSTRUCT FILENAMES IF THERE IS MORE THAN ONE PARAMETER VALUE.')
        print('gknoConfig.constructFilenameFromToolArgumentStub')
        self.errors.terminate()

      else:
        modifiedList = []
        for value in modifiedValues[iteration]: modifiedList.append(value + str(argumentNodeValues[iteration][0]))
        modifiedValues[iteration] = modifiedList

  def setModifiedValuesB(self, modifiedValues, argumentNodeValues):
    numberOfValues     = len(modifiedValues)
    numberOfNodeValues = len(argumentNodeValues)
    values             = modifiedValues[1]

    for iteration in range(1, numberOfNodeValues + 1):
      modifiedList = []
      for value in values: modifiedList.append(value + argumentNodeValues[iteration][0])
      modifiedValues[iteration] = modifiedList

  def setModifiedValuesC(self, modifiedValues, argumentNodeValues):
    numberOfValues     = len(modifiedValues)
    numberOfNodeValues = len(argumentNodeValues)
    values             = modifiedValues

    for iteration in range(1, numberOfValues + 1):
      modifiedList = []
      for value in values[iteration]: modifiedList.append(value + argumentNodeValues[1][0])
      modifiedValues[iteration] = modifiedList

  # Add additional text to the constructed filename.
  def addAdditionalText(self, textList, values, hasExtension = False, extensions = [''], isBefore = False):

    # If multiple pieces of text are included, concatenate them.
    text = ''
    for value in textList: text += value

    for iteration in values:
      modifiedValues = []
      for value in values[iteration]:

        # If the value has an extension, remove it, then replace it.
        if hasExtension:
          fileHasExtension = False
          for specificExtension in extensions:
            if value.endswith(specificExtension):
              fileHasExtension = True
              break
          extension = specificExtension

          if not fileHasExtension:
            #TODO ERROR
            print('Unexpected extension - addAdditionalText')
            self.errors.terminate()

          if isBefore: newValue = str(text) + str(value.split(extension)[0] + '.' + extension)
          else: newValue = str(value.split(extension)[0] + '.' + str(text) + extension)
          modifiedValues.append(newValue)

        else:
          if isBefore: modifiedValues.append(str(text) + value)
          else: modifiedValues.append(value + str(text))
      values[iteration] = modifiedValues

    return values

  # Remove text from the filename.
  def removeAdditionalText(self, config, task, tool, argument, textList, values, hasExtension = False, extensions = ['']):

    # If multiple pieces of text are included, concatenate them.
    text = ''
    for value in textList: text += value

    # Loop over all the iterations of data sets.
    for iteration in values:
      modifiedValues = []
      for value in values[iteration]:

        # If the value has an extension, remove it, then replace it.
        if hasExtension:
          fileHasExtension = False
          for specificExtension in extensions:
            if value.endswith(specificExtension):
              fileHasExtension = True
              break
          extension = specificExtension

          if not fileHasExtension:
            #TODO ERROR
            print('Unexpected extension - removeAdditionalText')
            self.errors.terminate()

          newValue = str(value.split(extension)[0])

        else:
          newValue  = value
          extension = None

        # Remove the requested text.
        if not newValue.endswith(text): self.errors.failedToRemoveText(task, tool, argument, newValue, text, config.isPipeline)
        newValue = newValue.split(text)[0]
        if extension: modifiedValues.append(str(newValue) + '.' + str(extension))
        else: modifiedValues.append(newValue)
      values[iteration] = modifiedValues

    return values

  # Construct the filenames for non-filename stub arguments.
  def constructFilenameFromToolArgumentNotStub(self, graph, config, task, fileNodeID, isInput):
    tool              = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    optionNodeID      = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
    shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'shortFormArgument')
    isInput           = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isInput')
    instructions      = config.tools.getArgumentAttribute(tool, longFormArgument, 'constructionInstructions')
    baseArgument      = instructions['use argument']
    modifyExtension   = instructions['modify extension']

    # Get the ID of the node corresponding to the baseArgument. If there are multiple nodes
    # available, pick one that has a predecessor node itself. TODO SORT THIS OUT
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument, 'option')
    if len(baseNodeIDs) == 1: baseNodeID = baseNodeIDs[0]
    elif len(baseNodeIDs) == 0:

      # It can be the case that the node is linked to file nodes only. If so, find the
      # associated option node.
      baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument, 'file')
      if baseNodeIDs: baseNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(baseNodeIDs[0])
      else: self.errors.unsetBaseNode(graph, config, task, longFormArgument, baseArgument)
    else: 

      # TODO CHECK THE LOGIC HERE
      # If there are multiple base nodes, return no values. Do not try to pick from a set, unless
      # this is an output file. In that case, pick a baseNodeID that has values.
      if isInput: return {}
      else:
        baseNodeID = config.nodeMethods.getNodeIDWithPredecessor(graph, baseNodeIDs, task)
        values     = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')

    # Find all predecessor file nodes and then identify the file associated with the baseNodeID.
    # Get the values from this file node.  Some of the values associated with option nodes are
    # for filename stubs, but those attached to file nodes will always be a full file name as
    # required here.
    fileNodeExists = False
    for nodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
      if nodeID.startswith(baseNodeID + '_'):
        values         = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))
        fileNodeExists = True
        break

    # If the file node has not been found, this might be because the tool argument being used is not
    # a file. If so, get the values from the option node.
    if not fileNodeExists:
      try: values = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'values')
      except:
        #TODO ERROR
        print('gknoConfig.constructFilenameFromToolArgumentNotStub')
        self.errors.terminate()

    # If the values are empty (e.g. the argument whose values are used to construct the filename have
    # not been set), check to see if gkno should terminate. By default, gkno will continue and request
    # that an output file be defined, however, the configuration can instruct termination if the
    # filename cannot be built.
    if not values:
      fail = instructions['fail if cannot construct'] if 'fail if cannot construct' in instructions else False
      if fail:
        baseTool          = config.nodeMethods.getSuccessorTaskNodes(graph, baseNodeID)[0]
        longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, baseNodeID, baseTool, 'longFormArgument')
        shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, baseNodeID, baseTool, 'shortFormArgument')
        description       = config.nodeMethods.getGraphNodeAttribute(graph, baseNodeID, 'description')
        if config.isPipeline:
          pipelineLongFormArgument, pipelineShortFormArgument = config.pipeline.getPipelineArgument(task, longFormArgument)

          # If the required argument is not a pipeline argument, recommend that the configuration should be
          # amended to include one.
          if pipelineLongFormArgument == None:
            self.errors.missingArgument(graph, config, task, longFormArgument, shortFormArgument, description, True)

          # If the pipeline argument exists, just terminate.
          else: self.errors.missingPipelineArgument(graph, config, pipelineLongFormArgument, pipelineShortFormArgument, description)

        # If gkno is being run in tool mode, terminate.
        self.errors.missingPipelineArgument(graph, config, longFormArgument, shortFormArgument, description)

    # Determine if the baseArgument is greedy. If so, the values associated with each iteration
    # will be used as input for a single iteration of this task. In this case, even if the values
    # have multiple iterations, this argument should only have one iteration of values.
    isBaseGreedy = config.edgeMethods.getEdgeAttribute(graph, baseNodeID, task, 'isGreedy')
    if isBaseGreedy:
      for i in range(2, len(values) + 1): del values[i]

    # Check if the path from the input file being used for construction should be retained.
    keepPath = instructions['use path'] if 'use path' in instructions else False

    # Check if the argument being created is allowed to have multiple values. If not, check each iteration
    # and ensure that the modifiedValues dictionary only has one entry per iteration.
    modifiedValues = {}
    if not config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowMultipleValues'):

      # Add the value to the modifiedValues list, but only include the filename and no path if the
      # file is an output, unless specifically instructed to keep the path intact. For input files
      # being constructed, assume that the path is the same as the file from which they are being derived.
      for iteration in values:
        if iteration in values:
          if values[iteration]:
            if isInput: modifiedValues[iteration] = [values[iteration][0]]
            else:
              if keepPath: modifiedValues[iteration] = [values[iteration][0]]
              else: modifiedValues[iteration] = [values[iteration][0].split('/')[-1]]
          else: modifiedValues[iteration] = []

    # If multiple values are allowed, cycle through them all and add them to the modifiedValues
    # list.
    else:
      for iteration in values:
        if isInput: modifiedValues[iteration] = [value for value in values[iteration]]
        else:
          if keepPath: modifiedValues[iteration] = [value for value in values[iteration]]
          else: modifiedValues[iteration] = [value.split('/')[-1] for value in values[iteration]]

    # If the extension is to be replaced, do that here. First check if the file has an extension.
    originalExtensions = config.tools.getArgumentAttribute(tool, baseArgument, 'extensions')
    if modifyExtension == 'replace':
      newExtensions             = config.tools.getArgumentAttribute(tool, longFormArgument, 'extensions')
      modifiedValues, extension, success = self.modifyExtensions(modifiedValues, originalExtensions, newExtensions, replace = True)

    # If the new extension should be appended to the end of the original file.
    elif modifyExtension == 'append':
      newExtensions             = config.tools.getArgumentAttribute(tool, longFormArgument, 'extensions')
      modifiedValues, extension, success = self.modifyExtensions(modifiedValues, originalExtensions, newExtensions, replace = False)

    # If the extension is to remain unchanged.
    elif modifyExtension == 'retain':
      if values: extension = '.' + values[1][0].rsplit('.')[-1]
      else: extension = ''
      newExtensions = [extension]
      success       = True

    elif modifyExtension == 'omit':
      newExtensions             = ['']
      modifiedValues, extension, success = self.modifyExtensions(modifiedValues, originalExtensions, '', replace = True)

    # If an unknown operation was included, terminate.
    else: self.errors.unknownExtensionModification(tool, longFormArgument, modifyExtension)

    # If the extension was not successfully set, terminate.
    if not success: self.errors.invalidExtensionInConstruction(task, tool, longFormArgument, baseArgument, modifiedValues)

    # If the construction instructions indicate that text in the values is to be modified, perform the
    # modifications.
    if 'modify text' in instructions:

      # Loop over the instructions.
      for instructionDict in instructions['modify text']:
        instruction = instructionDict.iterkeys().next()
        valueList   = instructionDict[instruction]

        # If values attributed to other tool arguments are to be included in the filename, or text is to
        # added or removed.
        #
        # If the instructions indicate that additional text should be added to the filename, add it.
        if instruction == 'add text':
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'strip')
          modifiedValues = self.addAdditionalText(valueList, modifiedValues, isBefore = False)
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'restore')

        # If the construction instructions indicate that values from another argument should be included
        # in the filename, include them here.
        if instruction == 'add argument values':
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'strip')
          modifiedValues = self.addArgumentValues(graph, config, valueList, task, modifiedValues)
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'restore')

        # If text is to be remove, remove it.
        if instruction == 'remove text': 
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'strip')
          modifiedValues = self.removeAdditionalText(config, task, tool, longFormArgument, valueList, modifiedValues)
          modifiedValues = self.updateExtensions(modifiedValues, extension, 'restore')

    # If a path is provided, add this to the values.
    if 'add path' in instructions:
      path = instructions['add path']
      if not path.endswith('/'): path += '/'
      modifiedValues = self.updateExtensions(modifiedValues, extension, 'strip')
      modifiedValues = self.addAdditionalText([path], modifiedValues, isBefore = True)
      modifiedValues = self.updateExtensions(modifiedValues, extension, 'restore')

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

    # Mark this node as having had its values constructed, rather than set by the user.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isConstructed', True)

  # Strip the extensions from a set of values.
  def updateExtensions(self, values, extension, action):
    modifiedValues = {}
    for iteration in values:
      modifiedValues[iteration] = []
      for value in values[iteration]:

        # If the extension is to be stripped off, but has the wrong value, terminate.
        if action == 'strip' and not value.endswith(extension): self.errors.stripWrongExtension(value, extension)
        if action == 'strip': modifiedValues[iteration].append(value.replace(extension, '', -1))
        elif action == 'restore': modifiedValues[iteration].append(value + str(extension))
        else:
          #TODO ERROR
          print('Unknown action - gknoConfig.updateExtensions', action)
          self.errors.terminate()

    return modifiedValues

  # Modify the extensions for files.
  def modifyExtensions(self, values, extensionsA, extensionsB, replace):
    modifiedValues    = {}
    matchedExtensions = True
    failedValue       = ''

    # The replacement extension may also be a list of allowed values.  Choose the first value in
    # this list as the extension to use.
    if extensionsB == '': replaceExtension = ''
    else: replaceExtension = str(extensionsB[0])

    # Loop over all values and change the extension.
    for valueID in values:
      newValuesList = []
      for value in values[valueID]:
        isValueMatched = False
        for extension in extensionsA:

          # If the value ends with the given extension, or the extension is not known.
          if value.endswith(extension) or (extension == 'no extension'):

            # If the extension wasn't provided, just use the extension that is on the file.
            string = extension
            if extension == 'no extension' and '.' in value: string = str(value.split('.')[-1])
            elif extension == 'no extension': string = ''

            # Replace the extension.
            if replace:
              if replaceExtension == 'no extension' and string != '': newValuesList.append(str(value.replace(string, '')))
              elif replaceExtension != 'no extension' and string != '': newValuesList.append(str(value.replace(string, replaceExtension)))
              elif replaceExtension != 'no extension': newValuesList.append(str(value) + str(replaceExtension))

            # If the new extension is just being appended.
            else:
              if replaceExtension != 'no extension': newValuesList.append(str(value + replaceExtension))

            # Mark that the extension has been handled.
            isValueMatched = True
            break

        # If the value failed to match an extension, set matchedExtensions to False. If any value
        # fails to match an extension, gkno will terminate.
        if not isValueMatched:
          matchedExtensions = False
          failedValue       = value

      # Update the modifiedValues dictionary to reflect the modified extensions.
      modifiedValues[valueID] = newValuesList

    # If any values failed, send a failed value back.
    if not matchedExtensions: modifiedValues[1] = [failedValue]

    return modifiedValues, replaceExtension, matchedExtensions

  # Construct a file of known name.
  def constructKnownFilename(self, graph, config, task, fileNodeID):
    modifiedValues   = {}
    tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
    instructions     = config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')

    # Get the filename and determine if the extensions needs to be added.
    filename     = config.tools.getAttributeFromDefinedConstruction(tool, argument, 'filename')
    addExtension = config.tools.getAttributeFromDefinedConstruction(tool, argument, 'add extension')

    # Determine the number of iterations of data values.
    numberOfDataSets = config.nodeMethods.getGraphNodeAttribute(graph, task, 'numberOfDataSets')

    # If there are no datasets associated with this task, there are required arguments that have not been
    # defined. Return and gkno will fail when checking data.
    if numberOfDataSets == 0: return

    # Check to see if the filenames to be created should be in a different directory.
    directoryArgument = instructions['directory argument'] if 'directory argument' in instructions else None
    if directoryArgument:
      if len(config.nodeMethods.getNodeForTaskArgument(graph, task, directoryArgument, 'option')) != 1:
        #TODO ERROR
        print('TOO MANY DIRECTORIES - constructKnownFilename')
        self.errors.terminate()

      nodeID          = config.nodeMethods.getNodeForTaskArgument(graph, task, directoryArgument, 'option')[0]
      directoryValues = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
      for iteration in directoryValues: modifiedValues[iteration] = [value + '/' for value in directoryValues[iteration]]

    # If there is no directory argument, use the connected argument to define the list of values. The
    # values themselves are irrelevant, but the number of iterations etc will be correctly defined.
    else:
      for counter in range(0, numberOfDataSets): modifiedValues[counter + 1] = []

    numberOfIterations = len(modifiedValues)
    for iteration in modifiedValues:
      if addExtension: extension = config.tools.getArgumentAttribute(tool, argument, 'extensions')[0]
      else: extension = ''

      # If there are multiple iterations, add the iteration to the name.
      if numberOfIterations > 1: finalFilename = str(filename) + '_' + str(iteration) + str(extension)
      else: finalFilename = str(filename) + str(extension)

      modifiedValues[iteration] = [value + finalFilename for value in modifiedValues[iteration]]
      if not modifiedValues[iteration]: modifiedValues[iteration].append(finalFilename)

    # Set the values.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

    # If no filename has been constructed, there is a problem with the construction. Terminate with an
    # error.
    if not modifiedValues: self.errors.failedToConstructDefinedFilename(task, tool, argument)

    # Mark this node as having had its values constructed, rather than set by the user.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isConstructed', True)

  # If an input argument is greedy and is given multiple sets of input values, collapse them into a single
  # data set.
  def setGreedyInputs(self, graph, config, fileNodeID, optionNodeID, task, longFormArgument):

    # Only modify the values if there is more than one set of data values.
    if len(config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')) > 1: self.setGreedyNodeValues(graph, config, optionNodeID)

    # Now perform the same tasks with the file node.
    if len(config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')) > 1: self.setGreedyNodeValues(graph, config, fileNodeID)

  # Update the node values.
  def setGreedyNodeValues(self, graph, config, nodeID):

    # Collapse all data sets into one.
    modifiedValues = []
    values         = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
    for iteration in values:
      for value in values[iteration]:
        modifiedValues.append(value)
    config.nodeMethods.addValuesToGraphNode(graph, nodeID, modifiedValues, write = 'replace', iteration = None)

  # Modify the number of iterations in a generated set of output values.
  def modifyNumberOfOutputIterations(self, graph, config, nodeID, numberOfIterations, task, longFormArgument, shortFormArgument):

    # Get the associated option node ID. It will be necessary to update the values associated
    # with the option node as well as the file nodes.
    optionNodeID = config.nodeMethods.getOptionNodeIDFromFileNodeID(nodeID)

    # Get the values associated with the file node.
    values = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

    # Determine if this task is greedy. If it is and there is already a single value, return without providing
    # any modifications.
    isGreedy = config.nodeMethods.getGraphNodeAttribute(graph, task, 'isGreedy')
    if isGreedy and len(values) == 1: return

    # It is possible that there is only a single input file and multiple output files, for example,
    # if the same input is used with a different parameter. If there are already multiple output
    # files defined and only a single input, return.
    if numberOfIterations == 1 and len(values) > 1: return

    # If there is more than one iteration in the values, terminate. This routine only works if there
    # are supposed to be multiple iterations, but only one was defined (e.g. a value was given on the
    # command line, but the value appears in multiple iterations and so the values must be unique for
    # each iteration to avoid multiple processes attempting to write to the same file). If there are
    # three defined input iterations and two output iterations, for example, it is not known how to
    # proceed.
    if len(values) != 1: self.errors.invalidNumberOfOutputIterations(task, longFormArgument, shortFormArgument, len(values), numberOfIterations)

    # Check if there is an extension associated with this argument.
    allowedExtensions = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions')

    # If there is no associated extension, modify the current values to be appended by '_1', then
    # add the required number of new iterations, each appended with the iteration ID.
    if allowedExtensions == ['no extension']:
      modifiedValues = [value + str('_1') for value in values[1]]
      config.nodeMethods.addValuesToGraphNode(graph, nodeID, modifiedValues, write = 'replace', iteration = None)
      for counter in range(2, numberOfIterations + 1):
        modifiedValues = [value + '_' + str(counter) for value in values[1]]
        config.nodeMethods.addValuesToGraphNode(graph, nodeID, modifiedValues, write = 'iteration', iteration = None)

    # If there are associated extensions, check that the values are appended with the extension. If not,
    # append the extension.
    else:
      baseValues    = []
      baseExtension = ''
      for value in values[1]:
        hasExtension = False
        for extension in allowedExtensions:
          if value.endswith(extension):
            hasExtension  = True
            baseExtension = extension
            break

        # If the value did not have an extension, add one.
        if not hasExtension: baseValues.append(value)
        else:
          baseValue = value.replace(baseExtension, '')
          baseValues.append(baseValue)

      # Now replace the existing values with values appended with the iteration ID, 1.
      if baseExtension == '': baseExtension = allowedExtensions[0]
      modifiedValues = [value + '_1' + baseExtension for value in baseValues]
      config.nodeMethods.addValuesToGraphNode(graph, nodeID, modifiedValues, write = 'replace', iteration = None)
      for counter in range(2, numberOfIterations + 1):
        modifiedValues = [value + '_' + str(counter) + baseExtension for value in baseValues]
        config.nodeMethods.addValuesToGraphNode(graph, nodeID, modifiedValues, write = 'iteration', iteration = None)

    # Having updated the file nodes, update the option node. If the option node is for a filename stub,
    # ensure that the lack of extension is preserved.
    isFilenameStub = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'isFilenameStub')

    if not isFilenameStub:
      modifiedValues = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))
      config.nodeMethods.addValuesToGraphNode(graph, optionNodeID, modifiedValues[1], write = 'replace', iteration = None)
      for counter in range(2, len(modifiedValues) + 1):
        config.nodeMethods.addValuesToGraphNode(graph, optionNodeID, modifiedValues[counter], write = 'iteration', iteration = None)
    else:
      modifiedValues = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

      # Strip the extension.
      for iteration in modifiedValues:
        for counter, value in enumerate(modifiedValues[iteration]):
          for extension in config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions'):
            if value.endswith(extension):
              modifiedValues[iteration][counter] = value.split(extension)[0]
              break

      config.nodeMethods.addValuesToGraphNode(graph, optionNodeID, modifiedValues[1], write = 'replace', iteration = None)
      for counter in range(2, len(modifiedValues) + 1):
        config.nodeMethods.addValuesToGraphNode(graph, optionNodeID, modifiedValues[counter], write = 'iteration', iteration = None)

  # Set file paths for all of the files.
  def setFilePaths(self, graph, config):

    # Get the path of the input and the output directories.
    inputPaths  = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-INPUT-PATH', 'values'))
    outputPaths = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-OUTPUT-PATH', 'values'))

    # Make sure the path is well formed. There can be multiple iterations of values, but only
    # one value per iteration, so replace the list for each iteration with the first value in
    # the list.
    #TODO Warning if more than one value in the list?
    if not inputPaths: inputPaths[1] = '$(PWD)/'
    else:
      for iteration in inputPaths:
        if not inputPaths[iteration][0].endswith('/'): inputPaths[iteration] = inputPaths[iteration][0] + '/'

    # Perform the same analysis for the output paths.
    if not outputPaths: outputPaths[1] = '$(PWD)/'
    else:
      for iteration in outputPaths:
        if not outputPaths[iteration][0].endswith('/'): outputPaths[iteration] = outputPaths[iteration][0] + '/'
        else: outputPaths[iteration] = outputPaths[iteration][0]

    # Parse all of the option nodes.
    for optionNodeID in config.nodeMethods.getNodes(graph, 'option'):
      if config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFile'):

        # Determine if the file is an input or output file. Since the node could be feeding
        # into or from multiple tasks, a file is an input, if and only if, the file nodes
        # associated with the option node have no predecessors.
        isInput = self.checkIfInputFile(config, graph, optionNodeID)

        # Loop over each iteration of lists of files.
        values = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
        task   = config.nodeMethods.getSuccessorTaskNodes(graph, optionNodeID)[0]

        # Get the tasks that use this option node and check if any of the arguments have a separate
        # path defined.
        if isInput: paths = self.checkForPathArguments(config, graph, optionNodeID, inputPaths)
        else: paths = self.checkForPathArguments(config, graph, optionNodeID, outputPaths)

        # If this is an input node, check that the number of values is equal to the number of values in
        # inputPaths, or that there is only a single value in inputPaths.
        if isInput:
          if (len(values) != len(paths)) and len(paths) != 1:
            print('ERROR - gknoConfig.setFilePaths')
            self.errors.terminate()

        # Perform the same check with the outputPaths for output files.
        else:
          if (len(values) != len(paths)) and len(paths) != 1:
            print('ERROR - gknoConfig.setFilePaths - output')
            self.errors.terminate()

        # Loop over all iterations.
        for iteration in values:

          # Get the input and output paths for this iteration.
          inputPath  = inputPaths[iteration] if iteration in inputPaths else inputPaths[1]
          outputPath = outputPaths[iteration] if iteration in outputPaths else outputPaths[1]
          if isInput: inputPath  = paths[iteration] if iteration in paths else paths[1]
          else: outputPath = paths[iteration] if iteration in paths else paths[1]
       
          modifiedOptionNodeValues = []
          for filename in values[iteration]:

            # Determine how the filename needs to be modified and then add to the given list of values.
            self.addModifiedValues(config, graph, filename, modifiedOptionNodeValues, isInput, inputPath, outputPath)

          # Reset the stored values.
          values[iteration] = modifiedOptionNodeValues

        # Loop over any associated file nodes and ensure that their paths are also set.
        for fileNodeID in config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID):
          values = config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')
          for iteration in values:
            modifiedFileNodeValues = []
            for filename in values[iteration]:
              self.addModifiedValues(config, graph, filename, modifiedFileNodeValues, isInput, inputPath, outputPath)
            values[iteration] = modifiedFileNodeValues

    return outputPaths

  # Determine if the file is an input or output file. Since the node could be feeding
  # into or from multiple tasks, a file is an input, if and only if, the file nodes
  # associated with the option node have no predecessors.
  def checkIfInputFile(self, config, graph, nodeID):
    fileNodeIDs = config.nodeMethods.getAssociatedFileNodeIDs(graph, nodeID)
    isInput     = True
    for fileNodeID in fileNodeIDs:
      if graph.predecessors(fileNodeID): isInput = False

    return isInput

  # Determine how the filename needs to be mofidied and then add to the given list of values.
  def addModifiedValues(self, config, graph, filename, values, isInput, inputPath, outputPath):

    # If the filename is missing, leave this blank. This will be caught as an error later, 
    # if the file is required.
    if not filename: values.append('')

    # If the filename already has a '/' in it, assume that the path is already defined.
    # In this case, leave the path as defined.
    elif '/' not in filename:
      if isInput: values.append(str(inputPath) + str(filename))
      else: values.append(str(outputPath) + str(filename))

    # If the filename begins with a '$', the path has been set using a variable that will be
    # understood by make. For example, the path might be $(PWD) representing the current
    # working directory. In this case, the value should be left as is.
    elif filename.startswith('$'): values.append(filename)

    # If the path is already defined, ensure the full path is written.
    else: values.append(os.path.abspath(filename))

  # Check all of the provided information.
  def checkData(self, graph, config, checkRequired):
    for optionNodeID in config.nodeMethods.getNodes(graph, 'option'):

      # Check if there are any values associated with this node and if it is required.
      values              = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
      isRequired          = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
      task                = graph.successors(optionNodeID)[0]
      longFormArgument    = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
      shortFormArgument   = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'shortFormArgument')
      description         = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'description')
      isCommandToEvaluate = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isCommandToEvaluate')

      # If the option is required but unset, terminate. The checkRequired flag allows the data checking
      # to proceed without failing if required files are not present. In particular, if an parameter set is being
      # exported, the presence of required values is not a cause for termination.
      if isRequired and not values and checkRequired:

        # If gkno is being run in pipeline mode, check if this argument is a pipeline argument.
        if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'pipeline':
          pipelineLongFormArgument, pipelineShortFormArgument = config.pipeline.getPipelineArgument(task, longFormArgument)

          # If the required argument is not a pipeline argument, recommend that the configuration should be
          # amended to include one.
          if pipelineLongFormArgument == None:
            self.errors.missingArgument(graph, config, task, longFormArgument, shortFormArgument, description, True)

          # If the pipeline argument exists, just terminate.
          else: self.errors.missingPipelineArgument(graph, config, pipelineLongFormArgument, pipelineShortFormArgument, description)

        # If gkno is being run in tool mode, terminate.
        self.errors.missingPipelineArgument(graph, config, longFormArgument, shortFormArgument, description)

      # Loop over the remaining values.
      if values and not isCommandToEvaluate:
        for iteration in values:

          # First check to see if multiple values have been given erroneously.
          numberOfValues      = len(values[iteration])
          allowMultipleValues = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowMultipleValues')

          # If there are no values associated with the iteration:
          if numberOfValues == 0: self.errors.missingPipelineArgument(graph, config, longFormArgument, shortFormArgument, description)
          if not allowMultipleValues and numberOfValues != 1:
            self.errors.givenMultipleValues(task, longFormArgument, shortFormArgument, values[iteration])

          # Determine the expected data type
          expectedDataType = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'dataType')
          for counter, value in enumerate(values[iteration]):

            # Get the data type for the value and check that it is as expected.
            success, modifiedValue     = self.checkDataType(expectedDataType, value)
            values[iteration][counter] = modifiedValue
            if not success: self.errors.invalidDataType(graph, config, longFormArgument, shortFormArgument, description, value, expectedDataType)

            # If the value refers to a file, check that the extension is valid. This is not necessary
            # for arguments representing a filename stub.
            if config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFile'):
              if not config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isFilenameStub'):
                for fileNodeID in config.nodeMethods.getAssociatedFileNodeIDs(graph, optionNodeID):

                  # Loop over the file names contained in the file nodes.
                  for fileValue in config.nodeMethods.getGraphNodeAttribute(graph, fileNodeID, 'values')[iteration]:
                    if not self.checkFileExtension(graph, config, optionNodeID, fileValue):
                      extensions = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowedExtensions')

                      # Check if the extension is listed as 'no extension'. If so, any extension is allowed, so do not
                      # fail.
                      if extensions[0] != 'no extension':
      
                        # If gkno is being run in tool mode, get the arguments.
                        if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'tool':
                          self.errors.invalidExtension(fileValue, extensions, longFormArgument, shortFormArgument, task, '', '')
        
                        # If gkno is being run in pipeline, mode, determine if the argument with the
                        # incorrect extension is a pipeline argument.
                        else:
                          longForm, shortForm = config.pipeline.getPipelineArgument(task, longFormArgument)
                          self.errors.invalidExtension(fileValue, extensions, longForm, shortForm, task, longFormArgument, shortFormArgument)

  # Get tasks for an option node, check if any of the arguments have a path defined from a different argument.
  # If so, return the paths.
  def checkForPathArguments(self, config, graph, optionNodeID, setPaths):
    for task in config.nodeMethods.getSuccessorTaskNodes(graph, optionNodeID):
      tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      longFormArgument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')

      # There are circumstances where there is no argument. If this is the case, do not proceed.
      if not longFormArgument: return setPaths

      pathArgument     = config.tools.getArgumentAttribute(tool, longFormArgument, 'pathArgument')
      if pathArgument:
        if config.isPipeline: pipelineArgument = config.pipeline.getPipelineArgument(task, pathArgument)[0]
        else: pipelineArgument = pathArgument

        # Get the option node associated with the pathArgument.
        pathArgumentNodeID = config.nodeMethods.getNodeForTaskArgument(graph, task, pipelineArgument, 'option')[0]
        pathArgumentValues = deepcopy(config.nodeMethods.getGraphNodeAttribute(graph, pathArgumentNodeID, 'values'))

        # Get the path values.
        for iteration in pathArgumentValues:
          if not pathArgumentValues[iteration][0].endswith('/'): pathArgumentValues[iteration] = pathArgumentValues[iteration][0] + '/'
          else: pathArgumentValues[iteration] = pathArgumentValues[iteration][0]

        return pathArgumentValues

    return setPaths

  # Loop over all of the gkno specific nodes and check that the values are valid.
  def checkNodeValues(self, graph, config):
    for nodeID in config.nodeMethods.getNodes(graph, 'general'):
      values   = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
      dataType = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'dataType')
      for iteration in values:
        for counter, value in enumerate(values[iteration]):
          success, modifiedValue = self.checkDataType(dataType, value)
          if not success:
            longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'longFormArgument')
            shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, 'gkno', 'shortFormArgument')
            description       = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'description')
            self.errors.invalidDataType(graph, config, longFormArgument, shortFormArgument, description, value, dataType)

          # If the value is of the correct type, replace the stored value with the returned value. For
          # example, if the value is 'true', and the expected type is a Boolean, this is fine, but would
          # not be recognised in the Python code as a Boolean. The checkDataType routine returns the value
          # in the correct form.
          values[iteration][counter] = modifiedValue

  # Check if data types agree.
  def checkDataType(self, expectedType, value):

    # Check that flags have the value "set" or "unset".
    if expectedType == 'flag':
      if value != 'set' and value != 'unset': return False, value

    # Boolean values should be set to 'true', 'True', 'false' or 'False'.
    elif expectedType == 'bool':

      # Check if the value is already a Boolean.
      if isinstance(value, bool): return True, value
      else:
        if value == 'true' or value == 'True': return True, True
        elif value == 'false' or value == 'False': return True, False
        else: return False, value

    # Check integers...
    elif expectedType == 'integer':
      try: intValue = int(value)
      except: return False, value

      return True, intValue

    # Check floats...
    elif expectedType == 'float':
      try: floatValue = float(value)
      except: return False, value

      return True, floatValue

    # and strings.
    elif expectedType == 'string':

      # First check if the value is a string.
      if isinstance(value, str): return True, value

      # If the value is not a string, check to see if it is unicode. If so, return a string.
      elif isinstance(value, unicode): return True, str(value)
      else: return False, value

    # If the data type is unknown.
    else: return False, value

    return True, value

  # Check that a file extension is valid.
  def checkFileExtension(self, graph, config, nodeID, value):
    for extension in config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions'):
      if value.endswith(extension):
        return True

    return False

  # Write out the list of missing files.
  def writeMissingFiles(self, graph, config, missingFiles):
    modifiedList = []

    # If there were files missing, write a warning and ensure that gkno will not execute.
    if missingFiles:
      self.hasMissingFiles = True

      # Check if any files appear multiple times.
      for missingFile in missingFiles:
        if missingFile not in modifiedList: modifiedList.append(missingFile)
      missingFiles = modifiedList

      self.errors.missingFiles(graph, config, missingFiles)
      config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-DO-NOT-EXECUTE', ['set'], write = 'replace')

  # Check to see if there are any files/directories present that are not allowed.  
  def checkForDisallowedFiles(self, graph, config, resourcePath):

    # Create a list of files/directories that cannot be present if the pipeline is to run
    # successfully.
    filesToCheck = []
    for task in config.pipeline.workflow:
      tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')

      # Check predecessor file nodes.
      for nodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
        longFormArgument   = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
        if longFormArgument != None:
          terminateIfPresent = config.tools.getArgumentAttribute(tool, longFormArgument, 'terminateIfPresent')
          if terminateIfPresent: filesToCheck.append(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

      # Check successor file nodes.
      for nodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        longFormArgument   = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'longFormArgument')
        if longFormArgument != None:
          terminateIfPresent = config.tools.getArgumentAttribute(tool, longFormArgument, 'terminateIfPresent')
          if terminateIfPresent: filesToCheck.append(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

      # Check option predecessor nodes for directories.
      for nodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
        longFormArgument = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
        if longFormArgument != None:
          if config.tools.getArgumentAttribute(tool, longFormArgument, 'isDirectory'):
            terminateIfPresent = config.tools.getArgumentAttribute(tool, longFormArgument, 'terminateIfPresent')
            if terminateIfPresent: filesToCheck.append(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

      # Check successor option nodes for directories.
      for nodeID in config.nodeMethods.getSuccessorOptionNodes(graph, task):
        longFormArgument = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'longFormArgument')
        if longFormArgument != None:
          if config.tools.getArgumentAttribute(tool, longFormArgument, 'isDirectory'):
            terminateIfPresent = config.tools.getArgumentAttribute(tool, longFormArgument, 'terminateIfPresent')
            if terminateIfPresent: filesToCheck.append(config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values'))

    # Loop over the filesToCheck and check if any of them already exist.
    for entry in filesToCheck:
      for iteration in entry:
        for filename in entry[iteration]:
          if filename.startswith('$(RESOURCES)'): filename = filename.replace('$(RESOURCES)', resourcePath)
          if filename.startswith('$(PWD)'): filename = filename.replace('$(PWD)', os.getcwd())
          if os.path.exists(filename): self.filesToRemove.append(filename)

    # If there are files that need to be removed prior to execution, inform the user, and ensure
    # that the makefile isn't executed.
    if self.filesToRemove:
      self.errors.removeFiles(graph, config, self.filesToRemove)
      config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-DO-NOT-EXECUTE', ['set'], write = 'replace')

  # Check that all of the executables required exist.
  def checkExecutables(self, config, graph, toolsPath):
    executablesList       = []
    missingExecutableList = []
    for task in config.pipeline.workflow:
      tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      executablePath = config.nodeMethods.getGraphNodeAttribute(graph, task, 'path')
      executable     = config.nodeMethods.getGraphNodeAttribute(graph, task, 'executable')

      # Only check tools that actually have an executable.
      if executablePath != 'no path':
        executable = toolsPath + executablePath + '/' + executable
        if executable not in executablesList: executablesList.append(executable)

    # Having identified all of the unique programmes, check that they exist.
    for executable in executablesList:
      try:
        with open(executable): pass
      except IOError: missingExecutableList.append(executable)

    # If there are any executable files that don't exist, print them out and fail.
    if len(missingExecutableList) != 0: self.errors.missingExecutables(graph, config, missingExecutableList)

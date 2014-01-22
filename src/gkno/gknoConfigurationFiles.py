#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import configurationClass.configurationClass
from configurationClass.configurationClass import *

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

    # Define dictionaries to hold argument information.
    self.validLongFormArguments  = {}
    self.validShortFormArguments = {}

    # Define a structure to hold missing files.
    self.missingFiles = []

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
      if not name or name == '-h' or name == '--help':
        gknoHelp.printHelp    = True
        gknoHelp.pipelineHelp = True
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

  # Attach the gkno specific instance arguments to the relevant nodes.
  def attachInstanceArgumentsToNodes(self, config, graph, runName, instance):
    for counter in range(len(config.instances.instanceAttributes[runName][instance].nodes) - 1, -1, -1):
      argument = config.instances.instanceAttributes[runName][instance].nodes[counter].argument
      values   = config.instances.instanceAttributes[runName][instance].nodes[counter].values

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

        # Remove the information from the instance data.
        config.instances.instanceAttributes[runName][instance].nodes.pop(counter)

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

    # Loop over each of the data sets and add to the correct iteration in the correct node.
    for iteration in range(1, self.loopData.numberOfDataSets + 1):
      for argument, values in zip(self.loopData.arguments, self.loopData.values[str(iteration)]):

        # Find the node for this argument.
        nodeID = config.pipeline.pipelineArguments[argument].ID

        # If this nodeID is not in the graph, an error has occured. Likely this node has been
        # deleted in the merge process.
        if nodeID not in graph.nodes(): self.errors.nodeNotInGraph(graph, config, nodeID, 'gknoConfigurationFiles.addLoopValuesToGraph')

        if iteration == 1: config.nodeMethods.addValuesToGraphNode(graph, nodeID, [str(values)], write = 'replace')
        else: config.nodeMethods.addValuesToGraphNode(graph, nodeID, [str(values)], write = 'iteration', iteration = str(iteration))

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
      tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')

      # Input files are predecessor nodes to the task.  Deal with the input files first.
      for fileNodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
        longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'longFormArgument')
        shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, fileNodeID, task, 'shortFormArgument')
        optionNodeID      = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
                                 
        # Use the argument to get information about the argument.
        isRequired = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
        isSet      = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'hasValue')

        # If input files aren't set, gkno should terminate.  If the input is linked to the output of
        # another task, the nodes are merged and so the input is set.  Thus, an empty value cannot be
        # filled without command line (or instance) information.
        if isRequired and not isSet:
          method = self.constructionInstructions(graph, config, task, longFormArgument, fileNodeID)
          if method == None:
            description = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'description')
  
            # Check if this argument is a pipeline argument.
            if task in config.pipeline.taskArgument:
              if longFormArgument in config.pipeline.taskArgument[task]:
                pipelineLongFormArgument  = config.pipeline.taskArgument[task][longFormArgument]
                pipelineShortFormArgument = config.pipeline.pipelineArguments[pipelineLongFormArgument].shortFormArgument
                self.errors.missingPipelineArgument(graph, config, pipelineLongFormArgument, pipelineShortFormArgument, description)

            # If not a pipeline argument, the error message needs to make the distinction. The error message
            # will also recommend adding the argument to the pipeline arguments since it is required.
            self.errors.missingArgument(graph, config, task, longFormArgument, shortFormArgument, description, isPipeline)

          # Build the input filename using the described method.
          else: self.constructFilename(graph, config, method, task, fileNodeID, isInput = True)

      # Now deal with output files,  These are all successor nodes.
      for fileNodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        longFormArgument = config.edgeMethods.getEdgeAttribute(graph, task, fileNodeID, 'longFormArgument')
        optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
                                 
        isRequired = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
        isSet      = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'hasValue')
        if isRequired and not isSet:
          method = self.constructionInstructions(graph, config, task, longFormArgument, fileNodeID)
          if method == None:     
  
            # TODO ERROR MESSAGE
            print('\tMISSING OUTPUT:', fileNodeID, task, tool, longFormArgument)
            self.errors.terminate()
  
          # If the tool configuration file has instructions on how to construct the filename,
          # built it using these instructions.
          else: self.constructFilename(graph, config, method, task, fileNodeID, isInput = False)

  # If a filename is not defined, check to see if there are instructions on how to 
  # construct the filename.
  def constructionInstructions(self, graph, config, task, argument, fileNodeID):
    tool = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    instructions = config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')
    if instructions == None: return None
    else: return instructions['ID']

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
    originalExtension = config.tools.getArgumentAttribute(tool, baseArgument, 'extension')
    modifiedValues    = self.modifyExtensions(values, originalExtension, '', replace = True)
    for iteration in modifiedValues: modifiedValues[iteration] = [value.split('/')[-1] for value in modifiedValues[iteration]]

    # If the construction instructions indicate that values from another argument should be included
    # in the filename, include them here.
    if 'add argument values' in instructions: modifiedValues = self.addArgumentValues(graph, config, instructions, task, modifiedValues, hasExtension = False)

    # If the instructions indicate that additional text should be added to the filename, add it.
    if 'add additional text' in instructions: modifiedValues = self.addAdditionalText(instructions, modifiedValues, hasExtension = False)

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
  def addArgumentValues(self, graph, config, instructions, task, modifiedValues, hasExtension):
    numberOfValues = len(modifiedValues)

    # The modifiedValues structure is a dictionary.  This contains values for each iteration of the
    # pipeline to be executed.  It must be the case that the modifiedValues dictionary has the same
    # number of iterations as the values structure associated with the node for the argument from
    # which the filenames are to be constructed, or one of the structured must have only one iteration.
    additionalArguments = []
    for taskArgument in instructions['add argument values']:

      # Find the option node that provides information for this argument.
      argumentNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, taskArgument, 'option')

      # If there is no node defined, the argument required to construct the filename has not been
      # defined. As such, it is impossible to construct the filename, so terminate gkno with an error
      # message.
      if len(argumentNodeIDs) == 0:
        if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'pipeline':
          self.errors.missingArgumentInFilenameConstructionNotPipelineArgument(graph, config, task, taskArgument)
        self.errors.missingArgumentInFilenameConstruction(graph, config, taskArgument)

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
      elif numberOfNodeValues == 0:

        # If gkno is being run in pipeline mode, check if this argument is a pipeline argument.
        if config.nodeMethods.getGraphNodeAttribute(graph, 'gkno', 'tool') == 'pipeline':
          isPipelineArgument = False
          if task in config.pipeline.pipelineArgument:
            if taskArgument in config.pipeline.pipelineArgument[task]:
               isPipelineArgument = True
               longForm           = config.pipeline.pipelineArgument[task][taskArgument]
               self.errors.missingArgumentInFilenameConstruction(graph, config, longForm)

          # Running in pipeline mode, but the argument required for filename construction is not a
          # pipeline argument. Fail, but recommend that the pipeline configurtaion file be modified
          # to include this argument.
          if not isPipelineArgument:
            self.errors.missingArgumentInFilenameConstructionNotPipelineArgument(graph, config, task, taskArgument)

        # If gkno is being run in tool mode, write the correct error message.
        self.errors.missingArgumentInFilenameConstruction(graph, config, taskArgument)
      else:
        print('NOT HANDLED VALUES - gknoConfig.addArgumentValues')
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
              if value.endswith(specificExtension):
                fileHasExtension = True
                break
            extension = specificExtension

            if not fileHasExtension:
              #TODO ERROR
              print('Unexpected extension - addAdditionalText')
              self.errors.terminate()

          newValue = str(value.split(extension)[0] + '.' + str(text) + extension)
          modifiedValues.append(newValue)

        else: modifiedValues.append(value + str(text))
      values[iteration] = modifiedValues

    return values

  # Construct the filenames for non-filename stub arguments.
  def constructFilenameFromToolArgumentNotStub(self, graph, config, task, fileNodeID, isInput):
    tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
    instructions     = config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')
    baseArgument     = instructions['use argument']
    modifyExtension  = instructions['modify extension']

    # Get the ID of the node corresponding to the baseArgument. If there are multiple nodes
    # available, pick one that has a predecessor node itself. TODO SORT THIS OUT
    baseNodeIDs = config.nodeMethods.getNodeForTaskArgument(graph, task, baseArgument, 'option')
    if len(baseNodeIDs) == 1: baseNodeID = baseNodeIDs[0]
    elif len(baseNodeIDs) == 0: self.errors.unsetBaseNode(graph, config, task, argument, baseArgument)
    else: baseNodeID = config.nodeMethods.getNodeIDWithPredecessor(graph, baseNodeIDs, task)

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

    # If no file node was found, terminate.
    if not fileNodeExists:
      #TODO ERROR
      print('gknoConfig.constructFilenameFromToolArgumentNotStub')
      self.errors.terminate()

    # Determine if the baseArgument is greedy. If so, the values associated with each iteration
    # will be used as input for a single iteration of this task. In this case, even if the values
    # have multiple iterations, this argument should only have one iteration of values.
    isBaseGreedy = config.edgeMethods.getEdgeAttribute(graph, baseNodeID, task, 'isGreedy')
    if isBaseGreedy:
      for i in range(2, len(values) + 1): del values[i]

    # Check if the argument being created is allowed to have multiple values. If not, check each iteration
    # and ensure that the modifiedValues dictionary only has one entry per iteration.
    modifiedValues = {}
    if not config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowMultipleValues'):

      # Add the value to the modifiedValues list, but only include the filename and no path if the
      # file is an output. For input files being constructed, assume that the path is the same as
      # the file from which they are being derived.
      for iteration in values:
        if isInput: modifiedValues[iteration] = [values[iteration][0]]
        else: modifiedValues[iteration] = [values[iteration][0].split('/')[-1]]

    # If multiple values are allowed, cycle through them all and add them to the modifiedValues
    # list.
    else:
      for iteration in values:
        if isInput: modifiedValues[iteration] = [value for value in values[iteration]]
        else: modifiedValues[iteration] = [value.split('/')[-1] for value in values[iteration]]

    # If the extension is to be replaced, do that here. First check if the file has an extension.
    originalExtension = config.tools.getArgumentAttribute(tool, baseArgument, 'extension')
    if modifyExtension == 'replace':
      newExtension      = config.tools.getArgumentAttribute(tool, argument, 'extension')
      modifiedValues    = self.modifyExtensions(modifiedValues, originalExtension, newExtension, replace = True)

    # If the new extension should be appended to the end of the original file.
    elif modifyExtension == 'append':
      newExtension      = config.tools.getArgumentAttribute(tool, argument, 'extension')
      modifiedValues    = self.modifyExtensions(modifiedValues, originalExtension, newExtension, replace = False)

    # If the construction instructions indicate that values from another argument should be included
    # in the filename, include them here.
    if 'add argument values' in instructions:
      modifiedValues = self.addArgumentValues(graph, config, instructions, task, modifiedValues, hasExtension = True, extension = originalExtension)

    # If the instructions indicate that additional text should be added to the filename, add it.
    if 'add additional text' in instructions:
      modifiedValues = self.addAdditionalText(instructions, modifiedValues, hasExtension = True, extension = originalExtension)

    # Reset the node values for the option and the file node.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

    # Mark this node as having had its values constructed, rather than set by the user.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isConstructed', True)

  # Modify the extensions for files.
  def modifyExtensions(self, values, extA, extB, replace):
    modifiedValues = {}

    # The extensions may be a list of allowed extension separated by '|'.  Break the extensions
    # into lists of allowed extensions.
    extAList = extA.split('|')

    # The replacement extension may also be a list of allowed values.  Choose the first value in
    # this list as the extension to use.
    if extB == '': replaceExtension = ''
    else: replaceExtension = str(extB.split('|')[0])

    # Loop over all values and change the extension.
    for valueID in values:
      newValuesList = []
      for value in values[valueID]:
        for extension in extAList:

          # If the value ends with the given extension, or the extension is not known.
          if value.endswith(extension) or extension == 'no extension':

            # If the extension wasn't provided, just use the extension that is on the
            # file.
            if extension == 'no extension': extension = value.split('.')[-1]
            string  = str(extension)

            if replace: newValuesList.append(value.replace(string, replaceExtension))
            else: newValuesList.append(value + replaceExtension)
            break

      # Update the modifiedValues dictionary to reflect the modified extensions.
      modifiedValues[valueID] = newValuesList

    return modifiedValues

  # Construct a file of known name.
  def constructKnownFilename(self, graph, config, task, fileNodeID):
    modifiedValues   = {}
    tool             = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
    optionNodeID     = config.nodeMethods.getOptionNodeIDFromFileNodeID(fileNodeID)
    argument         = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
    instructions     = config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')

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

    # If there is no directory argument, initialise the first iteration.
    else: modifiedValues[1] = []

    if 'filename' not in instructions:
      #TODO ERROR INCLUDE IN VALIDATION and include addExtension
      print('Creating filename with no given filename - constructKnownFilename.')
      self.errors.terminate()
    filename     = instructions['filename']
    addExtension = instructions['add extension']
    for iteration in modifiedValues:
      if addExtension: extension = config.tools.getArgumentAttribute(tool, argument, 'extension').split('|')[0]
      else: extension = ''
      filename = filename + extension
      modifiedValues[iteration] = [value + filename for value in modifiedValues[iteration]]

    # Set the values.
    config.nodeMethods.replaceGraphNodeValues(graph, optionNodeID, modifiedValues)
    config.nodeMethods.replaceGraphNodeValues(graph, fileNodeID, modifiedValues)

    # Mark this node as having had its values constructed, rather than set by the user.
    config.nodeMethods.setGraphNodeAttribute(graph, optionNodeID, 'isConstructed', True)

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

            # If the filename is missing, leave this blank. This will be caught as an error later, 
            # if the file is required.
            if not filename: modifiedValues.append('')

            # If the filename already has a '/' in it, assume that the path is already defined.
            # In this case, leave the path as defined.
            elif '/' not in filename:

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

            # If the filename begins with a '$', the path has been set using a variable that will be
            # understood by make. For example, the path might be $(PWD) representing the current
            # working directory. In this case, the value should be left as is.
            elif filename.startswith('$'): modifiedValues.append(filename)

            # If the path is already defined, ensure the full path is written.
            else: modifiedValues.append(os.path.abspath(filename))

          # Reset the stored values.
          values[iteration] = modifiedValues

  # Check all of the provided information.
  def checkData(self, graph, config, checkRequired):
    for optionNodeID in config.nodeMethods.getNodes(graph, 'option'):

      # Check if there are any values associated with this node and if it is required.
      values            = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'values')
      isRequired        = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'isRequired')
      task              = graph.successors(optionNodeID)[0]
      longFormArgument  = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'longFormArgument')
      shortFormArgument = config.edgeMethods.getEdgeAttribute(graph, optionNodeID, task, 'shortFormArgument')
      description       = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'description')

      # If the option is required but unset, terminate. The checkRequired flag allows the data checking
      # to proceed without failing if required files are not present. In particular, if an instance is being
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
          else: self.errors.missingPipelineArgument(graph, config, longFormArgument, shortFormArgument, description)

        # If gkno is being run in tool mode, terminate.
        self.errors.missingPipelineArgument(graph, config, longFormArgument, shortFormArgument, description)

      # Loop over the remaining values.
      if values:
        for iteration in values:

          # First check to see if multiple values have been given erroneously.
          numberOfValues      = len(values[iteration])
          allowMultipleValues = config.nodeMethods.getGraphNodeAttribute(graph, optionNodeID, 'allowMultipleValues')

          #TODO SORT OUT ERRORS.
          if not allowMultipleValues and numberOfValues != 1:
            print('GIVEN MULTIPLE VALUES WHEN NOT ALLOWED', values[iteration])
            self.errors.terminate()

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
      if isinstance(value, float): return True, value
      else: return False, value

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

  #TODO FINISH
  # Check that a file extension is valid.
  def checkFileExtension(self, graph, config, nodeID, value):
    for extension in config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions'):
      if value.endswith(extension):
        return True

    return False

  # Check that all required files exist prior to executing any makefiles.
  def checkFilesExist(self, graph, config, filenames, sourcePath):
    for nodeID, filename in filenames:

      # If the filename begins with $(PWD), replace it with the path of the current working
      # directory.
      if filename.startswith('$(PWD)'): filename = os.getcwd() + filename.split('$(PWD)')[1]

      # If the filename begins with $(RESOURCES), include the full path of the resources directory.
      elif filename.startswith('$(RESOURCES)'): filename = sourcePath + '/resources/' + filename.split('$(RESOURCES)')[1]

      if not os.path.exists(filename): self.missingFiles.append(filename)

  def writeMissingFiles(self, graph, config):
    modifiedList = []

    # If there were files missing, write a warning and ensure that gkno will not execute.
    if self.missingFiles:

      # Check if any files appear multiple times.
      for missingFile in self.missingFiles:
        if missingFile not in modifiedList: modifiedList.append(missingFile)
      self.missingFiles = modifiedList

      self.errors.missingFiles(graph, config, self.missingFiles)
      config.nodeMethods.addValuesToGraphNode(graph, 'GKNO-EXECUTE', [False], write = 'replace')

  # Draw the pipeline graph.
  def drawPipeline(self, graph, config, draw):
    filename = config.nodeMethods.getGraphNodeAttribute(graph, 'GKNO-DRAW-PIPELINE', 'values')[1][0]
    if filename == '': self.errors.noDrawFileProvided(graph, config)

    # If the filename does not have the '.dot' extension, add it.
    if not filename.endswith('.dot'): filename += '.dot'
    draw.drawDot(graph, config.nodeMethods, config.edgeMethods, config.tools, filename, nodes = 'file')
  
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

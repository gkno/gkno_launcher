#!/bin/bash/python

from __future__ import print_function

import fileHandling
import generalConfigurationFileMethods as methods
import parameterSets
import pipelineConfigurationErrors as errors

import json
import os
import sys

# Define a class to store task attribtues.
class taskAttributes:
  def __init__(self):

    # List this node type as a task.
    self.nodeType = 'task'

    # Store the task name along with the tool or pipeline used to execute the task.
    self.pipeline = None
    self.task     = None
    self.tool     = None

    # Mark greedy tasks.
    self.isGreedy = False

    # If a task is allowed to generate multiple output file nodes, set this flag. This can be used
    # when a task may have multiple input files and the input files are processed separately, but are
    # divided into segments for processing, e.g. splitting a BAM file into regions. Each BAM file can
    # be split into multiple regions, each of which are processed seperately, generating N nodes (one
    # for each BAM file), each containing M values (the number of genomic regions).
    self.generateMultipleOutputNodes = None

    # Related to the above, the task following that creating multiple output file nodes, can be run
    # multiple times (M times for each of the N inputs). If the following flag is set, multiple task
    # nodes will be generated, one task node for each of the N files.
    self.multipleTaskCalls = False

    # Following the above example, after the M regions have been called for each of the N samples, the
    # VCF files are combined. The 'combine' task will be run multiple times and each of the 'combine'
    # task nodes will generate a single output node. If the following flag is set, the output nodes
    # for each of the N 'combine' calls are consolidated into a single node with N values.
    self.consolidate = None

    # Identify any daughterer tasks. If the task is listed as being having multiple task calls, the same
    # task in the pipeline will appear as multiple nodes to handle different sets of data. Any task
    # that gets duplicated for this purpose has the IDs of the daughter tasks stored in this list.
    self.daughterTasks = []

    # Keep track of input and output nodes that have multiple nodes.
    self.multinodeInput  = None
    self.multinodeOutput = None

    # Store the node IDs of options that have multiple values.
    self.multivalueOptions = []

    # If the task outputs to a stream rather than a file, or the task accepts a stream.
    self.isInputStream  = False
    self.isOutputStream = False

    # Record if the unique node should be included in any plots.
    self.omitFromReducedPlot = False

# Define a class to hold the pipeline arguments.
class pipelineArguments:
  def __init__(self):

    # Store the description for the argument.
    self.description = 'No description'

    # Define the long and short form of the argument.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # Record the category to which the argument belongs.
    self.category = None

    # Record the expected data type.
    self.dataType = None

    # Define the configuration file and graph node that the argument points to.
    self.nodeID       = None
    self.graphNodeIDs = []

    # Record if the argument is listed as required in the pipeline configuration file.
    self.isRequired = False

    # Record if the argument should not be shown in the help message.
    self.hideInHelp = False

    # Record if the argument was defined in the pipeline configuration file, or if it was
    # imported from a tool. Store information about where the arguments were imported from.
    self.isImported       = False
    self.importedFromTask = None

# Define a class to store information on shared pipeline nodes.
class sharedGraphNodes:
  def __init__(self):

    # An id for the node.
    self.id = None

    # Define arguments.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # Information on the tasks and arguments sharing the node.
    self.nodes = {}

    # Store if the files associated with this node should be deleted.
    self.isDelete = False

    # Define a structure to hold information on all the tasks that the shared graph node points
    # to.
    self.sharedNodeTasks = []

# Define a class to hold information for shared nodes.
class nodeTaskAttributes:
  def __init__(self):

    # The task the node points to.
    self.task = None

    # If the task uses a tool, the argument associated with the tool needs to be defined.
    self.taskArgument = None

    # If, however, the task uses another pipeline, the node within the pipeline needs to be
    # specified.
    self.externalNodeID = None

    # If a non stub node is connecting to a stub node, the extension from the stub node
    # needs to be specified.
    self.stubExtension = None

    # If this is listed as being greedy (e.g. if multiple files are specified, use all the files in
    # one execution, rather than running the task multiple times).
    self.isGreedy = False

# Define a class to store information on unique pipeline nodes.
class uniqueGraphNodes:
  def __init__(self):

    # An id for the node.
    self.id = None

    # Define arguments.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # Define the task and argument to which this node applies.
    self.task         = None
    self.taskArgument = None

    # Record if this node is greedy.
    self.isGreedy = False

    # If the task associated with this node is being run multiple times and this node points to an output
    # file, then there is a node for each of the multiple executions of the task. This flag indicates that
    # all these versions of this node should be consolidated into a single node.
    self.consolidateNodes = False

    # Record if the task should be included in the plot.
    self.omitFromReducedPlot = False

# Define a class to store information on edges to be created. These are defined using the
# 'connect nodes and edges' section in the pipeline configuration file.
class edgeDefinitions:
  def __init__(self):

    #An id for the node.
    self.id = None

    # Store information on the source and targets.
    self.sourceInformation = []
    self.targetInformation = []

# Define a class to store general pipeline attributes,
class pipelineConfiguration:
  def __init__(self):

    # Handle errors.
    self.errors = errors.pipelineErrors()

    # Store the name of the pipeline.
    self.name = None

    # Store the path to the configuration file.
    self.path = None

    # Store the id for this pipeline.
    self.id = None

    # The pipeline description.
    self.description = 'No description'

    # The categories the pipeline is included in for help messages.
    self.categories = []

    # The parameter set information for this pipeline.
    self.parameterSets = parameterSets.parameterSets()

    # The tasks that the pipeline comprises. Also store all of the tasks and all of the tools
    # that are executed by the pipeline.
    self.pipelineTasks = {}
    self.allTasks      = []
    self.allTools      = []

    # The pipeline graph nodes that are shared between different tasks in the pipeline.
    self.sharedNodeAttributes = {}

    # Pipeline graph nodes that are kept as unique for a specific task,
    self.uniqueNodeAttributes = {}

    # The connections that need to be made between nodes and tasks.
    self.connections = {}

    # Store all of the valid top level pipeline arguments.
    self.longFormArguments  = {}
    self.shortFormArguments = {}

    # If the pipeline contains tasks that are themselves pipelines. Store all of the pipelines
    # used in this pipeline.
    self.hasPipelineAsTask = False
    self.requiredPipelines = []

    # If there is a request to import argument from a tool, store the name of the tool. This tool
    # will not be checked for validity, that is left to the methods that use the tool.
    self.importArgumentsFromTool = None

    # If the pipeline is nested within other pipelines, the nodes associated with this pipeline
    # have an address to locate them within the graph structure. For example, if the main pipeline
    # has a task 'run' which is a pipeline, all the nodes created for this pipeline are prepended
    # with 'run.' etc. Store this address.
    self.address = None

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

    # Flag if this pipeline contains instructions for building tasks that generate multiple output
    # file nodes.
    self.generatesMultipleNodes = False

    # As pipeline configuration files are processed, success will identify whether a problem was
    # encountered.
    self.success = True

  # Check that a supplied configuration file is a pipeline configuration file.
  def checkConfigurationFile(self, filename):

    # Get the name of the pipeline.
    self.name = self.getPipelineName(filename)

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Check that the configuration file is for a pipeline.
    try: configurationType = data['configuration type']
    except: return False
    if configurationType != 'pipeline': return False
    return True

  # Open a configuration file, process the data and return.
  def getConfigurationData(self, filename):

    # Get the name of the pipeline.
    self.name = self.getPipelineName(filename)

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, self.allowTermination)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

    # Return whether the configuration file was successfully parsed.
    return success

  # Get the pipeline name.
  def getPipelineName(self, filename):
    return (filename.rsplit('/')[-1]).rsplit('.json')[0]

  # Process the configuration file.
  def processConfigurationFile(self, data):

    # Check that the configuration file is a pipeline configuration file.
    self.success = self.checkIsPipeline(data)

    # Check the top level information, e.g. pipeline description.
    if self.success: self.checkTopLevelInformation(data)

    # Parse the tasks comprising the pipeline.
    if self.success: self.checkPipelineTasks(data['pipeline tasks'])

    # Parse the unique node information.
    if self.success: self.checkUniqueNodes(data)

    # Parse the shared node information.
    if self.success: self.checkSharedNodes(data)

    # Parse all of the arguments for the pipeline.
    if self.success: self.checkArguments(data)

    # Now check that the contents of each 'node' within the shared node information is valid.
    if self.success: self.checkSharedNodeTasks()

    # Check that any nodes and tasks to be joined are correctly defined.
    if self.success: self.checkDefinedEdges(data)

    # Check the parameter set information and store.
    if self.success: self.success = self.parameterSets.checkParameterSets(data['parameter sets'], self.allowTermination, self.name, isTool = False)

    # Parse all of the unique nodes and shared nodes and pull out all of the pipeline arguments and store them.
    if self.success: self.success = self.storeArguments()

    # Check if the pipeline defines any tasks that can generate multiple output file nodes. If so, check
    # that everything requires is defined.
    if self.success: self.success = self.checkMultipleNodeGeneration()

    # Return whether processing of the file was successful.
    return self.success

  # Check that the configuration file is for a pipeline.
  def checkIsPipeline(self, data):

    # Get the configuration type field. If this is not present, terminate, since this is the field that
    # defines if the configuration file is for a tool or for a pipeline.
    try: configurationType = data['configuration type']
    except:
      if self.allowTermination: self.errors.noConfigurationType(self.name)
      else: return False

    if configurationType != 'pipeline':
      if self.allowTermination: self.errors.invalidConfigurationType(self.name, configurationType)
      else: return False

    # If the configuration file is indeed for a pipeline, return true.
    return True

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                            = {}
    allowedAttributes['id']                      = (str, True, True, 'id')
    allowedAttributes['arguments']               = (dict, True, False, None)
    allowedAttributes['description']             = (str, True, True, 'description')
    allowedAttributes['categories']              = (list, True, True, 'categories')
    allowedAttributes['configuration type']      = (str, True, False, None)
    allowedAttributes['connect nodes to tasks' ] = (list, False, False, None)
    allowedAttributes['import arguments']        = (str, False, True, 'importArgumentsFromTool')
    allowedAttributes['parameter sets']          = (list, True, False, None)
    allowedAttributes['pipeline tasks']          = (list, True, False, None)
    allowedAttributes['shared graph nodes']      = (list, False, False, None)
    allowedAttributes['unique graph nodes']      = (list, False, False, None)

    # Define a set of information to be used in help messages.
    helpInfo = (self.name, None, None)

    # Check the attributes against the allowed attributes and make sure everything is ok.
    self = methods.checkAttributes(data, allowedAttributes, self, self.allowTermination, helpInfo)

  # Check the pipeline tasks. Ensure that all of the tasks are either available tools or other pipelines.
  def checkPipelineTasks(self, data):

    # Define the allowed general attributes.
    allowedAttributes                                   = {}
    allowedAttributes['consolidate nodes']              = (str, False, True, 'consolidate')
    allowedAttributes['omit from reduced plot']         = (bool, False, True, 'omitFromReducedPlot')
    allowedAttributes['input is stream']                = (bool, False, True, 'isInputStream')
    allowedAttributes['generate multiple output nodes'] = (str, False, True, 'generateMultipleOutputNodes')
    allowedAttributes['multiple task calls']            = (bool, False, True, 'multipleTaskCalls')
    allowedAttributes['output to stream']               = (bool, False, True, 'isOutputStream')
    allowedAttributes['pipeline']                       = (str, False, True, 'pipeline')
    allowedAttributes['task']                           = (str, True, True, 'task')
    allowedAttributes['tool']                           = (str, False, True, 'tool')

    for taskInformation in data:

      # Define a set of information to be used in help messages.
      #helpInfo = (self.name, 'pipeline tasks', taskInformation)
      helpInfo = (self.name, 'pipeline tasks', None)

      # Define a class to store task attribtues.
      attributes = taskAttributes()

      # Check all the supplied attributes.
      self.success, attributes = methods.checkAttributes(taskInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Check that the task name is unique.
      if attributes.task in self.pipelineTasks:
        if self.allowTermination: self.errors.repeatedTaskName(self.name, attributes.task)
        else:
          self.success = False
          return

      # Store the attributes for the task.
      self.pipelineTasks[attributes.task] = attributes

      # Get the tool or pipeline associated with the task.
      tool     = self.getTaskAttribute(attributes.task, 'tool')
      pipeline = self.getTaskAttribute(attributes.task, 'pipeline')

      # Each task must define either a tool or a pipeline. Check that one and only one is defined. 
      #TODO ERROR
      if not tool and not pipeline: print('pipeline.checkPipelineTasks - 5'); exit(0)
      if tool and pipeline: print('pipeline.checkPipelineTasks - 6'); exit(0)

      # If this is a tool, store the tool.
      if tool:
        self.allTools.append(tool)
        self.allTasks.append(attributes.task)
      
      # Checking if the tool or pipeline is valid is performed later when all pipelines
      # have been evaluated. If a task points to a pipeline, set the hasPipelineAsTask 
      # variable to True.
      if pipeline:
        self.requiredPipelines.append((attributes.task, pipeline))
        self.hasPipelineAsTask = True

  # If information on unique nodes exists, check that everything is valid.
  def checkUniqueNodes(self, data):

    # If there is not information on unique graph nodes, return.
    if 'unique graph nodes' not in data: return

    # Define the allowed nodes attributes.
    allowedAttributes                             = {}
    allowedAttributes['id']                       = (str, True, True, 'id')
    allowedAttributes['is greedy']                = (bool, False, True, 'isGreedy')
    allowedAttributes['omit from reduced plot']   = (bool, False, True, 'omitFromReducedPlot')
    allowedAttributes['task']                     = (str, True, True, 'task')
    allowedAttributes['task argument']            = (str, False, True, 'taskArgument')

    # Loop over all of the defined nodes.
    for uniqueNode in data['unique graph nodes']:

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(uniqueNode, self.allowTermination): return

      # Check that the node has a valid ID. This is required for help messages.
      id = methods.checkForId(uniqueNode, self.name, 'unique graph nodes', self.allowTermination, isTool = False)
      if not id: return

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'unique graph nodes', id)

      # Define the attributes object.
      attributes = uniqueGraphNodes()

      # Check the attributes conform to expectations.
      self.success, attributes = methods.checkAttributes(uniqueNode, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # If the nodeID already exists in the attributes, a node of this name has already been seen. All 
      #nodes must have a unique name.
      if attributes.id in self.uniqueNodeAttributes: self.errors.repeatedNodeID(uniqueNode, helpInfo)

      # Also check that the node id is not the name of a task.
      if attributes.id in self.allTasks: print('pipeline.checkUniqueNodes - 7'); exit(0)

      # Store the attributes.
      self.uniqueNodeAttributes[attributes.id] = attributes

  # If information on shared nodes exists, check that everything is valid.
  def checkSharedNodes(self, data):

    # If there is not information on unique graph nodes, return.
    if 'shared graph nodes' not in data: return

    # Defin the allowed nodes attributes.
    allowedAttributes                           = {}
    allowedAttributes['arguments sharing node'] = (list, True, True, 'nodes')
    allowedAttributes['delete files']           = (bool, False, True, 'isDelete')
    allowedAttributes['id']                     = (str, True, True, 'id')

    # Loop over all of the defined nodes.
    for sharedNode in data['shared graph nodes']:

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(sharedNode, self.allowTermination): return

      # Check that the node has a valid ID. This is required for help messages.
      id = methods.checkForId(sharedNode, self.name, 'shared graph nodes', self.allowTermination, isTool = False)
      if not id: return

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'shared graph nodes', id)

      # Define the attributes object.
      attributes = sharedGraphNodes()

      # Check the attributes conform to expectations.
      self.success, attributes = methods.checkAttributes(sharedNode, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # If the node id already exists in the attributes, a node of this name has already been seen. All 
      # nodes must have a unique name.
      if attributes.id in self.sharedNodeAttributes: print('pipeline.checkSharedNodes - 6'); exit(0)
      if attributes.id in self.uniqueNodeAttributes: print('pipeline.checkSharedNodes - 6'); exit(0)

      # Also check that the node id is not the name of a task.
      if attributes.id in self.allTasks: self.errors.nodeIDIsTaskID(self.name, 'shared graph nodes', id)

      # Store the attributes.
      self.sharedNodeAttributes[attributes.id] = attributes

  # For each task in each shared graph node, ensure that the information in the configuration
  # file is complete.
  def checkSharedNodeTasks(self):

    # Define the allowed nodes attributes.
    allowedAttributes                        = {}
    allowedAttributes['is greedy']           = (bool, False, True, 'isGreedy')
    allowedAttributes['node id']             = (str, False, True, 'externalNodeID')
    allowedAttributes['stub extension']      = (str, False, True, 'stubExtension')
    allowedAttributes['task']                = (str, True, True, 'task')
    allowedAttributes['task argument']       = (str, False, True, 'taskArgument')

    # Loop over all of the defined nodes.
    for nodeID in self.sharedNodeAttributes:
      for node in self.sharedNodeAttributes[nodeID].nodes:

        # Define a set of information to be used in help messages.
        helpInfo = (self.name, 'shared nodes', nodeID)

        # Check that the supplied structure is a dictionary.
        if not methods.checkIsDictionary(node, self.allowTermination): return

        # Define the attributes object.
        attributes = nodeTaskAttributes()
  
        # Check that the supplied attributes are valid.
        self.success, attributes = methods.checkAttributes(node, allowedAttributes, attributes, self.allowTermination, helpInfo)

        #TODO INCLUDE A CHECK TO ENSURE THAT AN ALLOWED COMBINATION OF FIELDS IS PRESENT. IN PARTICULAR,
        # IF THE TASK POINTS TO A PIPELINE RATHER THAN A TOOL, ENSURE THAT THE NODE ID IS PRESENT AND NOT
        # THE TASK ARGUMENT.

        # Store the attributes.
        self.sharedNodeAttributes[nodeID].sharedNodeTasks.append(attributes)

  # Check all of the defined arguments for the pipeline.
  def checkArguments(self, data):

    # If there is not information on unique graph nodes, return.
    if 'arguments' not in data: return

    # Define the allowed nodes attributes.
    allowedAttributes                        = {}
    allowedAttributes['description']         = (str, True, True, 'description')
    allowedAttributes['hide in help']        = (bool, False, True, 'hideInHelp')
    allowedAttributes['long form argument']  = (str, True, True, 'longFormArgument')
    allowedAttributes['node id']             = (str, True, True, 'nodeID')
    allowedAttributes['required']            = (bool, False, True, 'isRequired')
    allowedAttributes['short form argument'] = (str, True, True, 'shortFormArgument')

    # Loop over all of the argument categories.
    for category in data['arguments']:

      # Loop over all arguments in the category.
      for argumentInformation in data['arguments'][category]:
  
        # Check that the supplied structure is a dictionary.
        if not methods.checkIsDictionary(argumentInformation, self.allowTermination): return
  
        # Check that the node has a long form argument. This is required for help messages.
        longFormArgument = methods.checkForLongFormArgument(argumentInformation, self.allowTermination)
        if not longFormArgument: return
  
        # Define a set of information to be used in help messages.
        helpInfo = (self.name, 'arguments -> ' + category, longFormArgument)
  
        # Define the attributes object and add the help category.
        attributes          = pipelineArguments()
        attributes.category = category
  
        # Check the attributes conform to expectations.
        self.success, attributes = methods.checkAttributes(argumentInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)
  
        # If the long form argument already exists, there is a problem. All arguments must be unique.
        if longFormArgument in self.longFormArguments: print('pipeline.checkArguments - 6'); exit(0)
  
        # Also check that the node id is not the name of a task.
        if attributes.shortFormArgument in self.shortFormArguments: print('pipeline.checkArguments - 7'); exit(0)
  
        # Store the attributes.
        self.longFormArguments[longFormArgument]              = attributes
        self.shortFormArguments[attributes.shortFormArgument] = longFormArgument

  # Check that defined edges are correctly included.
  def checkDefinedEdges(self, data):

    if 'connect nodes to tasks' not in data: return

    # Define the allowed attributes.
    allowedAttributes            = {}
    allowedAttributes['id']      = (str, True, True, 'id')
    allowedAttributes['sources'] = (list, True, False, None)
    allowedAttributes['targets'] = (list, True, False, None)

    # Define the allowed source attributes.
    allowedSourceAttributes                  = {}
    allowedSourceAttributes['task']          = (str, True, True, 'task')
    allowedSourceAttributes['task argument'] = (str, True, True, 'taskArgument')

    # Define the allowed target attributes.
    allowedTargetAttributes                  = {}
    allowedTargetAttributes['task']          = (str, True, True, 'task')
    allowedTargetAttributes['task argument'] = (str, True, True, 'taskArgument')

    # Loop over all the defined definitions.
    for information in data['connect nodes to tasks']:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'connect nodes to tasks', information)

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(information, self.allowTermination): return

      # Define the attributes object.
      attributes = edgeDefinitions()

      # Check the attributes conform to expectations.
      self.success, attributes = methods.checkAttributes(information, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Loop over all the listed sources and check the information.
      for source in information['sources']:
        if not methods.checkIsDictionary(source, self.allowTermination): return
        sourceAttributes = nodeTaskAttributes()
        self.success, sourceAttributes = methods.checkAttributes(source, allowedSourceAttributes, sourceAttributes, self.allowTermination, helpInfo)
        attributes.sourceInformation.append(sourceAttributes)

      # Loop over all the listed targets and check the information.
      for target in information['targets']:
        if not methods.checkIsDictionary(target, self.allowTermination): return
        targetAttributes = nodeTaskAttributes()
        self.success, targetAttributes = methods.checkAttributes(target, allowedTargetAttributes, targetAttributes, self.allowTermination, helpInfo)
        attributes.targetInformation.append(targetAttributes)

      # Store the ID.
      self.connections[attributes.id] = attributes

  # Store all of the pipeline arguments.
  def storeArguments(self):
    observedShortFormArguments = []
    observedLongFormArguments  = []

    # Parse all of the unique nodes.
    for nodeID in self.getUniqueNodeIDs():

      # Get the long and short form arguments.
      longFormArgument  = self.getUniqueNodeAttribute(nodeID, 'longFormArgument')
      shortFormArgument = self.getUniqueNodeAttribute(nodeID, 'shortFormArgument')

      # Check that the arguments are unique and store the values
      if self.allowTermination:
        self.callArgumentErrors(nodeID, longFormArgument, shortFormArgument, observedLongFormArguments, observedShortFormArguments)
      if longFormArgument:
        observedLongFormArguments.append(longFormArgument)
        observedShortFormArguments.append(shortFormArgument)
        self.arguments[longFormArgument] = shortFormArgument

    # Parse all of the shared nodes.
    for nodeID in self.getSharedNodeIDs():

      # Get the long and short form arguments.
      longFormArgument  = self.getSharedNodeAttribute(nodeID, 'longFormArgument')
      shortFormArgument = self.getSharedNodeAttribute(nodeID, 'shortFormArgument')

      # Check that the arguments are unique and store the values.
      if self.allowTermination:
        self.callArgumentErrors(nodeID, longFormArgument, shortFormArgument, observedLongFormArguments, observedShortFormArguments)
      if longFormArgument:
        observedLongFormArguments.append(longFormArgument)
        observedShortFormArguments.append(shortFormArgument)
        self.arguments[longFormArgument] = shortFormArgument

    return True

  # If termination is allowed, call errors on the observed arguments.
  def callArgumentErrors(self, nodeID, longFormArgument, shortFormArgument, observedLongFormArguments, observedShortFormArguments):
    if longFormArgument in observedLongFormArguments: self.errors.repeatedLongFormArgument(nodeID, longFormArgument)
    if shortFormArgument in observedShortFormArguments: self.errors.repeatedShortFormArgument(nodeID, longFormArgument, shortFormArgument)
    if longFormArgument and not shortFormArgument: self.errors.noShortFormArgument(nodeID, longFormArgument)
    if shortFormArgument and not longFormArgument: self.errors.noLongFormArgument(nodeID, shortFormArgument)

  # If the pipeline contains any tasks that generate multiple ouptut nodes, check that all definitions
  # to make sense of the pipeline have been provided.
  def checkMultipleNodeGeneration(self):

    # Initialise variables.
    consolidatingNodes               = []
    isPreviousTaskConsolidatingNodes = False
    isPreviousTaskGeneratingMultiple = False
    isPreviousTaskMultipleTaskCalls  = False
    isUnterminated                   = False

    # Loop over all of the tasks in the pipeline and
    for task in self.getAllTasks():

      # Get the flags describing the task behaviour related to multiple node generation.
      isConsolidatingNodes = self.getTaskAttribute(task, 'consolidate')
      isGeneratingMultiple = self.getTaskAttribute(task, 'generateMultipleOutputNodes')
      isMultipleTaskCalls  = self.getTaskAttribute(task, 'multipleTaskCalls')

      # The isGeneratingMultiple flag cannot be set with either of the other flags.
      if isGeneratingMultiple:
        if isMultipleTaskCalls or isConsolidatingNodes: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 1'); exit(1)

        # If this task has isGeneratingMultiple set to true, the previous task cannot. In addition,
        # the previous task cannot have isMultipleTaskCalls set to true either, unless it also has
        # isConsolidatingNodes set to true.
        if isPreviousTaskGeneratingMultiple: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 2'); exit(1)
        if isPreviousTaskMultipleTaskCalls and not isPreviousTaskConsolidatingNodes: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 3'); exit(1)

        # Set isUnterminated to true. Once multiple output nodes have been generated by a task, the
        # nodes can pass through multiple tasks that run multlipe times, but ultimately, the nodes
        # need to be consolidated to a sinlge node prior to termination of the pipeline.
        isUnterminated = True

        # Record that this pipeline has instructions for tasks with multiple output nodes.
        self.generatesMultipleNodes = True

      # If the task is being run multiple times, a number of other conditions to be met need to be checked.
      if isMultipleTaskCalls:

        # If the previous task does not have isMultipleTaskCalls or isGeneratingMultiple set to true, this
        # task cannot be run multiple times as it will not have the necessary input nodes to operate on.
        if not isPreviousTaskGeneratingMultiple and not isPreviousTaskMultipleTaskCalls: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 4'); exit(1)

      # The isMultipleTaskCalls flag must be true if the isConsolidatingNodes is true. Output nodes can only
      # be consolidated if multiple tasks were run to generate the multiple nodes to be consolidated.
      if isConsolidatingNodes:
        if not isMultipleTaskCalls: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 5'); exit(1)

        # As the nodes have been consolidated, set isUnterminated to False and the run of tasks with multiple
        # task nodes has been completed.
        isUnterminated = False

      # If the previous task was listed as isGeneratingMultiple, this task must have the isMultipleTaskCalls flag
      # set to true. If a task generated multiple output nodes, at least one task must be run using those nodes
      # before consolidating output nodes back to a single node.
      if isPreviousTaskGeneratingMultiple and not isMultipleTaskCalls: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 6'); exit(1)

      # If the previous task has isMultipleTaskCalls set to true, but didn't consolidate the output file nodes, this
      # task must have isMultipleTaskCalls set to true
      if isPreviousTaskMultipleTaskCalls and not isPreviousTaskConsolidatingNodes and not isMultipleTaskCalls: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 7'); exit(1)

      # Update the flags for the previous task (e.g. the task just processed).
      isPreviousTaskConsolidatingNodes = isConsolidatingNodes
      isPreviousTaskGeneratingMultiple = isGeneratingMultiple
      isPreviousTaskMultipleTaskCalls  = isMultipleTaskCalls

    # If the run of tasks with multiple task nodes is not ultimately consolidated into a single node throw an error.
    if isUnterminated: print('ERROR - pipelineConfiguration.checkMultipleNodeGeneration - 8'); exit(1)

    return True

  ########################################################
  ## Methods for getting information about the pipeline ##
  ########################################################

  # Return a list of all of the tool arguments used in the pipeline.
  def getToolArguments(self):
    arguments = []

    # Get all the tool arguments associated with unique nodes.
    for nodeID in self.getUniqueNodeIDs():
      task         = self.getUniqueNodeAttribute(nodeID, 'task')
      taskArgument = self.getUniqueNodeAttribute(nodeID, 'taskArgument')
      if taskArgument: arguments.append(('unique', nodeID, task, taskArgument))

    # Get all the tool arguments associated with shared nodes.
    for nodeID in self.getSharedNodeIDs():
      for information in self.getSharedNodeTasks(nodeID):
        if information.taskArgument:
          arguments.append(('shared', nodeID, information.task, information.taskArgument))

    return arguments

  # Return a list of all the tasks in the pipeline.
  def getAllTasks(self):
    try: return self.allTasks
    except: return None

  # Get a pipeline task attribute.
  def getTaskAttribute(self, task, attribute):
    try: return getattr(self.pipelineTasks[task], attribute)
    except: return None

  # Get a list of all unique node IDs.
  def getUniqueNodeIDs(self):
    try: return self.uniqueNodeAttributes.keys()
    except: return None

  # Get an attribute about a unique node.
  def getUniqueNodeAttribute(self, nodeID, attribute):
    try: return getattr(self.uniqueNodeAttributes[nodeID], attribute)
    except: return None

  # Get a list of all shared node IDs.
  def getSharedNodeIDs(self):
    try: return self.sharedNodeAttributes.keys()
    except: return None

  # Get all of the tasks sharing a node.
  def getSharedNodeTasks(self, nodeID):
    try: return self.sharedNodeAttributes[nodeID].sharedNodeTasks
    except: return None

  # Get an attribute about a shared node.
  def getSharedNodeAttribute(self, nodeID, attribute):
    try: return getattr(self.sharedNodeAttributes[nodeID], attribute)
    except: return None

  # Get attributes for a task defined in the shared node section.
  def getNodeTaskAttribute(self, node, attribute):
    try: return getattr(node, attribute)
    except: return None

  # Get the names of all the parametes sets.
  def getParameterSetNames(self):
    try: return self.parameterSets.sets.keys()
    except: return None

  # Get the description of a parametes set.
  def getParameterSetDescription(self, name):
    try: return self.parameterSets.getDescription(name)
    except: return None

  # Get an attribute for an argument.
  def getArgumentAttribute(self, argument, attribute):

    # Ensure that the argument exists.
    try: longFormArgument = self.longFormArguments[argument].longFormArgument

    # If the supplied argument was in the short form.
    except:
      try: longFormArgument = self.shortFormArguments[argument]
      except: return False

    # Return the value.
    try: return getattr(self.longFormArguments[longFormArgument], attribute)
    except: return False

  # Get source information for edges defined in the configuration file.
  def getSources(self, node):
    try: return self.connections[node].sourceInformation
    except: return None

  # Get target information for edges defined in the configuration file.
  def getTargets(self, node):
    try: return self.connections[node].targetInformation
    except: return None

  # Return the long form version of an argument.
  def getLongFormArgument(self, argument):

    # Check if this argument is from a unique node.
    for nodeID in self.getUniqueNodeIDs():
      shortFormArgument = self.getUniqueNodeAttribute(nodeID, 'shortFormArgument')
      longFormArgument  = self.getUniqueNodeAttribute(nodeID, 'longFormArgument')

      # If the long form argument matches the given argument, return the long form. If the argument
      # matches the short from, return the associated long form.
      if argument == longFormArgument: return longFormArgument
      elif argument == shortFormArgument: return longFormArgument

    # If the argument was not an argument for a unique node, check the shared nodes.
    for nodeID in self.getSharedNodeIDs():
      shortFormArgument = self.getSharedNodeAttribute(nodeID, 'shortFormArgument')
      longFormArgument  = self.getSharedNodeAttribute(nodeID, 'longFormArgument')

      # If the long form argument matches the given argument, return the long form. If the argument
      # matches the short from, return the associated long form.
      if argument == longFormArgument: return longFormArgument
      elif argument == shortFormArgument: return longFormArgument

    # If not match was found, return False,
    return False

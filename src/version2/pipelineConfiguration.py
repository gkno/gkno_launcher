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
    self.pipeline        = None
    self.task            = None
    self.tool            = None

# Define a class to hold information for shared nodes.
class nodeTaskAttributes:
  def __init__(self):
    self.pipeline       = None
    self.pipelineNodeID = None
    self.task           = None
    self.taskArgument   = None

# Define a class to store information on shared pipeline nodes.
class sharedGraphNodes:
  def __init__(self):

    # An id for the node.
    self.id = None

    # A description for the node. If the node is associated with an argument, this description
    # will appear as the help message.
    self.description = 'No description'

    # Define arguments.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # Information on the tasks and arguments sharing the node.
    self.nodes = {}

    # Define a structure to hold information on all the tasks that the shared graph node points
    # to.
    self.sharedNodeTasks = []

    # If the shared node contains any task that points to another pipeline, mark it.
    self.containsTaskInAnotherPipeline = False
    self.containsNodeInAnotherPipeline = False

# Define a class to store information on unique pipeline nodes.
class uniqueGraphNodes:
  def __init__(self):

    # An id for the node.
    self.id = None

    # A description for the node. If the node is associated with an argument, this description
    # will appear as the help message.
    self.description = 'No description'

    # Define arguments.
    self.longFormArgument  = None
    self.shortFormArgument = None

    # Define the pipeline that the task and argument to which this node points resides. If None,
    # the task resides in the pipeline defined by the current pipeline configuration file.
    self.pipeline = None

    # Define the task and argument to which this node applies.
    self.task         = None
    self.taskArgument = None

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

    # Store all of the defined arguments.
    self.arguments = {}

    # If the pipeline contains tasks that are themselves pipelines. Store all of the pipelines
    # used in this pipeline.
    self.hasPipelineAsTask = False
    self.requiredPipelines = []

    # If the pipeline is nested within other pipelines, the nodes associated with this pipeline
    # have an address to locate them within the graph structure. For example, if the main pipeline
    # has a task 'run' which is a pipeline, all the nodes created for this pipeline are prepended
    # with 'run.' etc. Store this address.
    self.address = None

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

    # As pipeline configuration files are processed, success will identify whether a problem was
    # encountered.
    self.success = True

  # Open a configuration file, process the data and return.
  def getConfigurationData(self, filename):

    # Get the name of the pipeline.
    self.name = self.getPipelineName(filename)

    # Get the configuration file data.
    data = fileHandling.fileHandling.readConfigurationFile(filename, True)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

  # Get the pipeline name.
  def getPipelineName(self, filename):
    return (filename.rsplit('/')[-1]).rsplit('.json')[0]

  # Process the configuration file.
  def processConfigurationFile(self, data):

    # Check the top level information, e.g. pipeline description.
    self.checkTopLevelInformation(data)

    # Parse the tasks comprising the pipeline.
    if self.success: self.checkPipelineTasks(data['pipeline tasks'])

    # Parse the unique node information.
    if self.success: self.checkUniqueNodes(data)

    # Parse the shared node information.
    if self.success: self.checkSharedNodes(data)

    # Now check that the contents of each 'node' within the shared node information is valid.
    if self.success: self.checkSharedNodeTasks()

    # Check that any nodes and tasks to be joined are correctly defined.
    if self.success: self.checkDefinedEdges(data)

    # Check the parameter set information and store.
    if self.success: self.success = self.parameterSets.checkParameterSets(data['parameter sets'], self.allowTermination, self.name)

    # Parse all of the unique nodes and shared nodes and pull out all of the pipeline arguments and store them.
    if self.success: self.success = self.storeArguments()

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                            = {}
    allowedAttributes['id']                      = (str, True, True, 'id')
    allowedAttributes['description']             = (str, True, True, 'description')
    allowedAttributes['categories']              = (list, True, True, 'categories')
    allowedAttributes['connect nodes to tasks' ] = (list, False, False, None)
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
    allowedAttributes             = {}
    allowedAttributes['pipeline'] = (str, False, True, 'pipeline')
    allowedAttributes['task']     = (str, True, True, 'task')
    allowedAttributes['tool']     = (str, False, True, 'tool')

    for taskInformation in data:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'pipeline tasks', taskInformation)

      # Define a class to store task attribtues.
      attributes = taskAttributes()

      # Check all the supplied attributes.
      self.success, attributes = methods.checkAttributes(taskInformation, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # Check that the task name is unique.
      if attributes.task in self.pipelineTasks:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkPipelineTasks - 4', attributes.task); exit(0)
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
    allowedAttributes                        = {}
    allowedAttributes['id']                  = (str, True, True, 'id')
    allowedAttributes['description']         = (str, True, True, 'description')
    allowedAttributes['long form argument']  = (str, False, True, 'longFormArgument')
    allowedAttributes['pipeline']            = (str, False, True, 'pipeline')
    allowedAttributes['short form argument'] = (str, False, True, 'shortFormArgument')
    allowedAttributes['task']                = (str, True, True, 'task')
    allowedAttributes['task argument']       = (str, False, True, 'taskArgument')

    # Loop over all of the defined nodes.
    for uniqueNode in data['unique graph nodes']:

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'unique graph nodes', uniqueNode)

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(uniqueNode, self.allowTermination): return

      # Define the attributes object.
      attributes = uniqueGraphNodes()

      # Check the attributes conform to expectations.
      self.success, attributes = methods.checkAttributes(uniqueNode, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # If the nodeID already exists in the attributes, a node of this name has already been seen. All 
      #nodes must have a unique name.
      if attributes.id in self.uniqueNodeAttributes: print('pipeline.checkUniqueNodes - 6'); exit(0)

      # Also check that the node id is not the name of a task.
      if attributes.id in self.allTasks: print('pipeline.checkUniqueNodes - 7'); exit(0)

      # Store the attributes.
      self.uniqueNodeAttributes[attributes.id] = attributes

  # If information on shared nodes exists, check that everything is valid.
  def checkSharedNodes(self, data):

    # If there is not information on unique graph nodes, return.
    if 'shared graph nodes' not in data: return

    # Define the allowed nodes attributes.
    allowedAttributes                           = {}
    allowedAttributes['arguments sharing node'] = (list, True, True, 'nodes')
    allowedAttributes['id']                     = (str, True, True, 'id')
    allowedAttributes['description']            = (str, True, True, 'description')
    allowedAttributes['long form argument']     = (str, False, True, 'longFormArgument')
    allowedAttributes['short form argument']    = (str, False, True, 'shortFormArgument')

    # Loop over all of the defined nodes.
    for sharedNode in data['shared graph nodes']:

      # Check that the supplied structure is a dictionary.
      if not methods.checkIsDictionary(sharedNode, self.allowTermination): return

      # Define a set of information to be used in help messages.
      helpInfo = (self.name, 'shared graph nodes', sharedNode)

      # Define the attributes object.
      attributes = sharedGraphNodes()

      # Check the attributes conform to expectations.
      self.success, attributes = methods.checkAttributes(sharedNode, allowedAttributes, attributes, self.allowTermination, helpInfo)

      # If the nodeID already exists in the attributes, a node of this name has already been seen. All 
      #nodes must have a unique name.
      if attributes.id in self.sharedNodeAttributes: print('pipeline.checkSharedNodes - 6'); exit(0)

      # Also check that the node id is not the name of a task.
      if attributes.id in self.allTasks: print('pipeline.checkSharedNodes - 7'); exit(0)

      # Store the attributes.
      self.sharedNodeAttributes[attributes.id] = attributes

  # For each task in each shared graph node, ensure that the information in the configuration
  # file is complete.
  def checkSharedNodeTasks(self):

    # Define the allowed nodes attributes.
    allowedAttributes                        = {}
    allowedAttributes['pipeline']            = (str, False, True, 'pipeline')
    allowedAttributes['pipeline graph node'] = (str, False, True, 'pipelineNodeID')
    allowedAttributes['task']                = (str, False, True, 'task')
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

        #TODO INCLUDE A CHECK TO ENSURE THAT AN ALLOWED COMBINATION OF FIELDS IS PRESENT.

        # If this node contains a link to a task or a node in another pipeline, record this.
        if attributes.pipelineNodeID: self.sharedNodeAttributes[nodeID].containsNodeInAnotherPipeline = True
        if attributes.pipeline: self.sharedNodeAttributes[nodeID].containsTaskInAnotherPipeline = True

        # Store the attributes.
        self.sharedNodeAttributes[nodeID].sharedNodeTasks.append(attributes)

  # Check that defined edges are correctly included.
  def checkDefinedEdges(self, data):

    if 'connect nodes to tasks' not in data: return

    # Define the allowed attributes.
    allowedAttributes            = {}
    allowedAttributes['targets'] = (list, True, False, None)
    allowedAttributes['id']      = (str, True, True, 'id')
    allowedAttributes['sources'] = (list, True, False, None)

    # Define the allowed source attributes.
    allowedSourceAttributes                  = {}
    allowedSourceAttributes['pipeline']      = (str, False, True, 'pipeline')
    allowedSourceAttributes['task']          = (str, True, True, 'task')
    allowedSourceAttributes['task argument'] = (str, True, True, 'taskArgument')

    # Define the allowed target attributes.
    allowedTargetAttributes                  = {}
    allowedTargetAttributes['pipeline']      = (str, False, True, 'pipeline')
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

  # If termination is allowed, call errors on the observed arguments.
  def callArgumentErrors(self, nodeID, longFormArgument, shortFormArgument, observedLongFormArguments, observedShortFormArguments):
    if longFormArgument in observedLongFormArguments: self.errors.repeatedLongFormArgument(nodeID, longFormArgument)
    if shortFormArgument in observedShortFormArguments: self.errors.repeatedShortFormArgument(nodeID, longFormArgument, shortFormArgument)
    if longFormArgument and not shortFormArgument: self.errors.noShortFormArgument(nodeID, longFormArgument)
    if shortFormArgument and not longFormArgument: self.errors.noLongFormArgument(nodeID, shortFormArgument)

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

  # Get source information for edges defined in the configuration file.
  def getSources(self, node):
    try: return self.connections[node].sourceInformation
    except: return None

  # Get target information for edges defined in the configuration file.
  def getTargets(self, node):
    try: return self.connections[node].targetInformation
    except: return None

#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import fileOperations

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
class sharedNodeTaskAttributes:
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

# Define a class to store general pipeline attributes,
class pipelineConfiguration:
  def __init__(self):

    # Store the id for this pipeline.
    self.id = ''

    # The pipeline description.
    self.description = 'No description'

    # The categories the pipeline is included in for help messages.
    self.categories = []

    # The parameter set information for this pipeline.
    self.parameterSets = []

    # The tasks that the pipeline comprises. Also store all of the tasks and all of the tools
    # that are executed by the pipeline.
    self.pipelineTasks = {}
    self.allTasks      = []
    self.allTools      = []

    # The pipeline graph nodes that are shared between different tasks in the pipeline.
    self.sharedNodeAttributes = {}

    # Pipeline graph nodes that are kept as unique for a specific task,
    self.uniqueNodeAttributes = {}

    # If the pipeline contains tasks that are themselves pipelines. Store all of the pipelines
    # used in this pipeline.
    self.hasPipelineAsTask = False
    self.requiredPipelines = []

    # Store all of the unique and shared node IDs.
    self.uniqueNodeIDs = []
    self.sharedNodeIDs = []

    # If the pipeline is nested within other pipelines, the nodes associated with this pipeline
    # have an address to locate them within the graph structure. For example, if the main pipeline
    # has a task 'run' which is a pipeline, all the nodes created for this pipeline are prepended
    # with 'run.' etc. Store this address.
    self.address = None

    # It is sometimes desirable to allow all steps to be processed without termination. Other
    # times, if a problem is encountered, execution should terminate. Keep track of this.
    self.allowTermination = True

  # Open a configuration file, process the data and return.
  def getConfigurationData(self, filename):

    # Get the configuration file data.
    data = fileOperations.readConfigurationFile(filename, True)

    # Process the configuration file data.
    success = self.processConfigurationFile(data)

  # Process the configuration file.
  def processConfigurationFile(self, data):

    # Check the top level information, e.g. pipeline description.
    success = self.checkTopLevelInformation(data)

    # Parse the tasks comprising the pipeline.
    if success: success = self.checkPipelineTasks(data['pipeline tasks'])

    # Parse the unique node information.
    if success: success = self.checkUniqueNodes(data)

    # Parse the shared node information.
    if success: success = self.checkSharedNodes(data)

    # Now check that the contents of each 'node' within the shared node information is valid.
    if success: success = self.checkSharedNodeTasks()

  # Process the top level pipeline configuration information.
  def checkTopLevelInformation(self, data):

    # Define the allowed general attributes.
    allowedAttributes                       = {}
    allowedAttributes['id']                 = (str, True, True, 'id')
    allowedAttributes['description']        = (str, True, True, 'description')
    allowedAttributes['categories']         = (list, True, True, 'categories')
    allowedAttributes['parameter sets']     = (list, True, False, None)
    allowedAttributes['pipeline tasks']     = (list, True, False, None)
    allowedAttributes['shared graph nodes'] = (list, False, False, None)
    allowedAttributes['unique graph nodes'] = (list, False, False, None)

    # Keep track of the observed required values.
    observedAttributes = {}

    # Loop over all of the attributes in the configuration file.
    for attribute in data:

      # If the value is not in the allowedAttributes, it is not an allowed value and execution
      # should be terminate with an error.
      if attribute not in allowedAttributes:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkTopLevelInformation - 1'); exit(0) # invalidGeneralAttributeInConfigurationFile
        else: return False

      # Mark this values as having been observed,
      observedAttributes[attribute] = True

      # Check that the value given to the attribute is of the correct type. If the value is unicode,
      # convert to a string first.
      value = str(data[attribute]) if isinstance(data[attribute], unicode) else data[attribute]
      if allowedAttributes[attribute][0] != type(value):
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkTopLevelInformation - 2'); exit(0) # incorrectTypeInPipelineConfigurationFile
        else: return False

      # At this point, the attribute in the configuration file is allowed and of valid type. Check that 
      # the value itself is valid (if necessary) and store the value.
      if allowedAttributes[attribute][2]: setattr(self, attribute, value)

    # Having parsed all of the general attributes attributes, check that all those that are required
    # are present.
    for attribute in allowedAttributes:
      if allowedAttributes[attribute][1] and attribute not in observedAttributes:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkTopLevelInformation - 3'); exit(0) # missingGeneralAttributeInConfigurationFile
        return False

    return True

  # Check the pipeline tasks. Ensure that all of the tasks are either available tools or other pipelines.
  def checkPipelineTasks(self, data):

    # Define the allowed general attributes.
    allowedAttributes             = {}
    allowedAttributes['pipeline'] = (str, False, True, 'pipeline')
    allowedAttributes['task']     = (str, True, True, 'task')
    allowedAttributes['tool']     = (str, False, True, 'tool')

    for taskInformation in data:

      # Define a class to store task attribtues.
      attributes = taskAttributes()

      # Keep track of the observed required values.
      observedAttributes = {}

      # Loop over the included attributes.
      for attribute in taskInformation:
        value = str(taskInformation[attribute])

        if attribute not in allowedAttributes:
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkPipelineTasks - 1'); exit(0) # invalidAttributeInTasks
          return False

        # Check that the value given to the attribute is of the correct type.
        if allowedAttributes[attribute][0] != type(value):
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkPipelineTasks - 2'); exit(0) # incorrectTypeInPipelineConfigurationFile
          else: return False

        # Mark the attribute as seen.
        observedAttributes[attribute] = True

        # Store the given attribtue.
        if allowedAttributes[attribute][2]: self.setAttribute(attributes, allowedAttributes[attribute][3], value)

      # Having parsed all of the general attributes attributes, check that all those that are required
      # are present.
      for attribute in allowedAttributes:
        if allowedAttributes[attribute][1] and attribute not in observedAttributes:
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkPipelineTasks - 3', attribute); exit(0) # missingAttributeInPipelineConfigurationFile
          else: return False

      # Check that the task name is unique.
      if attributes.task in self.pipelineTasks:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkPipelineTasks - 4', attributes.task); exit(0)
        else: return False

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

    return True

  # If information on unique nodes exists, check that everything is valid.
  def checkUniqueNodes(self, data):

    # If there is not information on unique graph nodes, return.
    if 'unique graph nodes' not in data: return True

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

      # Check that the supplied structure is a dictionary.
      if not isinstance(uniqueNode, dict):
        #TODO ERROR
        if self.allowTermination: print('checkUniqueNodes - 1'); exit(0) # nodeIsNotADictionary
        else: return False

      # Define the attributes object.
      attributes = uniqueGraphNodes()

      # Keep track of the observed required values.
      observedAttributes = {}

      # Check that the node has an ID. This will be used to identify the node in error messages.
      try: nodeID = str(uniqueNode['id'])
      except:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkUniqueNodes - 2'); exit(0) # noIDInPipelineNode
        else: return False

      # Store the node ID.
      self.uniqueNodeIDs.append(nodeID)

      # Loop over all attributes in the node.
      for attribute in uniqueNode:
        if attribute not in allowedAttributes:
          # TODO ERROR
          if self.allowTermination: print('pipeline.checkUniqueNodes - 3'); exit(0) # invalidAttributeInNodes
          else: return False

        # Check that the value given to the attribute is of the correct type. If the value is unicode,
        # convert to a string first.
        value = str(uniqueNode[attribute]) if isinstance(uniqueNode[attribute], unicode) else uniqueNode[attribute]
        if allowedAttributes[attribute][0] != type(value):
          if self.allowTermination: print('pipeline.checkUniqueNodes - 4'); exit(0) # incorrectTypeInPipelineConfigurationFile
          else: return False

        # Mark the attribute as seen.
        observedAttributes[attribute] = True

        # Store the given attribtue.
        if allowedAttributes[attribute][2]: self.setAttribute(attributes, allowedAttributes[attribute][3], uniqueNode[attribute])

      # Having parsed all of the general attributes attributes, check that all those that are required
      # are present.
      for attribute in allowedAttributes:
        if allowedAttributes[attribute][1] and attribute not in observedAttributes:
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkUniqueNodes - 5'); exit(0) # missingAttributeInPipelineConfigurationFile
          else: return False

      # Store the attributes.
      self.uniqueNodeAttributes[nodeID] = attributes

    return True

  # If information on shared nodes exists, check that everything is valid.
  def checkSharedNodes(self, data):

    # If there is not information on unique graph nodes, return.
    if 'shared graph nodes' not in data: return True

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
      if not isinstance(sharedNode, dict):
        #TODO ERROR
        if self.allowTermination: print('checkSharedNodes - 1'); exit(0) # nodeIsNotADictionary
        else: return False

      # Define the attributes object.
      attributes = sharedGraphNodes()

      # Keep track of the observed required values.
      observedAttributes = {}

      # Check that the node has an ID. This will be used to identify the node in error messages.
      try: nodeID = str(sharedNode['id'])
      except:
        #TODO ERROR
        if self.allowTermination: print('pipeline.checkSharedNodes - 2'); exit(0) # noIDInPipelineNode
        else: return False

      # Store the node ID.
      self.sharedNodeIDs.append(nodeID)

      # Loop over all attributes in the node.
      for attribute in sharedNode:
        if attribute not in allowedAttributes:
          # TODO ERROR
          if self.allowTermination: print('pipeline.checkSharedNodes - 3'); exit(0) # invalidAttributeInNodes
          else: return False

        # Check that the value given to the attribute is of the correct type. If the value is unicode,
        # convert to a string first.
        value = str(sharedNode[attribute]) if isinstance(sharedNode[attribute], unicode) else sharedNode[attribute]
        if allowedAttributes[attribute][0] != type(value):
          if self.allowTermination: print('pipeline.checkSharedNodes - 4'); exit(0) # incorrectTypeInPipelineConfigurationFile
          else: return False

        # Mark the attribute as seen.
        observedAttributes[attribute] = True

        # Store the given attribtue.
        if allowedAttributes[attribute][2]: self.setAttribute(attributes, allowedAttributes[attribute][3], sharedNode[attribute])

      # Having parsed all of the general attributes attributes, check that all those that are required
      # are present.
      for attribute in allowedAttributes:
        if allowedAttributes[attribute][1] and attribute not in observedAttributes:
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkSharedNodes - 5'); exit(0) # missingAttributeInPipelineConfigurationFile
          else: return False

      # Store the attributes.
      self.sharedNodeAttributes[nodeID] = attributes

    return True

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

        # Check that the supplied structure is a dictionary.
        if not isinstance(node, dict):
          #TODO ERROR
          if self.allowTermination: print('pipeline.checkSharedNodeTasks - 1'); exit(0) # nodeIsNotADictionary
          else: return False
  
        # Define the attributes object.
        attributes = sharedNodeTaskAttributes()
  
        # Keep track of the observed required values.
        observedAttributes = {}
  
        # Loop over all attributes in the node.
        for attribute in node:
          if attribute not in allowedAttributes:
            # TODO ERROR
            if self.allowTermination: print('pipeline.checkSharedNodeTasks - 2'); exit(0) # invalidAttributeInNodes
            else: return False
  
          # Check that the value given to the attribute is of the correct type. If the value is unicode,
          # convert to a string first.
          value = str(node[attribute]) if isinstance(node[attribute], unicode) else node[attribute]
          if allowedAttributes[attribute][0] != type(value):
            if self.allowTermination: print('pipeline.checkSharedNodeTasks - 3'); exit(0) # incorrectTypeInPipelineConfigurationFile
            else: return False
  
          # Mark the attribute as seen.
          observedAttributes[attribute] = True
  
          # Store the given attribtue.
          if allowedAttributes[attribute][2]: self.setAttribute(attributes, allowedAttributes[attribute][3], str(node[attribute]))
  
        # Having parsed all of the general attributes attributes, check that all those that are required
        # are present.
        for attribute in allowedAttributes:
          if allowedAttributes[attribute][1] and attribute not in observedAttributes:
            #TODO ERROR
            if self.allowTermination: print('pipeline.checkSharedNodeTasks - 4'); exit(0) # missingAttributeInPipelineConfigurationFile
            else: return False
  
        #TODO INCLUDE A CHECK TO ENSURE THAT AN ALLOWED COMBINATION OF FIELDS IS PRESENT.

        # Store the attributes.
        self.sharedNodeAttributes[nodeID].sharedNodeTasks.append(attributes)

  # Set a value in the toolAttributes.
  def setAttribute(self, attributes, attribute, value):
    try: test = getattr(attributes, attribute)

    # If the attribute can't be set, determine the source of the problem and provide an
    # error message.
    except:

      # If the tool is not available.
      #TODO ERROR
      print('pipeline.setAttributes - 1 ', attribute); exit(0) # invalidAttributeInSetAttribute

    # Set the attribute.
    setattr(attributes, attribute, value)

    return attributes

  # Check that all references to tasks in the pipeline configuration file are valid. The task may
  # be a task in a contained pipeline and not within the pipeline being checked. The allTasks
  # list contains all of the tasks in all of the pipelines.
  def checkContainedTasks(self, allTasks, allUniqueNodeIDs, allSharedNodeIDs):

    # Check the tasks that any unique nodes point to.
    for nodeID in self.uniqueNodeAttributes.keys():

      # Get the name of the pipeline (if exists) and the task that this node points to.
      pipeline = self.getUniqueNodeAttribute(nodeID, 'pipeline')
      task     = self.getUniqueNodeAttribute(nodeID, 'task')

      # This pipeline may itself be called by an enveloping pipeline. If so, any tasks
      # will require prepending with the address of this pipeline.
      if pipeline: task = pipeline + '.' + task
      if self.address: task = self.address + '.' + task

      # If the task is not listed as one of the pipeline tasks. terminate.
      #TODO ERROR
      if task not in allTasks: print('pipeline.checkContainedTasks'); exit(0)

    # Check the tasks that shared nodes point to.
    for sharedNodeID in self.sharedNodeAttributes.keys():
      for node in self.sharedNodeAttributes[sharedNodeID].sharedNodeTasks:
        task           = self.getSharedNodeTaskAttribute(node, 'task')
        taskArgument   = self.getSharedNodeTaskAttribute(node, 'taskArgument')
        pipeline       = self.getSharedNodeTaskAttribute(node, 'pipeline')
        pipelineNodeID = self.getSharedNodeTaskAttribute(node, 'pipelineNodeID')

        # If the shared node is a defined node in another pipeline, ensure that no task or
        # argument are supplied. If they are terminate, as there is more information than
        # required, which suggests an error in the configuration file construction. The pipeline
        # in which the node resides is required.
        if pipelineNodeID:
          #TODO ERROR
          if task or taskArgument: print('pipeline.checkContainedTasks - 2'); exit(0)
          if not pipeline: print('pipeline.checkContainedTasks - 3'); exit(0)
          pipelineNodeID = pipeline + '.' + pipelineNodeID
          if self.address: pipelineNodeID = self.address + '.' + pipelineNodeID

          # If the task is not listed as one of the pipeline tasks. terminate.
          #TODO ERROR
          if pipelineNodeID not in allUniqueNodeIDs and pipelineNodeID not in allSharedNodeIDs: print('pipeline.checkContainedTasks - 4'); exit(0)

        # If the shared node is a task in another pipeline, check that the task exists.
        elif pipeline:
          task = pipeline + '.' + task
          if self.address: task = self.address + '.' + task
          #TODO ERROR
          if task not in allTasks: print('pipeline.checkContainedTasks - 5'); exit(0)

        # Finally, if the shared node points to a task from this pipeline.
        else:
          if self.address: task = self.address + '.' + task
          #TODO ERROR
          if task not in allTasks: print('pipeline.checkContainedTasks - 6'); exit(0)

  # Get a pipeline task attribute.
  def getTaskAttribute(self, task, attribute):
    try: return getattr(self.pipelineTasks[task], attribute)
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
  def getSharedNodeTaskAttribute(self, node, attribute):
    try: return getattr(node, attribute)
    except: return None

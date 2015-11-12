#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import fileHandling
import parameterSets
import pipelineConfiguration
import pipelineConfigurationErrors as pce
import stringOperations as strOps
import toolConfiguration

import json
import os
import sys

# Define a class to store task attributes.
class superpipelineClass:
  def __init__(self, pipeline):

    # Define errors.
    self.pipelineErrors = pce.pipelineErrors()

    # Record the name of the top level pipeline, e.g. that defined on the command line.
    self.pipeline = None

    # The number of tiers in the super pipeline.
    self.numberOfTiers = 1

    # Store all of the pipeline configuration files comprising the superpipeline in a
    # dictionary, indexed by the name of the pipeline.
    self.pipelineConfigurationData = {}

    # Store information on all the constituent tools.
    self.toolConfigurationData = {}

    # Store all the tasks in the superpipeline along with the tools,
    self.tools = []
    self.tasks = {}

    # Store the unique and shared node IDs in all the pipeline.
    self.uniqueNodeIds = []
    self.sharedNodeIds = []

    # Store all of the constituent pipeline with their tier and also all the pipelines indexed
    # by tier.
    self.pipelinesByTier = {}
    self.tiersByPipeline = {}

    # Keep track of the tasks that should be included in a plot.
    self.tasksInPlot = {}

    # Associate a random string with the graph. This will be used in any makefiles and intermediate
    # files to ensure simultaneous executions of gkno will not produced filename conflicts.
    self.randomString = strOps.getRandomString(8)

  # Starting from the defined pipeline, process and validate the configuration file contents,
  # then dig down through all the nested pipelines and validate their configuration files.
  def getNestedPipelineData(self, files, path, userPath, filename):

    # Get the top level pipeline configuration file data.
    pipeline = pipelineConfiguration.pipelineConfiguration()
    pipeline.getConfigurationData(filename)
    pipeline.path = filename.rstrip(str(pipeline.name + '.json'))[:-1]
    self.pipelineConfigurationData[pipeline.name] = pipeline

    # Store the name of the tier 1 pipeline (e.g. the pipeline selected on the command line).
    self.tiersByPipeline[pipeline.name] = 1
    self.pipelinesByTier[1]             = [pipeline.name]
    self.pipeline                       = pipeline.name

    # Now dig into the nested pipeline and build up the superpipeline structure.
    tier = 2
    checkForNestedPipelines = True
    while checkForNestedPipelines:
      tierHasNestedPipeline = False
      for currentPipelineName in self.pipelinesByTier[tier - 1]:
        currentPipeline = self.pipelineConfigurationData[currentPipelineName]

        # Check for external parameter sets for this pipeline.
        externalFilename = str(currentPipeline.path + '/' + currentPipeline.name + '-parameter-sets.json')

        # Get the configuration file data.
        data                  = fileHandling.fileHandling.readConfigurationFile(externalFilename, False)
        externalParameterSets = parameterSets.parameterSets()

        # If the external parameter set file exists, copy the parameter sets to the current pipeline configuration
        # data and mark them as external.
        try: parameterSetData = data['parameter sets']
        except: parameterSetData = None
        if parameterSetData:
          if externalParameterSets.checkParameterSets(parameterSetData, False, currentPipelineName, False):
            for parameterSet in externalParameterSets.sets.keys():
              if parameterSet in currentPipeline.parameterSets.sets.keys():
                externalParameterSets.errors.externalSetRepeat(currentPipelineName, parameterSet)
              externalParameterSets.sets[parameterSet].isExternal = True
              currentPipeline.parameterSets.sets[parameterSet] = externalParameterSets.sets[parameterSet]
  
        # If the pipeline contains a pipeline as a task, process the configuration file for that
        # pipeline and add to the pipelines in the current tier.
        if currentPipeline.hasPipelineAsTask:
          tierHasNestedPipeline = True
          for taskPointingToNestedPipeline, nestedPipeline in currentPipeline.requiredPipelines:
            pipeline = pipelineConfiguration.pipelineConfiguration()

            # Check that the requried pipeline is available (first check in the user defined configuration
            # file path if defined).
            isPipeline = False
            if nestedPipeline in files.userConfigurationFiles:
              configurationPath = str(userPath)
              externalFilename  = str(configurationPath + '/' + nestedPipeline + '-parameters-sets.json')
              filename          = str(configurationPath + '/' + nestedPipeline + '.json')
              isPipeline        = pipeline.checkConfigurationFile(filename)

            # If there is a pipeline configuration file with the given name in the user defined configuration
            # file directory, use this file. Otherwise, default to the standard gkno configuration files.
            if not isPipeline:
              configurationPath = str(path)
              externalFilename  = str(path + '/' + nestedPipeline + '-parameters-sets.json')
              filename          = str(path + '/' + nestedPipeline + '.json')

            # Process the configuration file.
            pipeline.getConfigurationData(filename)
            pipeline.path = configurationPath
  
            # Get the configuration file data.
            externalData = fileHandling.fileHandling.readConfigurationFile(externalFilename, False)
            if externalData: print('TEST HANDLE EXTERNAL PARAMETER SET FOR NESETD PIPELINE', externalFilename, externalData); exit(0)

            # Construct the address of the task.
            pipeline.address = '' if currentPipeline.address == None else str(currentPipeline.address) + '.'
            pipeline.address += str(taskPointingToNestedPipeline)
            self.pipelineConfigurationData[pipeline.address] = pipeline

            # Store the pipeline name with the tier it's on.
            if tier not in self.pipelinesByTier: self.pipelinesByTier[tier] = []
            self.pipelinesByTier[tier].append(pipeline.address)
            self.tiersByPipeline[pipeline.address] = tier

        # Increment the tier. If no pipelines in the just processed tier had a nested pipeline, the
        # loop can end.
        tier += 1
        if not tierHasNestedPipeline: checkForNestedPipelines = False
  
  # Check that none of the pipeline arguments conflict with gkno arguments.
  def checkForArgumentConflicts(self, longForms, shortForms):
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]:
        for longFormArgument in self.pipelineConfigurationData[pipeline].longFormArguments:
          shortFormArgument = self.pipelineConfigurationData[pipeline].longFormArguments[longFormArgument].shortFormArgument
          if longFormArgument in longForms: self.pipelineErrors.conflictWithGknoArguments(longFormArgument, shortFormArgument, isLongForm = True)
          if shortFormArgument in shortForms: self.pipelineErrors.conflictWithGknoArguments(longFormArgument, shortFormArgument, isLongForm = False)

  # Get all of the tools from each pipeline in the super pipeline and store them.
  def setTools(self):
    for tier in self.pipelinesByTier:
      for pipelineName in self.pipelinesByTier[tier]:
        pipeline = self.pipelineConfigurationData[pipelineName]

        # Loop over all of the pipeline tasks.
        for task in pipeline.getAllTasks():

          # Get the pipeline relative address of the task.
          taskAddress = str(pipeline.address + '.' + task) if pipeline.address else str(task)

          # Get the tool for the task.
          tool = pipeline.getTaskAttribute(task, 'tool')

          # If this tool is not yet in the tools list, include it.
          if tool not in self.tools: self.tools.append(tool)

          # Store the task with its tool.
          self.tasks[taskAddress] = tool

          # Store whether the task should be included in a plot.
          self.tasksInPlot[taskAddress] = not pipeline.getTaskAttribute(task, 'omitFromReducedPlot')

        # Store the unique and shared node IDs for each pipeline.
        self.uniqueNodeIds += [str(pipeline.address + '.' + nodeId) if pipeline.address else str(nodeId) for nodeId in pipeline.getUniqueNodeIds()]
        self.sharedNodeIds += [str(pipeline.address + '.' + nodeId) if pipeline.address else str(nodeId) for nodeId in pipeline.getSharedNodeIds()]

  # Check that all references to tasks in the pipeline configuration file are valid. The task may
  # be a task in a contained pipeline and not within the pipeline being checked. The allTasks
  # list contains all of the tasks in all of the pipelines.
  def checkContainedTasks(self):

    # Loop over all the tiers in the super pipeline.
    for tier in self.pipelinesByTier:
      for pipelineName in self.pipelinesByTier[tier]:
        pipelineObject = self.pipelineConfigurationData[pipelineName]

        # Check the tasks that any unique nodes point to.
        for nodeId in pipelineObject.uniqueNodeAttributes.keys():
    
          # Get the name of the task that this node points to. This is the full address of the
          # task and so may live in a nested pipeline.
          task = pipelineObject.getUniqueNodeAttribute(nodeId, 'task')
    
          # This pipeline may itself be called by an enveloping pipeline. If so, any tasks
          # will require prepending with the address of this pipeline.
          if pipelineObject.address: task = pipelineObject.address + '.' + task

          # If the node points to a node in an external pipeline, get the address of the node.
          externalNodeId = pipelineObject.getUniqueNodeAttribute(nodeId, 'nodeId')
          if externalNodeId:
            if pipelineObject.getUniqueNodeAttribute(nodeId, 'taskArgument'): print('superpipeline.checkContainedTasks - 1'); exit(0)

            # Define the node addres.
            nodeAddress = task + '.' + externalNodeId

            # If the nodeAddress is not an available node in the pipeline, there has been a problem.
            if nodeAddress not in self.uniqueNodeIds + self.sharedNodeIds:

              # If the task is valid, but the node address is not, the supplied external node id is invalid.
              if task in pipelineObject.pipelineTasks.keys():
                externalPipeline = pipelineObject.pipelineTasks[task].pipeline
                if externalPipeline: pipelineObject.errors.invalidNodeForExternalPipeline(pipelineName, 'unique', nodeId, task, externalPipeline, externalNodeId)
                else: pipelineObject.errors.externalNodeForTask(pipelineName, 'unique', nodeId, task, externalNodeId)
              else: pipelineObject.errors.invalidTaskInNode(pipelineName, 'unique', nodeId, nodeAddress)
    
          # If the task is not listed as a task for the pipeline, there are a couple of potential problems.
          elif task not in self.tasks:

            # If the task is listed in the pipelineTasks, but isn't in self.tasks, then the task could be running
            # another pipeline. If this is the case, the external node needs to be set.
            if task in pipelineObject.pipelineTasks.keys(): pipelineObject.errors.missingNodeIdForPipelineTask(pipelineName, 'unique', nodeId, task)

            # If the task is not a pipeline and isn't present in the tasks, then the task doesn't exist.
            else: pipelineObject.errors.invalidTaskInNode(pipelineName, 'unique', nodeId, task)
    
        # Check the tasks that shared nodes point to.
        for sharedNodeId in pipelineObject.sharedNodeAttributes.keys():
          for node in pipelineObject.sharedNodeAttributes[sharedNodeId].sharedNodeTasks:
            task           = pipelineObject.getNodeTaskAttribute(node, 'task')
            taskArgument   = pipelineObject.getNodeTaskAttribute(node, 'taskArgument')
            externalNodeId = pipelineObject.getNodeTaskAttribute(node, 'externalNodeId')

            # Add the address of the current pipeline if this is not the top tier pipeline.
            if pipelineObject.address: task = pipelineObject.address + '.' + task

            # If the externalNode is set, the node is in an external pipeline and is being pointed
            # to directly. Ensure that the task argument is not also defined and then construct the
            # name of the graph node to test for existence.
            if externalNodeId:
              if taskArgument: print('superpipeline.checkContainedTasks - 2'); exit(0)

              # Define the node addres.
              nodeAddress = task + '.' + externalNodeId

              # If the nodeAddress is not an available node in the pipeline, there has been a problem.
              if nodeAddress not in self.uniqueNodeIds + self.sharedNodeIds:

                # If the task is valid, but the node address is not, the supplied external node id is invalid.
                if task in pipelineObject.pipelineTasks.keys():
                  externalPipeline = pipelineObject.pipelineTasks[task].pipeline
                  if externalPipeline: pipelineObject.errors.invalidNodeForExternalPipeline(pipelineName, 'shared', sharedNodeId, task, externalPipeline, externalNodeId)
                  else: pipelineObject.errors.externalNodeForTask(pipelineName, 'shared', sharedNodeId, task, externalNodeId)
                else: pipelineObject.errors.invalidTaskInNode(pipelineName, 'shared', sharedNodeId, nodeAddress)
    
            # If the task is not listed as a task for the pipeline, there are a couple of potential problems.
            elif task not in self.tasks:
  
              # If the task is listed in the pipelineTasks, but isn't in self.tasks, then the task could be running
              # another pipeline. If this is the case, the external node needs to be set.
              if task in pipelineObject.pipelineTasks.keys(): pipelineObject.errors.missingNodeIdForPipelineTask(pipelineName, 'shared', sharedNodeId, task)
  
              # If the task is not a pipeline and isn't present in the tasks, then the task doesn't exist.
              else: pipelineObject.errors.invalidTaskInNode(pipelineName, 'shared', sharedNodeId, task)

  # Given a pipeline name and a node ID, return the node type (i.e. unique or shared).
  def getNodeType(self, pipeline, nodeId):

    # Define the node address.
    address = pipeline + '.' + nodeId
    if address in self.uniqueNodeIds: return 'unique'
    elif address in self.sharedNodeIds: return 'shared'
    else: return None

  # Loop over the list of required tools, open and process their configuration files and store.
  def addTools(self, files, gknoPath, userPath):
    for tool in self.getTools():
      toolData = toolConfiguration.toolConfiguration()

      # First check to see if a configuration file of this name is available in the user defined
      # configuration files directory, if specified.
      isTool = False
      if tool in files.userConfigurationFiles:
        filename = str(userPath + '/' + tool + '.json')
        isTool   = toolData.checkConfigurationFile(filename)

      # If the tool is not available in the user defined path, default to the standard gkno path.
      if not isTool: filename = str(gknoPath + '/' + tool + '.json')

      # Check that the tool exists. If not, terminate since the configuration file will not be found.
      if tool not in files.tools: self.pipelineErrors.invalidTool(tool)

      # Get the configuration file data.
      toolData.getConfigurationData(tool, filename)
      self.toolConfigurationData[tool] = toolData

  # Check that all tool arguments reference in pipeline configuration files are valid.
  def checkArgumentsInPipeline(self):
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]: 

        # Get a list of all the tool arguments contained in each pipeline.
        arguments = self.pipelineConfigurationData[pipeline].getToolArguments()

        # Check that each argument is valid.
        for nodeType, nodeId, task, argument in arguments:

          # Get the tool associated with the task.
          address     = self.pipelineConfigurationData[pipeline].address + '.' if self.pipelineConfigurationData[pipeline].address else ''
          taskAddress = str(address + task)
          tool        = self.tasks[taskAddress]

          # Get the long form of the supplied argument.
          longFormArgument = self.toolConfigurationData[tool].getLongFormArgument(argument)

          # If the long form does not exist, the argument in the pipeline configuration file is not valid.
          if not longFormArgument:
            self.pipelineConfigurationData[pipeline].errors.invalidToolArgument(pipeline, nodeType, nodeId, task, tool, argument)

  #
  def checkStreams(self, graph):

    # Loop over all of the pipelines in the superpipeline.
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]:
        data = self.getPipelineData(pipeline)

        # Loop over all tasks defined for the pipeline:
        for task in data.pipelineTasks:

          # Identify tasks that run pipelines.
          if data.pipelineTasks[task].pipeline: 

            # If this task is marked as accepting a stream as input, 
            if data.getTaskAttribute(task, 'isInputStream'):

              # Find the first task in the pipeline workflow associated with this nested pipeline.
              isStreamSet = False
              for pipelineTask in graph.workflow:
                if pipelineTask.startswith(task):
                  isStreamSet = True
                  graph.setGraphNodeAttribute(pipelineTask, 'isInputStream', True)

                  # If the task is marked as greedy, reset it to not be greedy. If accepting a stream, this
                  # is not permitted. The value can be set as greedy since the pipeline which the task is
                  # running could be greedy if run in isolation and not as part of a superpipeline.
                  graph.setGraphNodeAttribute(pipelineTask, 'isGreedy', False)
                  break

              # If no task was found in the pipeline, terminate with an error.
              #TODO ERROR
              if not isStreamSet: print('NO STREAM SET - superpipeline.checkStreams'); exit(1)

            # TODO HANDLE PIPELINES WHOSE OUTPUT IS A STREAM.
            if data.getTaskAttribute(task, 'isOutputStream'): 

              # Find the first task in the pipeline workflow associated with this nested pipeline.
              isStreamSet = False
              for pipelineTask in reversed(graph.workflow):
                if pipelineTask.startswith(task):
                  isStreamSet = True
                  graph.setGraphNodeAttribute(pipelineTask, 'isOutputStream', True)
                  break

              # If no task was found in the pipeline, terminate with an error.
              #TODO ERROR
              if not isStreamSet: print('NO STREAM SET - superpipeline.checkStreams'); exit(1)

  # Determine which nodes are intermediate (e.g. are listed in the nodes section of the pipeline configuration file 
  # with the 'delete files' set).
  def determineFilesToDelete(self, graph):

    # Loop over all pipelines in the superpipeline.
    for tier in self.pipelinesByTier:
      for pipeline in self.pipelinesByTier[tier]:

        # Loop over all of the nodes.
        for nodeId in self.pipelineConfigurationData[pipeline].getUniqueNodeIds():
          address     = self.pipelineConfigurationData[pipeline].address
          nodeAddress = str(address + '.' + nodeId) if address else str(nodeId)

          # Check if the file is marked for deletion.
          if self.pipelineConfigurationData[pipeline].getUniqueNodeAttribute(nodeId, 'isDelete'):
            for graphNodeId in graph.configurationFileToGraphNodeId[nodeAddress]:
              graph.setGraphNodeAttribute(graphNodeId, 'isIntermediate', True)

              # Check if the temp string should be omitted.
              noRandomString = False
              for predecessorID in graph.graph.predecessors(graphNodeId):
                instructions = graph.getArgumentAttribute(predecessorID, graphNodeId, 'constructionInstructions')
                if 'no temp string' in instructions:
                  if instructions['no temp string']:
                    noRandomString = True
                    break
              if noRandomString: randomString = ''
              else: randomString = self.randomString + '.'

              # Prepend all intermediate files (and child nodes) with the superpipeline random string.
              updatedValues = []
              for value in graph.getGraphNodeAttribute(graphNodeId, 'values'): updatedValues.append(randomString + value)
              graph.setGraphNodeAttribute(graphNodeId, 'values', updatedValues)

              # Handle child nodes.
              for child in graph.getGraphNodeAttribute(graphNodeId, 'children'):
                updatedValues = []
                for value in graph.getGraphNodeAttribute(child, 'values'): updatedValues.append(randomString + value)
                graph.setGraphNodeAttribute(child, 'values', updatedValues)

          # Check if the file is marked as having additional text to add when filenames are constructed.
          text = self.pipelineConfigurationData[pipeline].getUniqueNodeAttribute(nodeId, 'addTextToFilename')
          if text:
            for graphNodeId in graph.configurationFileToGraphNodeId[nodeAddress]: graph.setGraphNodeAttribute(graphNodeId, 'addTextToFilename', text)

  #######################################################
  ## Methods to get information from the superpipeline ##
  #######################################################

  # Return all the tools used in the superpipeline.
  def getTools(self):
    return self.tools

  # Return the tool used for a task. The task is the full address, so may well be a task
  # buried within enclosed pipelines.
  def getTool(self, taskAddress):

    # Consider a task from a tier two pipeline. This would have an address of the form,
    # 'pipeline.task'. The tier one pipeline would just have the name of the task in the pipeline.
    namesList    = taskAddress.split('.')
    task         = namesList.pop()
    pipelineName = '.'.join(namesList) if namesList else self.pipeline

    # Get the pipeline configuration data for this pipeline.
    try: return self.pipelineConfigurationData[pipelineName].getTaskAttribute(task, 'tool')
    except: return False

  # Return data for a specified tool.
  def getToolData(self, tool):
    try: return self.toolConfigurationData[tool]
    except: return False

  # Get a parameter set for a tool.
  def getToolParameterSet(self, tool, parameterSet):
    try: return self.toolConfigurationData[tool].parameterSets.sets[parameterSet]
    except: return None

  # Get a tool argument attribute.
  def getToolArgumentAttribute(self, tool, argument, attribute):
    try: return self.toolConfigurationData[tool].getArgumentAttribute(argument, attribute)
    except: return False

  # Return all the arguments for a tool.
  def getToolArguments(self, tool):
    return self.toolConfigurationData[tool].arguments

  # Return pipeline data.
  def getPipelineData(self, pipeline):
    try: return self.pipelineConfigurationData[pipeline]
    except: return False

  # Get a list of available parameter sets.
  def getAvailablePipelineParameterSets(self, pipeline):
    try: return self.pipelineConfigurationData[pipeline].parameterSets.sets.keys()
    except: return [None]

  # Get a parameter set for a pipeline.
  def getPipelineParameterSet(self, pipeline, parameterSet):
    try: return self.pipelineConfigurationData[pipeline].parameterSets.sets[parameterSet]
    except: return None

  # Get a node attribute.
  def getNodeAttribute(self, nodeId, attribute):

    # Consider a task from a tier two pipeline. This would have an address of the form,
    # 'pipeline.task'. The tier one pipeline would just have the name of the task in the pipeline.
    namesList    = nodeId.split('.')
    nestedNodeId = namesList.pop()
    pipelineName = '.'.join(namesList) if namesList else self.pipeline
    nodeType     = self.getNodeType(pipelineName, nestedNodeId)

    # If this is a unique node, get the attribute.
    if nodeType == 'unique':
      try: return self.pipelineConfigurationData[pipelineName].getUniqueNodeAttribute(nestedNodeId, 'description')
      except: return False

    # If this is a shared node, get the attribute.
    if nodeType == 'shared':
      try: return self.pipelineConfigurationData[pipelineName].getSharedNodeAttribute(nestedNodeId, 'description')
      except: return False

#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class pipelineErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '7'

  ##################################
  ## Errors with top level fields ##
  ##################################

  # If the configuration file type (tool or pipeline) has not been defined.
  def noConfigurationType(self, name):
    self.text.append('Error processing pipeline configuration file: ' + name + '.json.')
    self.text.append('All gkno configuration files are required to contain the \'configuration type\' field. This can take the value \'tool\' ' + \
    'or \'pipeline\' and is used to ensure that it is possible to distinguish between tool and pipeline configuration files.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the configuration file type is not set to pipeline.
  def invalidConfigurationType(self, name, configurationType):
    self.text.append('Error processing configuration file: ' + name + '.json.')
    self.text.append('All gkno configuration files are required to contain the \'configuration type\' field. The configuration file \'' + name + \
    '.json\' is being processed as a pipeline, however, the type is listed as \'' + configurationType + '\'. Please ensure that \'' + name + \
    '\' is a pipeline and not a tool, and that the configuration file type is correctly defined within the configuration file (i.e. the ' + \
    'configuration type is set to \'pipeline\').')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ###################################
  ## Errors with the tasks section ##
  ###################################

  # Invalid tool.
  def invalidTool(self, tool):
    self.text.append('Invalid tool in pipeline tasks.')
    self.text.append('The pipeline tasks section of the pipeline configuration file contains a user defined task name and the tool or ' + \
    'pipeline with which it is associated. In this section, the tool \'' + tool + '\' is defined, but this is not a tool within gkno. ' + \
    'Please check the pipeline configuration file and ensure that all defined tasks point to valid tools or pipelines.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If two tasks have been given the same name.
  def repeatedTaskName(self, pipeline, task):
    self.text.append('Repeated task name in pipeline: ' + pipeline + '.')
    self.text.append('Each task in the pipeline is defined in the \'pipeline tasks\' section of the pipeline configuration file. Each task name must be ' + \
    'unique so that there is no ambiguity about how to construct the pipeline graph, however, multiple tasks in this section have been given the name \'' + \
    task + '\'. Please ensure that all task names in the pipeline configuration file are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a configuration file contains has repeated definitions of the same long form argument.
  def repeatedLongFormArgument(self, nodeId, longFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeId + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. This argument has already been defined in the configuration file. Please ensure that all ' + \
    'arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a configuration file contains has repeated definitions of the same short form argument.
  def repeatedShortFormArgument(self, nodeId, longFormArgument, shortFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeId + '\' which defines the ' + \
    'short form argument \'' + shortFormArgument + '\' associated with the long form argument \'' + longFormArgument + '\'. This argument has ' + \
    'already been defined in the configuration file. Please ensure that all arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a long form argument is defined with no short form.
  def noShortFormArgument(self, nodeId, longFormArgument):
    self.text.append('No defined short form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeId + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. There is no short form argument associated with this, however. Please ensure that all ' + \
    'nodes in the configuration file defining arguments contain both a short and long form version of the argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a short form argument is defined with no long form.
  def noLongFormArgument(self, nodeId, shortFormArgument):
    self.text.append('No defined long form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeId + '\' which defines the ' + \
    'short form argument \'' + shortFormArgument + '\'. There is no long form argument associated with this, however. Please ensure that all ' + \
    'nodes in the configuration file defining arguments contain both a short and long form version of the argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A pipeline long form argument conflicts with a gkno argument.
  def conflictWithGknoArguments(self, longFormArgument, shortFormArgument, isLongForm):
    self.text.append('Pipeline argument conflicts with a gkno argument.')

    # If a long form argument conflicts.
    if isLongForm:
      self.text.append('The pipeline argument \'' + longFormArgument + '\' is also a gkno argument. Please modify the pipeline configuration ' + \
      'file such that all arguments are unique.')

    # If a short form argument conflicts.
    else:
      self.text.append('The pipeline argument \'' + longFormArgument + '\' has the short form \'' + shortFormArgument + '\'. This short form is ' + \
      'shared with the short form version of a gkno argument. Please modify the pipeline configuration file such that all arguments (both the ' + \
      'long and short forms are unique.')

    # Write out the error and terminate.
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A node ID is also the name of a task.
  def nodeIdIsTaskID(self, name, node, id):
    self.text.append('Node ID conflicts with a task ID.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains a node in the \'' + node + '\' section with the ' + \
    'id \'' + id + '\'. This is also the name of a task in the pipeline. All the task names and node ids within a single configuration ' + \
    'file must be unique. Please amend the configuration file to make sure that all of the ids are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a task argument is listed as greedy, but the argument is not a valid argument for the tool that the task uses.
  def invalidGreedyArgument(self, name, task, tool, argument):
    self.text.append('Invalid greedy argument.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains information for the task \'' + task + '\', which ' + \
    'uses the tool \'' + tool + '\'. The configuration file identifies the argument \'' + argument + '\' as being greedy, but this argument ' + \
    'is not a valid argument for the tool. Please ensure that the correct argument has been supplied as a greedy argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a task argument is listed as greedy, but the argument is not identified as accepting multiple values.
  def greedySingleValueArgument(self, name, task, tool, argument):
    self.text.append('Invalid greedy argument.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains information for the task \'' + task + '\', which ' + \
    'uses the tool \'' + tool + '\'. The configuration file identifies the argument \'' + argument + '\' as being greedy, but this argument ' + \
    'is not listed as accepting multiple values in the tool configuration file. Please ensure that the correct argument has been supplied as ' + \
    'a greedy argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a task is marked as being terminated if there are no files to consolidate, but the task is not marked as a consolidating task.
  def terminateConsolidateError(self, name, task):
    self.text.append('Invalid termination instructions.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains information for the task \'' + task + '\'. This task has ' + \
    'the attribute \'terminate if no consolidation\' set, but this attribute is only valid for tasks that also have \'consolidate divisions\' set ' + \
    'to true, which this task does not. Please correct the errors in the pipeline configuration file.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If an invalid set of streaming instructions is requested.
  def invalidStreamSet(self, pipeline, task, name, validSets, isInput):
    text = 'input' if isInput else 'output'
    self.text.append('Invalid ' + text + ' streaming instruction set.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains information for the task \'' + task + '\'. This task ' + \
    'deals with streaming files and, in particular, the ' + text + ' stream has the instruction set \'' + name + '\' specified. This is an invalid ' + \
    'set of instructions; the valid values are:')
    self.text.append('\t')
    for setName in validSets: self.text.append('\t' + setName)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  #############################################
  ## Errors in the terminate pipeline section #
  #############################################

  # If a node in the 'replace nodes' section is invalid.
  def invalidNodeInTermination(self, name, nodeId, text):
    self.text.append('Invalid node Id in the \'terminate pipeline\' section.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains information in the \'terminate pipeline\' section ' + \
    'that describes conditions and instructions for creating a pipeline that doesn\'t use all of the defined tasks. In the \'replace nodes\' ' + \
    'section, one of the \'' + text + '\' nodes (' + nodeId + ') is invalid for the pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  #####################################
  ## Errors in the arguments section ##
  #####################################

  # A node id supplied with a pipeline argument is not valid.
  def invalidNodeInArgument(self, pipeline, argument, address, category):
    self.text.append('Invalid node address supplied with argument.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains information in the \'' + category + '\' section ' + \
    'of \'arguments\' for the argument \'' + argument + '\'. This argument is defined as pointing to the node with address \'' + \
    address + '\', but this address does not point to a valid node in the configuration file. Please ensure that the node address provided ' + \
    'with the argument is the ID of one of the nodes in the unique or shared nodes of the configuration file. Note that if the pipeline contains ' + \
    'tasks that are themselves pipelines, this address could be pointing to a node in one of the nested configuration files.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A long form argument is defined multiple times.
  def repeatedLongFormArgument(self, helpInfo):
    self.text.append('Repeated long form argument in pipeline configuration file.')
    self.text.append('The configuration file for pipeline \'' + helpInfo[0] + '\' contains information for a number of pipeline arguments. The \'' + \
    helpInfo[1] + '\' section contains information for the argument \'' + helpInfo[2] + '\' but this long form argument has already been defined ' + \
    'in the configuration file. Please ensure that all arguments in the configuration file are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A short form argument is defined multiple times.
  def repeatedShortFormArgument(self, helpInfo):
    self.text.append('Repeated short form argument in pipeline configuration file.')
    self.text.append('The configuration file for pipeline \'' + helpInfo[0] + '\' contains information for a number of pipeline arguments. The \'' + \
    helpInfo[1] + '\' section contains information for the argument \'' + helpInfo[2] + '\' but this short form argument has already been defined ' + \
    'in the configuration file. Please ensure that all arguments in the configuration file are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If an argument shares a name with a pipeline task.
  def argumentIsTask(self, longFormArgument, shortFormArgument, isLongForm):
    text = 'long' if isLongForm else 'short'
    self.text.append('A pipeline argument shares a name with a pipeline task.')
    self.text.append('The user is permitted to define the name of a pipeline task on the command line in order to set parameters for that task ' + \
    'that have not been given specific pipeline arguments. In order for this to work, no arguments for the pipeline may share a name with a ' + \
    'pipeline task. There is a defined pipeline argument \'' + longFormArgument + ' (' + shortFormArgument + ')\', where the ' + text + ' ' + \
    'form of the argument is the name of a pipeline task. Please change the name of the pipeline task or the argument to remove this conflict')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##########################################
  ## Errors in the unique or shared nodes ##
  ##########################################

  # A configuraiton node supplies an argument to a task which is running a pipeline and the node within the pipeline is not specified.
  def missingNodeIdForPipelineTask(self, pipeline, nodeType, nodeId, task):
    self.text.append('Invalid information in configuration file node.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeId + '\' in the \'' + \
    nodeType + ' graph nodes\' section. This node connects with the task \'' + task + '\', which is a task that itself runs a pipeline. ' + \
    'In this case, the node id of the node in the associated pipeline needs to supplied (and not task argument information). The node id ' + \
    'has not been supplied in this case. Please check the configuration file and ensure that the correct information is provided.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # An external node id is invalid.
  def invalidNodeForExternalPipeline(self, pipeline, nodeType, nodeId, task, externalPipeline, externalNodeId):
    if not externalPipeline: externalPipeline = 'bob'
    self.text.append('Invalid external node id in configuration file node.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeId + '\' in the \'' + \
    nodeType + ' graph nodes\' section. This node connects with the task \'' + task + '\', which is a task that itself runs the pipeline ' + \
    '\'' + externalPipeline + '\'. The node id \'' + externalNodeId + '\' is supplied as the node within the external pipeline with which ' + \
    'to connect, but this is not a valid node for the pipeline. Please check that all information in the configuration file is correct.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # An external node id is provided for a task that runs a tool.
  def externalNodeForTask(self, pipeline, nodeType, nodeId, task, externalNodeId):
    self.text.append('Invalid external node id in configuration file node.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeId + '\' in the \'' + \
    nodeType + ' graph nodes\' section. This node connects with the task \'' + task + '\', which is a task that runs a tool. When this ' + \
    'is the case, the \'task argument\' field must also be present to define which of the tools arguments this node connects with. Instead, ' + \
    'the \'node id\' field has been provided. This is only valid for tasks that themselves run pipelines.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A supplied task is not valid.
  def invalidTaskInNode(self, pipeline, nodeType, nodeId, task):
    self.text.append('Invalid task in configuration file node.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeId + '\' in the \'' + \
    nodeType + ' graph nodes\' section. Within this node, the task \'' + task + '\' is used, but this task has not been defined in the ' + \
    '\'pipeline tasks\' section of the configuration file and consequently is not valid. Please check that all tasks in the configuration ' + \
    'file are valid for the pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A configuration file node contains a tool argument that is not valid.
  def invalidToolArgument(self, pipeline, nodeType, nodeId, task, tool, argument):
    self.text.append('Invalid tool argument.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeId + '\' in the \'' + \
    nodeType + ' graph nodes\' section. Within this node, the task \'' + task + '\' which uses the tool \'' + tool + '\' is associated ' + \
    'with the argument \'' + argument + '\', but this argument is not valid for the tool. Please check that all of the tool arguments ' + \
    'in the pipeline configuration file are valid for the tools they are linked to.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a node has a non-unique id.
  def repeatedNodeId(self, helpInfo):
    self.text.append('Repeated pipeline node id.')
    self.text.append('The configuration file for the pipeline \'' + helpInfo[0] + '\' contains a node in the \'' + helpInfo[1] + '\' section ' + \
    'with the same id (' + helpInfo[2] + ') as another node in the pipeline. All nodes must have unique ids in order to construct the ' + \
    'pipeline graph. Please ensure that all nodes defined in the configuration file are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a node has the same id as a task.
  def nodeIdIsTaskId(self, nodeType, helpInfo):
    self.text.append('Configuration file node has the same id as a task.')
    self.text.append('A node in the \'' + helpInfo[1] + '\' section of the pipeline configuration file for pipeline \'' + helpInfo[0] + \
    '\' has the id \'' + helpInfo[2] + '\'. This is the same id as a task defined in the \'pipeline tasks\' section. All the node ids ' + \
    'in the configuration file (across all task, unique nodes and shared nodes) must be unique. Please update the ids to ensure that they ' + \
    'are all unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##################################
  ## Errors with connecting nodes ##
  ##################################

  # A node connection references a non-existent node.
  def invalidNodeConnection(self, source, target, text):
    self.text.append('Error with node connections.')
    self.text.append('In the \'connect nodes\' section of the pipeline configuration file, a connection is defined between the nodes \'' + \
    source + '\' and \'' + target + '\'. The ' + text + ' node is not a valid node in the graph. Please ensure that all of the connections ' + \
    'are defined between a valid pair of graph nodes.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##################################################
  ## Errors generated while dealing with streams. ##
  ##################################################

  # If a task is marked as outputting to a stream, but has no argument marked as
  # being able to output to a stream.
  def noOutputStreamArgument(self, task, tool):
    self.text.append('Error with output stream.')
    self.text.append('The task \'' + task + '\', using the tool \'' + tool + '\' is marked as outputting to a stream in the \'pipeline ' + \
    'tasks\' section of the configuration file, but no output arguments are identified with streaming outputs. Please check that this task is ' + \
    'supposed to be outputting to a stream and if so, ensure that one of the output arguments in the tool configuration file has instructions ' + \
    'on how to be handled if the output is a stream.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool is marked as outputting to a stream, but no task in the pipeline is 
  # marked as accepting a stream.
  def noStreamInstructions(self, task, tool, inputTask, inputTool):
    self.text.append('Error with streaming files.')
    self.text.append('The task \'' + task + '\', using the tool \'' + tool + '\' is marked as outputting to a stream in the \'pipeline ' + \
    'tasks\' section of the configuration file and the task \'' + inputTask + '\', using the tool \'' + inputTool + '\' accepts the stream as ' + \
    'input. There are no input arguments for the \'' + inputTask + '\' task that have instructions on how to use a stream as input. Please check ' + \
    'that the correct task is marked as accepting a stream, and ensure that an input argument in it\'s tool configuration file has instructions ' + \
    'on how to modify the argument to handle a streaming input.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a tool is marked as outputting to a stream, but no task in the pipeline is 
  # marked as accepting a stream.
  def noNodeAcceptingStream(self, task, tool):
    self.text.append('Error with streaming files.')
    self.text.append('The task \'' + task + '\', using the tool \'' + tool + '\' is marked as outputting to a stream in the \'pipeline ' + \
    'tasks\' section of the configuration file, but no tasks are marked as accepting a stream. Since a task is outputting to a stream, ' + \
    'another task (by convention, the next task in the list) must be able to accept the stream as input. This is achieved by including the ' + \
    '\'"input is stream" : true\' field in the \'pipeline tasks\' section for the task that will accept a streaming input. Please ensure that ' + \
    'this is the case.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

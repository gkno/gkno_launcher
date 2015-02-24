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
    self.text.append('Error processing configuration file: ' + name + '.json.')
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

  # If two tasks have been given the same name.
  def repeatedTaskName(self, pipeline, task):
    self.text.append('Repeated task name in pipeline: ' + pipeline + '.')
    self.text.append('Each task in the pipeline is defined in the \'pipeline tasks\' section of the pipeline configuration file. Each task name must be ' + \
    'unique so that there is no ambiguity about how to construct the pipeline graph, however, multiple tasks in this section have been given the name \'' + \
    task + '\'. Please ensure that all task names in the pipeline configuration file are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a configuration file contains has repeated definitions of the same long form argument.
  def repeatedLongFormArgument(self, nodeID, longFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. This argument has already been defined in the configuration file. Please ensure that all ' + \
    'arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a configuration file contains has repeated definitions of the same short form argument.
  def repeatedShortFormArgument(self, nodeID, longFormArgument, shortFormArgument):
    self.text.append('Repeated argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'short form argument \'' + shortFormArgument + '\' associated with the long form argument \'' + longFormArgument + '\'. This argument has ' + \
    'already been defined in the configuration file. Please ensure that all arguments are unique.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a long form argument is defined with no short form.
  def noShortFormArgument(self, nodeID, longFormArgument):
    self.text.append('No defined short form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
    'long form argument \'' + longFormArgument + '\'. There is no short form argument associated with this, however. Please ensure that all ' + \
    'nodes in the configuration file defining arguments contain both a short and long form version of the argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a short form argument is defined with no long form.
  def noLongFormArgument(self, nodeID, shortFormArgument):
    self.text.append('No defined long form argument in the pipeline configuration file.')
    self.text.append('The pipeline configuration file contains a definition for a graph node with ID \'' + nodeID + '\' which defines the ' + \
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
  def nodeIDIsTaskID(self, name, node, id):
    self.text.append('Node ID conflicts with a task ID.')
    self.text.append('The configuration file for the \'' + name + '\' pipeline contains a node in the \'' + node + '\' section with the ' + \
    'id \'' + id + '\'. This is also the name of a task in the pipeline. All the task names and node ids within a single configuration ' + \
    'file must be unique. Please amend the configuration file to make sure that all of the ids are unique.')
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
    address + '\', but this address does not point to a valid node in the pipeline. Please ensure that the node address is correct.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  ##########################################
  ## Errors in the unique or shared nodes ##
  ##########################################

  # A supplied task is not valid.
  def invalidTaskInNode(self, pipeline, nodeType, nodeID, task, tasks):
    self.text.append('Invalid task in configuration file node.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeID + '\' in the \'' + \
    nodeType + ' graph nodes\' secion. Within this node, the task \'' + task + '\' is used, but this task has not been defined in the ' + \
    '\'pipeline tasks\' section of the configuration file and consequently is not valid. Please check that all tasks in the configuration ' + \
    'file are valid for the pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # A configuration file node contains a tool argument that is not valid.
  def invalidToolArgument(self, pipeline, nodeType, nodeID, task, tool, argument):
    self.text.append('Invalid tool argument.')
    self.text.append('The configuration file for the \'' + pipeline + '\' pipeline contains a node with id \'' + nodeID + '\' in the \'' + \
    nodeType + ' graph nodes\' section. Within this node, the task \'' + task + '\' which uses the tool \'' + tool + '\' is associated ' + \
    'with the argument \'' + argument + '\', but this argument is not valid for the tool. Please check that all of the tool arguments ' + \
    'in the pipeline configuration file are valid for the tools they are linked to.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If a node has a non-unique id.
  def repeatedNodeID(self, node, helpInfo):
    self.text.append('Repeated pipeline node ID.')
    self.text.append('The configuration file for the pipeline \'' + helpInfo[0] + '\' contains at least two nodes in the \'' + helpInfo[1] + \
    '\' section with the same ID (' + helpInfo[2] + '). All nodes must have unique IDs in order to construct the pipeline graph. Please ' + \
    'ensure that all nodes defined in the configuration file are unique')
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

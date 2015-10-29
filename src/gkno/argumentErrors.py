#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors as errors

import os
import sys

class argumentErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors.errors()

    # The error messages are stored in the following list.
    self.text = []

    # Different segments of gkno produce different error codes. The list of which
    # values correspond to which aspect of the code are held in the adminErrors.

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '9'

  # If arguments are to be imported from a tool, but the tool is not available,
  def invalidImportTool(self, task):
    self.text.append('Unable to import arguments.')
    self.text.append('The pipeline configuration file includes the field \'import arguments\', which identifies a task from which to import ' + \
    'arguments. Note that this task must be the address of a task in the pipeline, and this task could point to a tool or another pipeline. If ' + \
    'the task points to a pipeline, the arguments for that pipeline will be imported, otherwise the arguments from a tool will be imported. If ' + \
    'successful, the arguments from this tool/pipeilne will be available on the command line.')
    self.text.append('\tThe tool identified \'' + task + '\' is not available as part of this pipeline. Please check the configuration file and ' + \
    'replace the tool name with a tool available in the pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If the long and short form version of a tool argument conflict with arguments for the pipeline,
  # this is likely because the tool whose arguments are being imported has a standard argument that 
  # is also defined at the pipeline level (e.g. an  argument such as --region, -rg is standardised
  # across all tools using a region). The resolution to this is to either link the pipeline argument
  # to the relevant node in the graph, or create a unique node in the pipeline that can be addressed
  # with a new argument.
  def importedArgumentIsDefined(self, task, tool, pipeline, longFormArgument, shortFormArgument):
    self.text.append('Imported tool argument conflicts with a pipeline argument.')
    self.text.append('Arguments for the task \'' + task + '\' using tool \'' + tool + '\' are being imported to be available on the command ' + \
    'line for the pipeline \'' + pipeline + '\'. The tool and pipeline share the argument \'' + longFormArgument + ' (' + shortFormArgument + \
    ')\'. It is likely that if these arguments are shared, they perform the same function. In order to operate, this conflict must be ' + \
    'resolved by one of the following steps:')
    self.text.append('\t')
    self.text.append('1. Identify the pipeline argument in the configuration file and the configuration file node that the argument sets. ' + \
    'Ensure that this node is a shared node, and then include the argument from the tool being imported as sharing this pipeline argument.')
    self.text.append('\t')
    self.text.append('2. If the value for the tool is not shared with other tasks in the pipeline, create a unique node in the pipeline ' + \
    'configuration file and identify a new (unique) argument for this node. This node can then be identified with the tool argument.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The long form of an argument being imported from a tool conflicts with a pipeline argument.
  def importedArgumentLongFormConflict(self, task, tool, pipeline, argument):
    self.text.append('Imported tool argument conflicts with a pipeline argument.')
    self.text.append('Arguments for the task \'' + task + '\' using tool \'' + tool + '\' are being imported to be available on the command ' + \
    'line for the pipeline \'' + pipeline + '\'. Both the pipeline and the tool have an argument with the long form \'' + argument + '\'. In ' + \
    'order to avoid ambiguity, all arguments (both long and short form versions) must be unique. Please modify the argument in the pipeline ' + \
    'configuration, to ensure that there are no conflicts with the imported tool arguments.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # The short form of an argument being imported from a tool conflicts with a pipeline argument.
  def importedArgumentShortFormConflict(self, task, tool, pipeline, argument, shortFormArgument, pipelineArgument):
    self.text.append('Imported tool argument conflicts with a pipeline argument.')
    self.text.append('Arguments for the task \'' + task + '\' using tool \'' + tool + '\' are being imported to be available on the command ' + \
    'line for the pipeline \'' + pipeline + '\'. The tool has an argument \'' + argument + '\' with the short form \'' + shortFormArgument + \
    '\'. The pipeline argument \'' + pipelineArgument + '\' shares this short form. In order to avoid ambiguity, all arguments (both long ' + \
    'and short form versions) must be unique. Please modify the argument in the pipeline configuration, to ensure that there are no conflicts ' + \
    'with the imported tool arguments.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

  # If an argument has the same name as a task.
  def argumentIsTask(self, argument):
    self.text.append('Imported tool argument conflicts with a pipeline task.')
    self.text.append('No arguments for the pipeline may share a name with a pipeline task. The imported argument \'' + argument + '\' is, ' + \
    'however, the name of a pipeline task. Please change the name of the pipeline task or the argument to remove this conflict')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

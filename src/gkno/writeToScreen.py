#!/usr/bin/python

from __future__ import print_function

import gknoErrors
from gknoErrors import *

import inspect
from inspect import currentframe, getframeinfo
import os
import sys

class writeToScreen:
  def __init__(self):
    self.errors = gknoErrors()

  # For most of the usage requests, the version number and date are printed out
  # at the start of the message.  Print these here.
  def printHeader(self, version, date, gknoCommitID):
    print(file = sys.stdout)
    commitLength = len(gknoCommitID) + 14
    length       = max(commitLength, 29)
    print('=' * length, file = sys.stdout)
    print('  Boston College gkno package', file = sys.stdout)
    print(file = sys.stdout)
    print('  version:    ', version, sep = '', file = sys.stdout)
    print('  date:       ', date, sep = '', file = sys.stdout)
    print('  git commit: ', gknoCommitID, sep = '', file = sys.stdout)
    print('=' * length, file = sys.stdout)
    print(file = sys.stdout)
  
  def beginToolConfigurationFileCheck(self):
    print('Checking tool configuration files...', file = sys.stdout)
    sys.stdout.flush()
  
  def writeToolConfigurationFile(self, filename):
    print('     ', filename, '...', sep = '', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeDone(self):
    print('done.', file = sys.stdout)
    sys.stdout.flush()
  
  def writeBlankLine(self):
    print(file = sys.stdout)
    sys.stdout.flush()
  
  def checkPipelineConfigurationFile(self, filename):
    print('Checking pipeline configuration file...', end = '', file = sys.stdout) 
    sys.stdout.flush()
  
  def writeReadingCommandLineArguments(self):
    print('Reading in command line arguments...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writePipelineWorkflow(self, graph, config, gknoHelp):
    print(file = sys.stdout)

    # Determine the length of the longest tool name.
    length  = 0
    for task in config.pipeline.workflow:
      tool   = graph.node[task]['attributes'].tool
      text   = task + ' (' + tool + '):'
      length = len(text) if len(text) > length else length
    length += 5
  
    print('Workflow:', sep = '', file = sys.stdout)
    sys.stdout.flush()
    for task in config.pipeline.workflow:
      tool        = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      text        = task + ' (' + tool + '):'
      description = config.nodeMethods.getGraphNodeAttribute(graph, task, 'description')
      gknoHelp.writeFormattedText(text, description, length, 1, '')
    print(file = sys.stdout)
  
  def writeCheckingLists(self):
    print('Checking for lists of argument values...', end = '', file = sys.stdout)
    sys.stdout.flush()

  def writeAssignPipelineArgumentsToNodes(self):
    print('Assigning command line arguments to graph nodes...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeAssignLoopArguments(self, hasMultipleRuns):
    if hasMultipleRuns: print('Assigning multiple runs information to graph nodes...', end = '', file = sys.stdout)
    else: print('Assigning internal loop information to graph nodes...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeCheckingParameterSetInformation(self):
    print('Checking parameter set information...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeCheckingEvaluateCommands(self):
    print('Checking for commands to execute at command line...', end = '', file = sys.stdout)
    sys.stdout.flush()

  def writeTracking(self, ID):
    print("Logging gkno usage with ID: ", ID, "...", sep = '', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeExecuting(self, filename):
    print('Executing makefile: ', filename, '...', sep = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeComplete(self, success):
    if success != 0:
      print('.failed', file = sys.stdout)
      print('\ngkno failed to complete successfully.  Please check the output files to identify the cause of the problem.', file = sys.stderr)
      self.errors.terminate()
      sys.stdout.flush()

  # Write debugging text.
  def writeDebug(self, text):
    frameInfo = getframeinfo(currentframe().f_back)
    print('\tdebugging - ', frameInfo.filename, ' line ', frameInfo.lineno, ': ', text, sep = '', file = sys.stdout)
    sys.stdout.flush()

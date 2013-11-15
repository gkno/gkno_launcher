#!/usr/bin/python

from __future__ import print_function

import nodeAttributes
from nodeAttributes import *

import os
import sys

class writeToScreen:
  # For most of the usage requests, the version number and date are printed out
  # at the start of the message.  Print these here.
  def printHeader(self, version, date):
    print(file = sys.stdout)
    print('===============================', file = sys.stdout)
    print('  Boston College gkno package', file = sys.stdout)
    print(file = sys.stdout)
    print('  version: ', version, sep = '', file = sys.stdout)
    print('  date:    ', date, sep = '', file = sys.stdout)
    print('===============================', file = sys.stdout)
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
  
  def writePipelineWorkflow(self, graph, config, workflow, gknoHelp):
  
    # Determine the length of the longest tool name.
    length  = 0
    for task in workflow:
      tool   = graph.node[task]['attributes'].tool
      text   = task + ' (' + tool + '):'
      length = len(text) if len(text) > length else length
    length += 5
  
    print('Workflow:', sep = '', file = sys.stdout)
    sys.stdout.flush()
    for task in workflow:
      tool        = config.nodeMethods.getGraphNodeAttribute(graph, task, 'tool')
      text        = task + ' (' + tool + '):'
      description = config.nodeMethods.getGraphNodeAttribute(graph, task, 'description')
      gknoHelp.writeFormattedText(text, description, length, 1, '')
    print(file = sys.stdout)
  
  def writeAssignPipelineArgumentsToNodes(self):
    print('Assigning command line arguments to graph nodes...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeAssignLoopArguments(self, hasMultipleRuns):
    if hasMultipleRuns: print('Assigning multiple runs information to graph nodes...', end = '', file = sys.stdout)
    else: print('Assigning internal loop information to graph nodes...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeCheckingInstanceInformation(self):
    print('Checking instance information...', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeTracking(self, ID):
    print("Logging gkno usage with ID: ", ID, "...", sep = '', end = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeExecuting(self, filename):
    print('Executing makefile: ', filename, sep = '', file = sys.stdout)
    sys.stdout.flush()
  
  def writeComplete(self, success):
    if success == 0:print("\ngkno completed tasks successfully.", file = sys.stdout)
    else: print("\ngkno failed to complete successfully.  Check operation and repair.", file = sys.stderr)
    sys.stdout.flush()

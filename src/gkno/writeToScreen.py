#!/usr/bin/python

from __future__ import print_function
import os
import sys

def beginToolConfigurationFileCheck():
  print('Checking tool configuration files...', file = sys.stdout)
  sys.stdout.flush()

def writeToolConfigurationFile(filename):
  print('     ', filename, '...', sep = '', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeDone():
  print('done.', file = sys.stdout)
  sys.stdout.flush()

def writeBlankLine():
  print(file = sys.stdout)
  sys.stdout.flush()

def checkPipelineConfigurationFile(filename):
  print('Checking pipeline configuration file...', end = '', file = sys.stdout) 
  sys.stdout.flush()

def gettingCommandLineArguments():
  print('Reading in command line arguments...', end = '', file = sys.stdout)
  sys.stdout.flush()

def writePipelineWorkflow(workflow, taskToTool, availableTools, descriptions, gknoHelp):

  # Determine the length of the longest tool name.
  length  = 0
  for task in workflow:
    tool   = taskToTool[task]
    text   = task + ' (' + tool + '):'
    length = len(text) if len(text) > length else length
  length += 5

  print('Workflow:', sep = '', file = sys.stdout)
  sys.stdout.flush()
  for task in workflow:
    tool        = taskToTool[task]
    text        = task + ' (' + tool + '):'
    description = descriptions[tool]
    gknoHelp.writeFormattedText(text, description, length, 1, '')
  print(file = sys.stdout)

def writeAssignPipelineArgumentsToTasks():
  print('Assigning command line arguments to tasks...', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeParseCommandLineArguments():
  print('Checking the command line arguments...', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeCheckingInstanceInformation():
  print('Checking instance information...', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeCheckingMultipleRunsInformation():
  print('Checking multiple runs information...', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeTracking(ID):
  print("Logging gkno usage with ID: ", ID, "...", sep = '', end = '', file = sys.stdout)
  sys.stdout.flush()

def writeExecuting(filename):
  print('Executing makefile: ', filename, sep = '', file = sys.stdout)
  sys.stdout.flush()

def writeComplete(success):
  if success == 0:print("\ngkno completed tasks successfully.", file = sys.stdout)
  else: print("\ngkno failed to complete successfully.  Check operation and repair.", file = sys.stderr)
  sys.stdout.flush()

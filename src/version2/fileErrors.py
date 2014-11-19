#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class fileErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # Admin errors generate an error code of '2'.
    # Command line errors generate an error code of '3'.
    # File handling errors generate an error code of '4'.
    # General configuration file errors generate an error code of '5'.
    # Tool configuration file errors generate an error code of '6'.
    # Pipeline configuration file errors generate an error code of '7'.
    # Errors associated with the graph construction generate an error code of '8'.
    self.errorCode = '4'

  # If a tool is added, but the tool is already available.
  def invalidPipelineName(self, tools, pipelines, pipeline):
    self.text.append('Invalid pipeline.')
    self.text.append('The requested pipeline is not recognised. The command line must have the syntax \'gkno <pipeline>\' where the \'pipeline\' ' + \
    'is the name of a pipeline or a tool. The requested pipeline \'' + pipeline + '\' is neither a pipeline or a tool. Please check the command ' + \
    'line or request help (\'gkno --help\') to identify the required pipeline.')
    if tools:
      self.text.append('\t')
      self.text.append('The following tools (single task pipelines) have similar names to that requested:')
      for task in tools: self.text.append('\t' + task)
    if pipelines:
      self.text.append('\t')
      self.text.append('The following pipelines have similar names to that requested:')
      for task in pipelines: self.text.append('\t' + task)
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

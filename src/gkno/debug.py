#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import configurationClass.configurationClass
from configurationClass.configurationClass import *

import gknoErrors
from gknoErrors import *

import json
import os
import sys

class debug:
  def __init__(self):

    # Errors class.
    self.errors = gknoErrors()

  # Print out all nodes.
  def writeNodes(self, graph, config):
    for task in config.pipeline.workflow:
      print(task)

      # Print out all options.
      print('\tOPTIONS')
      for nodeID in config.nodeMethods.getPredecessorOptionNodes(graph, task):
        argument = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
        values   = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        print('\t\t', nodeID, ' ', argument, ' ', values, sep = '')

      # Print out all input files.
      print('\tINPUT FILES')
      for nodeID in config.nodeMethods.getPredecessorFileNodes(graph, task):
        argument   = config.edgeMethods.getEdgeAttribute(graph, nodeID, task, 'longFormArgument')
        values     = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        extensions = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions')
        print('\t\t', nodeID, ' ', argument, ' ', values, ' ', extensions, sep = '')

      # Print out all output files.
      print('\tOUTPUT FILES')
      for nodeID in config.nodeMethods.getSuccessorFileNodes(graph, task):
        argument   = config.edgeMethods.getEdgeAttribute(graph, task, nodeID, 'longFormArgument')
        values     = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'values')
        extensions = config.nodeMethods.getGraphNodeAttribute(graph, nodeID, 'allowedExtensions')
        print('\t\t', nodeID, ' ', argument, ' ', values, ' ', extensions, sep = '')

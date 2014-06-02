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

class constructFilenames:
  def __init__(self):

    # Errors class.
    self.errors = gknoErrors()

  # Check if a tool argument can be constructed from a differenr tool argument.
  def canToolArgumentBeConstructed(self, graph, config, tool, argument):
    if config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions'):
      if config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')['method'] == 'from tool argument':
        longFormArgument  = config.tools.getArgumentAttribute(tool, argument, 'constructionInstructions')['use argument']
        shortFormArgument = config.tools.getArgumentAttribute(tool, longFormArgument, 'shortFormArgument')
        return longFormArgument, shortFormArgument

    # If no argument were found, return nothing.
    return None, None

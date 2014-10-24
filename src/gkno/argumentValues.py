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

class argumentValues:
  def __init__(self):

    # Errors class.
    self.errors = gknoErrors()

  # Check if any arguments have instructions on how to modify argument values before
  # writing them to the command line.
  def modifyArgumentValues(self, config, tool, argument, values):

    # Check if instructions exist.
    instructions = config.tools.getArgumentAttribute(tool, argument, 'modifyValues')
    if instructions:

      # Check if the instructions are only applied to certain extensions.
      if 'extensions' in instructions:
        modifiedValues = []
        for value in values:
          valueUpdated = False
          for extension in instructions['extensions']:
            if value.endswith(extension):
              modifiedValues.append(str(instructions['command'].replace('VALUE', value)))
              valueUpdated = True
              break

          # If the value did not get modified, add the unmodified value to the list.
          if not valueUpdated: modifiedValues.append(value)

      # Return the updated values.
      return modifiedValues

    # If there are no instructions, return the original values.
    else: return values

  # Modify the list of values to produce a comma separated list.
  def produceCommaSeparatedList(self, values):
    output = str(values[0])

    # Loop over the list.
    for value in values[1:]: output = output + str(',') + str(value)

    # Return the string of comma separated values as a list.
    return [output]

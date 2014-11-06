#!/bin/bash/python

from __future__ import print_function

import json
import os
import sys

# Define a class to handle parameter sets.
class parameterSets:
  def __init__(self):
    pass

  # Check the parameter set information from a configuration file.
  @staticmethod
  def checkConfiguration(data):

    # Define the allowed attributes.
    allowedAttributes                = {}
    allowedAttributes['argument']    = (str, True)
    allowedAttributes['description'] = (str, True)
    allowedAttributes['data']        = (list, True)

    # Loop over all of the defined parameter sets.
    for parameterSet in data:
      for attribute in parameterSet:
        print('TEST', attribute)
    exit(0)

#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors
from errors import *

import os
import sys

class parameterSetErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '14'

  # If a parameter set includes an invalid node ID.
  def invalidNodeInPipelineParameterSet(self, pipeline, pSet, nodeID, ID):
    self.text.append('Invalid node ID in parameter set.')
    self.text.append('The configuration file for pipeline \'' + pipeline + '\' contains information for the parameter set with the ID \'' + pSet + \
    '\'. Within this set, the data with the ID \'' + ID + '\' contains the node ID \'' + nodeID + '\', which is not a valid node ID in the pipeline. ' + \
    'Please ensure that all parameter set data points to a valid node within this pipeline, or has the correct address to point to a node in a ' + \
    'contained pipeline.')
    self.errors.writeFormattedText(self.text, errorType = 'error')
    self.errors.terminate(self.errorCode)

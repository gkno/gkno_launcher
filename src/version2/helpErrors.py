#!/usr/bin/python

from __future__ import print_function

import inspect
from inspect import currentframe, getframeinfo

import errors as err

import os
import sys

class helpErrors:

  # Initialise.
  def __init__(self):

    # Get general error writing and termination methods.
    self.errors = err.errors()

    # The error messages are stored in the following list.
    self.text = []

    # For a list of all error code values, see adminErrors.py.
    self.errorCode = '11'

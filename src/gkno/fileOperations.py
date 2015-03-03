#!/bin/bash/python

from __future__ import print_function
from copy import deepcopy

import json
import os
import sys

# Check if a file exists.
def checkIfFileExists(filename):
  return os.path.isfile(filename)

# Open a configuration file and return the contents.
def readConfigurationFile(filename, allowTermination = True):
  try: jsonData = open(filename)
  except:
    # TODO ERROR
    if allowTermination: print('ERROR - failed to open json file - ' + str(filename)); exit(0)
    else: return False

  try: data = json.load(jsonData)
  except:
    if allowTermination:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      print('ERROR - failed to extract json information - ' + str(filename))
      print(exc_type, exc_value, exc_traceback)
      exit(0)
    else: return False

  return data

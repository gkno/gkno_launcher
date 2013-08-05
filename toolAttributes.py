#!/bin/bash/python

from __future__ import print_function
import networkx as nx
from copy import deepcopy

import json
import os
import sys

class toolAttributes:
  def __init__(self):
      self.jsonExists = False
      self.jsonError  = ''

  # Open a configuration file and store the contents of the file in the
  # configuration dictionary.
  def readConfiguration(self, filename):
    try: jsonData = open(filename)
    except: return False
    self.jsonExists = True

    try: self.configuration = json.load(jsonData)
    except:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.jsonError = exc_value
      return False

    return True

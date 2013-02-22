#!/usr/bin/python

from __future__ import print_function
import os
import sys

import subprocess
from subprocess import PIPE

# Ping the website with usage information.
def phoneHome(sourcePath, ID):
  executable = sourcePath + '/src/gkno/ga.sh'
  subprocess.call([executable, ID], stdout=PIPE, stderr=PIPE)
